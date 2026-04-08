from __future__ import annotations

import argparse
import asyncio
import json
import logging
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .context_pack import (
    build_context_pack as _build_context_pack_impl,
    feature_mandatory_docs,
    load_context_document,
    mandatory_doc_paths,
)
from .lightrag_runtime import (
    _load_lightrag_runtime,
    _tighten_entity_extraction_prompts,
    build_query_param,
    create_rag,
    validate_index_artifacts,
)
from .markdown_chunks import (
    build_prepared_chunks,
    chunk_markdown,
    detect_language,
    doc_class_for_path,
    ensure_debug_dirs,
    extract_title,
    feature_id_for_path,
    parse_markdown_sections,
    read_repo_text,
    serialize_chunk_for_rag,
    split_large_section,
    collapse_small_sections,
    write_debug_exports,
)
from .pilot_config import (
    BASE_PILOT_CORPUS,
    FEATURE_OWNERSHIP_CANONICAL_DOCS,
    FEATURE_TASK_FILES,
    LIGHTRAG_ENTITY_EXTRACT_MAX_GLEANING,
    LIGHTRAG_MAX_EXTRACT_INPUT_TOKENS,
    LIGHTRAG_MAX_PARALLEL_INSERT,
    MANDATORY_DOCS,
    MAX_CHUNK_CHARS,
    MIN_SECTION_CHARS,
    OLLAMA_EMBED_MODEL,
    OLLAMA_HOST,
    OLLAMA_LLM_MAX_ASYNC,
    OLLAMA_LLM_MODEL,
    OLLAMA_LLM_NUM_PREDICT,
    OLLAMA_LLM_TIMEOUT_SECONDS,
    PATH_RE,
    PILOT_CORPUS,
    POLICY_CANONICAL_DOCS,
    PR_LOOP_CANONICAL_DOCS,
    PR_LOOP_COMPLETION_CANONICAL_DOCS,
    READ_ORDER_CANONICAL_DOCS,
    SETUP_CANONICAL_DOCS,
    TASK_TYPE_CHOICES,
    TAXONOMY_CANONICAL_DOCS,
    TRACK_B_CORPUS_ADDITIONS,
    corpus_paths,
    pilot_working_dir,
    relative_repo_path,
    repo_root,
)
from .pilot_types import ContextDocument, ContextPack, MarkdownSection, PreparedChunk
from .query_policy import (
    format_feature_ownership_answer,
    format_implementation_location_answer,
    format_pilot_boundary_answer,
    format_policy_answer,
    format_pr_loop_completion_answer,
    format_pr_loop_contract_answer,
    format_read_order_answer,
    format_setup_answer,
    format_taxonomy_answer,
    is_feature_ownership_question,
    is_implementation_location_question,
    is_local_pilot_setup_question,
    is_mandatory_policy_question,
    is_pilot_boundary_question,
    is_policy_or_taxonomy_question,
    is_pr_loop_completion_question,
    is_pr_loop_contract_question,
    is_read_order_question,
    is_taxonomy_question,
    normalize_query_text,
    normalize_query_tokens,
    policy_bias_paths,
    retrieval_user_prompt,
    shape_raw_retrieval_result,
)
from .reference_resolution import (
    extract_reference_paths,
    fallback_retrieved_paths,
    merge_ranked_paths,
    normalize_reference_candidate,
    resolve_retrieved_paths,
    score_chunk_for_query,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExistingIndexedDoc:
    doc_id: str
    file_path: str
    status: str
    is_duplicate: bool


@dataclass(frozen=True)
class IncrementalRefreshPlan:
    delete_doc_ids: list[str]
    insert_chunks: list[PreparedChunk]
    unchanged_paths: list[str]
    added_paths: list[str]
    updated_paths: list[str]
    removed_paths: list[str]
    duplicate_cleanup_paths: list[str]


def load_doc_status_payload(index_dir: Path) -> dict[str, dict[str, Any]]:
    status_path = index_dir / "kv_store_doc_status.json"
    if not status_path.exists():
        return {}
    payload = json.loads(status_path.read_text(encoding="utf-8"))
    return {
        doc_id: item
        for doc_id, item in payload.items()
        if isinstance(item, dict)
    }


def load_existing_indexed_docs(index_dir: Path) -> list[ExistingIndexedDoc]:
    records: list[ExistingIndexedDoc] = []
    for doc_id, item in load_doc_status_payload(index_dir).items():
        file_path = item.get("file_path")
        if not isinstance(file_path, str) or not file_path:
            continue
        metadata = item.get("metadata", {})
        is_duplicate = (
            doc_id.startswith("dup-")
            or (isinstance(metadata, dict) and metadata.get("is_duplicate") is True)
        )
        records.append(
            ExistingIndexedDoc(
                doc_id=doc_id,
                file_path=file_path,
                status=str(item.get("status", "")),
                is_duplicate=is_duplicate,
            )
        )
    return records


def plan_incremental_refresh(
    chunks: list[PreparedChunk],
    existing_docs: list[ExistingIndexedDoc],
) -> IncrementalRefreshPlan:
    chunks_by_path: dict[str, list[PreparedChunk]] = {}
    for chunk in chunks:
        chunks_by_path.setdefault(chunk.path, []).append(chunk)

    existing_by_path: dict[str, list[ExistingIndexedDoc]] = {}
    for doc in existing_docs:
        existing_by_path.setdefault(doc.file_path, []).append(doc)

    delete_doc_ids: list[str] = []
    insert_chunks: list[PreparedChunk] = []
    unchanged_paths: list[str] = []
    added_paths: list[str] = []
    updated_paths: list[str] = []
    removed_paths: list[str] = []
    duplicate_cleanup_paths: list[str] = []

    all_paths = sorted(set(chunks_by_path) | set(existing_by_path))
    for path in all_paths:
        desired_chunks = chunks_by_path.get(path, [])
        existing_records = existing_by_path.get(path, [])
        primary_records = [record for record in existing_records if not record.is_duplicate]
        duplicate_records = [record for record in existing_records if record.is_duplicate]

        if not desired_chunks:
            if existing_records:
                removed_paths.append(path)
                delete_doc_ids.extend(record.doc_id for record in existing_records)
            continue

        desired_ids = {chunk.chunk_id for chunk in desired_chunks}
        existing_primary_ids = {record.doc_id for record in primary_records}
        primary_statuses = {record.status for record in primary_records}

        if not existing_records:
            added_paths.append(path)
            insert_chunks.extend(desired_chunks)
            continue

        duplicate_only_cleanup = bool(duplicate_records)
        identical_primary_ids = existing_primary_ids == desired_ids
        all_processed = primary_statuses <= {"processed"} if primary_records else False

        if identical_primary_ids and all_processed:
            if duplicate_only_cleanup:
                duplicate_cleanup_paths.append(path)
                delete_doc_ids.extend(record.doc_id for record in duplicate_records)
            unchanged_paths.append(path)
            continue

        updated_paths.append(path)
        delete_doc_ids.extend(record.doc_id for record in existing_records)
        insert_chunks.extend(desired_chunks)

    # Preserve operation order while deduplicating doc ids.
    seen_doc_ids: set[str] = set()
    ordered_delete_doc_ids: list[str] = []
    for doc_id in delete_doc_ids:
        if doc_id not in seen_doc_ids:
            seen_doc_ids.add(doc_id)
            ordered_delete_doc_ids.append(doc_id)

    return IncrementalRefreshPlan(
        delete_doc_ids=ordered_delete_doc_ids,
        insert_chunks=insert_chunks,
        unchanged_paths=sorted(unchanged_paths),
        added_paths=sorted(added_paths),
        updated_paths=sorted(updated_paths),
        removed_paths=sorted(removed_paths),
        duplicate_cleanup_paths=sorted(duplicate_cleanup_paths),
    )


async def build_index(root: Path, clean: bool = False, dry_run: bool = False) -> dict[str, Any]:
    working_dir = pilot_working_dir(root)
    ensure_debug_dirs(working_dir)

    index_dir = working_dir / "index"
    if clean and index_dir.exists():
        shutil.rmtree(index_dir)
        index_dir.mkdir(parents=True, exist_ok=True)

    chunks = build_prepared_chunks(root)
    write_debug_exports(root, chunks)
    existing_docs = load_existing_indexed_docs(index_dir) if index_dir.exists() else []
    refresh_plan = plan_incremental_refresh(chunks, existing_docs) if not clean else IncrementalRefreshPlan(
        delete_doc_ids=[],
        insert_chunks=chunks,
        unchanged_paths=[],
        added_paths=[],
        updated_paths=[],
        removed_paths=[],
        duplicate_cleanup_paths=[],
    )

    result = {
        "pilot_corpus": list(PILOT_CORPUS),
        "working_dir": str(working_dir),
        "index_dir": str(index_dir),
        "chunk_count": len(chunks),
        "chunk_manifest": str(working_dir / "chunks" / "pilot_chunks.json"),
        "effective_clean_rebuild": clean,
        "incremental_refresh": not clean,
        "delete_doc_count": len(refresh_plan.delete_doc_ids),
        "insert_chunk_count": len(refresh_plan.insert_chunks),
        "unchanged_paths": refresh_plan.unchanged_paths,
        "added_paths": refresh_plan.added_paths,
        "updated_paths": refresh_plan.updated_paths,
        "removed_paths": refresh_plan.removed_paths,
        "duplicate_cleanup_paths": refresh_plan.duplicate_cleanup_paths,
    }
    if dry_run:
        return result

    rag = create_rag(index_dir)
    await rag.initialize_storages()
    try:
        for doc_id in refresh_plan.delete_doc_ids:
            await rag.adelete_by_doc_id(doc_id)
        if refresh_plan.insert_chunks:
            await rag.ainsert(
                input=[serialize_chunk_for_rag(chunk) for chunk in refresh_plan.insert_chunks],
                ids=[chunk.chunk_id for chunk in refresh_plan.insert_chunks],
                file_paths=[chunk.path for chunk in refresh_plan.insert_chunks],
            )
    finally:
        await rag.finalize_storages()

    validate_index_artifacts(index_dir)

    return result


async def query_index(
    root: Path,
    query: str,
    mode: str = "hybrid",
    include_references: bool = True,
) -> Any:
    index_dir = pilot_working_dir(root) / "index"
    if not index_dir.exists():
        raise RuntimeError("Pilot index directory does not exist. Run `build` first.")

    _, QueryParam, _, _, _, _ = _load_lightrag_runtime()
    rag = create_rag(index_dir)
    await rag.initialize_storages()
    try:
        raw_result = await rag.aquery(
            query,
            param=build_query_param(
                query,
                mode=mode,
                include_references=include_references,
                query_param_factory=QueryParam,
            ),
        )
        chunks = build_prepared_chunks(root)
        mandatory_paths: list[str] = []
        retrieved_paths = resolve_retrieved_paths(
            root,
            query,
            raw_result=raw_result,
            task_type="general",
            chunks=chunks,
            mandatory_paths=mandatory_paths,
        )
        return shape_raw_retrieval_result(
            raw_result,
            question=query,
            task_type="general",
            mandatory_paths=mandatory_paths,
            retrieved_paths=retrieved_paths,
        )
    finally:
        await rag.finalize_storages()


async def build_context_pack(
    root: Path,
    question: str,
    mode: str = "hybrid",
    active_feature_id: str | None = None,
    task_type: str = "general",
    retrieved_doc_limit: int = 4,
    query_runner: Any | None = None,
) -> ContextPack:
    runner = query_runner or query_index
    return await _build_context_pack_impl(
        root,
        question,
        mode=mode,
        active_feature_id=active_feature_id,
        task_type=task_type,
        retrieved_doc_limit=retrieved_doc_limit,
        query_runner=runner,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LightRAG repository-memory pilot")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build or refresh the pilot index")
    build_parser.add_argument("--clean", action="store_true", help="Delete the current pilot index first")
    build_parser.add_argument("--dry-run", action="store_true", help="Prepare chunks without inserting into LightRAG")

    query_parser = subparsers.add_parser("query", help="Query the pilot index")
    query_parser.add_argument("question", help="Question to send to the pilot index")
    query_parser.add_argument("--mode", default="hybrid", choices=["local", "global", "hybrid", "naive", "mix", "bypass"])

    context_pack_parser = subparsers.add_parser(
        "context-pack",
        help="Build a policy-driven context pack from retrieval results",
    )
    context_pack_parser.add_argument("question", help="Question to send to the pilot index")
    context_pack_parser.add_argument("--mode", default="hybrid", choices=["local", "global", "hybrid", "naive", "mix", "bypass"])
    context_pack_parser.add_argument("--feature-id", default=None, help="Optional active feature id for feature-scoped mandatory docs")
    context_pack_parser.add_argument("--task-type", default="general", choices=TASK_TYPE_CHOICES)
    context_pack_parser.add_argument("--retrieved-doc-limit", type=int, default=4)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = repo_root()

    if args.command == "build":
        result = asyncio.run(build_index(root, clean=args.clean, dry_run=args.dry_run))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    if args.command == "query":
        result = asyncio.run(query_index(root, args.question, mode=args.mode))
        if isinstance(result, str):
            print(result)
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    if args.command == "context-pack":
        result = asyncio.run(
            build_context_pack(
                root,
                args.question,
                mode=args.mode,
                active_feature_id=args.feature_id,
                task_type=args.task_type,
                retrieved_doc_limit=args.retrieved_doc_limit,
            )
        )
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
        return 0

    raise RuntimeError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
