from pathlib import Path

from src.repo_memory.lightrag_pilot import (
    MANDATORY_DOCS,
    build_prepared_chunks,
    chunk_markdown,
    corpus_paths,
    doc_class_for_path,
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
