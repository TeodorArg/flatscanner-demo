from __future__ import annotations

import json
from functools import partial
from pathlib import Path
from typing import Any

from .pilot_config import (
    LIGHTRAG_ENTITY_EXTRACT_MAX_GLEANING,
    LIGHTRAG_MAX_EXTRACT_INPUT_TOKENS,
    LIGHTRAG_MAX_PARALLEL_INSERT,
    OLLAMA_EMBED_MODEL,
    OLLAMA_HOST,
    OLLAMA_LLM_MAX_ASYNC,
    OLLAMA_LLM_MODEL,
    OLLAMA_LLM_NUM_PREDICT,
    OLLAMA_LLM_TIMEOUT_SECONDS,
)
from .query_policy import (
    is_pilot_boundary_question,
    is_pr_loop_completion_question,
    is_pr_loop_contract_question,
    is_read_order_question,
    retrieval_user_prompt,
)


class LocalCharTokenizerBackend:
    def encode(self, content: str) -> list[int]:
        return [ord(char) for char in content]

    def decode(self, tokens: list[int]) -> str:
        return "".join(chr(token) for token in tokens)


def validate_index_artifacts(index_dir: Path) -> None:
    status_path = index_dir / "kv_store_doc_status.json"
    chunks_vdb_path = index_dir / "vdb_chunks.json"

    if not status_path.exists():
        raise RuntimeError("LightRAG did not persist doc status; indexing run is incomplete.")
    if not chunks_vdb_path.exists():
        raise RuntimeError("LightRAG did not create chunk vector storage; indexing run failed.")

    doc_status = json.loads(status_path.read_text(encoding="utf-8"))
    failed_items = [
        item for item in doc_status.values() if isinstance(item, dict) and item.get("status") == "failed"
    ]
    if failed_items:
        sample_paths = sorted(
            {
                item.get("file_path", "unknown")
                for item in failed_items[:5]
                if isinstance(item, dict)
            }
        )
        raise RuntimeError(
            f"LightRAG indexing failed for {len(failed_items)} chunk document(s). "
            f"Sample files: {', '.join(sample_paths)}"
        )


def _load_lightrag_runtime() -> tuple[Any, Any, Any, Any, Any, Any]:
    try:
        from lightrag import LightRAG, QueryParam
        from lightrag.llm.ollama import ollama_embed, ollama_model_complete
        from lightrag.prompt import PROMPTS
        from lightrag.utils import EmbeddingFunc, Tokenizer
    except ImportError as exc:
        raise RuntimeError(
            "LightRAG pilot dependencies are missing. Install them with "
            "`uv sync --extra repo_memory --extra dev`."
        ) from exc
    _tighten_entity_extraction_prompts(PROMPTS)
    return (
        LightRAG,
        QueryParam,
        EmbeddingFunc,
        Tokenizer,
        ollama_embed,
        ollama_model_complete,
    )


