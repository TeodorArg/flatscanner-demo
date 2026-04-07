from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
import re

from .pilot_config import repo_root


DECISION_CHOICES = (
    "neither",
    "lightrag_only",
    "mcp_local_only",
    "both",
)
TRISTATE_CHOICES = ("auto", "yes", "no")
POLICY_SECTION_START = "### Included In Pilot Corpus"
POLICY_SECTION_END = "### Explicitly Excluded From Pilot Corpus"
POLICY_PATH_RE = re.compile(r"^- `([^`]+)`\s*$")
FEATURE_MEMORY_RE = re.compile(r"^specs/([^/]+)/(spec|plan|tasks)\.md$")
ADR_PATH_RE = re.compile(r"^docs/adr/[^/]+\.md$")

REPO_SCOPED_DURABLE_PATHS = {
    ".specify/memory/constitution.md",
    "AGENTS.md",
    "README_PROCESS_RU.md",
    "PROCESS_OVERVIEW_EN.md",
    "DELIVERY_FLOW_RU.md",
    "docs/README.md",
    "docs/project-idea.md",
    "docs/project/frontend/frontend-docs.md",
    "docs/project/backend/backend-docs.md",
    "docs/ai-pr-workflow.md",
    "docs/context-policy.md",
    "docs/context-economy-workflow.md",
    "docs/local-memory-sync.md",
    "docs/lightrag-local-pilot.md",
}


@dataclass(frozen=True)
class CheckpointDecision:
    decision: str
    changed_paths: list[str]
    indexed_corpus_changed: bool
    durable_repo_facts_changed: bool
    local_parity_recommended: bool
    reasons: list[str]


def _parse_tristate(value: str) -> bool | None:
    if value == "yes":
        return True
    if value == "no":
        return False
    return None


def normalize_changed_paths(root: Path, paths: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    base = root.resolve()

    for raw_path in paths:
        candidate = raw_path.strip()
        if not candidate:
            continue
        path = Path(candidate)
        if path.is_absolute():
            try:
                candidate = path.resolve().relative_to(base).as_posix()
            except ValueError:
                candidate = path.as_posix()
        else:
            candidate = path.as_posix().removeprefix("./")
        if candidate in seen:
            continue
        seen.add(candidate)
        normalized.append(candidate)

    return normalized


def load_indexed_corpus_allowlist(root: Path) -> set[str]:
    policy_path = root / "docs" / "context-policy.md"
    lines = policy_path.read_text().splitlines()
    in_section = False
    allowlist: set[str] = set()

    for line in lines:
        if line.strip() == POLICY_SECTION_START:
            in_section = True
            continue
        if line.strip() == POLICY_SECTION_END:
            break
        if not in_section:
            continue
        match = POLICY_PATH_RE.match(line.strip())
        if match:
            allowlist.add(match.group(1))

    if not allowlist:
        raise ValueError("Unable to parse indexed pilot corpus allowlist from docs/context-policy.md")

    return allowlist


def load_local_memory_entity_names(root: Path) -> set[str]:
    memory_path = root / "in_memory" / "memory.jsonl"
    if not memory_path.exists():
        return set()

    entity_names: set[str] = set()
    for raw_line in memory_path.read_text().splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        name = payload.get("name")
        if isinstance(name, str) and name.strip():
            entity_names.add(name)
    return entity_names


def discover_changed_paths_from_git(root: Path, base_ref: str = "HEAD") -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", base_ref, "--"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _detect_indexed_corpus_changed(
    changed_paths: list[str],
    indexed_allowlist: set[str],
) -> tuple[bool, list[str]]:
    matched_paths = [path for path in changed_paths if path in indexed_allowlist]
    if matched_paths:
        return True, [
            "Indexed pilot corpus changed: " + ", ".join(f"`{path}`" for path in matched_paths)
        ]
    return False, ["Indexed pilot corpus unchanged for the supplied paths."]


def _detect_durable_repo_facts_changed(
    changed_paths: list[str],
) -> tuple[bool, list[str], set[str]]:
    feature_ids: set[str] = set()
    reasons: list[str] = []

    feature_paths: list[str] = []
    repo_paths: list[str] = []
    adr_paths: list[str] = []

    for path in changed_paths:
        feature_match = FEATURE_MEMORY_RE.match(path)
        if feature_match:
            feature_ids.add(feature_match.group(1))
            feature_paths.append(path)
            continue
        if ADR_PATH_RE.match(path):
            adr_paths.append(path)
            continue
        if path in REPO_SCOPED_DURABLE_PATHS:
            repo_paths.append(path)

    if feature_paths:
        reasons.append(
            "Feature memory changed on canonical files: "
            + ", ".join(f"`{path}`" for path in feature_paths)
        )
    if adr_paths:
        reasons.append(
            "ADR files changed and count as durable architecture decisions: "
            + ", ".join(f"`{path}`" for path in adr_paths)
        )
    if repo_paths:
        reasons.append(
            "Repo-scoped canonical policy/docs changed: "
            + ", ".join(f"`{path}`" for path in repo_paths)
        )

    if reasons:
        return True, reasons, feature_ids
    return False, ["No durable repo-fact trigger matched the supplied paths."], feature_ids


