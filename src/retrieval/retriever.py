"""
FAISS retriever initialization and management — Service class.

``RetrieverService`` encapsulates loading or creating the FAISS
vector store and exposing it as a LangChain retriever.
"""
from __future__ import annotations

import json
from typing import Tuple

from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

from data.data_embedding import SentenceTransformerEmbeddings
from src.config.settings import (
    FAISS_INDEX_DIR,
    FAISS_STATS_PATH,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K_DOCUMENTS,
)


class RetrieverService:
    """Manages the lifecycle of the FAISS retriever.

    Responsibilities:
      - Load an existing FAISS index from disk, **or**
      - Build a new one from source documents.
      - Provide a ready-to-use LangChain retriever.
    """

    def __init__(
        self,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP,
        top_k: int = TOP_K_DOCUMENTS,
    ) -> None:
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._top_k = top_k
        self._embeddings = SentenceTransformerEmbeddings()

    def prepare(self, data_path: str) -> Tuple:
        """Prepare (load or create) the retriever.

        Args:
            data_path: Path to the labour-law markdown file (kept for
                compatibility; ignored when a cached index exists).

        Returns:
            ``(retriever, total_pdf_pages, total_chunks, supplemental_sources_count)``
        """
        vector_store, stats = self._load_or_create(data_path)

        retriever = vector_store.as_retriever(
            search_kwargs={"k": self._top_k}
        )

        self._smoke_test(retriever)

        return (
            retriever,
            stats.get("pdf_pages", 0),
            stats.get("chunks", 0),
            stats.get("supplemental_sources", 0),
        )

    # ── Private helpers ────────────────────────────────────────────
    def _load_or_create(self, data_path: str) -> Tuple[FAISS, dict]:
        """Load an existing FAISS index or create a new one."""
        if self._index_exists():
            return self._load_existing_index()
        return self._create_new_index(data_path)

    @staticmethod
    def _index_exists() -> bool:
        return FAISS_INDEX_DIR.exists() and any(FAISS_INDEX_DIR.glob("*"))

    def _load_existing_index(self) -> Tuple[FAISS, dict]:
        """Load a FAISS index and its stats from disk."""
        try:
            vector_store = FAISS.load_local(
                str(FAISS_INDEX_DIR),
                self._embeddings,
                allow_dangerous_deserialization=True,
            )
            print(f"[DEBUG] Loaded FAISS index from {FAISS_INDEX_DIR}")

            stats: dict = {}
            if FAISS_STATS_PATH.exists():
                stats = json.loads(FAISS_STATS_PATH.read_text(encoding="utf-8"))
                print(f"[DEBUG] Index stats: {stats}")

            return vector_store, stats

        except Exception as e:
            print(f"[ERROR] Failed to load FAISS index: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _create_new_index(self, data_path: str) -> Tuple[FAISS, dict]:
        """Build a FAISS index from source documents."""
        # NOTE: collect_labour_documents is defined in the data ingestion
        # pipeline and is only needed when creating the index from scratch.
        from src.retrieval.retriever import collect_labour_documents  # type: ignore[attr-defined]

        base_documents, prechunked_documents, total_pdf_pages, supplemental_sources_count = (
            collect_labour_documents()
        )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
        )
        chunks = splitter.split_documents(base_documents)
        chunks.extend(prechunked_documents)

        vector_store = FAISS.from_documents(chunks, self._embeddings)

        # Persist
        FAISS_INDEX_DIR.parent.mkdir(parents=True, exist_ok=True)
        vector_store.save_local(str(FAISS_INDEX_DIR))

        stats = {
            "pdf_pages": total_pdf_pages,
            "chunks": len(chunks),
            "supplemental_sources": supplemental_sources_count,
        }
        FAISS_STATS_PATH.write_text(
            json.dumps(stats, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return vector_store, stats

    @staticmethod
    def _smoke_test(retriever) -> None:
        """Run a quick retrieval test to verify the index is healthy."""
        print("[DEBUG] Testing retriever with multiple queries...")
        test_queries = ["قانون العمل", "العامل", "المادة 1", "تعريف"]

        for query in test_queries:
            try:
                docs = retriever.invoke(query)
                if docs:
                    print(f"[SUCCESS] Retriever test: Retrieved {len(docs)} docs")
                    print(f"[DEBUG] Sample doc source: {docs[0].metadata.get('source', 'unknown')}")
                    return  # one success is enough
            except Exception as e:
                print(f"[WARNING] Retriever test '{query}' failed: {e}")

        print("[ERROR] Retriever failed all test queries! This is a critical issue.")
        print("[ERROR] The vector store might be empty or corrupted.")


# ── Backward-compatible module-level function ──────────────────────
def prepare_retriever(
    pdf_path: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> Tuple:
    """Prepare or load the FAISS retriever (backward-compatible wrapper).

    Returns:
        ``(retriever, total_pdf_pages, total_chunks, supplemental_sources_count)``
    """
    service = RetrieverService(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return service.prepare(pdf_path)
