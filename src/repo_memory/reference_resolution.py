from __future__ import annotations

from pathlib import Path
from typing import Any

from .pilot_config import PATH_RE
from .pilot_types import PreparedChunk
from .query_policy import normalize_query_tokens, policy_bias_paths


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
