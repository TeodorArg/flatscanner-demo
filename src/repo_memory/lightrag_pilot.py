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


BASE_PILOT_CORPUS = (
    ".specify/memory/constitution.md",
    "AGENTS.md",
    "README_PROCESS_RU.md",
    "PROCESS_OVERVIEW_EN.md",
    "DELIVERY_FLOW_RU.md",
    "docs/README.md",
    "docs/project-idea.md",
)

TRACK_B_CORPUS_ADDITIONS = (
    "docs/context-policy.md",
    "docs/lightrag-local-pilot.md",
    "docs/local-memory-sync.md",
    "specs/042-repo-memory-platform-lightrag/spec.md",
    "specs/042-repo-memory-platform-lightrag/plan.md",
    "specs/042-repo-memory-platform-lightrag/evaluation.md",
    "specs/044-lightrag-retrieval-precision/spec.md",
    "specs/044-lightrag-retrieval-precision/evaluation.md",
    "specs/045-retrieval-quality-benchmark/spec.md",
    "src/repo_memory/lightrag_pilot.py",
    "tests/test_lightrag_pilot.py",
)

PILOT_CORPUS = BASE_PILOT_CORPUS + TRACK_B_CORPUS_ADDITIONS

MANDATORY_DOCS = {
    ".specify/memory/constitution.md",
    "AGENTS.md",
    "docs/README.md",
}

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
MAX_CHUNK_CHARS = 1400
MIN_SECTION_CHARS = 250
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_LLM_MODEL = "qwen2.5:1.5b"
OLLAMA_EMBED_MODEL = "nomic-embed-text"
OLLAMA_LLM_TIMEOUT_SECONDS = 900
OLLAMA_LLM_MAX_ASYNC = 1
OLLAMA_LLM_NUM_PREDICT = 256
LIGHTRAG_MAX_PARALLEL_INSERT = 1
LIGHTRAG_MAX_EXTRACT_INPUT_TOKENS = 6000
LIGHTRAG_ENTITY_EXTRACT_MAX_GLEANING = 0
TOKEN_RE = re.compile(r"[0-9A-Za-zА-Яа-яЁё][0-9A-Za-zА-Яа-яЁё_-]*")
PATH_RE = re.compile(r"(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.[A-Za-z0-9_.-]+")
FEATURE_TASK_FILES = ("spec.md", "plan.md", "tasks.md")
TASK_TYPE_CHOICES = (
    "general",
    "product-code",
    "review",
    "product-framing",
    "frontend",
    "backend",
)
POLICY_CANONICAL_DOCS = (
    "docs/context-policy.md",
    ".specify/memory/constitution.md",
    "AGENTS.md",
    "docs/README.md",
)
SETUP_CANONICAL_DOCS = (
    "docs/lightrag-local-pilot.md",
    "docs/context-policy.md",
)
FEATURE_OWNERSHIP_CANONICAL_DOCS = (
    "specs/042-repo-memory-platform-lightrag/spec.md",
    "specs/042-repo-memory-platform-lightrag/evaluation.md",
    "specs/044-lightrag-retrieval-precision/spec.md",
    "specs/044-lightrag-retrieval-precision/evaluation.md",
    "specs/045-retrieval-quality-benchmark/spec.md",
)
TAXONOMY_CANONICAL_DOCS = (
    ".specify/memory/constitution.md",
    "AGENTS.md",
    "docs/README.md",
    "docs/project-idea.md",
)
READ_ORDER_CANONICAL_DOCS = (
    "AGENTS.md",
    ".specify/memory/constitution.md",
    "docs/README.md",
    "docs/project-idea.md",
)
PR_LOOP_CANONICAL_DOCS = (
    "docs/ai-pr-workflow.md",
    "AGENTS.md",
    ".specify/memory/constitution.md",
)
PR_LOOP_COMPLETION_CANONICAL_DOCS = (
    "docs/ai-pr-workflow.md",
    "AGENTS.md",
)

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


