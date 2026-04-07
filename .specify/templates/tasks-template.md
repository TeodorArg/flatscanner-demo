# Tasks: <feature-name>

## Spec

- [ ] Confirm requirements
- [ ] Confirm acceptance criteria

## Implementation

- [ ] Update code
- [ ] Add or update tests

## Validation

- [ ] Run relevant checks
- [ ] Run `python scripts/checkpoint_decision.py decide --git-diff`
- [ ] Apply checkpoint outcome:
- [ ] If needed, run `LightRAG` refresh/rebuild validation
- [ ] If needed, update MCP memory
- [ ] If useful, refresh local `in_memory/memory.jsonl`
- [ ] Prepare PR notes
