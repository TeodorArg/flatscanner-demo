from __future__ import annotations

import json
import re
from dataclasses import asdict
from hashlib import sha1
from pathlib import Path

from .pilot_config import (
    HEADING_RE,
    MANDATORY_DOCS,
    MAX_CHUNK_CHARS,
    MIN_SECTION_CHARS,
    PILOT_CORPUS,
    corpus_paths,
    pilot_working_dir,
    relative_repo_path,
    repo_root,
)
from .pilot_types import MarkdownSection, PreparedChunk


def doc_class_for_path(relative_path: str) -> str:
    if relative_path.startswith(".specify/"):
        return "process_memory"
    if relative_path in {
        "AGENTS.md",
        "README_PROCESS_RU.md",
        "PROCESS_OVERVIEW_EN.md",
        "DELIVERY_FLOW_RU.md",
    }:
        return "process_memory"
    if relative_path.startswith("specs/"):
        return "feature_memory"
    if relative_path.startswith("docs/"):
        return "durable_doc"
    if relative_path.startswith("src/"):
        return "implementation_code"
    if relative_path.startswith("tests/"):
        return "test_code"
    return "draft"


def feature_id_for_path(relative_path: str) -> str | None:
    if not relative_path.startswith("specs/"):
        return None
    parts = relative_path.split("/")
    return parts[1] if len(parts) > 1 else None


def detect_language(relative_path: str, content: str) -> str:
    filename = Path(relative_path).name
    if "_RU" in filename:
        return "ru"
    if "_EN" in filename:
        return "en"

    cyrillic_chars = len(re.findall(r"[А-Яа-яЁё]", content))
    latin_chars = len(re.findall(r"[A-Za-z]", content))
    return "ru" if cyrillic_chars > latin_chars else "en"


def extract_title(relative_path: str, content: str) -> str:
    for line in content.splitlines():
        match = HEADING_RE.match(line.strip())
        if match and len(match.group(1)) == 1:
            return match.group(2).strip()
    return Path(relative_path).stem


def common_heading_prefix(paths: list[tuple[str, ...]]) -> list[str]:
    if not paths:
        return []
    prefix = list(paths[0])
    for path in paths[1:]:
        max_prefix = min(len(prefix), len(path))
        cursor = 0
        while cursor < max_prefix and prefix[cursor] == path[cursor]:
            cursor += 1
        prefix = prefix[:cursor]
        if not prefix:
            break
    return prefix


def parse_markdown_sections(content: str) -> list[MarkdownSection]:
    sections: list[MarkdownSection] = []
    heading_stack: list[str] = []
    current_heading_path: tuple[str, ...] | None = None
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer, current_heading_path
        text = "\n".join(buffer).strip()
        if text:
            sections.append(
                MarkdownSection(
                    heading_path=current_heading_path or tuple(),
                    content=text,
                )
            )
        buffer = []

    for raw_line in content.splitlines():
        line = raw_line.rstrip()
        match = HEADING_RE.match(line.strip())
        if match:
            flush()
            level = len(match.group(1))
            heading = match.group(2).strip()
            heading_stack = heading_stack[: level - 1]
            heading_stack.append(heading)
            current_heading_path = tuple(heading_stack)
            buffer = [line]
            continue
        buffer.append(line)

    flush()
    return sections


def split_large_section(
    section: MarkdownSection,
    max_chars: int = MAX_CHUNK_CHARS,
) -> list[MarkdownSection]:
    if len(section.content) <= max_chars:
        return [section]

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", section.content) if part.strip()]
    if len(paragraphs) <= 1:
        return [section]

    split_sections: list[MarkdownSection] = []
    chunk_parts: list[str] = []
    heading_block = paragraphs[0]

    for paragraph in paragraphs[1:]:
        candidate_parts = chunk_parts + [paragraph]
        candidate_text = "\n\n".join([heading_block] + candidate_parts).strip()
        if chunk_parts and len(candidate_text) > max_chars:
            split_sections.append(
                MarkdownSection(
                    heading_path=section.heading_path,
                    content="\n\n".join([heading_block] + chunk_parts).strip(),
                )
            )
            chunk_parts = [paragraph]
            continue
        chunk_parts = candidate_parts

    if chunk_parts:
        split_sections.append(
            MarkdownSection(
                heading_path=section.heading_path,
                content="\n\n".join([heading_block] + chunk_parts).strip(),
            )
        )

    return split_sections or [section]


