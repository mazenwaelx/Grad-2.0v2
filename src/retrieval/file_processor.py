"""
FileProcessor — Facade for uploaded document processing.

Delegates to:
  - ``ocr_strategies`` for OCR
  - ``file_handlers`` for file-type extraction
  - ``relevance_analyzer`` for question-file relevance
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from src.retrieval.ocr_strategies import CompositeOCR
from src.retrieval.file_handlers import (
    PDFHandler, DocxHandler, ExcelHandler, ImageHandler, FileTypeHandler,
)
from src.retrieval.relevance_analyzer import FileRelevanceAnalyzer

_SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".png", ".jpg", ".jpeg"}


class FileProcessor:
    """Facade for processing uploaded files and integrating with the chat system."""

    def __init__(self, embeddings, chunk_size: int = 1000, chunk_overlap: int = 200) -> None:
        self._embeddings = embeddings
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap,
        )
        self.uploaded_files: Dict[str, Dict[str, Any]] = {}
        self.file_vectorstores: Dict[str, FAISS] = {}
        self.chat_files: Dict[str, set[str]] = {}

        self._ocr = CompositeOCR()
        self._relevance = FileRelevanceAnalyzer()
        self._handlers: Dict[str, FileTypeHandler] = {
            ".pdf": PDFHandler(self._ocr), ".docx": DocxHandler(), ".doc": DocxHandler(),
            ".xlsx": ExcelHandler(), ".xls": ExcelHandler(),
            ".png": ImageHandler(self._ocr), ".jpg": ImageHandler(self._ocr), ".jpeg": ImageHandler(self._ocr),
        }

    # ── Public API ─────────────────────────────────────────────────

    @staticmethod
    def get_file_hash(content: bytes) -> str:
        return hashlib.md5(content, usedforsecurity=False).hexdigest()

    @staticmethod
    def is_supported_file(filename: str) -> bool:
        return Path(filename).suffix.lower() in _SUPPORTED_EXTENSIONS

    def process_file(self, content: bytes, filename: str, chat_id: str) -> Tuple[List[Document], str]:
        fh = self.get_file_hash(content)
        if chat_id not in self.chat_files:
            self.chat_files[chat_id] = set()
        self.chat_files[chat_id].add(fh)

        if fh in self.uploaded_files:
            return self.uploaded_files[fh]["documents"], fh

        ext = Path(filename).suffix.lower()
        handler = self._handlers.get(ext)
        if not handler:
            raise ValueError(f"Unsupported file type: {ext}")

        docs = handler.process(content, filename)
        chunked = self._chunk(docs)

        self.uploaded_files[fh] = {
            "filename": filename, "documents": chunked, "original_documents": docs,
            "file_type": ext, "is_ocr": any(d.metadata.get("ocr") for d in docs),
        }
        return chunked, fh

    def create_file_vectorstore(self, fh: str) -> FAISS:
        if fh in self.file_vectorstores:
            return self.file_vectorstores[fh]
        docs = self.uploaded_files[fh]["documents"]
        vs = FAISS.from_documents(docs, self._embeddings)
        self.file_vectorstores[fh] = vs
        return vs

    def search_in_file(self, fh: str, query: str, k: int = 3) -> List[Document]:
        info = self.uploaded_files.get(fh)
        if not info:
            raise ValueError(f"File {fh} not found")
        if info.get("is_ocr"):
            return info["documents"]
        if fh not in self.file_vectorstores:
            self.create_file_vectorstore(fh)
        return self.file_vectorstores[fh].as_retriever(search_kwargs={"k": k}).invoke(query)

    def get_file_info(self, fh: str) -> Optional[Dict[str, Any]]:
        return self.uploaded_files.get(fh)

    def remove_file(self, fh: str, chat_id: Optional[str] = None) -> bool:
        if chat_id:
            if chat_id in self.chat_files and fh in self.chat_files[chat_id]:
                self.chat_files[chat_id].remove(fh)
                return True
            return False

        r = fh in self.uploaded_files or fh in self.file_vectorstores
        self.uploaded_files.pop(fh, None)
        self.file_vectorstores.pop(fh, None)
        return r

    def list_uploaded_files(self, chat_id: str) -> List[Dict[str, Any]]:
        hashes = self.chat_files.get(chat_id, set())
        return [{"hash": h, "filename": self.uploaded_files[h]["filename"], "file_type": self.uploaded_files[h]["file_type"],
                 "document_count": len(self.uploaded_files[h]["documents"])} for h in hashes if h in self.uploaded_files]

    # ── Relevance delegation ───────────────────────────────────────

    def calculate_question_relevance(self, question: str, fh: str) -> float:
        info = self.uploaded_files.get(fh)
        return self._relevance.calculate_relevance(question, info) if info else 0.0

    def is_question_about_file(self, question: str, fh: str) -> bool:
        info = self.uploaded_files.get(fh)
        return self._relevance.is_question_about_file(question, info) if info else False

    # ── Private ────────────────────────────────────────────────────

    def _chunk(self, docs: List[Document]) -> List[Document]:
        is_ocr = any(d.metadata.get("ocr") for d in docs)
        if is_ocr and sum(len(d.page_content) for d in docs) < 8000:
            return docs
        chunked: List[Document] = []
        for d in docs:
            chunked.extend(self._splitter.split_documents([d]))
        return chunked or docs


# ── Global instance ────────────────────────────────────────────────
_file_processor: Optional[FileProcessor] = None

def get_file_processor() -> Optional[FileProcessor]:
    return _file_processor

def set_file_processor(p: FileProcessor) -> None:
    global _file_processor
    _file_processor = p