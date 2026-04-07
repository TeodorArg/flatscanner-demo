from __future__ import annotations

from pathlib import Path
from typing import Any

from .markdown_chunks import (
    build_prepared_chunks,
    doc_class_for_path,
    extract_title,
    read_repo_text,
)
from .pilot_config import FEATURE_TASK_FILES, MANDATORY_DOCS, TASK_TYPE_CHOICES
from .pilot_types import ContextDocument, ContextPack
from .query_policy import (
    is_pilot_boundary_question,
    policy_bias_paths,
    shape_raw_retrieval_result,
)
from .reference_resolution import merge_ranked_paths, resolve_retrieved_paths


def feature_mandatory_docs(feature_id: str) -> list[str]:
    return [f"specs/{feature_id}/{name}" for name in FEATURE_TASK_FILES]


def mandatory_doc_paths(
    root: Path,
    active_feature_id: str | None = None,
    task_type: str = "general",
) -> list[str]:
    paths: list[str] = sorted(MANDATORY_DOCS)

    if active_feature_id:
        paths.extend(feature_mandatory_docs(active_feature_id))

    if task_type in {"product-code", "review"}:
        paths.append("docs/ai-pr-workflow.md")
    if task_type == "product-framing":
        paths.append("docs/project-idea.md")
    if task_type == "frontend":
        paths.extend(
            [
                "docs/ai-pr-workflow.md",
                "docs/project/frontend/frontend-docs.md",
            ]
        )
    if task_type == "backend":
        paths.extend(
            [
                "docs/ai-pr-workflow.md",
                "docs/project/backend/backend-docs.md",
            ]
        )

    seen: set[str] = set()
    existing_paths: list[str] = []
    for relative_path in paths:
        if relative_path in seen:
            continue
        if not (root / relative_path).exists():
            continue
        seen.add(relative_path)
        existing_paths.append(relative_path)
    return existing_paths


def load_context_document(root: Path, relative_path: str, source: str, reason: str) -> ContextDocument:
    content = read_repo_text(root, relative_path)
    return ContextDocument(
        path=relative_path,
        doc_class=doc_class_for_path(relative_path),
        title=extract_title(relative_path, content),
        source=source,
        reason=reason,
        content=content,
    )


async def build_context_pack(
    root: Path,
    question: str,
    mode: str = "hybrid",
    active_feature_id: str | None = None,
    task_type: str = "general",
    retrieved_doc_limit: int = 4,
    query_runner: Any | None = None,
) -> ContextPack:
    if task_type not in TASK_TYPE_CHOICES:
        raise ValueError(f"Unsupported task type: {task_type}")

    if query_runner is None:
        from .lightrag_pilot import query_index as query_runner

    raw_result = await query_runner(root, question, mode=mode, include_references=True)
    chunks = build_prepared_chunks(root)
    mandatory_paths = mandatory_doc_paths(root, active_feature_id=active_feature_id, task_type=task_type)
    retrieved_paths = resolve_retrieved_paths(
        root,
        question,
        raw_result=raw_result,
        task_type=task_type,
        chunks=chunks,
        mandatory_paths=mandatory_paths,
        retrieved_doc_limit=retrieved_doc_limit,
    )
    if is_pilot_boundary_question(question):
        retrieved_paths = merge_ranked_paths(
            policy_bias_paths(root, question, task_type=task_type),
            retrieved_paths,
            exclude_paths=set(mandatory_paths),
            limit=retrieved_doc_limit,
        )
    shaped_raw_result = shape_raw_retrieval_result(
        raw_result,
        question=question,
        task_type=task_type,
        mandatory_paths=mandatory_paths,
        retrieved_paths=retrieved_paths,
    )

    mandatory_documents = [
        load_context_document(
            root,
            relative_path,
            source="mandatory",
            reason="Injected by repository context policy.",
        )
        for relative_path in mandatory_paths
    ]
    retrieved_documents = [
        load_context_document(
            root,
            relative_path,
            source="retrieved",
            reason=f"Retrieved for question using {mode} mode.",
        )
        for relative_path in retrieved_paths
    ]

    final_documents = mandatory_documents + [
        document
        for document in retrieved_documents
        if document.path not in {mandatory.path for mandatory in mandatory_documents}
    ]

    return ContextPack(
        question=question,
        mode=mode,
        task_type=task_type,
        active_feature_id=active_feature_id,
        mandatory_documents=mandatory_documents,
        retrieved_documents=retrieved_documents,
        final_documents=final_documents,
        raw_retrieval_result=shaped_raw_result,
    )