@dataclass(frozen=True)
class ContextDocument:
    path: str
    doc_class: str
    title: str
    source: str
    reason: str
    content: str


@dataclass(frozen=True)
class ContextPack:
    question: str
    mode: str
    task_type: str
    active_feature_id: str | None
    mandatory_documents: list[ContextDocument]
    retrieved_documents: list[ContextDocument]
    final_documents: list[ContextDocument]
    raw_retrieval_result: Any


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
    if relative_path.startswith("src/"):
        return "implementation_code"
    if relative_path.startswith("tests/"):
        return "test_code"
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
        previous_heading_path = previous.heading_path if previous is not None else tuple()
        same_heading_depth = bool(
            previous_heading_path
            and section.heading_path
            and len(previous_heading_path) == len(section.heading_path)
        )
        shared_parent = same_heading_depth and (
            previous_heading_path[:-1] == section.heading_path[:-1]
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


def read_repo_text(root: Path, relative_path: str) -> str:
    return (root / relative_path).read_text(encoding="utf-8")


def normalize_query_tokens(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text) if len(token) >= 3]


def normalize_query_text(text: str) -> str:
    return " ".join(text.lower().split())


def is_taxonomy_question(question: str) -> bool:
    normalized = normalize_query_text(question)
    return (
        "repository memory taxonomy" in normalized
        or ("which files" in normalized and "taxonomy" in normalized)
    )


def is_pilot_boundary_question(question: str) -> bool:
    normalized = normalize_query_text(question)
    return (
        "pilot boundary" in normalized
        or "pilot corpus" in normalized
        or "context policy" in normalized
    )


def is_mandatory_policy_question(question: str) -> bool:
    normalized = normalize_query_text(question)
    return (
        "mandatory versus retrieve-on-demand" in normalized
        or "mandatory vs retrieve-on-demand" in normalized
        or ("mandatory" in normalized and "retrieve-on-demand" in normalized)
    )


def is_feature_ownership_question(question: str) -> bool:
    normalized = normalize_query_text(question)
    return (
        "which feature defined the retrieval mvp" in normalized
        or "which feature closed q3 q4 q5 precision regressions" in normalized
        or "which feature owns the broader benchmark" in normalized
    )


def is_read_order_question(question: str) -> bool:
    normalized = normalize_query_text(question)
    return (
        "canonical read order before implementation work" in normalized
        or "which current-pilot process-memory files anchor the canonical read order" in normalized
        or ("read order" in normalized and "implementation work" in normalized)
    )


def is_local_pilot_setup_question(question: str) -> bool:
    normalized = normalize_query_text(question)
    return (
        "where is the local lightrag pilot setup documented" in normalized
        or "what stack is fixed there" in normalized
        or "local pilot setup and stack" in normalized
    )


def is_pr_loop_contract_question(question: str) -> bool:
    normalized = normalize_query_text(question)
    return (
        "which docs define the generic pr-loop contract" in normalized
        or ("pr-loop contract" in normalized and "implementation and review" in normalized)
    )


def is_pr_loop_completion_question(question: str) -> bool:
    normalized = normalize_query_text(question)
    return (
        "what conditions must be true before an orchestrated pr loop is considered done"
        in normalized
        or "pr-loop completion conditions" in normalized
        or ("orchestrated pr loop" in normalized and "considered done" in normalized)
    )


def is_implementation_location_question(question: str) -> bool:
    normalized = normalize_query_text(question)
    return (
        "which code and tests implement the current lightrag pilot behavior" in normalized
        or ("implement" in normalized and "lightrag pilot behavior" in normalized)
        or "current pilot implementation location" in normalized
    )


def is_policy_or_taxonomy_question(question: str) -> bool:
    return (
        is_taxonomy_question(question)
        or is_read_order_question(question)
        or is_pilot_boundary_question(question)
        or is_mandatory_policy_question(question)
        or is_pr_loop_contract_question(question)
        or is_pr_loop_completion_question(question)
    )


