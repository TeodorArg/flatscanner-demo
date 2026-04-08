from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from .checkpoint_decision import (
    CheckpointDecision,
    TRISTATE_CHOICES,
    _parse_tristate,
    decide_checkpoint_action,
    discover_changed_paths_from_git,
)
from .pilot_config import repo_root


STEP_LIGHTRAG = "lightrag"
STEP_MCP_MEMORY = "mcp_memory"
STEP_LOCAL_MEMORY = "local_memory"
STEP_STATUS_APPLIED = "applied"
STEP_STATUS_SKIPPED = "skipped"
STEP_STATUS_MANUAL = "manual_follow_up"


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    stdout: str
    stderr: str


@dataclass(frozen=True)
class ApplyStepResult:
    name: str
    status: str
    detail: str
    command: list[str] | None = None


@dataclass(frozen=True)
class CheckpointApplyResult:
    decision: str
    changed_paths: list[str]
    indexed_corpus_changed: bool
    durable_repo_facts_changed: bool
    local_parity_recommended: bool
    applied_steps: list[str]
    skipped_steps: list[str]
    manual_follow_up: list[str]
    step_results: list[ApplyStepResult]
    reasons: list[str]


CommandRunner = Callable[[Path, list[str]], CommandResult]


def _run_repo_command(root: Path, command: list[str]) -> CommandResult:
    completed = subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return CommandResult(
        command=command,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )


def _build_lightrag_command(root: Path, *, clean: bool, dry_run: bool) -> list[str]:
    command = [sys.executable, str(root / "scripts" / "lightrag_pilot.py"), "build"]
    if clean:
        command.append("--clean")
    if dry_run:
        command.append("--dry-run")
    return command


def _build_sync_memory_upsert_command(
    root: Path,
    *,
    entity_file: str,
    memory_file: str | None,
) -> list[str]:
    command = [
        sys.executable,
        str(root / "scripts" / "sync_memory.py"),
        "upsert",
        "--json-file",
        entity_file,
    ]
    if memory_file:
        command[2:2] = ["--memory-file", memory_file]
    return command


def _build_sync_memory_validate_command(root: Path, *, memory_file: str | None) -> list[str]:
    command = [sys.executable, str(root / "scripts" / "sync_memory.py")]
    if memory_file:
        command.extend(["--memory-file", memory_file])
    command.append("validate")
    return command


def _build_apply_result(
    checkpoint: CheckpointDecision,
    step_results: list[ApplyStepResult],
    manual_follow_up: list[str],
) -> CheckpointApplyResult:
    applied_steps = [step.name for step in step_results if step.status == STEP_STATUS_APPLIED]
    skipped_steps = [step.name for step in step_results if step.status == STEP_STATUS_SKIPPED]
    return CheckpointApplyResult(
        decision=checkpoint.decision,
        changed_paths=checkpoint.changed_paths,
        indexed_corpus_changed=checkpoint.indexed_corpus_changed,
        durable_repo_facts_changed=checkpoint.durable_repo_facts_changed,
        local_parity_recommended=checkpoint.local_parity_recommended,
        applied_steps=applied_steps,
        skipped_steps=skipped_steps,
        manual_follow_up=manual_follow_up,
        step_results=step_results,
        reasons=checkpoint.reasons,
    )


