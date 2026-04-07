from pathlib import Path

import pytest

from src.repo_memory.lightrag_pilot import (
    MANDATORY_DOCS,
    build_prepared_chunks,
    build_context_pack,
    chunk_markdown,
    corpus_paths,
    doc_class_for_path,
    mandatory_doc_paths,
)


def test_doc_class_policy_matches_phase_5_scope():
    assert doc_class_for_path(".specify/memory/constitution.md") == "process_memory"
    assert doc_class_for_path("AGENTS.md") == "process_memory"
    assert doc_class_for_path("docs/README.md") == "durable_doc"
    assert doc_class_for_path("specs/042-repo-memory-platform-lightrag/spec.md") == "feature_memory"


def test_chunk_markdown_preserves_preface_and_heading_metadata():
    content = """Intro paragraph.\n\n# One\nSection body.\n\n## Two\nSecond body.\n"""

    chunks = chunk_markdown("docs/example.md", content)

    assert len(chunks) == 3
    assert chunks[0].heading_path == []
    assert chunks[0].title == "One"
    assert chunks[1].heading_path == ["One"]
    assert chunks[2].heading_path == ["One", "Two"]


def test_small_adjacent_sections_are_collapsed():
    content = """# Root\nMain body.\n\n## A\nTiny.\n\n## B\nAlso tiny.\n"""

    chunks = chunk_markdown("docs/example.md", content)

    assert len(chunks) == 2
    assert "## A" in chunks[1].content
    assert "## B" in chunks[1].content


def test_build_prepared_chunks_uses_fixed_pilot_corpus():
    root = Path(__file__).resolve().parents[1]
    chunks = build_prepared_chunks(root)
    chunk_paths = {chunk.path for chunk in chunks}

    assert chunk_paths == {path.relative_to(root).as_posix() for path in corpus_paths(root)}
    mandatory_chunk_paths = {chunk.path for chunk in chunks if chunk.mandatory_candidate}
    assert mandatory_chunk_paths == MANDATORY_DOCS


def test_mandatory_doc_paths_follow_context_policy():
    root = Path(__file__).resolve().parents[1]

    paths = mandatory_doc_paths(
        root,
        active_feature_id="042-repo-memory-platform-lightrag",
        task_type="product-code",
    )

    assert paths[:3] == sorted(MANDATORY_DOCS)
    assert "specs/042-repo-memory-platform-lightrag/spec.md" in paths
    assert "specs/042-repo-memory-platform-lightrag/plan.md" in paths
    assert "specs/042-repo-memory-platform-lightrag/tasks.md" in paths
    assert "docs/ai-pr-workflow.md" in paths


@pytest.mark.asyncio
async def test_build_context_pack_injects_mandatory_docs_when_retrieval_has_no_references():
    root = Path(__file__).resolve().parents[1]

    async def fake_runner(_root: Path, _question: str, mode: str, include_references: bool) -> str:
        assert mode == "hybrid"
        assert include_references is True
        return "No explicit references returned."

    pack = await build_context_pack(
        root,
        "which files define the repository memory taxonomy",
        mode="hybrid",
        active_feature_id="042-repo-memory-platform-lightrag",
        task_type="product-code",
        query_runner=fake_runner,
    )

    mandatory_paths = [document.path for document in pack.mandatory_documents]

    assert sorted(MANDATORY_DOCS) == mandatory_paths[:3]
    assert "docs/ai-pr-workflow.md" in mandatory_paths
    assert "specs/042-repo-memory-platform-lightrag/spec.md" in mandatory_paths
    assert pack.final_documents[: len(pack.mandatory_documents)] == pack.mandatory_documents


@pytest.mark.asyncio
async def test_build_context_pack_preserves_retrieval_mode_and_references():
    root = Path(__file__).resolve().parents[1]

    async def fake_runner(_root: Path, _question: str, mode: str, include_references: bool) -> dict[str, object]:
        assert mode == "mix"
        assert include_references is True
        return {
            "answer": "Relevant docs found.",
            "references": [
                "docs/project-idea.md",
                "AGENTS.md",
            ],
        }

    pack = await build_context_pack(
        root,
        "where the local LightRAG pilot boundary and pilot corpus are defined",
        mode="mix",
        task_type="general",
        query_runner=fake_runner,
    )

    assert pack.mode == "mix"
    assert [document.path for document in pack.retrieved_documents] == ["docs/project-idea.md"]
    assert [document.path for document in pack.final_documents[:3]] == sorted(MANDATORY_DOCS)
