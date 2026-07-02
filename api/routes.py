"""
API route definitions — chat, file, and admin endpoints.

All routes are registered on a FastAPI ``APIRouter`` and mounted
by ``main.py``.
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException, Request, UploadFile, File

from api.models import ChatRequest, ChatResponseWithFiles, FileUploadResponse
from database import (
    create_chat, get_user_chats, update_chat_title, delete_chat, get_chat_messages,
)


router = APIRouter(prefix="/api")


# ── Helpers ────────────────────────────────────────────────────────

def _get_state(request: Request):
    return request.app.state.app_state


def _resolve_user_id(identifier: str) -> str:
    if "@" not in identifier:
        return identifier
    from database.user_manager import get_user
    user = get_user(identifier)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return str(user["Id"])


def _get_user_or_404(email: str) -> dict:
    from database.user_manager import get_user
    user = get_user(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ── Health ─────────────────────────────────────────────────────────

@router.get("/health")
async def health():
    return {"status": "healthy"}


# ── Chat CRUD ──────────────────────────────────────────────────────

@router.get("/chats/{user_email}")
def get_chats(user_email: str):
    user = _get_user_or_404(user_email)
    print(f"[DEBUG] get_chats - Email: {user_email}, Resolved User ID: {user['Id']}")
    chats = get_user_chats(user["Id"])
    print(f"[DEBUG] get_chats - Found {len(chats)} chats for user {user['Id']}")
    for chat in chats:
        print(f"[DEBUG]   - Chat: {chat.get('chat_id')} | Title: {chat.get('title')}")
    return {"chats": chats}


@router.get("/messages/{chat_id}")
def get_messages(chat_id: str):
    return {"messages": get_chat_messages(chat_id)}


@router.post("/chat")
def chat(request: Request, body: ChatRequest):
    try:
        state = _get_state(request)
        uid = _resolve_user_id(body.user_id)
        
        print(f"[DEBUG] chat - Raw user_id: {body.user_id}, Resolved: {uid}, Chat ID: {body.chat_id}")

        files_before = state.file_processor.list_uploaded_files(body.chat_id) if state.file_processor else []

        from main import AgentService
        agent = AgentService(state).get_or_create(uid, body.chat_id)

        response = agent.ask(body.message)

        files_after = state.file_processor.list_uploaded_files(body.chat_id) if state.file_processor else []
        removed: List[str] = []
        if len(files_before) > len(files_after):
            after_h = {f["hash"] for f in files_after}
            removed = [f["filename"] for f in files_before if f["hash"] not in after_h]

        return ChatResponseWithFiles(
            response=response, chat_id=body.chat_id,
            files_removed=bool(removed), removed_files=removed,
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chat/{user_id}/{chat_id}")
def delete_chat_endpoint(request: Request, user_id: str, chat_id: str):
    state = _get_state(request)
    uid = user_id
    if "@" in user_id:
        from database.user_manager import get_user
        u = get_user(user_id)
        if u:
            uid = str(u["Id"])
    key = f"{uid}_{chat_id}"
    state.user_agents.pop(key, None)
    state.user_histories.pop(key, None)
    if delete_chat(chat_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=500, detail="Failed to delete chat")


@router.put("/chat/{chat_id}/title")
def update_title(chat_id: str, title: dict):
    if update_chat_title(chat_id, title.get("title", "New Chat")):
        return {"status": "updated"}
    raise HTTPException(status_code=500, detail="Failed to update title")


# ── File endpoints ─────────────────────────────────────────────────

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(request: Request, chat_id: str = None, file: UploadFile = File(...)):
    try:
        if not chat_id:
            return FileUploadResponse(success=False, message="chat_id is required")
        fp = _get_state(request).file_processor
        if not fp:
            raise HTTPException(status_code=500, detail="File processor not initialized")
        if not fp.is_supported_file(file.filename):
            return FileUploadResponse(success=False, message=f"نوع الملف غير مدعوم: {file.filename}")
        docs, fh = fp.process_file(await file.read(), file.filename, chat_id)
        return FileUploadResponse(success=True, message=f"تم رفع الملف بنجاح: {file.filename}",
                                  file_hash=fh, document_count=len(docs))
    except HTTPException:
        raise
    except Exception as e:
        import traceback; traceback.print_exc()
        return FileUploadResponse(success=False, message=f"خطأ: {e}")


@router.get("/files")
def list_files(request: Request, chat_id: str = None):
    if not chat_id:
        return {"files": []}
    fp = _get_state(request).file_processor
    return {"files": fp.list_uploaded_files(chat_id) if fp else []}


@router.delete("/files/{file_hash}")
def delete_file(request: Request, file_hash: str, chat_id: str = None):
    fp = _get_state(request).file_processor
    if not fp:
        raise HTTPException(status_code=500, detail="File processor not initialized")
    if fp.remove_file(file_hash, chat_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="File not found")


@router.delete("/files")
def clear_all_files(request: Request, chat_id: str = None):
    fp = _get_state(request).file_processor
    if not fp or not chat_id:
        return {"status": "no_processor"}
    removed = sum(1 for f in fp.list_uploaded_files(chat_id) if fp.remove_file(f["hash"], chat_id))
    return {"status": "cleared", "removed_count": removed}
