from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PreparedChunk:
    path: str
    doc_class: str
    title: str
    heading_path: list[str]
    language: str
    feature_id: str | None
    chunk_id: str
    chunk_order: int
    mandatory_candidate: bool
    content: str


@dataclass(frozen=True)
class MarkdownSection:
    heading_path: tuple[str, ...]
    content: str


@dataclass(frozen=True)
class ContextDocument:
    path: str
    doc_class: str
    title: str
    source: str
    reason: str
    content: str


@dataclass(frozen=True)
class ContextPack:
    question: str
    mode: str
    task_type: str
    active_feature_id: str | None
    mandatory_documents: list[ContextDocument]
    retrieved_documents: list[ContextDocument]
    final_documents: list[ContextDocument]
    raw_retrieval_result: Any
