from pathlib import Path

import pytest

from src.repo_memory.lightrag_pilot import (
    MANDATORY_DOCS,
    TRACK_B_CORPUS_ADDITIONS,
    build_query_param,
    build_prepared_chunks,
    build_context_pack,
    chunk_markdown,
    corpus_paths,
    doc_class_for_path,
    extract_reference_paths,
    format_feature_ownership_answer,
    format_setup_answer,
    format_taxonomy_answer,
    format_policy_answer,
    mandatory_doc_paths,
    policy_bias_paths,
    resolve_retrieved_paths,
    retrieval_user_prompt,
    shape_raw_retrieval_result,
)


def test_doc_class_policy_matches_phase_5_scope():
    assert doc_class_for_path(".specify/memory/constitution.md") == "process_memory"
    assert doc_class_for_path("AGENTS.md") == "process_memory"
    assert doc_class_for_path("docs/README.md") == "durable_doc"
    assert doc_class_for_path("specs/042-repo-memory-platform-lightrag/spec.md") == "feature_memory"
    assert doc_class_for_path("src/repo_memory/lightrag_pilot.py") == "implementation_code"
    assert doc_class_for_path("tests/test_lightrag_pilot.py") == "test_code"


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


def test_track_b_additions_cover_the_expected_benchmark_targets():
    assert TRACK_B_CORPUS_ADDITIONS == (
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


def test_retrieval_user_prompt_is_file_first_for_policy_questions():
    prompt = retrieval_user_prompt(
        "where the local LightRAG pilot boundary and pilot corpus are defined"
    )

    assert prompt is not None
    assert "exact canonical Markdown file paths" in prompt
    assert "docs/context-policy.md" in prompt


def test_build_query_param_disables_rerank_and_adds_policy_prompt():
    captured: dict[str, object] = {}

    def fake_query_param_factory(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return kwargs

    result = build_query_param(
        "which artifacts are mandatory versus retrieve-on-demand for product-code work",
        mode="hybrid",
        include_references=True,
        query_param_factory=fake_query_param_factory,
    )

    assert result["enable_rerank"] is False
    assert result["mode"] == "hybrid"
    assert result["include_references"] is True
    assert "docs/context-policy.md" in str(result["user_prompt"])
    assert captured == result


def test_build_query_param_adds_implementation_location_prompt():
    result = build_query_param(
        "Which code and tests implement the current LightRAG pilot behavior",
        mode="hybrid",
        include_references=True,
        query_param_factory=lambda **kwargs: kwargs,
    )

    assert "src/repo_memory/lightrag_pilot.py" in str(result["user_prompt"])
    assert "tests/test_lightrag_pilot.py" in str(result["user_prompt"])


def test_build_query_param_adds_setup_prompt():
    result = build_query_param(
        "Where is the local LightRAG pilot setup documented and what stack is fixed there",
        mode="mix",
        include_references=True,
        query_param_factory=lambda **kwargs: kwargs,
    )

    assert "docs/lightrag-local-pilot.md" in str(result["user_prompt"])
    assert "docs/context-policy.md" in str(result["user_prompt"])
    assert ".lightrag/" in str(result["user_prompt"])


def test_extract_reference_paths_normalizes_absolute_and_nested_file_paths():
    allowed_paths = {
        "AGENTS.md",
        "docs/context-policy.md",
        "docs/project-idea.md",
        "src/repo_memory/lightrag_pilot.py",
        "tests/test_lightrag_pilot.py",
    }
    payload = {
        "response": (
            "See `/tmp/flatscanner-demo-044-precision/docs/project-idea.md`, "
            "`/tmp/flatscanner-demo-044-precision/src/repo_memory/lightrag_pilot.py`, "
            "and AGENTS.md."
        ),
        "references": [
            {"file_path": "/tmp/flatscanner-demo-044-precision/docs/context-policy.md"},
            {"file_path": "/tmp/flatscanner-demo-044-precision/AGENTS.md"},
            {"file_path": "/tmp/flatscanner-demo-044-precision/tests/test_lightrag_pilot.py"},
        ],
    }

    assert extract_reference_paths(payload, allowed_paths) == [
        "docs/context-policy.md",
        "AGENTS.md",
        "tests/test_lightrag_pilot.py",
        "docs/project-idea.md",
        "src/repo_memory/lightrag_pilot.py",
    ]


def test_resolve_retrieved_paths_prefers_feature_ownership_files():
    root = Path(__file__).resolve().parents[1]
    chunks = build_prepared_chunks(root)

    retrieved_paths = resolve_retrieved_paths(
        root,
        "Which feature defined the retrieval MVP, which feature closed Q3 Q4 Q5 precision regressions, and which feature owns the broader benchmark",
        raw_result="The answer drifts to abstract feature summaries.",
        task_type="general",
        chunks=chunks,
        mandatory_paths=[],
        retrieved_doc_limit=5,
    )

    assert retrieved_paths[:5] == [
        "specs/042-repo-memory-platform-lightrag/spec.md",
        "specs/042-repo-memory-platform-lightrag/evaluation.md",
        "specs/044-lightrag-retrieval-precision/spec.md",
        "specs/044-lightrag-retrieval-precision/evaluation.md",
        "specs/045-retrieval-quality-benchmark/spec.md",
    ]


def test_policy_bias_paths_prioritize_context_policy_for_policy_questions():
    root = Path(__file__).resolve().parents[1]

    assert policy_bias_paths(
        root,
        "where the local LightRAG pilot boundary and pilot corpus are defined",
    )[:2] == ["docs/context-policy.md", ".specify/memory/constitution.md"]


def test_policy_bias_paths_prioritize_setup_docs_for_setup_questions():
    root = Path(__file__).resolve().parents[1]

    assert policy_bias_paths(
        root,
        "Where is the local LightRAG pilot setup documented and what stack is fixed there",
    )[:2] == ["docs/lightrag-local-pilot.md", "docs/context-policy.md"]


def test_policy_bias_paths_prioritize_feature_memory_for_ownership_questions():
    root = Path(__file__).resolve().parents[1]

    assert policy_bias_paths(
        root,
        "Which feature defined the retrieval MVP, which feature closed Q3 Q4 Q5 precision regressions, and which feature owns the broader benchmark",
    )[:5] == [
        "specs/042-repo-memory-platform-lightrag/spec.md",
        "specs/042-repo-memory-platform-lightrag/evaluation.md",
        "specs/044-lightrag-retrieval-precision/spec.md",
        "specs/044-lightrag-retrieval-precision/evaluation.md",
        "specs/045-retrieval-quality-benchmark/spec.md",
    ]


def test_shape_raw_retrieval_result_rewrites_q5_to_file_first_answer():
    result = shape_raw_retrieval_result(
        "Mandatory docs are different from retrieve-on-demand docs.",
        question="which artifacts are mandatory versus retrieve-on-demand for product-code work",
        task_type="product-code",
        mandatory_paths=[
            ".specify/memory/constitution.md",
            "AGENTS.md",
            "docs/README.md",
            "docs/ai-pr-workflow.md",
        ],
        retrieved_paths=["docs/context-policy.md"],
    )

    assert isinstance(result, str)
    assert result.startswith("Mandatory files for `product-code` work are:")
    assert "`docs/context-policy.md`" in result
    assert "higher-level category summaries" in result


def test_format_policy_answer_lists_mandatory_and_retrieved_files():
    result = format_policy_answer(
        task_type="product-code",
        mandatory_paths=["AGENTS.md", "docs/ai-pr-workflow.md"],
        retrieved_paths=["docs/context-policy.md"],
    )

    assert "- `AGENTS.md`" in result
    assert "- `docs/ai-pr-workflow.md`" in result
    assert "- `docs/context-policy.md`" in result


def test_format_taxonomy_answer_lists_frozen_canonical_files():
    result = format_taxonomy_answer()

    assert result.startswith("The canonical files that define the repository memory taxonomy are:")
    assert "- `.specify/memory/constitution.md`" in result
    assert "- `AGENTS.md`" in result
    assert "- `docs/README.md`" in result
    assert "- `docs/project-idea.md`" in result


def test_format_setup_answer_lists_canonical_docs_and_stack():
    result = format_setup_answer()

    assert result.startswith("The local LightRAG pilot setup is defined by:")
    assert "- `docs/lightrag-local-pilot.md`" in result
    assert "- `docs/context-policy.md`" in result
    assert "- `Ollama`" in result
    assert "- `qwen2.5:1.5b`" in result
    assert "- `nomic-embed-text`" in result
    assert "generic README" in result


def test_format_feature_ownership_answer_lists_expected_files():
    result = format_feature_ownership_answer()

    assert result.startswith("The canonical feature-memory files for retrieval ownership are:")
    assert "- `specs/042-repo-memory-platform-lightrag/spec.md`" in result
    assert "- `specs/042-repo-memory-platform-lightrag/evaluation.md`" in result
    assert "- `specs/044-lightrag-retrieval-precision/spec.md`" in result
    assert "- `specs/044-lightrag-retrieval-precision/evaluation.md`" in result
    assert "- `specs/045-retrieval-quality-benchmark/spec.md`" in result
    assert "not only feature ids" in result


def test_shape_raw_retrieval_result_rewrites_q3_to_taxonomy_file_list():
    result = shape_raw_retrieval_result(
        "The taxonomy is described in some docs.",
        question="which files define the repository memory taxonomy",
        task_type="general",
        mandatory_paths=sorted(MANDATORY_DOCS),
        retrieved_paths=["docs/project-idea.md"],
    )

    assert isinstance(result, str)
    assert result.startswith("The canonical files that define the repository memory taxonomy are:")
    assert "`docs/project-idea.md`" in result
    assert "invented file names" in result


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
        "which document frames the repository identity",
        mode="mix",
        task_type="general",
        query_runner=fake_runner,
    )

    assert pack.mode == "mix"
    assert [document.path for document in pack.retrieved_documents] == ["docs/project-idea.md"]
    assert [document.path for document in pack.final_documents[:3]] == sorted(MANDATORY_DOCS)


@pytest.mark.asyncio
async def test_build_context_pack_biases_q4_toward_context_policy():
    root = Path(__file__).resolve().parents[1]

    async def fake_runner(_root: Path, _question: str, mode: str, include_references: bool) -> dict[str, object]:
        assert mode == "mix"
        assert include_references is True
        return {
            "answer": "The pilot boundary is described in the repository policy docs.",
            "references": [],
        }

    pack = await build_context_pack(
        root,
        "where the local LightRAG pilot boundary and pilot corpus are defined",
        mode="mix",
        task_type="general",
        query_runner=fake_runner,
    )

    assert pack.mode == "mix"
    assert [document.path for document in pack.retrieved_documents] == ["docs/context-policy.md"]


@pytest.mark.asyncio
async def test_build_context_pack_biases_q5_toward_context_policy():
    root = Path(__file__).resolve().parents[1]

    async def fake_runner(_root: Path, _question: str, mode: str, include_references: bool) -> str:
        assert mode == "hybrid"
        assert include_references is True
        return "Mandatory docs and retrieve-on-demand artifacts are different categories."

    pack = await build_context_pack(
        root,
        "which artifacts are mandatory versus retrieve-on-demand for product-code work",
        mode="hybrid",
        task_type="product-code",
        active_feature_id="044-lightrag-retrieval-precision",
        query_runner=fake_runner,
    )

    mandatory_paths = [document.path for document in pack.mandatory_documents]

    assert "docs/ai-pr-workflow.md" in mandatory_paths
    assert "specs/044-lightrag-retrieval-precision/spec.md" in mandatory_paths
    assert [document.path for document in pack.retrieved_documents] == ["docs/context-policy.md"]
    assert isinstance(pack.raw_retrieval_result, str)
    assert pack.raw_retrieval_result.startswith("Mandatory files for `product-code` work are:")
    assert "`docs/context-policy.md`" in pack.raw_retrieval_result


@pytest.mark.asyncio
async def test_build_context_pack_shapes_q3_to_frozen_taxonomy_file_list():
    root = Path(__file__).resolve().parents[1]

    async def fake_runner(_root: Path, _question: str, mode: str, include_references: bool) -> str:
        assert mode == "mix"
        assert include_references is True
        return "The taxonomy seems to be described in docs/memory.md."

    pack = await build_context_pack(
        root,
        "which files define the repository memory taxonomy",
        mode="mix",
        task_type="general",
        query_runner=fake_runner,
    )

    assert isinstance(pack.raw_retrieval_result, str)
    assert pack.raw_retrieval_result.startswith("The canonical files that define the repository memory taxonomy are:")
    assert "`docs/project-idea.md`" in pack.raw_retrieval_result
    assert "docs/memory.md" not in pack.raw_retrieval_result


def test_shape_raw_retrieval_result_rewrites_setup_question_to_file_first_answer():
    result = shape_raw_retrieval_result(
        "The setup is probably somewhere in the docs.",
        question="Where is the local LightRAG pilot setup documented and what stack is fixed there",
        task_type="general",
        mandatory_paths=sorted(MANDATORY_DOCS),
        retrieved_paths=["docs/lightrag-local-pilot.md", "docs/context-policy.md"],
    )

    assert isinstance(result, str)
    assert result.startswith("The local LightRAG pilot setup is defined by:")
    assert "`docs/lightrag-local-pilot.md`" in result
    assert "`docs/context-policy.md`" in result


def test_shape_raw_retrieval_result_rewrites_feature_ownership_to_file_first_answer():
    result = shape_raw_retrieval_result(
        "042, 044, and 045 own different retrieval phases.",
        question="Which feature defined the retrieval MVP, which feature closed Q3 Q4 Q5 precision regressions, and which feature owns the broader benchmark",
        task_type="general",
        mandatory_paths=sorted(MANDATORY_DOCS),
        retrieved_paths=["specs/042-repo-memory-platform-lightrag/spec.md"],
    )

    assert isinstance(result, str)
    assert result.startswith("The canonical feature-memory files for retrieval ownership are:")
    assert "`specs/042-repo-memory-platform-lightrag/spec.md`" in result
    assert "`specs/045-retrieval-quality-benchmark/spec.md`" in result