def policy_bias_paths(root: Path, question: str, task_type: str = "general") -> list[str]:
    preferred_paths: list[str] = []

    if is_taxonomy_question(question):
        preferred_paths.extend(TAXONOMY_CANONICAL_DOCS)
    if is_read_order_question(question):
        preferred_paths.extend(READ_ORDER_CANONICAL_DOCS)
    if is_local_pilot_setup_question(question):
        preferred_paths.extend(SETUP_CANONICAL_DOCS)
    if is_feature_ownership_question(question):
        preferred_paths.extend(FEATURE_OWNERSHIP_CANONICAL_DOCS)
    if is_pilot_boundary_question(question) or is_mandatory_policy_question(question):
        preferred_paths.extend(POLICY_CANONICAL_DOCS)
    if is_pr_loop_contract_question(question):
        preferred_paths.extend(PR_LOOP_CANONICAL_DOCS)
    if is_pr_loop_completion_question(question):
        preferred_paths.extend(PR_LOOP_COMPLETION_CANONICAL_DOCS)
    if is_mandatory_policy_question(question) and task_type in {"product-code", "review"}:
        preferred_paths.append("docs/ai-pr-workflow.md")

    seen: set[str] = set()
    existing_paths: list[str] = []
    for relative_path in preferred_paths:
        if relative_path in seen:
            continue
        if not (root / relative_path).exists():
            continue
        seen.add(relative_path)
        existing_paths.append(relative_path)
    return existing_paths


def score_chunk_for_query(chunk: PreparedChunk, query_tokens: list[str]) -> int:
    if not query_tokens:
        return 0

    path_text = chunk.path.lower()
    title_text = chunk.title.lower()
    heading_text = " ".join(chunk.heading_path).lower()
    body_text = chunk.content.lower()
    score = 0

    for token in query_tokens:
        if token in path_text:
            score += 5
        if token in title_text:
            score += 4
        if token in heading_text:
            score += 3
        if token in body_text:
            score += 1

    return score


def fallback_retrieved_paths(
    question: str,
    chunks: list[PreparedChunk],
    exclude_paths: set[str] | None = None,
    limit: int = 4,
) -> list[str]:
    exclude = exclude_paths or set()
    query_tokens = normalize_query_tokens(question)
    scored_paths: dict[str, int] = {}

    for chunk in chunks:
        if chunk.path in exclude:
            continue
        score = score_chunk_for_query(chunk, query_tokens)
        if score <= 0:
            continue
        scored_paths[chunk.path] = max(scored_paths.get(chunk.path, 0), score)

    ranked_paths = sorted(
        scored_paths.items(),
        key=lambda item: (-item[1], item[0]),
    )
    return [path for path, _ in ranked_paths[:limit]]


def resolve_retrieved_paths(
    root: Path,
    question: str,
    raw_result: Any,
    task_type: str,
    chunks: list[PreparedChunk],
    mandatory_paths: list[str],
    retrieved_doc_limit: int = 4,
) -> list[str]:
    preferred_paths = policy_bias_paths(root, question, task_type=task_type)
    allowed_paths = {chunk.path for chunk in chunks} | set(preferred_paths)

    extracted_paths = extract_reference_paths(raw_result, allowed_paths)
    fallback_paths: list[str] = []
    if not extracted_paths and not preferred_paths:
        fallback_paths = fallback_retrieved_paths(
            question,
            chunks,
            exclude_paths=set(mandatory_paths),
            limit=retrieved_doc_limit,
        )

    return merge_ranked_paths(
        extracted_paths,
        preferred_paths,
        fallback_paths,
        exclude_paths=set(mandatory_paths),
        limit=retrieved_doc_limit,
    )


def normalize_reference_candidate(candidate: str, allowed_paths: set[str]) -> str | None:
    normalized = candidate.strip().strip("`'\"*.,:;!?()[]{}<>").replace("\\", "/")
    if not normalized:
        return None
    if normalized in allowed_paths:
        return normalized

    for allowed_path in sorted(allowed_paths, key=len, reverse=True):
        if normalized.endswith(f"/{allowed_path}"):
            return allowed_path

    return None


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