def collapse_small_sections(
    sections: list[MarkdownSection],
    min_chars: int = MIN_SECTION_CHARS,
    max_chars: int = MAX_CHUNK_CHARS,
) -> list[MarkdownSection]:
    collapsed: list[MarkdownSection] = []

    for section in sections:
        section_size = len(section.content)
        previous = collapsed[-1] if collapsed else None
        previous_heading_path = previous.heading_path if previous is not None else tuple()
        same_heading_depth = bool(
            previous_heading_path
            and section.heading_path
            and len(previous_heading_path) == len(section.heading_path)
        )
        shared_parent = same_heading_depth and (
            previous_heading_path[:-1] == section.heading_path[:-1]
        )
        if (
            previous
            and section_size < min_chars
            and shared_parent
            and len(collapsed[-1].content) + 2 + section_size <= max_chars
        ):
            previous = collapsed.pop()
            merged_paths = [tuple(previous.heading_path), tuple(section.heading_path)]
            collapsed.append(
                MarkdownSection(
                    heading_path=tuple(common_heading_prefix(merged_paths)) or previous.heading_path,
                    content=f"{previous.content}\n\n{section.content}".strip(),
                )
            )
            continue
        collapsed.append(section)

    return collapsed


def chunk_markdown(relative_path: str, content: str) -> list[PreparedChunk]:
    title = extract_title(relative_path, content)
    doc_class = doc_class_for_path(relative_path)
    feature_id = feature_id_for_path(relative_path)
    language = detect_language(relative_path, content)
    mandatory_candidate = relative_path in MANDATORY_DOCS

    sections = parse_markdown_sections(content)
    expanded_sections: list[MarkdownSection] = []
    for section in sections:
        expanded_sections.extend(split_large_section(section))

    final_sections = collapse_small_sections(expanded_sections)
    chunks: list[PreparedChunk] = []

    for index, section in enumerate(final_sections):
        stable_key = f"{relative_path}:{index}"
        digest = sha1(stable_key.encode("utf-8")).hexdigest()[:12]
        chunk_id = f"{Path(relative_path).stem}-{index:03d}-{digest}"
        chunks.append(
            PreparedChunk(
                path=relative_path,
                doc_class=doc_class,
                title=title,
                heading_path=list(section.heading_path),
                language=language,
                feature_id=feature_id,
                chunk_id=chunk_id,
                chunk_order=index,
                mandatory_candidate=mandatory_candidate,
                content=section.content.strip(),
            )
        )

    return chunks


def read_repo_text(root: Path, relative_path: str) -> str:
    return (root / relative_path).read_text(encoding="utf-8")


def serialize_chunk_for_rag(chunk: PreparedChunk) -> str:
    return chunk.content


def build_prepared_chunks(root: Path | None = None) -> list[PreparedChunk]:
    base = root or repo_root()
    chunks: list[PreparedChunk] = []
    for path in corpus_paths(base):
        relative_path = relative_repo_path(path, base)
        content = path.read_text(encoding="utf-8")
        chunks.extend(chunk_markdown(relative_path, content))
    return chunks


def ensure_debug_dirs(working_dir: Path) -> None:
    for relative in ("input", "chunks", "index", "logs"):
        (working_dir / relative).mkdir(parents=True, exist_ok=True)


def write_debug_exports(root: Path, chunks: list[PreparedChunk]) -> None:
    working_dir = pilot_working_dir(root)
    ensure_debug_dirs(working_dir)

    corpus_export = {
        "repo_root": str(root),
        "working_dir": str(working_dir),
        "pilot_corpus": list(PILOT_CORPUS),
        "chunk_count": len(chunks),
    }
    (working_dir / "input" / "pilot_corpus.json").write_text(
        json.dumps(corpus_export, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (working_dir / "chunks" / "pilot_chunks.json").write_text(
        json.dumps([asdict(chunk) for chunk in chunks], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
