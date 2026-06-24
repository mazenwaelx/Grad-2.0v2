"""
FastAPI server to connect the frontend with the Streamlit backend
"""
import os
from pathlib import Path


# Load environment variables (override=True to ensure .env takes precedence)
from dotenv import load_dotenv
load_dotenv(override=True)

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager
import uvicorn


# Import your existing components
from src.retrieval.retriever import prepare_retriever
from src.retrieval.file_processor import FileProcessor, set_file_processor
from src.agents.langchain_react_agent import LangChainReActAgent, build_langchain_tools
from src.llm.llm_manager import init_llm
from src.config.settings import MODEL_NAME
from data.data_embedding import SentenceTransformerEmbeddings
from database import (
    init_database, create_user, verify_user,
    create_chat, get_user_chats, update_chat_title, delete_chat, get_chat_messages
)
from database.db_memory_store import DatabaseChatMessageHistory

@asynccontextmanager
async def lifespan(app):
    """Initialize database and file processor on startup"""
    global file_processor
    print("[INFO] Initializing database...")
    init_database()
    print("[SUCCESS] SQL Server database tables initialized")
    print("[INFO] Database ready")
    
    # Initialize file processor
    print("[INFO] Initializing file processor...")
    embeddings = SentenceTransformerEmbeddings()
    file_processor = FileProcessor(embeddings)
    set_file_processor(file_processor)
    print("[INFO] File processor ready")
    yield

app = FastAPI(title="Egyptian Legal AI API", lifespan=lifespan)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (Frontend)
frontend_path = Path(__file__).parent / "react-frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path), html=True), name="static")

# Models
class ChatRequest(BaseModel):
    message: str
    chat_id: str
    user_id: str  # Can be email (for backward compatibility) or actual user_id

class UserRegister(BaseModel):

    email: str
    name: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    email: str
    name: str
    token: str = "demo_token"  # For demo purposes

class FileUploadResponse(BaseModel):
    success: bool
    message: str
    file_hash: Optional[str] = None
    document_count: Optional[int] = None

# Global state (in production, use a database)
user_agents = {}
user_histories = {}
file_processor = None

def get_or_create_agent(user_id: str, chat_id: str):
    """Get or create an agent for a specific user and chat"""
    key = f"{user_id}_{chat_id}"
    
    # Always create a fresh agent - don't cache
    # This ensures the agent has no memory/context from previous messages
    # But messages are still stored in database for display
    
    # Initialize retriever (shared across all users)
    if "retriever" not in globals():
        global retriever
        print("[INFO] Initializing retriever...")
        retriever, _, _, _ = prepare_retriever("data/labour_data/labour_law.md")
        print("[INFO] Retriever ready")
    
    # Create chat in database if it doesn't exist
    create_chat(chat_id, user_id)
    
    # Create database-backed history store (for display only, not for context)
    history_store = DatabaseChatMessageHistory(chat_id)
    
    # Build LLM
    llm = init_llm(MODEL_NAME)
    
    # Build LangChain tools with file processor
    global file_processor
    tools = build_langchain_tools(retriever, history_store, file_processor)
    
    # Create LangChain ReAct agent with EMPTY history for fresh context
    # The history_store still saves messages to DB, but agent doesn't use them for context
    from langchain_core.chat_history import InMemoryChatMessageHistory
    empty_history = InMemoryChatMessageHistory()  # Fresh memory every time
    
    agent = LangChainReActAgent(
        llm=llm,
        tools=tools,
        history_store=empty_history,  # Use empty history for no context
        log_callback=lambda msg: print(f"[AGENT] {msg}"),
        max_iterations=10,  # Increased to handle complex queries
        verbose=True,
    )
    
    # Still save the database history store to save messages
    user_histories[key] = history_store
    
    return agent