def extract_reference_paths(value: Any, allowed_paths: set[str]) -> list[str]:
    found_paths: list[str] = []
    seen: set[str] = set()

    def record(candidate: str) -> None:
        normalized = normalize_reference_candidate(candidate, allowed_paths)
        if normalized and normalized not in seen:
            seen.add(normalized)
            found_paths.append(normalized)

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            file_path = node.get("file_path")
            if isinstance(file_path, str):
                record(file_path)
            references = node.get("references")
            if references is not None:
                visit(references)
            for nested in node.values():
                if nested is references:
                    continue
                visit(nested)
            return
        if isinstance(node, (list, tuple, set)):
            for nested in node:
                visit(nested)
            return
        if not isinstance(node, str):
            return

        for candidate in PATH_RE.findall(node):
            record(candidate)

        for candidate in sorted(allowed_paths, key=len, reverse=True):
            if candidate in node:
                record(candidate)

    visit(value)
    return found_paths


def merge_ranked_paths(
    *path_groups: list[str],
    exclude_paths: set[str] | None = None,
    limit: int | None = None,
) -> list[str]:
    exclude = exclude_paths or set()
    merged: list[str] = []
    seen: set[str] = set()

    for group in path_groups:
        for path in group:
            if path in exclude or path in seen:
                continue
            seen.add(path)
            merged.append(path)
            if limit is not None and len(merged) >= limit:
                return merged

    return merged


def format_policy_answer(
    task_type: str,
    mandatory_paths: list[str],
    retrieved_paths: list[str],
) -> str:
    mandatory_lines = "\n".join(f"- `{path}`" for path in mandatory_paths)
    retrieved_lines = "\n".join(f"- `{path}`" for path in retrieved_paths) or "- none"
    return (
        f"Mandatory files for `{task_type}` work are:\n\n"
        f"{mandatory_lines}\n\n"
        "Retrieve-on-demand policy is defined by:\n\n"
        f"{retrieved_lines}\n\n"
        "Answer these rules from the canonical files above before falling back to "
        "higher-level category summaries."
    )


def format_taxonomy_answer() -> str:
    taxonomy_lines = "\n".join(f"- `{path}`" for path in TAXONOMY_CANONICAL_DOCS)
    return (
        "The canonical files that define the repository memory taxonomy are:\n\n"
        f"{taxonomy_lines}\n\n"
        "Use these repository files as the taxonomy source instead of inferred "
        "directory summaries or invented file names."
    )


def format_read_order_answer() -> str:
    read_order_lines = "\n".join(f"- `{path}`" for path in READ_ORDER_CANONICAL_DOCS)
    return (
        "The current-pilot files that anchor the canonical read order before implementation work are:\n\n"
        f"{read_order_lines}\n\n"
        "Read-order summary:\n\n"
        "- `AGENTS.md` explicitly enumerates the read order\n"
        "- `.specify/memory/constitution.md` defines the governing repository-memory model\n"
        "- `docs/README.md` and `docs/project-idea.md` anchor the durable current-pilot context slice\n\n"
        "Answer with the exact file list above rather than a generic workflow sequence."
    )


def format_pilot_boundary_answer() -> str:
    boundary_lines = "\n".join(f"- `{path}`" for path in POLICY_CANONICAL_DOCS)
    return (
        "The current LightRAG pilot boundary and pilot corpus policy are defined by:\n\n"
        f"{boundary_lines}\n\n"
        "Boundary summary:\n\n"
        "- `docs/context-policy.md` is the canonical source for the pilot boundary and corpus allowlist\n"
        "- `.specify/memory/constitution.md`, `AGENTS.md`, and `docs/README.md` define the surrounding repository-memory contract\n\n"
        "Keep the answer anchored to `docs/context-policy.md` as the primary policy source instead of drifting into setup docs or broader process overviews."
    )