def apply_checkpoint(
    root: Path,
    changed_paths: list[str],
    *,
    durable_facts_override: bool | None = None,
    local_parity_override: bool | None = None,
    memory_entity_files: list[str] | None = None,
    memory_file: str | None = None,
    lightrag_clean: bool = False,
    lightrag_dry_run: bool = False,
    command_runner: CommandRunner = _run_repo_command,
) -> CheckpointApplyResult:
    checkpoint = decide_checkpoint_action(
        root,
        changed_paths,
        durable_facts_override=durable_facts_override,
        local_parity_override=local_parity_override,
    )

    step_results: list[ApplyStepResult] = []
    manual_follow_up: list[str] = []
    entity_files = list(memory_entity_files or [])

    if checkpoint.decision in {"lightrag_only", "both"}:
        command = _build_lightrag_command(
            root,
            clean=lightrag_clean,
            dry_run=lightrag_dry_run,
        )
        command_runner(root, command)
        detail = "Applied the canonical LightRAG build validation path."
        if lightrag_clean:
            detail = "Applied the canonical LightRAG clean rebuild validation path."
        if lightrag_dry_run:
            detail = "Applied the LightRAG dry-run validation path for checkpoint review."
        step_results.append(
            ApplyStepResult(
                name=STEP_LIGHTRAG,
                status=STEP_STATUS_APPLIED,
                detail=detail,
                command=command,
            )
        )
    else:
        step_results.append(
            ApplyStepResult(
                name=STEP_LIGHTRAG,
                status=STEP_STATUS_SKIPPED,
                detail="Skipped because the checkpoint decision does not require LightRAG work.",
            )
        )

    if checkpoint.decision in {"mcp_local_only", "both"}:
        if entity_files:
            for entity_file in entity_files:
                command_runner(
                    root,
                    _build_sync_memory_upsert_command(
                        root,
                        entity_file=entity_file,
                        memory_file=memory_file,
                    ),
                )
            step_results.append(
                ApplyStepResult(
                    name=STEP_MCP_MEMORY,
                    status=STEP_STATUS_APPLIED,
                    detail=(
                        "Applied the repository-local memory sync path from explicit entity snapshots. "
                        f"Entity files: {', '.join(entity_files)}"
                    ),
                    command=_build_sync_memory_upsert_command(
                        root,
                        entity_file="<entity-file>",
                        memory_file=memory_file,
                    ),
                )
            )
            if checkpoint.local_parity_recommended:
                validate_command = _build_sync_memory_validate_command(
                    root,
                    memory_file=memory_file,
                )
                command_runner(root, validate_command)
                step_results.append(
                    ApplyStepResult(
                        name=STEP_LOCAL_MEMORY,
                        status=STEP_STATUS_APPLIED,
                        detail=(
                            "Validated local memory parity after MCP-backed sync because local parity "
                            "was recommended for this checkpoint."
                        ),
                        command=validate_command,
                    )
                )
            else:
                step_results.append(
                    ApplyStepResult(
                        name=STEP_LOCAL_MEMORY,
                        status=STEP_STATUS_SKIPPED,
                        detail="Skipped because local parity is not recommended for this checkpoint.",
                    )
                )
        else:
            manual_reason = (
                "Checkpoint decision requires MCP/local apply, but no `--memory-entity-file` inputs "
                "were provided for durable facts already recorded in canonical files."
            )
            manual_follow_up.append(manual_reason)
            step_results.append(
                ApplyStepResult(
                    name=STEP_MCP_MEMORY,
                    status=STEP_STATUS_MANUAL,
                    detail=manual_reason,
                )
            )
            local_detail = (
                "Local parity cannot be refreshed automatically because the MCP/local apply input "
                "was not provided."
            )
            if checkpoint.local_parity_recommended:
                manual_follow_up.append(local_detail)
                step_results.append(
                    ApplyStepResult(
                        name=STEP_LOCAL_MEMORY,
                        status=STEP_STATUS_MANUAL,
                        detail=local_detail,
                    )
                )
            else:
                step_results.append(
                    ApplyStepResult(
                        name=STEP_LOCAL_MEMORY,
                        status=STEP_STATUS_SKIPPED,
                        detail="Skipped because local parity is not recommended for this checkpoint.",
                    )
                )
    else:
        step_results.append(
            ApplyStepResult(
                name=STEP_MCP_MEMORY,
                status=STEP_STATUS_SKIPPED,
                detail="Skipped because the checkpoint decision does not require MCP memory work.",
            )
        )
        step_results.append(
            ApplyStepResult(
                name=STEP_LOCAL_MEMORY,
                status=STEP_STATUS_SKIPPED,
                detail="Skipped because the checkpoint decision does not require local parity work.",
            )
        )

    return _build_apply_result(
        checkpoint,
        step_results=step_results,
        manual_follow_up=manual_follow_up,
    )