@app.get("/")
async def root():
    """Redirect to login page"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/login.html")

@app.post("/api/register", response_model=UserResponse)
def register(user: UserRegister):
    """Register a new user"""
    success, message = create_user(user.email, user.name, user.password)
    if success:
        return UserResponse(email=user.email, name=user.name)
    else:
        raise HTTPException(status_code=400, detail=message)

@app.post("/api/login", response_model=UserResponse)
def login(credentials: UserLogin):
    """Login user"""
    success, user = verify_user(credentials.email, credentials.password)
    if success:
        # Use PascalCase field names from SQL Server
        return UserResponse(email=user['Email'], name=user['Name'])
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/chats/{user_email}")
def get_chats(user_email: str):
    """Get all chats for a user (accepts email, converts to user_id)"""
    # Get user to find their ID
    from database.user_manager import get_user
    user = get_user(user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Use user_id to get chats
    chats = get_user_chats(user['Id'])  # SQL Server uses 'Id' as column name
    return {"chats": chats}

@app.get("/api/messages/{chat_id}")
def get_messages(chat_id: str):
    """Get all messages for a chat"""
    messages = get_chat_messages(chat_id)
    return {"messages": messages}

class ChatResponseWithFiles(BaseModel):
    response: str
    chat_id: str
    files_removed: bool = False
    removed_files: List[str] = []

@app.post("/api/chat")
def chat(request: ChatRequest):
    """Handle chat messages"""
    try:
        global file_processor
        
        # Convert email to user_id if necessary (backward compatibility)
        user_identifier = request.user_id
        if '@' in user_identifier:  # It's an email
            from database.user_manager import get_user
            user = get_user(user_identifier)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            actual_user_id = str(user['Id'])
        else:
            actual_user_id = user_identifier
        
        # Check files before processing
        files_before = file_processor.list_uploaded_files() if file_processor else []
        
        # Get agent (fresh one with no context each time)
        agent = get_or_create_agent(actual_user_id, request.chat_id)
        
        # Manually save user message to database
        key = f"{actual_user_id}_{request.chat_id}"
        if key in user_histories:
            user_histories[key].add_user_message(request.message)
        
        # Get response from agent (with no memory/context)
        response = agent.ask(request.message)
        
        # Manually save AI response to database
        if key in user_histories:
            user_histories[key].add_ai_message(response)
        
        # Check files after processing
        files_after = file_processor.list_uploaded_files() if file_processor else []
        
        # Determine if files were removed
        files_removed = len(files_before) > len(files_after)
        removed_files = []
        
        if files_removed:
            # Find which files were removed
            after_hashes = {f["hash"] for f in files_after}
            for file_info in files_before:
                if file_info["hash"] not in after_hashes:
                    removed_files.append(file_info["filename"])
        
        return ChatResponseWithFiles(
            response=response,
            chat_id=request.chat_id,
            files_removed=files_removed,
            removed_files=removed_files
        )
    
    except Exception as e:
        print(f"[ERROR] Chat error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.delete("/api/chat/{user_id}/{chat_id}")
def delete_chat_endpoint(user_id: str, chat_id: str):
    """Delete a chat and its history"""
    # Convert email to user_id if necessary
    actual_user_id = user_id
    if '@' in user_id:  # It's an email
        from database.user_manager import get_user
        user = get_user(user_id)
        if user:
            actual_user_id = str(user['Id'])
    
    key = f"{actual_user_id}_{chat_id}"
    
    # Remove from memory
    if key in user_agents:
        del user_agents[key]
    if key in user_histories:
        del user_histories[key]
    
    # Delete from database
    success = delete_chat(chat_id)
    
    if success:
        return {"status": "deleted"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete chat")

@app.put("/api/chat/{chat_id}/title")
def update_title(chat_id: str, title: dict):
    """Update chat title"""
    success = update_chat_title(chat_id, title.get("title", "New Chat"))
    if success:
        return {"status": "updated"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update title")

@app.post("/api/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload and process a file"""
    try:
        global file_processor
        if not file_processor:
            raise HTTPException(status_code=500, detail="File processor not initialized")
        
        # Check file type
        if not file_processor.is_supported_file(file.filename):
            return FileUploadResponse(
                success=False,
                message=f"نوع الملف غير مدعوم: {file.filename}. الأنواع المدعومة: PDF, DOCX, Excel, PNG, JPG"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Process file
        documents, file_hash = file_processor.process_file(file_content, file.filename)
        
        return FileUploadResponse(
            success=True,
            message=f"تم رفع الملف بنجاح: {file.filename}",
            file_hash=file_hash,
            document_count=len(documents)
        )
        
    except Exception as e:
        print(f"[ERROR] File upload error: {e}")
        import traceback
        traceback.print_exc()
        return FileUploadResponse(
            success=False,
            message=f"خطأ في معالجة الملف: {str(e)}"
        )

@app.get("/api/files")
def list_files():
    """List all uploaded files"""
    try:
        global file_processor
        if not file_processor:
            return {"files": []}
        
        files = file_processor.list_uploaded_files()
        return {"files": files}
        
    except Exception as e:
        print(f"[ERROR] List files error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/files/{file_hash}")
def delete_file(file_hash: str):
    """Delete an uploaded file"""
    try:
        global file_processor
        if not file_processor:
            raise HTTPException(status_code=500, detail="File processor not initialized")
        
        success = file_processor.remove_file(file_hash)
        
        if success:
            return {"status": "deleted"}
        else:
            raise HTTPException(status_code=404, detail="File not found")
            
    except Exception as e:
        print(f"[ERROR] Delete file error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/files")
def clear_all_files():
    """Clear all uploaded files (used when switching to legal database)"""
    try:
        global file_processor
        if not file_processor:
            return {"status": "no_processor"}
        
        uploaded_files = file_processor.list_uploaded_files()
        removed_count = 0
        
        for file_info in uploaded_files:
            if file_processor.remove_file(file_info["hash"]):
                removed_count += 1
        
        return {"status": "cleared", "removed_count": removed_count}
        
    except Exception as e:
        print(f"[ERROR] Clear files error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def start_react_frontend():
    """Start the React frontend dev server in a subprocess"""
    import subprocess
    import sys
    import shutil
    
    react_dir = Path(__file__).parent / "react-frontend"
    
    if not react_dir.exists():
        print("⚠️  React frontend not found, skipping...")
        return None
    
    # Resolve npm path (on Windows, npm is a .cmd file and needs full path)
    npm_path = shutil.which("npm")
    if npm_path is None:
        print("⚠️  npm not found in PATH, skipping React frontend...")
        return None
    
    # Check if node_modules exists
    if not (react_dir / "node_modules").exists():
        print("📦 Installing React dependencies...")
        subprocess.run([npm_path, "install"], cwd=str(react_dir))  # ✅ SECURE: shell=True removed
    
    print("🎨 Starting React frontend on http://localhost:3000")
    
    # Start React dev server as a subprocess
    if sys.platform == "win32":
        process = subprocess.Popen(
            [npm_path, "start"],
            cwd=str(react_dir),
            # ✅ SECURE: shell=True removed to prevent shell injection
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        process = subprocess.Popen(
            [npm_path, "start"],
            cwd=str(react_dir),
            # ✅ SECURE: shell=True removed to prevent shell injection
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )
    
    return process

if __name__ == "__main__":
    import signal
    import atexit
    
    react_process = None
    
    def cleanup():
        """Cleanup function to terminate React process on exit"""
        if react_process:
            print("\n🛑 Shutting down React frontend...")
            try:
                if os.name == 'nt':
                    react_process.terminate()
                else:
                    os.killpg(os.getpgid(react_process.pid), signal.SIGTERM)
            except:
                pass
    
    atexit.register(cleanup)
    
    print("=" * 80)
    print("🚀 Starting Egyptian Legal AI Full Stack Server")
    print("=" * 80)
    
    # Start React frontend
    react_process = start_react_frontend()
    
    print("\n🔧 Backend API: http://localhost:8000")
    print("📚 API Docs:    http://localhost:8000/docs")
    print("🎨 React App:   http://localhost:3000")
    print("\n" + "=" * 80 + "\n")
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    finally:
        cleanup()
