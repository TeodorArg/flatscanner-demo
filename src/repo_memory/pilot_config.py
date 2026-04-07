from __future__ import annotations

import re
from pathlib import Path


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
    "src/repo_memory/pilot_config.py",
    "src/repo_memory/pilot_types.py",
    "src/repo_memory/markdown_chunks.py",
    "src/repo_memory/query_policy.py",
    "src/repo_memory/reference_resolution.py",
    "src/repo_memory/lightrag_runtime.py",
    "src/repo_memory/context_pack.py",
    "tests/test_lightrag_pilot.py",
)

PILOT_CORPUS = BASE_PILOT_CORPUS + TRACK_B_CORPUS_ADDITIONS

MANDATORY_DOCS = {
    ".specify/memory/constitution.md",
    "AGENTS.md",
    "docs/README.md",
}

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
TOKEN_RE = re.compile(r"[0-9A-Za-zА-Яа-яЁё][0-9A-Za-zА-Яа-яЁё_-]*")
PATH_RE = re.compile(r"(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.[A-Za-z0-9_.-]+")

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
IMPLEMENTATION_CANONICAL_DOCS = (
    "src/repo_memory/lightrag_pilot.py",
    "src/repo_memory/pilot_config.py",
    "src/repo_memory/pilot_types.py",
    "src/repo_memory/markdown_chunks.py",
    "src/repo_memory/query_policy.py",
    "src/repo_memory/reference_resolution.py",
    "src/repo_memory/lightrag_runtime.py",
    "src/repo_memory/context_pack.py",
    "tests/test_lightrag_pilot.py",
    "docs/lightrag-local-pilot.md",
    "specs/042-repo-memory-platform-lightrag/plan.md",
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
