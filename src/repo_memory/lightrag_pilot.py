from __future__ import annotations

import argparse
import asyncio
import json
import re
import shutil
from dataclasses import asdict, dataclass
from functools import partial
from hashlib import sha1
from pathlib import Path
from typing import Any


PILOT_CORPUS = (
    ".specify/memory/constitution.md",
    "AGENTS.md",
    "README_PROCESS_RU.md",
    "PROCESS_OVERVIEW_EN.md",
    "DELIVERY_FLOW_RU.md",
    "docs/README.md",
    "docs/project-idea.md",
)

MANDATORY_DOCS = {
    ".specify/memory/constitution.md",
    "AGENTS.md",
    "docs/README.md",
}

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
MAX_CHUNK_CHARS = 2400
MIN_SECTION_CHARS = 350
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_LLM_MODEL = "qwen3:4b"
OLLAMA_EMBED_MODEL = "nomic-embed-text"


@dataclass(frozen=True)
class PreparedChunk:
    path: str
    doc_class: str
    title: str
    heading_path: list[str]
    language: str
    feature_id: str | None
    chunk_id: str
    chunk_order: int
    mandatory_candidate: bool
    content: str


@dataclass(frozen=True)
class MarkdownSection:
    heading_path: tuple[str, ...]
    content: str


class LocalCharTokenizerBackend:
    def encode(self, content: str) -> list[int]:
        return [ord(char) for char in content]

    def decode(self, tokens: list[int]) -> str:
        return "".join(chr(token) for token in tokens)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def pilot_working_dir(root: Path | None = None) -> Path:
    base = root or repo_root()
    return base / ".lightrag"


def corpus_paths(root: Path | None = None) -> list[Path]:
    base = root or repo_root()
    return [base / rel_path for rel_path in PILOT_CORPUS]


def relative_repo_path(path: Path, root: Path | None = None) -> str:
    base = root or repo_root()
    return path.resolve().relative_to(base.resolve()).as_posix()


def doc_class_for_path(relative_path: str) -> str:
    if relative_path.startswith(".specify/"):
        return "process_memory"
    if relative_path in {
        "AGENTS.md",
        "README_PROCESS_RU.md",
        "PROCESS_OVERVIEW_EN.md",
        "DELIVERY_FLOW_RU.md",
    }:
        return "process_memory"
    if relative_path.startswith("specs/"):
        return "feature_memory"
    if relative_path.startswith("docs/"):
        return "durable_doc"
    return "draft"


def feature_id_for_path(relative_path: str) -> str | None:
    if not relative_path.startswith("specs/"):
        return None
    parts = relative_path.split("/")
    return parts[1] if len(parts) > 1 else None


def detect_language(relative_path: str, content: str) -> str:
    filename = Path(relative_path).name
    if "_RU" in filename:
        return "ru"
    if "_EN" in filename:
        return "en"

    cyrillic_chars = len(re.findall(r"[А-Яа-яЁё]", content))
    latin_chars = len(re.findall(r"[A-Za-z]", content))
    return "ru" if cyrillic_chars > latin_chars else "en"


def extract_title(relative_path: str, content: str) -> str:
    for line in content.splitlines():
        match = HEADING_RE.match(line.strip())
        if match and len(match.group(1)) == 1:
            return match.group(2).strip()
    return Path(relative_path).stem


def common_heading_prefix(paths: list[tuple[str, ...]]) -> list[str]:
    if not paths:
        return []
    prefix = list(paths[0])
    for path in paths[1:]:
        max_prefix = min(len(prefix), len(path))
        cursor = 0
        while cursor < max_prefix and prefix[cursor] == path[cursor]:
            cursor += 1
        prefix = prefix[:cursor]
        if not prefix:
            break
    return prefix


def parse_markdown_sections(content: str) -> list[MarkdownSection]:
    sections: list[MarkdownSection] = []
    heading_stack: list[str] = []
    current_heading_path: tuple[str, ...] | None = None
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer, current_heading_path
        text = "\n".join(buffer).strip()
        if text:
            sections.append(
                MarkdownSection(
                    heading_path=current_heading_path or tuple(),
                    content=text,
                )
            )
        buffer = []

    for raw_line in content.splitlines():
        line = raw_line.rstrip()
        match = HEADING_RE.match(line.strip())
        if match:
            flush()
            level = len(match.group(1))
            heading = match.group(2).strip()
            heading_stack = heading_stack[: level - 1]
            heading_stack.append(heading)
            current_heading_path = tuple(heading_stack)
            buffer = [line]
            continue
        buffer.append(line)

    flush()
    return sections