def format_text_report(result: CheckpointApplyResult) -> str:
    lines = [
        f"decision: {result.decision}",
        f"indexed_corpus_changed: {str(result.indexed_corpus_changed).lower()}",
        f"durable_repo_facts_changed: {str(result.durable_repo_facts_changed).lower()}",
        f"local_parity_recommended: {str(result.local_parity_recommended).lower()}",
        "changed_paths:",
    ]
    if result.changed_paths:
        lines.extend(f"- {path}" for path in result.changed_paths)
    else:
        lines.append("- <none>")
    lines.append("applied_steps:")
    if result.applied_steps:
        lines.extend(f"- {step}" for step in result.applied_steps)
    else:
        lines.append("- <none>")
    lines.append("skipped_steps:")
    if result.skipped_steps:
        lines.extend(f"- {step}" for step in result.skipped_steps)
    else:
        lines.append("- <none>")
    lines.append("manual_follow_up:")
    if result.manual_follow_up:
        lines.extend(f"- {item}" for item in result.manual_follow_up)
    else:
        lines.append("- <none>")
    lines.append("step_results:")
    for step in result.step_results:
        lines.append(f"- {step.name}: {step.status} :: {step.detail}")
        if step.command:
            lines.append(f"  command: {' '.join(step.command)}")
    lines.append("reasons:")
    lines.extend(f"- {reason}" for reason in result.reasons)
    return "\n".join(lines)


def cmd_apply(args: argparse.Namespace) -> int:
    root = repo_root()
    changed_paths: list[str] = []
    if args.git_diff or not args.path:
        changed_paths.extend(discover_changed_paths_from_git(root, base_ref=args.git_base))
    changed_paths.extend(args.path)

    result = apply_checkpoint(
        root,
        changed_paths,
        durable_facts_override=_parse_tristate(args.durable_facts),
        local_parity_override=_parse_tristate(args.local_parity),
        memory_entity_files=args.memory_entity_file,
        memory_file=args.memory_file,
        lightrag_clean=args.lightrag_clean,
        lightrag_dry_run=args.lightrag_dry_run,
    )

    if args.format == "text":
        print(format_text_report(result))
    else:
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))

    return 2 if result.manual_follow_up else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Apply the checkpoint outcome for LightRAG versus MCP/local sync."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    apply_parser = subparsers.add_parser(
        "apply",
        help="Run checkpoint classification first, then apply the required downstream steps.",
    )
    apply_parser.add_argument(
        "--path",
        action="append",
        default=[],
        help="Changed path relative to the repository root. Repeat for multiple paths.",
    )
    apply_parser.add_argument(
        "--git-diff",
        action="store_true",
        help="Also include changed paths from `git diff --name-only <git-base>`.",
    )
    apply_parser.add_argument(
        "--git-base",
        default="HEAD",
        help="Git base used with --git-diff. Defaults to HEAD.",
    )
    apply_parser.add_argument(
        "--durable-facts",
        choices=TRISTATE_CHOICES,
        default="auto",
        help="Override durable-fact detection when path-only heuristics are insufficient.",
    )
    apply_parser.add_argument(
        "--local-parity",
        choices=TRISTATE_CHOICES,
        default="auto",
        help="Override local parity recommendation when needed.",
    )
    apply_parser.add_argument(
        "--memory-entity-file",
        action="append",
        default=[],
        help="JSON file with one durable memory entity snapshot. Repeat for multiple entities.",
    )
    apply_parser.add_argument(
        "--memory-file",
        default=None,
        help="Optional path passed through to scripts/sync_memory.py.",
    )
    apply_parser.add_argument(
        "--lightrag-clean",
        action="store_true",
        help="Use a clean LightRAG rebuild instead of the default refresh/build path.",
    )
    apply_parser.add_argument(
        "--lightrag-dry-run",
        action="store_true",
        help="Run the LightRAG build path in dry-run mode.",
    )
    apply_parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format.",
    )
    apply_parser.set_defaults(func=cmd_apply)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except subprocess.CalledProcessError as exc:
        print(exc.stderr.strip() or str(exc), file=sys.stderr)
        return exc.returncode or 1
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
