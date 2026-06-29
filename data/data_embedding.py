"""
LangChain-compatible wrapper for SentenceTransformers embeddings.

Provides a ``SentenceTransformerEmbeddings`` class that implements
the LangChain ``Embeddings`` interface using the BGE-M3 model.
"""
from typing import List

from pydantic import BaseModel, Field
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer


class SentenceTransformerEmbeddings(BaseModel, Embeddings):
    """LangChain-compatible wrapper for SentenceTransformers embeddings."""

    model_id: str = Field(
        default="BAAI/bge-m3",
        description="SentenceTransformer model ID from HuggingFace",
    )
    device: str = Field(
        default="auto",
        description=(
            "Device to run the model on (auto, cpu, cuda, mps). "
            "'auto' will detect the best available device."
        ),
    )
    show_progress: bool = Field(
        default=True,
        description="Whether to show progress bar during encoding",
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        actual_device = self._resolve_device(self.device)
        self._model = SentenceTransformer(self.model_id, device=actual_device)
        print(f"[INFO] Loaded SentenceTransformer model: {self.model_id}")
        print(f"[INFO] Using device: {actual_device}")
        print(f"[INFO] Embedding dimension: {self._model.get_sentence_embedding_dimension()}")

    # ── LangChain Embeddings interface ─────────────────────────────
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        texts = [text.replace("\n", " ") for text in texts]
        embeddings = self._model.encode(
            texts,
            show_progress_bar=self.show_progress,
            convert_to_numpy=False,
        )
        if hasattr(embeddings, "tolist"):
            return embeddings.tolist()
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query text."""
        text = text.replace("\n", " ")
        embedding = self._model.encode(
            text,
            show_progress_bar=False,
            convert_to_numpy=False,
        )
        return self._to_flat_list(embedding)

    # ── Private helpers ────────────────────────────────────────────
    @staticmethod
    def _resolve_device(device_preference: str) -> str:
        """Determine the best available compute device."""
        if device_preference != "auto":
            return device_preference

        try:
            import torch

            if torch.cuda.is_available():
                return "cuda"
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass

        return "cpu"

    @staticmethod
    def _to_flat_list(embedding) -> List[float]:
        """Normalise an embedding to a flat ``List[float]``."""
        if hasattr(embedding, "tolist"):
            result = embedding.tolist()
            # Handle 2-D arrays of shape [1, dim]
            if isinstance(result, list) and result and isinstance(result[0], list):
                return result[0]
            return result

        if isinstance(embedding, list) and embedding and isinstance(embedding[0], list):
            return embedding[0]

        return embedding