def split_large_section(section: MarkdownSection, max_chars: int = MAX_CHUNK_CHARS) -> list[MarkdownSection]:
    if len(section.content) <= max_chars:
        return [section]

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", section.content) if part.strip()]
    if len(paragraphs) <= 1:
        return [section]

    split_sections: list[MarkdownSection] = []
    chunk_parts: list[str] = []
    heading_block = paragraphs[0]

    for index, paragraph in enumerate(paragraphs[1:], start=1):
        candidate_parts = chunk_parts + [paragraph]
        candidate_text = "\n\n".join([heading_block] + candidate_parts).strip()
        if chunk_parts and len(candidate_text) > max_chars:
            split_sections.append(
                MarkdownSection(
                    heading_path=section.heading_path,
                    content="\n\n".join([heading_block] + chunk_parts).strip(),
                )
            )
            chunk_parts = [paragraph]
            continue
        chunk_parts = candidate_parts

    if chunk_parts:
        split_sections.append(
            MarkdownSection(
                heading_path=section.heading_path,
                content="\n\n".join([heading_block] + chunk_parts).strip(),
            )
        )

    return split_sections or [section]


def collapse_small_sections(
    sections: list[MarkdownSection],
    min_chars: int = MIN_SECTION_CHARS,
    max_chars: int = MAX_CHUNK_CHARS,
) -> list[MarkdownSection]:
    collapsed: list[MarkdownSection] = []

    for section in sections:
        section_size = len(section.content)
        previous = collapsed[-1] if collapsed else None
        same_heading_depth = previous and previous.heading_path and section.heading_path and (
            len(previous.heading_path) == len(section.heading_path)
        )
        shared_parent = same_heading_depth and (
            previous.heading_path[:-1] == section.heading_path[:-1]
        )
        if (
            previous
            and section_size < min_chars
            and shared_parent
            and len(collapsed[-1].content) + 2 + section_size <= max_chars
        ):
            previous = collapsed.pop()
            merged_paths = [tuple(previous.heading_path), tuple(section.heading_path)]
            collapsed.append(
                MarkdownSection(
                    heading_path=tuple(common_heading_prefix(merged_paths)) or previous.heading_path,
                    content=f"{previous.content}\n\n{section.content}".strip(),
                )
            )
            continue
        collapsed.append(section)

    return collapsed


def chunk_markdown(relative_path: str, content: str) -> list[PreparedChunk]:
    title = extract_title(relative_path, content)
    doc_class = doc_class_for_path(relative_path)
    feature_id = feature_id_for_path(relative_path)
    language = detect_language(relative_path, content)
    mandatory_candidate = relative_path in MANDATORY_DOCS

    sections = parse_markdown_sections(content)
    expanded_sections: list[MarkdownSection] = []
    for section in sections:
        expanded_sections.extend(split_large_section(section))

    final_sections = collapse_small_sections(expanded_sections)
    chunks: list[PreparedChunk] = []

    for index, section in enumerate(final_sections):
        stable_key = f"{relative_path}:{index}"
        digest = sha1(stable_key.encode("utf-8")).hexdigest()[:12]
        chunk_id = f"{Path(relative_path).stem}-{index:03d}-{digest}"
        chunks.append(
            PreparedChunk(
                path=relative_path,
                doc_class=doc_class,
                title=title,
                heading_path=list(section.heading_path),
                language=language,
                feature_id=feature_id,
                chunk_id=chunk_id,
                chunk_order=index,
                mandatory_candidate=mandatory_candidate,
                content=section.content.strip(),
            )
        )

    return chunks


def serialize_chunk_for_rag(chunk: PreparedChunk) -> str:
    heading_path = " > ".join(chunk.heading_path) if chunk.heading_path else "(document preface)"
    metadata_lines = [
        f"Path: {chunk.path}",
        f"Doc Class: {chunk.doc_class}",
        f"Title: {chunk.title}",
        f"Heading Path: {heading_path}",
        f"Language: {chunk.language}",
        f"Feature ID: {chunk.feature_id or 'null'}",
        f"Chunk ID: {chunk.chunk_id}",
        f"Chunk Order: {chunk.chunk_order}",
        f"Mandatory Candidate: {str(chunk.mandatory_candidate).lower()}",
        "",
    ]
    return "\n".join(metadata_lines) + chunk.content


def build_prepared_chunks(root: Path | None = None) -> list[PreparedChunk]:
    base = root or repo_root()
    chunks: list[PreparedChunk] = []
    for path in corpus_paths(base):
        relative_path = relative_repo_path(path, base)
        content = path.read_text(encoding="utf-8")
        chunks.extend(chunk_markdown(relative_path, content))
    return chunks


def ensure_debug_dirs(working_dir: Path) -> None:
    for relative in ("input", "chunks", "index", "logs"):
        (working_dir / relative).mkdir(parents=True, exist_ok=True)