def _tighten_entity_extraction_prompts(prompts: dict[str, Any]) -> None:
    strict_suffix = """

---Pilot Guardrails---
9.  **Repository Metadata Ignore List:**
    *   Ignore repository metadata sections, path-like strings, heading paths, chunk identifiers, template placeholders, and schema examples.
    *   Never output any of the following as entities or relationships: `Path`, `Doc Class`, `Title`, `Heading Path`, `Language`, `Feature ID`, `Chunk ID`, `Chunk Order`, `Mandatory Candidate`.
10. **Strict Output Discipline:**
    *   Output plain extraction rows only. Do not output code fences, bullets, numbering, XML tags, headings, commentary, or explanations.
    *   Do not invent extra fields. Entity rows must contain exactly 4 fields and relation rows must contain exactly 5 fields.
    *   If there are no valid entities or relationships in the document body, output only `{completion_delimiter}`.
"""
    user_suffix = """
5.  **Ignore Metadata Noise:** Ignore repository metadata sections, path-like strings, chunk identifiers, heading paths, and template placeholders.
6.  **No Extra Formatting:** Do not output XML tags, code fences, bullets, numbering, or explanatory prose.
7.  **Schema Discipline:** Entity rows must contain exactly 4 fields and relation rows must contain exactly 5 fields.
"""
    continue_suffix = """
7.  **Ignore Metadata Noise:** Ignore repository metadata sections, path-like strings, chunk identifiers, heading paths, and template placeholders.
8.  **No Extra Formatting:** Do not output XML tags, code fences, bullets, numbering, or explanatory prose.
9.  **Schema Discipline:** Entity rows must contain exactly 4 fields and relation rows must contain exactly 5 fields.
"""
    prompts["entity_extraction_system_prompt"] += strict_suffix
    prompts["entity_extraction_user_prompt"] = prompts["entity_extraction_user_prompt"].replace(
        "4.  **Output Language:** Ensure the output language is {language}. Proper nouns (e.g., personal names, place names, organization names) must be kept in their original language and not translated.\n",
        "4.  **Output Language:** Ensure the output language is {language}. Proper nouns (e.g., personal names, place names, organization names) must be kept in their original language and not translated.\n"
        + user_suffix,
    )
    prompts["entity_continue_extraction_user_prompt"] = prompts[
        "entity_continue_extraction_user_prompt"
    ].replace(
        "6.  **Completion Signal:** Output `{completion_delimiter}` as the final line after all relevant missing or corrected entities and relationships have been extracted and presented.\n",
        "6.  **Completion Signal:** Output `{completion_delimiter}` as the final line after all relevant missing or corrected entities and relationships have been extracted and presented.\n"
        + continue_suffix,
    )


def create_rag(index_dir: Path) -> Any:
    LightRAG, _, EmbeddingFunc, Tokenizer, ollama_embed, ollama_model_complete = _load_lightrag_runtime()
    embedding_func = EmbeddingFunc(
        embedding_dim=768,
        max_token_size=8192,
        model_name=OLLAMA_EMBED_MODEL,
        func=partial(
            ollama_embed.func,
            embed_model=OLLAMA_EMBED_MODEL,
            host=OLLAMA_HOST,
        ),
    )
    tokenizer = Tokenizer(
        model_name="local-char-tokenizer",
        tokenizer=LocalCharTokenizerBackend(),
    )
    return LightRAG(
        working_dir=str(index_dir),
        max_parallel_insert=LIGHTRAG_MAX_PARALLEL_INSERT,
        max_extract_input_tokens=LIGHTRAG_MAX_EXTRACT_INPUT_TOKENS,
        entity_extract_max_gleaning=LIGHTRAG_ENTITY_EXTRACT_MAX_GLEANING,
        chunk_token_size=700,
        chunk_overlap_token_size=50,
        llm_model_func=ollama_model_complete,
        llm_model_name=OLLAMA_LLM_MODEL,
        llm_model_max_async=OLLAMA_LLM_MAX_ASYNC,
        default_llm_timeout=OLLAMA_LLM_TIMEOUT_SECONDS,
        llm_model_kwargs={
            "host": OLLAMA_HOST,
            "options": {
                "num_ctx": 8192,
                "num_predict": OLLAMA_LLM_NUM_PREDICT,
                "temperature": 0,
            },
            "timeout": OLLAMA_LLM_TIMEOUT_SECONDS,
        },
        tokenizer=tokenizer,
        embedding_func=embedding_func,
    )


def build_query_param(
    query: str,
    mode: str,
    include_references: bool,
    query_param_factory: Any,
) -> Any:
    params: dict[str, Any] = {
        "mode": mode,
        "include_references": include_references,
        "enable_rerank": False,
    }
    if is_read_order_question(query):
        params.update(
            {
                "top_k": 8,
                "chunk_top_k": 4,
                "response_type": "Bullet Points",
            }
        )
    elif is_pr_loop_contract_question(query) or is_pr_loop_completion_question(query):
        params.update(
            {
                "top_k": 8,
                "chunk_top_k": 4,
                "response_type": "Bullet Points",
            }
        )
    elif is_pilot_boundary_question(query):
        params.update(
            {
                "top_k": 6,
                "chunk_top_k": 3,
                "response_type": "Bullet Points",
            }
        )
    user_prompt = retrieval_user_prompt(query)
    if user_prompt:
        params["user_prompt"] = user_prompt
    return query_param_factory(**params)