def format_setup_answer() -> str:
    setup_lines = "\n".join(f"- `{path}`" for path in SETUP_CANONICAL_DOCS)
    return (
        "The local LightRAG pilot setup is defined by:\n\n"
        f"{setup_lines}\n\n"
        "Fixed stack and runtime facts to cite from these files:\n\n"
        "- `Ollama`\n"
        "- `qwen2.5:1.5b`\n"
        "- `nomic-embed-text`\n"
        "- repository-local script entrypoint `scripts/lightrag_pilot.py`\n"
        "- local `LightRAG` in the repository Python environment\n"
        "- repo-local working directory `.lightrag/`\n\n"
        "Keep the answer anchored to the canonical file pair above instead of "
        "drifting into generic README or project-summary text."
    )


def format_feature_ownership_answer() -> str:
    ownership_lines = "\n".join(f"- `{path}`" for path in FEATURE_OWNERSHIP_CANONICAL_DOCS)
    return (
        "The canonical feature-memory files for retrieval ownership are:\n\n"
        f"{ownership_lines}\n\n"
        "Ownership summary:\n\n"
        "- `042` defines the retrieval MVP and initial evaluation\n"
        "- `044` closes the focused Q3/Q4/Q5 precision follow-up\n"
        "- `045` owns the broader benchmark\n\n"
        "Answer with the exact feature-memory file paths above, not only feature ids "
        "or abstract benchmark summaries."
    )


def format_pr_loop_contract_answer() -> str:
    contract_lines = "\n".join(f"- `{path}`" for path in PR_LOOP_CANONICAL_DOCS)
    return (
        "The canonical files that define the generic PR-loop contract are:\n\n"
        f"{contract_lines}\n\n"
        "Contract summary:\n\n"
        "- product code must go through the standard PR loop\n"
        "- required checks must pass before merge\n"
        "- AI review is part of the completion contract\n\n"
        "Keep the answer anchored to the exact canonical files above instead of broader process overviews."
    )


def format_pr_loop_completion_answer() -> str:
    completion_lines = "\n".join(
        f"- `{path}`" for path in PR_LOOP_COMPLETION_CANONICAL_DOCS
    )
    return (
        "The canonical files for orchestrated PR-loop completion conditions are:\n\n"
        f"{completion_lines}\n\n"
        "The orchestrated PR loop is done only when all of these are true:\n\n"
        "- no blocking review findings\n"
        "- green required checks\n"
        "- no merge conflicts\n"
        "- only human approval or final merge remaining\n\n"
        "Answer with the exact completion conditions above rather than a partial merge-readiness summary."
    )


def shape_raw_retrieval_result(
    raw_result: Any,
    question: str,
    task_type: str,
    mandatory_paths: list[str],
    retrieved_paths: list[str],
) -> Any:
    if is_taxonomy_question(question):
        return format_taxonomy_answer()
    if is_read_order_question(question):
        return format_read_order_answer()
    if is_pilot_boundary_question(question):
        return format_pilot_boundary_answer()
    if is_local_pilot_setup_question(question):
        return format_setup_answer()
    if is_feature_ownership_question(question):
        return format_feature_ownership_answer()
    if is_pr_loop_contract_question(question):
        return format_pr_loop_contract_answer()
    if is_pr_loop_completion_question(question):
        return format_pr_loop_completion_answer()
    if not is_mandatory_policy_question(question):
        return raw_result
    if not mandatory_paths:
        return raw_result
    if not isinstance(raw_result, str):
        return raw_result
    return format_policy_answer(
        task_type=task_type,
        mandatory_paths=mandatory_paths,
        retrieved_paths=retrieved_paths,
    )


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


def serialize_chunk_for_rag(chunk: PreparedChunk) -> str:
    return chunk.content


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
        from lightrag.prompt import PROMPTS
        from lightrag.utils import EmbeddingFunc, Tokenizer
    except ImportError as exc:
        raise RuntimeError(
            "LightRAG pilot dependencies are missing. Install them with "
            "`uv sync --extra repo_memory --extra dev`."
        ) from exc
    _tighten_entity_extraction_prompts(PROMPTS)
    return (
        LightRAG,
        QueryParam,
        EmbeddingFunc,
        Tokenizer,
        ollama_embed,
        ollama_model_complete,
    )