def write_debug_exports(root: Path, chunks: list[PreparedChunk]) -> None:
    working_dir = pilot_working_dir(root)
    ensure_debug_dirs(working_dir)

    corpus_export = {
        "repo_root": str(root),
        "working_dir": str(working_dir),
        "pilot_corpus": list(PILOT_CORPUS),
        "chunk_count": len(chunks),
    }
    (working_dir / "input" / "pilot_corpus.json").write_text(
        json.dumps(corpus_export, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (working_dir / "chunks" / "pilot_chunks.json").write_text(
        json.dumps([asdict(chunk) for chunk in chunks], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def validate_index_artifacts(index_dir: Path) -> None:
    status_path = index_dir / "kv_store_doc_status.json"
    chunks_vdb_path = index_dir / "vdb_chunks.json"

    if not status_path.exists():
        raise RuntimeError("LightRAG did not persist doc status; indexing run is incomplete.")
    if not chunks_vdb_path.exists():
        raise RuntimeError("LightRAG did not create chunk vector storage; indexing run failed.")

    doc_status = json.loads(status_path.read_text(encoding="utf-8"))
    failed_items = [
        item for item in doc_status.values() if isinstance(item, dict) and item.get("status") == "failed"
    ]
    if failed_items:
        sample_paths = sorted(
            {
                item.get("file_path", "unknown")
                for item in failed_items[:5]
                if isinstance(item, dict)
            }
        )
        raise RuntimeError(
            f"LightRAG indexing failed for {len(failed_items)} chunk document(s). "
            f"Sample files: {', '.join(sample_paths)}"
        )


def _load_lightrag_runtime() -> tuple[Any, Any, Any, Any, Any, Any]:
    try:
        from lightrag import LightRAG, QueryParam
        from lightrag.llm.ollama import ollama_embed, ollama_model_complete
        from lightrag.utils import EmbeddingFunc, Tokenizer
    except ImportError as exc:
        raise RuntimeError(
            "LightRAG pilot dependencies are missing. Install them with "
            "`uv sync --extra repo_memory --extra dev`."
        ) from exc
    return (
        LightRAG,
        QueryParam,
        EmbeddingFunc,
        Tokenizer,
        ollama_embed,
        ollama_model_complete,
    )


def create_rag(index_dir: Path) -> Any:
    LightRAG, _, EmbeddingFunc, Tokenizer, ollama_embed, ollama_model_complete = _load_lightrag_runtime()
    embedding_func = EmbeddingFunc(
        embedding_dim=768,
        max_token_size=8192,
        model_name=OLLAMA_EMBED_MODEL,
        func=partial(
            ollama_embed.func,
            embed_model=OLLAMA_EMBED_MODEL,
            host=OLLAMA_HOST,
        ),
    )
    tokenizer = Tokenizer(
        model_name="local-char-tokenizer",
        tokenizer=LocalCharTokenizerBackend(),
    )
    return LightRAG(
        working_dir=str(index_dir),
        llm_model_func=ollama_model_complete,
        llm_model_name=OLLAMA_LLM_MODEL,
        llm_model_kwargs={
            "host": OLLAMA_HOST,
            "options": {"num_ctx": 8192},
            "timeout": 300,
        },
        tokenizer=tokenizer,
        embedding_func=embedding_func,
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

    result = {
        "pilot_corpus": list(PILOT_CORPUS),
        "working_dir": str(working_dir),
        "index_dir": str(index_dir),
        "chunk_count": len(chunks),
        "chunk_manifest": str(working_dir / "chunks" / "pilot_chunks.json"),
    }
    if dry_run:
        return result

    rag = create_rag(index_dir)
    await rag.initialize_storages()
    try:
        await rag.ainsert(
            input=[serialize_chunk_for_rag(chunk) for chunk in chunks],
            ids=[chunk.chunk_id for chunk in chunks],
            file_paths=[chunk.path for chunk in chunks],
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

    _, QueryParam, _, _, _ = _load_lightrag_runtime()
    rag = create_rag(index_dir)
    await rag.initialize_storages()
    try:
        return await rag.aquery(
            query,
            param=QueryParam(mode=mode, include_references=include_references),
        )
    finally:
        await rag.finalize_storages()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LightRAG repository-memory pilot")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build or refresh the pilot index")
    build_parser.add_argument("--clean", action="store_true", help="Delete the current pilot index first")
    build_parser.add_argument("--dry-run", action="store_true", help="Prepare chunks without inserting into LightRAG")

    query_parser = subparsers.add_parser("query", help="Query the pilot index")
    query_parser.add_argument("question", help="Question to send to the pilot index")
    query_parser.add_argument("--mode", default="hybrid", choices=["local", "global", "hybrid", "naive", "mix", "bypass"])

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

    raise RuntimeError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
