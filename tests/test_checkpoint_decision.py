from pathlib import Path

from src.repo_memory import checkpoint_decision as helper


def test_load_indexed_corpus_allowlist_reads_current_context_policy():
    root = Path(__file__).resolve().parents[1]

    allowlist = helper.load_indexed_corpus_allowlist(root)

    assert "docs/context-policy.md" in allowlist
    assert "src/repo_memory/query_policy.py" in allowlist
    assert "docs/ai-pr-workflow.md" not in allowlist


def test_decide_neither_for_non_durable_non_indexed_change():
    root = Path(__file__).resolve().parents[1]

    decision = helper.decide_checkpoint_action(root, ["in_memory/memory.jsonl"])

    assert decision.decision == "neither"
    assert decision.indexed_corpus_changed is False
    assert decision.durable_repo_facts_changed is False
    assert decision.local_parity_recommended is False


def test_decide_lightrag_only_for_indexed_implementation_change():
    root = Path(__file__).resolve().parents[1]

    decision = helper.decide_checkpoint_action(root, ["src/repo_memory/query_policy.py"])

    assert decision.decision == "lightrag_only"
    assert decision.indexed_corpus_changed is True
    assert decision.durable_repo_facts_changed is False
    assert decision.local_parity_recommended is False


def test_decide_mcp_local_only_for_mirrored_feature_memory_change(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(
        helper,
        "load_local_memory_entity_names",
        lambda current_root: {"Feature: 051-checkpoint-decision-helper"},
    )

    decision = helper.decide_checkpoint_action(root, ["specs/051-checkpoint-decision-helper/tasks.md"])

    assert decision.decision == "mcp_local_only"
    assert decision.indexed_corpus_changed is False
    assert decision.durable_repo_facts_changed is True
    assert decision.local_parity_recommended is True


def test_decide_both_for_indexed_repo_policy_change(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(
        helper,
        "load_local_memory_entity_names",
        lambda current_root: {"Project: flatscanner-demo repo-memory migration"},
    )

    decision = helper.decide_checkpoint_action(root, ["docs/context-policy.md"])

    assert decision.decision == "both"
    assert decision.indexed_corpus_changed is True
    assert decision.durable_repo_facts_changed is True
    assert decision.local_parity_recommended is True


def test_decide_mcp_local_only_without_local_parity_for_unmirrored_feature():
    root = Path(__file__).resolve().parents[1]

    decision = helper.decide_checkpoint_action(root, ["specs/999-example/tasks.md"])

    assert decision.decision == "mcp_local_only"
    assert decision.indexed_corpus_changed is False
    assert decision.durable_repo_facts_changed is True
    assert decision.local_parity_recommended is False


def test_durable_override_supports_wording_only_repo_doc_changes():
    root = Path(__file__).resolve().parents[1]

    decision = helper.decide_checkpoint_action(
        root,
        ["docs/context-economy-workflow.md"],
        durable_facts_override=False,
    )

    assert decision.decision == "neither"
    assert decision.indexed_corpus_changed is False
    assert decision.durable_repo_facts_changed is False


def test_cli_text_output_uses_git_diff_when_requested(monkeypatch, capsys):
    monkeypatch.setattr(
        helper,
        "discover_changed_paths_from_git",
        lambda root, base_ref="HEAD": ["docs/context-policy.md"],
    )

    exit_code = helper.main(["decide", "--git-diff", "--format", "text"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "decision: both" in captured.out
    assert "- docs/context-policy.md" in captured.out