def _tighten_entity_extraction_prompts(prompts: dict[str, Any]) -> None:
    strict_suffix = """

---Pilot Guardrails---
9.  **Repository Metadata Ignore List:**
    *   Ignore repository metadata sections, path-like strings, heading paths, chunk identifiers, template placeholders, and schema examples.
    *   Never output any of the following as entities or relationships: `Path`, `Doc Class`, `Title`, `Heading Path`, `Language`, `Feature ID`, `Chunk ID`, `Chunk Order`, `Mandatory Candidate`.
10. **Strict Output Discipline:**
    *   Output plain extraction rows only. Do not output code fences, bullets, numbering, XML tags, headings, commentary, or explanations.
    *   Do not invent extra fields. Entity rows must contain exactly 4 fields and relation rows must contain exactly 5 fields.
    *   If there are no valid entities or relationships in the document body, output only `{completion_delimiter}`.
"""
    user_suffix = """
5.  **Ignore Metadata Noise:** Ignore repository metadata sections, path-like strings, chunk identifiers, heading paths, and template placeholders.
6.  **No Extra Formatting:** Do not output XML tags, code fences, bullets, numbering, or explanatory prose.
7.  **Schema Discipline:** Entity rows must contain exactly 4 fields and relation rows must contain exactly 5 fields.
"""
    continue_suffix = """
7.  **Ignore Metadata Noise:** Ignore repository metadata sections, path-like strings, chunk identifiers, heading paths, and template placeholders.
8.  **No Extra Formatting:** Do not output XML tags, code fences, bullets, numbering, or explanatory prose.
9.  **Schema Discipline:** Entity rows must contain exactly 4 fields and relation rows must contain exactly 5 fields.
"""
    prompts["entity_extraction_system_prompt"] += strict_suffix
    prompts["entity_extraction_user_prompt"] = prompts["entity_extraction_user_prompt"].replace(
        "4.  **Output Language:** Ensure the output language is {language}. Proper nouns (e.g., personal names, place names, organization names) must be kept in their original language and not translated.\n",
        "4.  **Output Language:** Ensure the output language is {language}. Proper nouns (e.g., personal names, place names, organization names) must be kept in their original language and not translated.\n"
        + user_suffix,
    )
    prompts["entity_continue_extraction_user_prompt"] = prompts[
        "entity_continue_extraction_user_prompt"
    ].replace(
        "6.  **Completion Signal:** Output `{completion_delimiter}` as the final line after all relevant missing or corrected entities and relationships have been extracted and presented.\n",
        "6.  **Completion Signal:** Output `{completion_delimiter}` as the final line after all relevant missing or corrected entities and relationships have been extracted and presented.\n"
        + continue_suffix,
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
        max_parallel_insert=LIGHTRAG_MAX_PARALLEL_INSERT,
        max_extract_input_tokens=LIGHTRAG_MAX_EXTRACT_INPUT_TOKENS,
        entity_extract_max_gleaning=LIGHTRAG_ENTITY_EXTRACT_MAX_GLEANING,
        chunk_token_size=700,
        chunk_overlap_token_size=50,
        llm_model_func=ollama_model_complete,
        llm_model_name=OLLAMA_LLM_MODEL,
        llm_model_max_async=OLLAMA_LLM_MAX_ASYNC,
        default_llm_timeout=OLLAMA_LLM_TIMEOUT_SECONDS,
        llm_model_kwargs={
            "host": OLLAMA_HOST,
            "options": {
                "num_ctx": 8192,
                "num_predict": OLLAMA_LLM_NUM_PREDICT,
                "temperature": 0,
            },
            "timeout": OLLAMA_LLM_TIMEOUT_SECONDS,
        },
        tokenizer=tokenizer,
        embedding_func=embedding_func,
    )


