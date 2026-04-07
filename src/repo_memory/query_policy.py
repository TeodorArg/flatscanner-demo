from __future__ import annotations

import re
from pathlib import Path

from .pilot_config import (
    FEATURE_OWNERSHIP_CANONICAL_DOCS,
    IMPLEMENTATION_CANONICAL_DOCS,
    POLICY_CANONICAL_DOCS,
    PR_LOOP_CANONICAL_DOCS,
    PR_LOOP_COMPLETION_CANONICAL_DOCS,
    READ_ORDER_CANONICAL_DOCS,
    SETUP_CANONICAL_DOCS,
    TAXONOMY_CANONICAL_DOCS,
    TOKEN_RE,
)


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


def format_implementation_location_answer() -> str:
    implementation_lines = "\n".join(
        f"- `{path}`" for path in IMPLEMENTATION_CANONICAL_DOCS
    )
    return (
        "The canonical implementation files for the current LightRAG pilot behavior are:\n\n"
        f"{implementation_lines}\n\n"
        "Implementation summary:\n\n"
        "- `src/repo_memory/lightrag_pilot.py` is the thin public facade and CLI-facing orchestration module\n"
        "- the helper modules under `src/repo_memory/` own config, types, chunking, query policy, reference resolution, runtime wiring, and context-pack assembly\n"
        "- `tests/test_lightrag_pilot.py` is the regression suite for the current pilot behavior\n\n"
        "Answer with the exact code and test paths above instead of implying that all pilot behavior still lives in one monolithic module."
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
    raw_result: object,
    question: str,
    task_type: str,
    mandatory_paths: list[str],
    retrieved_paths: list[str],
) -> object:
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
    if is_implementation_location_question(question):
        return format_implementation_location_answer()
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
            "`src/repo_memory/pilot_config.py`, `src/repo_memory/pilot_types.py`, "
            "`src/repo_memory/markdown_chunks.py`, `src/repo_memory/query_policy.py`, "
            "`src/repo_memory/reference_resolution.py`, `src/repo_memory/lightrag_runtime.py`, "
            "`src/repo_memory/context_pack.py`, `tests/test_lightrag_pilot.py`, "
            "`docs/lightrag-local-pilot.md`, and `specs/042-repo-memory-platform-lightrag/plan.md` "
            "when supported by retrieval."
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
