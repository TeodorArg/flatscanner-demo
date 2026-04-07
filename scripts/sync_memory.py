#!/usr/bin/env python3
"""Manage the local MCP memory mirror stored in JSONL.

This helper keeps `in_memory/memory.jsonl` easy to update manually after
durable doc/spec changes. The configured MCP memory server already uses the
same file as its backing store, so updating this file updates the local memory
snapshot used by the repository.

Examples:
    python scripts/sync_memory.py validate
    python scripts/sync_memory.py upsert \\
        --name "Project: flatscanner-demo repo-memory migration" \\
        --entity-type project \\
        --observation "Phase 5 chunking rules were documented."
    python scripts/sync_memory.py upsert --json-file /tmp/entity.json
    python scripts/sync_memory.py remove-observation \\
        --name "Project: flatscanner-demo repo-memory migration" \\
        --observation "Phase 5 chunking rules were documented."
    python scripts/sync_memory.py delete-entity \\
        --name "Project: flatscanner-demo repo-memory migration"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MEMORY_FILE = REPO_ROOT / "in_memory" / "memory.jsonl"


def load_entities(memory_file: Path) -> list[dict[str, Any]]:
    if not memory_file.exists():
        return []

    entities: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(memory_file.read_text().splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            entity = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSON in {memory_file} on line {line_number}: {exc}"
            ) from exc
        validate_entity(entity, context=f"{memory_file}:{line_number}")
        entities.append(entity)
    return entities


def write_entities(memory_file: Path, entities: list[dict[str, Any]]) -> None:
    memory_file.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(entity, ensure_ascii=False, separators=(",", ":"))
        for entity in entities
    ]
    content = "\n".join(lines)
    if content:
        content += "\n"
    memory_file.write_text(content)


def validate_entity(entity: dict[str, Any], *, context: str) -> None:
    if not isinstance(entity, dict):
        raise ValueError(f"{context}: entity must be a JSON object")

    required_fields = ("name", "entityType", "observations")
    for field in required_fields:
        if field not in entity:
            raise ValueError(f"{context}: missing required field {field!r}")

    if not isinstance(entity["name"], str) or not entity["name"].strip():
        raise ValueError(f"{context}: 'name' must be a non-empty string")
    if not isinstance(entity["entityType"], str) or not entity["entityType"].strip():
        raise ValueError(f"{context}: 'entityType' must be a non-empty string")
    if not isinstance(entity["observations"], list):
        raise ValueError(f"{context}: 'observations' must be an array")
    for index, observation in enumerate(entity["observations"], start=1):
        if not isinstance(observation, str) or not observation.strip():
            raise ValueError(
                f"{context}: observations[{index}] must be a non-empty string"
            )


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def build_entity_from_args(args: argparse.Namespace) -> dict[str, Any]:
    if args.json_file:
        entity = json.loads(Path(args.json_file).read_text())
        validate_entity(entity, context=str(args.json_file))
        return entity

    if not args.name or not args.entity_type:
        raise ValueError("--name and --entity-type are required unless --json-file is used")
    if not args.observation:
        raise ValueError("At least one --observation is required unless --json-file is used")

    entity = {
        "name": args.name,
        "entityType": args.entity_type,
        "observations": dedupe_preserve_order(args.observation),
    }
    validate_entity(entity, context="command line")
    return entity


def upsert_entity(
    entities: list[dict[str, Any]],
    entity: dict[str, Any],
    *,
    replace_observations: bool,
) -> tuple[list[dict[str, Any]], str]:
    existing_index = next(
        (index for index, current in enumerate(entities) if current["name"] == entity["name"]),
        None,
    )

    if existing_index is None:
        entities.append(entity)
        return entities, "created"

    current = entities[existing_index]
    current["entityType"] = entity["entityType"]
    if replace_observations:
        current["observations"] = dedupe_preserve_order(entity["observations"])
    else:
        merged = current["observations"] + entity["observations"]
        current["observations"] = dedupe_preserve_order(merged)
    entities[existing_index] = current
    return entities, "updated"


def remove_observations_from_entity(
    entities: list[dict[str, Any]],
    *,
    name: str,
    observations_to_remove: list[str],
) -> tuple[list[dict[str, Any]], int]:
    existing_index = next(
        (index for index, current in enumerate(entities) if current["name"] == name),
        None,
    )
    if existing_index is None:
        raise ValueError(f"Entity {name!r} was not found")

    current = entities[existing_index]
    remove_set = set(observations_to_remove)
    original_count = len(current["observations"])
    current["observations"] = [
        observation
        for observation in current["observations"]
        if observation not in remove_set
    ]
    removed_count = original_count - len(current["observations"])
    if removed_count == 0:
        raise ValueError(f"No matching observations were found in entity {name!r}")
    if not current["observations"]:
        raise ValueError(
            f"Removing these observations would leave entity {name!r} empty; "
            "use delete-entity instead"
        )
    entities[existing_index] = current
    return entities, removed_count


def delete_entity(
    entities: list[dict[str, Any]],
    *,
    name: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    existing_index = next(
        (index for index, current in enumerate(entities) if current["name"] == name),
        None,
    )
    if existing_index is None:
        raise ValueError(f"Entity {name!r} was not found")

    removed = entities.pop(existing_index)
    return entities, removed


def resolve_memory_file(args: argparse.Namespace) -> Path:
    explicit = getattr(args, "memory_file", None)
    if explicit:
        return Path(explicit).expanduser().resolve()

    env_value = os.getenv("MEMORY_FILE_PATH")
    if env_value:
        return Path(env_value).expanduser().resolve()

    return DEFAULT_MEMORY_FILE


def cmd_validate(args: argparse.Namespace) -> int:
    memory_file = resolve_memory_file(args)
    entities = load_entities(memory_file)
    print(f"[OK] Validated {len(entities)} entities in {memory_file}")
    return 0


def cmd_upsert(args: argparse.Namespace) -> int:
    memory_file = resolve_memory_file(args)
    entities = load_entities(memory_file)
    entity = build_entity_from_args(args)
    entities, status = upsert_entity(
        entities,
        entity,
        replace_observations=args.replace_observations,
    )
    write_entities(memory_file, entities)
    observation_count = len(entity["observations"])
    print(
        f"[OK] {status} entity {entity['name']!r} with {observation_count} "
        f"observation(s) in {memory_file}"
    )
    return 0


def cmd_remove_observation(args: argparse.Namespace) -> int:
    memory_file = resolve_memory_file(args)
    entities = load_entities(memory_file)
    if not args.name:
        raise ValueError("--name is required")
    if not args.observation:
        raise ValueError("At least one --observation is required")
    entities, removed_count = remove_observations_from_entity(
        entities,
        name=args.name,
        observations_to_remove=dedupe_preserve_order(args.observation),
    )
    write_entities(memory_file, entities)
    print(
        f"[OK] removed {removed_count} observation(s) from entity "
        f"{args.name!r} in {memory_file}"
    )
    return 0


def cmd_delete_entity(args: argparse.Namespace) -> int:
    memory_file = resolve_memory_file(args)
    entities = load_entities(memory_file)
    if not args.name:
        raise ValueError("--name is required")
    entities, removed = delete_entity(entities, name=args.name)
    write_entities(memory_file, entities)
    print(
        f"[OK] deleted entity {removed['name']!r} "
        f"({removed['entityType']}) from {memory_file}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate or update the local JSONL memory mirror."
    )
    parser.add_argument(
        "--memory-file",
        help=(
            "Path to memory.jsonl. Defaults to MEMORY_FILE_PATH from the "
            "environment or the repository-local in_memory/memory.jsonl."
        ),
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser(
        "validate", help="Validate the configured memory.jsonl file."
    )
    validate_parser.set_defaults(func=cmd_validate)

    upsert_parser = subparsers.add_parser(
        "upsert", help="Create or update one entity snapshot."
    )
    upsert_parser.add_argument("--name", help="Stable entity name.")
    upsert_parser.add_argument("--entity-type", help="Entity class, for example project.")
    upsert_parser.add_argument(
        "--observation",
        action="append",
        help="Observation to add. Repeat the flag for multiple observations.",
    )
    upsert_parser.add_argument(
        "--json-file",
        help="Path to a JSON file containing one full entity object.",
    )
    upsert_parser.add_argument(
        "--replace-observations",
        action="store_true",
        help="Replace existing observations instead of merging unique values.",
    )
    upsert_parser.set_defaults(func=cmd_upsert)

    remove_parser = subparsers.add_parser(
        "remove-observation",
        help="Remove one or more observations from an existing entity.",
    )
    remove_parser.add_argument("--name", help="Stable entity name.")
    remove_parser.add_argument(
        "--observation",
        action="append",
        help="Observation to remove. Repeat the flag for multiple observations.",
    )
    remove_parser.set_defaults(func=cmd_remove_observation)

    delete_parser = subparsers.add_parser(
        "delete-entity", help="Delete one entity snapshot by name."
    )
    delete_parser.add_argument("--name", help="Stable entity name.")
    delete_parser.set_defaults(func=cmd_delete_entity)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