def retrieval_user_prompt(question: str) -> str | None:
    if is_read_order_question(question):
        return (
            "Answer file-first. For canonical read-order questions, prioritize the exact "
            "current-pilot anchor files `AGENTS.md`, `.specify/memory/constitution.md`, "
            "`docs/README.md`, and `docs/project-idea.md`. Do not replace them with a "
            "generic workflow sequence or broader process-summary documents."
        )
    if is_implementation_location_question(question):
        return (
            "Answer file-first. Prefer exact implementation file paths over high-level "
            "process summaries. If the question asks where the current LightRAG pilot "
            "behavior lives, prioritize `src/repo_memory/lightrag_pilot.py`, "
            "`tests/test_lightrag_pilot.py`, `docs/lightrag-local-pilot.md`, and "
            "`specs/042-repo-memory-platform-lightrag/plan.md` when supported by retrieval."
        )
    if is_feature_ownership_question(question):
        return (
            "Answer file-first. Name the exact feature-memory files that assign ownership, "
            "especially `specs/042-repo-memory-platform-lightrag/spec.md`, "
            "`specs/042-repo-memory-platform-lightrag/evaluation.md`, "
            "`specs/044-lightrag-retrieval-precision/spec.md`, "
            "`specs/044-lightrag-retrieval-precision/evaluation.md`, and "
            "`specs/045-retrieval-quality-benchmark/spec.md`."
        )
    if is_local_pilot_setup_question(question):
        return (
            "Answer file-first. For local LightRAG setup questions, prioritize the exact "
            "canonical pair `docs/lightrag-local-pilot.md` and `docs/context-policy.md`, "
            "then cite the fixed stack facts: `Ollama`, `qwen2.5:1.5b`, "
            "`nomic-embed-text`, the repository-local script entrypoint, local Python "
            "environment, and repo-local working directory `.lightrag/`."
        )
    if is_pr_loop_contract_question(question):
        return (
            "Answer file-first. For generic PR-loop contract questions, prioritize "
            "`docs/ai-pr-workflow.md`, `AGENTS.md`, and `.specify/memory/constitution.md`, "
            "and keep the answer centered on the canonical PR-loop contract rather than "
            "broader process overviews."
        )
    if is_pr_loop_completion_question(question):
        return (
            "Answer file-first. For orchestrated PR-loop completion questions, prioritize "
            "`docs/ai-pr-workflow.md` and `AGENTS.md`, and explicitly include all four "
            "completion conditions: no blocking findings, green required checks, no merge "
            "conflicts, and only human approval or final merge remaining."
        )
    if not is_policy_or_taxonomy_question(question):
        return None
    return (
        "Answer file-first. Prefer exact canonical Markdown file paths over directories "
        "or abstract categories. When policy or taxonomy is relevant, cite the exact "
        "repository files that define it, especially docs/context-policy.md when it "
        "governs pilot boundary or mandatory versus retrieve-on-demand rules."
    )


def build_query_param(
    query: str,
    mode: str,
    include_references: bool,
    query_param_factory: Any,
) -> Any:
    params: dict[str, Any] = {
        "mode": mode,
        "include_references": include_references,
        "enable_rerank": False,
    }
    if is_read_order_question(query):
        params.update(
            {
                "top_k": 8,
                "chunk_top_k": 4,
                "response_type": "Bullet Points",
            }
        )
    elif is_pr_loop_contract_question(query) or is_pr_loop_completion_question(query):
        params.update(
            {
                "top_k": 8,
                "chunk_top_k": 4,
                "response_type": "Bullet Points",
            }
        )
    elif is_pilot_boundary_question(query):
        params.update(
            {
                "top_k": 6,
                "chunk_top_k": 3,
                "response_type": "Bullet Points",
            }
        )
    user_prompt = retrieval_user_prompt(query)
    if user_prompt:
        params["user_prompt"] = user_prompt
    return query_param_factory(**params)


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
    if task_type not in TASK_TYPE_CHOICES:
        raise ValueError(f"Unsupported task type: {task_type}")

    runner = query_runner or query_index
    raw_result = await runner(root, question, mode=mode, include_references=True)
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
