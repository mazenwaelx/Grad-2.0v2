from typing import List
from sentence_transformers import SentenceTransformer
from langchain_core.embeddings import Embeddings
from pydantic import BaseModel, Field


def _get_device(device_preference: str = "auto") -> str:
    """Determine the device to use for the model."""
    if device_preference != "auto":
        return device_preference
    
    # Auto-detect device
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"  # Apple Silicon
    except ImportError:
        pass
    
    return "cpu"


class SentenceTransformerEmbeddings(BaseModel, Embeddings):
    """LangChain-compatible wrapper for SentenceTransformers embeddings."""
    
    model_id: str = Field(
        default="BAAI/bge-m3",
        description="SentenceTransformer model ID from HuggingFace"
    )
    device: str = Field(
        default="auto",
        description="Device to run the model on (auto, cpu, cuda, mps). 'auto' will detect the best available device."
    )
    show_progress: bool = Field(
        default=True,
        description="Whether to show progress bar during encoding"
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Resolve device from "auto" to actual device
        actual_device = _get_device(self.device)
        self._model = SentenceTransformer(self.model_id, device=actual_device)
        print(f"[INFO] Loaded SentenceTransformer model: {self.model_id}")
        print(f"[INFO] Using device: {actual_device}")
        print(f"[INFO] Embedding dimension: {self._model.get_sentence_embedding_dimension()}")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        # Replace newlines with spaces for better embedding
        texts = [text.replace("\n", " ") for text in texts]
        embeddings = self._model.encode(
            texts,
            show_progress_bar=self.show_progress,
            convert_to_numpy=False
        )
        # Convert to list of lists
        if hasattr(embeddings, 'tolist'):
            return embeddings.tolist()
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query text."""
        text = text.replace("\n", " ")
        embedding = self._model.encode(
            text,
            show_progress_bar=False,
            convert_to_numpy=False
        )
        # Convert to list - handle both 1D and 2D arrays
        if hasattr(embedding, 'tolist'):
            result = embedding.tolist()
            # If it's a 2D array (shape [1, dim]), flatten to 1D
            if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
                return result[0]
            return result
        # If it's already a list but nested, flatten it
        if isinstance(embedding, list) and len(embedding) > 0 and isinstance(embedding[0], list):
            return embedding[0]
        return embedding