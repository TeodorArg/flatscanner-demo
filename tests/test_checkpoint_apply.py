from pathlib import Path

from src.repo_memory import checkpoint_apply as helper


def test_apply_neither_skips_all_steps():
    root = Path(__file__).resolve().parents[1]
    calls: list[list[str]] = []

    def fake_runner(current_root: Path, command: list[str]) -> helper.CommandResult:
        calls.append(command)
        return helper.CommandResult(command=command, stdout="", stderr="")

    result = helper.apply_checkpoint(
        root,
        ["notes/draft.txt"],
        command_runner=fake_runner,
    )

    assert result.decision == "neither"
    assert result.applied_steps == []
    assert result.skipped_steps == ["lightrag", "mcp_memory", "local_memory"]
    assert result.manual_follow_up == []
    assert calls == []


def test_apply_lightrag_only_runs_only_lightrag_step():
    root = Path(__file__).resolve().parents[1]
    calls: list[list[str]] = []

    def fake_runner(current_root: Path, command: list[str]) -> helper.CommandResult:
        calls.append(command)
        return helper.CommandResult(command=command, stdout="", stderr="")

    result = helper.apply_checkpoint(
        root,
        ["src/repo_memory/query_policy.py"],
        lightrag_dry_run=True,
        command_runner=fake_runner,
    )

    assert result.decision == "lightrag_only"
    assert result.applied_steps == ["lightrag"]
    assert result.skipped_steps == ["mcp_memory", "local_memory"]
    assert result.manual_follow_up == []
    assert len(calls) == 1
    assert calls[0][1].endswith("scripts/lightrag_pilot.py")
    assert calls[0][2:] == ["build", "--dry-run"]


def test_apply_mcp_local_only_runs_memory_then_local_validate(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    calls: list[list[str]] = []
    entity_file = "/tmp/entity.json"

    monkeypatch.setattr(
        helper,
        "decide_checkpoint_action",
        lambda *args, **kwargs: _decision(
            decision="mcp_local_only",
            changed_paths=["specs/052-checkpoint-apply-pipeline/tasks.md"],
            indexed=False,
            durable=True,
            local=True,
        ),
    )

    def fake_runner(current_root: Path, command: list[str]) -> helper.CommandResult:
        calls.append(command)
        return helper.CommandResult(command=command, stdout="", stderr="")

    result = helper.apply_checkpoint(
        root,
        ["specs/052-checkpoint-apply-pipeline/tasks.md"],
        memory_entity_files=[entity_file],
        command_runner=fake_runner,
    )

    assert result.applied_steps == ["mcp_memory", "local_memory"]
    assert result.skipped_steps == ["lightrag"]
    assert result.manual_follow_up == []
    assert len(calls) == 2
    assert calls[0][1].endswith("scripts/sync_memory.py")
    assert calls[0][2:] == ["upsert", "--json-file", entity_file]
    assert calls[1][1].endswith("scripts/sync_memory.py")
    assert calls[1][2:] == ["validate"]


def test_apply_both_requires_manual_memory_follow_up_without_entity_input(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    calls: list[list[str]] = []

    monkeypatch.setattr(
        helper,
        "decide_checkpoint_action",
        lambda *args, **kwargs: _decision(
            decision="both",
            changed_paths=["docs/context-policy.md"],
            indexed=True,
            durable=True,
            local=True,
        ),
    )

    def fake_runner(current_root: Path, command: list[str]) -> helper.CommandResult:
        calls.append(command)
        return helper.CommandResult(command=command, stdout="", stderr="")

    result = helper.apply_checkpoint(
        root,
        ["docs/context-policy.md"],
        command_runner=fake_runner,
    )

    assert result.applied_steps == ["lightrag"]
    assert result.manual_follow_up
    assert "memory-entity-file" in result.manual_follow_up[0]
    assert len(calls) == 1
    assert calls[0][1].endswith("scripts/lightrag_pilot.py")
    assert calls[0][2:] == ["build"]


def test_cli_text_output_reports_manual_follow_up(monkeypatch, capsys):
    monkeypatch.setattr(
        helper,
        "discover_changed_paths_from_git",
        lambda root, base_ref="HEAD": ["docs/context-policy.md"],
    )
    monkeypatch.setattr(
        helper,
        "apply_checkpoint",
        lambda *args, **kwargs: helper.CheckpointApplyResult(
            decision="both",
            changed_paths=["docs/context-policy.md"],
            indexed_corpus_changed=True,
            durable_repo_facts_changed=True,
            local_parity_recommended=True,
            applied_steps=["lightrag"],
            skipped_steps=[],
            manual_follow_up=["Provide memory entity input."],
            step_results=[
                helper.ApplyStepResult(
                    name="lightrag",
                    status="applied",
                    detail="Applied the canonical LightRAG build validation path.",
                )
            ],
            reasons=["Final decision: `both`."],
        ),
    )

    exit_code = helper.main(["apply", "--git-diff", "--format", "text"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "decision: both" in captured.out
    assert "manual_follow_up:" in captured.out
    assert "- Provide memory entity input." in captured.out


def _decision(
    *,
    decision: str,
    changed_paths: list[str],
    indexed: bool,
    durable: bool,
    local: bool,
) -> helper.CheckpointDecision:
    return helper.CheckpointDecision(
        decision=decision,
        changed_paths=changed_paths,
        indexed_corpus_changed=indexed,
        durable_repo_facts_changed=durable,
        local_parity_recommended=local,
        reasons=[f"Final decision: `{decision}`."],
    )
