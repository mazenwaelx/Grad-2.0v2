"""
FastAPI server — Egyptian Legal AI.

Single entry point to run the AI backend and React frontend.
App creation, lifespan, AgentService, and startup logic.
Routes live in ``api/routes.py``, models in ``api/models.py``.
"""
from __future__ import annotations

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv
load_dotenv(override=True)

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.retrieval.retriever import prepare_retriever
from src.retrieval.file_processor import FileProcessor, set_file_processor
from src.agents.langchain_react_agent import LangChainReActAgent

from src.llm.llm_manager import init_llm
from src.config.settings import MODEL_NAME
from data.data_embedding import SentenceTransformerEmbeddings
from database import init_database, create_chat
from database.db_memory_store import DatabaseChatMessageHistory

from api.routes import router as api_router


# ── Application state ─────────────────────────────────────────────

@dataclass
class AppState:
    user_agents: Dict[str, LangChainReActAgent] = field(default_factory=dict)
    user_histories: Dict[str, DatabaseChatMessageHistory] = field(default_factory=dict)
    file_processor: Optional[FileProcessor] = None
    retriever: object = None


# ── Agent service ──────────────────────────────────────────────────

class AgentService:
    """Creates fresh AI agents per user-chat pair."""

    def __init__(self, state: AppState) -> None:
        self._s = state

    def get_or_create(self, user_id: str, chat_id: str) -> LangChainReActAgent:
        self._ensure_retriever()
        create_chat(chat_id, user_id)
        history = DatabaseChatMessageHistory(chat_id)


        agent = LangChainReActAgent(
            llm=init_llm(MODEL_NAME),
            retriever=self._s.retriever,
            history_store=history,
            file_processor=self._s.file_processor,
            chat_id=chat_id,
            log_callback=lambda msg: None,
            max_iterations=10, verbose=True,
        )
        self._s.user_histories[f"{user_id}_{chat_id}"] = history
        return agent

    def _ensure_retriever(self) -> None:
        if self._s.retriever is not None:
            return
        print("[INFO] Initializing retriever...")
        self._s.retriever, _, _, _ = prepare_retriever("data/labour_data/labour_law.md")
        print("[INFO] Retriever ready")


# ── Lifespan ───────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    state = AppState()
    print("[INFO] Initializing database...")
    init_database()
    print("[INFO] Database ready")

    embeddings = SentenceTransformerEmbeddings()
    state.file_processor = FileProcessor(embeddings)
    set_file_processor(state.file_processor)
    print("[INFO] File processor ready")

    app.state.app_state = state
    yield


# ── App ────────────────────────────────────────────────────────────

app = FastAPI(title="Egyptian Legal AI API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(api_router)

_fe = Path(__file__).parent / "react-frontend"
if _fe.exists():
    app.mount("/static", StaticFiles(directory=str(_fe), html=True), name="static")


@app.get("/")
async def root():
    return {"name": "Egyptian Legal AI API", "version": "1.0.0", "docs": "/docs", "health": "/api/health"}


# ── React launcher & main ─────────────────────────────────────────

def _start_react():
    import subprocess, sys, shutil
    rd = Path(__file__).parent / "react-frontend"
    if not rd.exists():
        return None
    npm = shutil.which("npm")
    if not npm:
        return None
    if not (rd / "node_modules").exists():
        subprocess.run([npm, "install"], cwd=str(rd))
    kw = {"stdout": subprocess.PIPE, "stderr": subprocess.STDOUT}
    if sys.platform == "win32":
        kw["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kw["preexec_fn"] = os.setsid
    return subprocess.Popen([npm, "start"], cwd=str(rd), **kw)


if __name__ == "__main__":
    import signal, atexit
    rp = _start_react()
    atexit.register(lambda: rp and rp.terminate())
    print("Backend: http://localhost:8000 | React: http://localhost:3000")
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    finally:
        rp and rp.terminate()