def _detect_local_parity_recommended(
    root: Path,
    changed_paths: list[str],
    durable_repo_facts_changed: bool,
    feature_ids: set[str],
) -> tuple[bool, list[str]]:
    if not durable_repo_facts_changed:
        return False, ["Local parity is unnecessary because no durable repo facts changed."]

    entity_names = load_local_memory_entity_names(root)
    feature_entities = {f"Feature: {feature_id}" for feature_id in feature_ids}
    mirrored_features = sorted(feature_entities & entity_names)
    repo_scope_touched = any(
        path in REPO_SCOPED_DURABLE_PATHS or ADR_PATH_RE.match(path) for path in changed_paths
    )

    if mirrored_features:
        return True, [
            "Local parity is useful because the changed feature already has a mirrored MCP entity: "
            + ", ".join(f"`{name}`" for name in mirrored_features)
        ]

    if repo_scope_touched and any(name.startswith("Project: ") for name in entity_names):
        return True, [
            "Local parity is useful because repo-scoped durable docs changed and the project entity is mirrored locally."
        ]

    return False, [
        "Local parity is not recommended automatically because no matching mirrored feature/project entity was detected."
    ]


def decide_checkpoint_action(
    root: Path,
    changed_paths: list[str],
    *,
    durable_facts_override: bool | None = None,
    local_parity_override: bool | None = None,
) -> CheckpointDecision:
    normalized_paths = normalize_changed_paths(root, changed_paths)
    indexed_allowlist = load_indexed_corpus_allowlist(root)

    indexed_corpus_changed, indexed_reasons = _detect_indexed_corpus_changed(
        normalized_paths,
        indexed_allowlist,
    )
    detected_durable_repo_facts_changed, durable_reasons, feature_ids = (
        _detect_durable_repo_facts_changed(normalized_paths)
    )

    if durable_facts_override is None:
        durable_repo_facts_changed = detected_durable_repo_facts_changed
        durable_reason_prefix = "Durable fact detection used automatic path-based classification."
    else:
        durable_repo_facts_changed = durable_facts_override
        durable_reason_prefix = (
            "Durable fact detection was overridden explicitly to "
            f"`{str(durable_facts_override).lower()}`."
        )

    detected_local_parity_recommended, local_parity_reasons = _detect_local_parity_recommended(
        root,
        normalized_paths,
        durable_repo_facts_changed,
        feature_ids,
    )
    if local_parity_override is None:
        local_parity_recommended = detected_local_parity_recommended
        local_parity_prefix = "Local parity evaluation used automatic mirror-aware classification."
    else:
        local_parity_recommended = local_parity_override
        local_parity_prefix = (
            "Local parity evaluation was overridden explicitly to "
            f"`{str(local_parity_override).lower()}`."
        )

    if indexed_corpus_changed and durable_repo_facts_changed:
        decision = "both"
    elif indexed_corpus_changed:
        decision = "lightrag_only"
    elif durable_repo_facts_changed:
        decision = "mcp_local_only"
    else:
        decision = "neither"

    reasons = [
        f"Final decision: `{decision}`.",
        *indexed_reasons,
        durable_reason_prefix,
        *durable_reasons,
        local_parity_prefix,
        *local_parity_reasons,
    ]

    return CheckpointDecision(
        decision=decision,
        changed_paths=normalized_paths,
        indexed_corpus_changed=indexed_corpus_changed,
        durable_repo_facts_changed=durable_repo_facts_changed,
        local_parity_recommended=local_parity_recommended,
        reasons=reasons,
    )


def format_text_report(decision: CheckpointDecision) -> str:
    lines = [
        f"decision: {decision.decision}",
        f"indexed_corpus_changed: {str(decision.indexed_corpus_changed).lower()}",
        f"durable_repo_facts_changed: {str(decision.durable_repo_facts_changed).lower()}",
        f"local_parity_recommended: {str(decision.local_parity_recommended).lower()}",
        "changed_paths:",
    ]
    if decision.changed_paths:
        lines.extend(f"- {path}" for path in decision.changed_paths)
    else:
        lines.append("- <none>")
    lines.append("reasons:")
    lines.extend(f"- {reason}" for reason in decision.reasons)
    return "\n".join(lines)


def cmd_decide(args: argparse.Namespace) -> int:
    root = repo_root()
    changed_paths: list[str] = []
    if args.git_diff or not args.path:
        changed_paths.extend(discover_changed_paths_from_git(root, base_ref=args.git_base))
    changed_paths.extend(args.path)

    decision = decide_checkpoint_action(
        root,
        changed_paths,
        durable_facts_override=_parse_tristate(args.durable_facts),
        local_parity_override=_parse_tristate(args.local_parity),
    )

    if args.format == "text":
        print(format_text_report(decision))
    else:
        print(json.dumps(asdict(decision), indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Recommend the checkpoint action for LightRAG versus MCP/local sync."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    decide_parser = subparsers.add_parser(
        "decide",
        help="Classify the current checkpoint as neither, lightrag_only, mcp_local_only, or both.",
    )
    decide_parser.add_argument(
        "--path",
        action="append",
        default=[],
        help="Changed path relative to the repository root. Repeat for multiple paths.",
    )
    decide_parser.add_argument(
        "--git-diff",
        action="store_true",
        help="Also include changed paths from `git diff --name-only <git-base>`.",
    )
    decide_parser.add_argument(
        "--git-base",
        default="HEAD",
        help="Git base used with --git-diff. Defaults to HEAD.",
    )
    decide_parser.add_argument(
        "--durable-facts",
        choices=TRISTATE_CHOICES,
        default="auto",
        help="Override durable-fact detection when path-only heuristics are insufficient.",
    )
    decide_parser.add_argument(
        "--local-parity",
        choices=TRISTATE_CHOICES,
        default="auto",
        help="Override local parity recommendation when needed.",
    )
    decide_parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format.",
    )
    decide_parser.set_defaults(func=cmd_decide)

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
