"""
Pydantic request/response models for the API.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    chat_id: str
    user_id: str


class FileUploadResponse(BaseModel):
    success: bool
    message: str
    file_hash: Optional[str] = None
    document_count: Optional[int] = None


class ChatResponseWithFiles(BaseModel):
    response: str
    chat_id: str
    files_removed: bool = False
    removed_files: List[str] = []
