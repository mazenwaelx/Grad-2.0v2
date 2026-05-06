"""
Comprehensive Automated Test Suite for Egyptian Legal AI Assistant
Tests every major functionality in the project.

Modules tested:
  1. Database Layer       (db_config, user_manager, chat_manager, db_memory_store)
  2. Settings & Config    (settings.py)
  3. Dynamic Retrieval    (dynamic_retrieval.py)
  4. Agent Utilities      (greetings, out-of-scope, multiple questions, normalize, cache)
  5. File Processor       (supported types, hash, process files, relevance)
  6. Data Embedding       (SentenceTransformerEmbeddings wrapper)
  7. Labour Data Loader   (collect_labour_documents)
  8. API Endpoints        (FastAPI routes via TestClient)
"""

import os
import sys
import json
import hashlib
import tempfile
import sqlite3
import re
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock
from io import BytesIO

import pytest

# ---------------------------------------------------------------------------
# Make sure project root is on sys.path
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("GOOGLE_API_KEY", "test-key-for-testing")


# ===================================================================
# 1. DATABASE LAYER TESTS
# ===================================================================
class TestDatabaseConfig:
    """Tests for database/db_config.py"""

    def setup_method(self):
        """Force SQLite mode for testing and use a temp db"""
        import database.db_config as dbc
        # Reset module-level state
        dbc.USE_SQLITE = True
        self.tmp = tempfile.mkdtemp()
        dbc.DB_PATH = os.path.join(self.tmp, "test.db")
        # Drain the pool so tests are isolated
        while not dbc._pool.empty():
            try:
                dbc._pool.get_nowait()
            except Exception:
                break

    def teardown_method(self):
        import shutil, database.db_config as dbc
        # Reset
        dbc.USE_SQLITE = None
        dbc.WORKING_CONN_STR = None
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_get_db_connection_returns_pooled(self):
        from database.db_config import get_db_connection
        conn = get_db_connection()
        assert conn is not None
        # Should have cursor method
        assert hasattr(conn, "cursor")
        conn.close()

    def test_init_database_creates_tables(self):
        from database.db_config import init_database, get_db_connection
        result = init_database()
        assert result is True

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cur.fetchall()}
        assert "users" in tables
        assert "chats" in tables
        assert "messages" in tables
        cur.close()
        conn.close()

    def test_is_using_sqlite(self):
        from database.db_config import is_using_sqlite
        assert is_using_sqlite() is True

    def test_connection_pool_reuse(self):
        """Closing a connection should return it to the pool"""
        from database.db_config import get_db_connection, _pool
        conn = get_db_connection()
        conn.close()
        # Pool should have one connection now
        assert not _pool.empty()


class TestUserManager:
    """Tests for database/user_manager.py"""

    def setup_method(self):
        import database.db_config as dbc
        dbc.USE_SQLITE = True
        self.tmp = tempfile.mkdtemp()
        dbc.DB_PATH = os.path.join(self.tmp, "test.db")
        while not dbc._pool.empty():
            try: dbc._pool.get_nowait()
            except: break
        from database.db_config import init_database
        init_database()

    def teardown_method(self):
        import shutil, database.db_config as dbc
        dbc.USE_SQLITE = None
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_create_user_success(self):
        from database.user_manager import create_user
        success, msg = create_user("test@example.com", "Test User", "pass123")
        assert success is True
        assert "success" in msg.lower()

    def test_create_user_duplicate_email(self):
        from database.user_manager import create_user
        create_user("dup@example.com", "User1", "pass1")
        success, msg = create_user("dup@example.com", "User2", "pass2")
        assert success is False
        assert "exists" in msg.lower() or "unique" in msg.lower()

    def test_get_user_found(self):
        from database.user_manager import create_user, get_user
        create_user("find@example.com", "Find Me", "pw")
        user = get_user("find@example.com")
        assert user is not None
        assert user["email"] == "find@example.com"
        assert user["name"] == "Find Me"

    def test_get_user_not_found(self):
        from database.user_manager import get_user
        user = get_user("nonexistent@example.com")
        assert user is None

    def test_verify_user_correct_credentials(self):
        from database.user_manager import create_user, verify_user
        create_user("v@e.com", "V User", "secret")
        success, user = verify_user("v@e.com", "secret")
        assert success is True
        assert user["email"] == "v@e.com"

    def test_verify_user_wrong_password(self):
        from database.user_manager import create_user, verify_user
        create_user("v2@e.com", "V2", "right")
        success, user = verify_user("v2@e.com", "wrong")
        assert success is False
        assert user is None


class TestChatManager:
    """Tests for database/chat_manager.py"""

    def setup_method(self):
        import database.db_config as dbc
        dbc.USE_SQLITE = True
        self.tmp = tempfile.mkdtemp()
        dbc.DB_PATH = os.path.join(self.tmp, "test.db")
        while not dbc._pool.empty():
            try: dbc._pool.get_nowait()
            except: break
        from database.db_config import init_database
        init_database()
        from database.user_manager import create_user
        create_user("chat_user@test.com", "Chat User", "pw")

    def teardown_method(self):
        import shutil, database.db_config as dbc
        dbc.USE_SQLITE = None
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_create_chat(self):
        from database.chat_manager import create_chat
        result = create_chat("chat-001", "chat_user@test.com", "My Chat")
        assert result is True

    def test_create_chat_duplicate_returns_true(self):
        from database.chat_manager import create_chat
        create_chat("chat-dup", "chat_user@test.com")
        result = create_chat("chat-dup", "chat_user@test.com")
        assert result is True  # Not an error

    def test_get_user_chats(self):
        from database.chat_manager import create_chat, get_user_chats
        create_chat("c1", "chat_user@test.com", "Chat 1")
        create_chat("c2", "chat_user@test.com", "Chat 2")
        chats = get_user_chats("chat_user@test.com")
        assert len(chats) == 2

    def test_update_chat_title(self):
        from database.chat_manager import create_chat, update_chat_title, get_user_chats
        create_chat("c-title", "chat_user@test.com", "Old Title")
        result = update_chat_title("c-title", "New Title")
        assert result is True
        chats = get_user_chats("chat_user@test.com")
        titles = [c["title"] for c in chats]
        assert "New Title" in titles

    def test_delete_chat(self):
        from database.chat_manager import create_chat, delete_chat, get_user_chats
        create_chat("c-del", "chat_user@test.com")
        result = delete_chat("c-del")
        assert result is True
        chats = get_user_chats("chat_user@test.com")
        ids = [c["chat_id"] for c in chats]
        assert "c-del" not in ids

    def test_add_and_get_messages(self):
        from database.chat_manager import create_chat, add_message, get_chat_messages
        create_chat("c-msg", "chat_user@test.com")
        add_message("c-msg", "user", "Hello")
        add_message("c-msg", "assistant", "Hi there")
        msgs = get_chat_messages("c-msg")
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"

    def test_get_recent_messages(self):
        from database.chat_manager import create_chat, add_message, get_recent_messages
        create_chat("c-recent", "chat_user@test.com")
        for i in range(15):
            add_message("c-recent", "user", f"Message {i}")
        recent = get_recent_messages("c-recent", limit=5)
        assert len(recent) == 5

    def test_get_messages_empty_chat(self):
        from database.chat_manager import get_chat_messages
        msgs = get_chat_messages("nonexistent-chat")
        assert msgs == []


class TestDatabaseMemoryStore:
    """Tests for database/db_memory_store.py"""

    def setup_method(self):
        import database.db_config as dbc
        dbc.USE_SQLITE = True
        self.tmp = tempfile.mkdtemp()
        dbc.DB_PATH = os.path.join(self.tmp, "test.db")
        while not dbc._pool.empty():
            try: dbc._pool.get_nowait()
            except: break
        from database.db_config import init_database
        init_database()
        from database.user_manager import create_user
        create_user("mem@test.com", "Mem User", "pw")
        from database.chat_manager import create_chat
        create_chat("mem-chat", "mem@test.com")

    def teardown_method(self):
        import shutil, database.db_config as dbc
        dbc.USE_SQLITE = None
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_add_user_message(self):
        from database.db_memory_store import DatabaseChatMessageHistory
        from langchain_core.messages import HumanMessage
        history = DatabaseChatMessageHistory("mem-chat")
        history.add_user_message("Test question")
        assert len(history.messages) == 1
        assert isinstance(history.messages[0], HumanMessage)

    def test_add_ai_message(self):
        from database.db_memory_store import DatabaseChatMessageHistory
        from langchain_core.messages import AIMessage
        history = DatabaseChatMessageHistory("mem-chat")
        history.add_ai_message("Test answer")
        assert len(history.messages) == 1
        assert isinstance(history.messages[0], AIMessage)

    def test_message_limit(self):
        from database.db_memory_store import DatabaseChatMessageHistory
        history = DatabaseChatMessageHistory("mem-chat")
        for i in range(12):
            history.add_user_message(f"Msg {i}")
        # Should keep only last 10 in memory
        assert len(history.messages) <= 10

    def test_clear(self):
        from database.db_memory_store import DatabaseChatMessageHistory
        history = DatabaseChatMessageHistory("mem-chat")
        history.add_user_message("hello")
        history.clear()
        assert len(history.messages) == 0


# ===================================================================
# 2. SETTINGS & CONFIG TESTS
# ===================================================================
class TestSettings:
    """Tests for src/config/settings.py"""

    def test_model_name_defined(self):
        from src.config.settings import MODEL_NAME
        assert MODEL_NAME is not None
        assert "gemini" in MODEL_NAME.lower()

    def test_faiss_paths_defined(self):
        from src.config.settings import FAISS_INDEX_DIR, FAISS_STATS_PATH
        assert FAISS_INDEX_DIR is not None
        assert FAISS_STATS_PATH is not None

    def test_chunk_settings(self):
        from src.config.settings import CHUNK_SIZE, CHUNK_OVERLAP
        assert CHUNK_SIZE > 0
        assert CHUNK_OVERLAP > 0
        assert CHUNK_OVERLAP < CHUNK_SIZE

    def test_dynamic_retrieval_settings(self):
        from src.config.settings import ENABLE_DYNAMIC_RETRIEVAL, MIN_DOCUMENTS, MAX_DOCUMENTS
        assert isinstance(ENABLE_DYNAMIC_RETRIEVAL, bool)
        assert MIN_DOCUMENTS < MAX_DOCUMENTS

    def test_get_api_key(self):
        from src.config.settings import get_api_key
        key = get_api_key()
        assert isinstance(key, str)

    def test_validate_api_key_rejects_placeholder(self):
        from src.config.settings import validate_api_key
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "YOUR_GEMINI_API_KEY_HERE"}):
            assert validate_api_key() is False

    def test_validate_api_key_rejects_empty(self):
        from src.config.settings import validate_api_key
        with patch.dict(os.environ, {"GOOGLE_API_KEY": ""}):
            assert validate_api_key() is False


# ===================================================================
# 3. DYNAMIC RETRIEVAL TESTS
# ===================================================================
class TestDynamicRetrieval:
    """Tests for src/retrieval/dynamic_retrieval.py"""

    def test_simple_question_low_docs(self):
        from src.retrieval.dynamic_retrieval import DynamicRetrieval
        dr = DynamicRetrieval()
        result = dr.analyze_question_complexity("ما هي ساعات العمل؟")
        assert result["complexity_level"] == "simple"
        assert result["recommended_docs"] <= 3

    def test_complex_question_high_docs(self):
        from src.retrieval.dynamic_retrieval import DynamicRetrieval
        dr = DynamicRetrieval()
        result = dr.analyze_question_complexity(
            "اشرح بالتفصيل إجراءات فصل العامل وما هي حقوقه في هذه الحالة؟"
        )
        assert result["recommended_docs"] >= 4

    def test_short_question(self):
        from src.retrieval.dynamic_retrieval import DynamicRetrieval
        dr = DynamicRetrieval()
        result = dr.analyze_question_complexity("كم الراتب؟")
        assert "short_question" in result["indicators_found"]

    def test_long_question(self):
        from src.retrieval.dynamic_retrieval import DynamicRetrieval
        dr = DynamicRetrieval()
        # 16+ words
        long_q = "ما هي جميع أنواع الإجازات المتاحة للعامل وما هي شروط كل منها وكيف يمكن الحصول عليها من صاحب العمل بشكل قانوني سليم"
        result = dr.analyze_question_complexity(long_q)
        assert result["word_count"] > 15
        assert "long_question" in result["indicators_found"]

    def test_get_optimal_k_returns_int(self):
        from src.retrieval.dynamic_retrieval import get_dynamic_k
        k = get_dynamic_k("ما هو قانون العمل؟")
        assert isinstance(k, int)
        assert 2 <= k <= 6

    def test_multi_topic_question(self):
        from src.retrieval.dynamic_retrieval import DynamicRetrieval
        dr = DynamicRetrieval()
        result = dr.analyze_question_complexity(
            "ما هي جميع أنواع الإجازات المتاحة للعامل وشروط كل منها؟"
        )
        assert result["recommended_docs"] >= 3

    def test_comparison_question(self):
        from src.retrieval.dynamic_retrieval import DynamicRetrieval
        dr = DynamicRetrieval()
        result = dr.analyze_question_complexity(
            "ما الفرق بين إجازة الأمومة وإجازة الوضع؟"
        )
        assert result["recommended_docs"] >= 3


# ===================================================================
# 4. AGENT UTILITIES TESTS (greetings, out-of-scope, etc.)
# ===================================================================
class TestGreetings:
    """Tests for greeting detection and responses"""

    def test_arabic_greeting_ahlan(self):
        from src.agents.langchain_react_agent import is_greeting
        assert is_greeting("أهلا") is True

    def test_arabic_greeting_marhaba(self):
        from src.agents.langchain_react_agent import is_greeting
        assert is_greeting("مرحبا") is True

    def test_arabic_greeting_salam(self):
        from src.agents.langchain_react_agent import is_greeting
        assert is_greeting("السلام عليكم") is True

    def test_english_greeting(self):
        from src.agents.langchain_react_agent import is_greeting
        assert is_greeting("hello") is True
        assert is_greeting("hi") is True

    def test_not_greeting_question(self):
        from src.agents.langchain_react_agent import is_greeting
        assert is_greeting("ما هي ساعات العمل؟") is False

    def test_not_greeting_legal_term(self):
        from src.agents.langchain_react_agent import is_greeting
        assert is_greeting("قانون العمل المصري") is False

    def test_salam_response_different(self):
        from src.agents.langchain_react_agent import get_greeting_response
        resp = get_greeting_response("السلام عليكم")
        assert "وعليكم السلام" in resp

    def test_generic_greeting_response(self):
        from src.agents.langchain_react_agent import get_greeting_response
        resp = get_greeting_response("أهلا")
        assert "أهلاً" in resp or "مساعدك" in resp


class TestMultipleQuestions:
    """Tests for multiple question detection"""

    def test_single_question_allowed(self):
        from src.agents.langchain_react_agent import has_multiple_questions
        assert has_multiple_questions("ما هي ساعات العمل؟") is False

    def test_three_questions_allowed(self):
        from src.agents.langchain_react_agent import has_multiple_questions
        # 3 questions should be allowed
        text = "سؤال 1؟ سؤال 2؟ سؤال 3؟"
        assert has_multiple_questions(text) is False

    def test_four_plus_questions_rejected(self):
        from src.agents.langchain_react_agent import has_multiple_questions
        text = "سؤال 1؟ سؤال 2؟ سؤال 3؟ سؤال 4؟"
        assert has_multiple_questions(text) is True


class TestOutOfScope:
    """Tests for out-of-scope question detection"""

    def test_travel_question_out_of_scope(self):
        from src.agents.langchain_react_agent import LangChainReActAgent
        result = LangChainReActAgent._check_out_of_scope(None, "كيف أحصل على تأشيرة سفر؟")
        assert result is not None  # Should be rejected

    def test_cooking_question_out_of_scope(self):
        from src.agents.langchain_react_agent import LangChainReActAgent
        result = LangChainReActAgent._check_out_of_scope(None, "ما هي وصفة الكبسة؟")
        assert result is not None

    def test_labor_question_in_scope(self):
        from src.agents.langchain_react_agent import LangChainReActAgent
        result = LangChainReActAgent._check_out_of_scope(None, "ما هي حقوق العامل في الإجازة السنوية؟")
        assert result is None  # Should be accepted

    def test_mixed_context_labor_in_scope(self):
        """Travel keyword but labor context should be in scope"""
        from src.agents.langchain_react_agent import LangChainReActAgent
        result = LangChainReActAgent._check_out_of_scope(None, "هل يحق للعامل الحصول على تأشيرة سفر من صاحب العمل؟")
        assert result is None  # Has labor context


class TestNormalization:
    """Tests for question normalization and caching"""

    def test_normalize_removes_diacritics(self):
        from src.agents.langchain_react_agent import normalize_question
        result = normalize_question("مَا هُوَ الأَجْر؟")
        assert "مَ" not in result  # Diacritics removed

    def test_normalize_alef_variations(self):
        from src.agents.langchain_react_agent import normalize_question
        r1 = normalize_question("إجازة")
        r2 = normalize_question("اجازة")
        assert r1 == r2

    def test_normalize_whitespace(self):
        from src.agents.langchain_react_agent import normalize_question
        result = normalize_question("  ما   هو   القانون  ")
        assert "  " not in result

    def test_cache_key_deterministic(self):
        from src.agents.langchain_react_agent import get_cache_key
        k1 = get_cache_key("ما هي الإجازات؟")
        k2 = get_cache_key("ما هي الإجازات؟")
        assert k1 == k2

    def test_cache_key_normalized(self):
        from src.agents.langchain_react_agent import get_cache_key
        k1 = get_cache_key("إجازة")
        k2 = get_cache_key("اجازة")
        assert k1 == k2


# ===================================================================
# 5. FILE PROCESSOR TESTS
# ===================================================================
class TestFileProcessor:
    """Tests for src/retrieval/file_processor.py"""

    def _make_processor(self):
        """Create a FileProcessor with mock embeddings"""
        mock_embeddings = MagicMock()
        mock_embeddings.embed_documents.return_value = [[0.1] * 768]
        mock_embeddings.embed_query.return_value = [0.1] * 768
        from src.retrieval.file_processor import FileProcessor
        return FileProcessor(mock_embeddings)

    def test_supported_file_types(self):
        fp = self._make_processor()
        assert fp.is_supported_file("doc.pdf") is True
        assert fp.is_supported_file("doc.docx") is True
        assert fp.is_supported_file("data.xlsx") is True
        assert fp.is_supported_file("image.png") is True
        assert fp.is_supported_file("image.jpg") is True
        assert fp.is_supported_file("image.jpeg") is True

    def test_unsupported_file_types(self):
        fp = self._make_processor()
        assert fp.is_supported_file("script.py") is False
        assert fp.is_supported_file("data.csv") is False
        assert fp.is_supported_file("video.mp4") is False

    def test_file_hash_deterministic(self):
        fp = self._make_processor()
        content = b"test content"
        h1 = fp.get_file_hash(content)
        h2 = fp.get_file_hash(content)
        assert h1 == h2

    def test_file_hash_different_content(self):
        fp = self._make_processor()
        h1 = fp.get_file_hash(b"content A")
        h2 = fp.get_file_hash(b"content B")
        assert h1 != h2

    def test_list_uploaded_files_empty(self):
        fp = self._make_processor()
        files = fp.list_uploaded_files()
        assert files == []

    def test_remove_nonexistent_file(self):
        fp = self._make_processor()
        result = fp.remove_file("nonexistent-hash")
        assert result is False

    def test_get_file_info_nonexistent(self):
        fp = self._make_processor()
        info = fp.get_file_info("nonexistent-hash")
        assert info is None

    def test_question_relevance_explicit_file_keyword(self):
        fp = self._make_processor()
        # Mock an uploaded file
        fp.uploaded_files["abc123"] = {
            "filename": "contract.pdf",
            "documents": [MagicMock(page_content="عقد عمل بين الطرف الأول والطرف الثاني", metadata={})],
            "file_type": ".pdf",
        }
        score = fp.calculate_question_relevance("ما محتوى الملف؟", "abc123")
        assert score == 1.0  # Explicit file keyword

    def test_is_question_about_file_explicit(self):
        fp = self._make_processor()
        fp.uploaded_files["abc123"] = {
            "filename": "contract.pdf",
            "documents": [MagicMock(page_content="عقد العمل", metadata={})],
            "file_type": ".pdf",
        }
        assert fp.is_question_about_file("اشرح لي الملف", "abc123") is True

    def test_set_and_get_file_processor(self):
        from src.retrieval.file_processor import set_file_processor, get_file_processor
        fp = self._make_processor()
        set_file_processor(fp)
        assert get_file_processor() is fp
        set_file_processor(None)  # Cleanup


# ===================================================================
# 6. DATA EMBEDDING TESTS (mocked to avoid downloading models)
# ===================================================================
class TestDataEmbedding:
    """Tests for data/data_embedding.py"""

    def test_device_detection_auto(self):
        from data.data_embedding import _get_device
        device = _get_device("auto")
        assert device in ("cpu", "cuda", "mps")

    def test_device_detection_explicit(self):
        from data.data_embedding import _get_device
        assert _get_device("cpu") == "cpu"
        assert _get_device("cuda") == "cuda"


# ===================================================================
# 7. LABOUR DATA LOADER TESTS
# ===================================================================
class TestLabourDataLoader:
    """Tests for labour_data_loader.py"""

    def test_data_root_path_defined(self):
        from labour_data_loader import DATA_ROOT
        assert DATA_ROOT is not None

    def test_collect_documents_returns_tuple(self):
        from labour_data_loader import collect_labour_documents
        result = collect_labour_documents()
        assert isinstance(result, tuple)
        assert len(result) == 4
        base_docs, prechunked_docs, pdf_pages, sources_count = result
        assert isinstance(base_docs, list)
        assert isinstance(prechunked_docs, list)

    def test_documents_have_content(self):
        """Verify loaded documents have page_content"""
        from labour_data_loader import collect_labour_documents
        base_docs, prechunked_docs, _, _ = collect_labour_documents()
        all_docs = base_docs + prechunked_docs
        if all_docs:
            for doc in all_docs[:5]:  # Check first 5
                assert hasattr(doc, "page_content")
                assert len(doc.page_content) > 0

    def test_documents_have_metadata(self):
        from labour_data_loader import collect_labour_documents
        base_docs, prechunked_docs, _, _ = collect_labour_documents()
        all_docs = base_docs + prechunked_docs
        if all_docs:
            for doc in all_docs[:5]:
                assert hasattr(doc, "metadata")
                assert "source" in doc.metadata


# ===================================================================
# 8. API ENDPOINT TESTS (FastAPI TestClient)
# ===================================================================
class TestAPIEndpoints:
    """Tests for api_server.py FastAPI endpoints"""

    @pytest.fixture(autouse=True)
    def setup_api(self):
        """Setup test client with mocked dependencies"""
        import database.db_config as dbc
        dbc.USE_SQLITE = True
        self.tmp = tempfile.mkdtemp()
        dbc.DB_PATH = os.path.join(self.tmp, "test.db")
        while not dbc._pool.empty():
            try: dbc._pool.get_nowait()
            except: break
        from database.db_config import init_database
        init_database()

        # Now import and create test client
        from fastapi.testclient import TestClient
        from api_server import app
        self.client = TestClient(app, raise_server_exceptions=False)
        yield

        import shutil
        dbc.USE_SQLITE = None
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_health_check(self):
        response = self.client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_register_user(self):
        response = self.client.post("/api/register", json={
            "email": "api_test@example.com",
            "name": "API Test User",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "api_test@example.com"
        assert data["name"] == "API Test User"

    def test_register_duplicate(self):
        self.client.post("/api/register", json={
            "email": "dup_api@example.com", "name": "U1", "password": "p1"
        })
        response = self.client.post("/api/register", json={
            "email": "dup_api@example.com", "name": "U2", "password": "p2"
        })
        assert response.status_code == 400

    def test_login_success(self):
        self.client.post("/api/register", json={
            "email": "login@test.com", "name": "Login User", "password": "pass"
        })
        response = self.client.post("/api/login", json={
            "email": "login@test.com", "password": "pass"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "login@test.com"

    def test_login_wrong_password(self):
        self.client.post("/api/register", json={
            "email": "wrong@test.com", "name": "Wrong", "password": "right"
        })
        response = self.client.post("/api/login", json={
            "email": "wrong@test.com", "password": "wrong"
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self):
        response = self.client.post("/api/login", json={
            "email": "ghost@test.com", "password": "pass"
        })
        assert response.status_code == 401

    def test_get_chats_empty(self):
        self.client.post("/api/register", json={
            "email": "chats@test.com", "name": "Chats User", "password": "p"
        })
        response = self.client.get("/api/chats/chats@test.com")
        assert response.status_code == 200
        data = response.json()
        assert "chats" in data
        assert isinstance(data["chats"], list)

    def test_get_messages_empty(self):
        response = self.client.get("/api/messages/nonexistent-chat")
        assert response.status_code == 200
        data = response.json()
        assert data["messages"] == []

    def test_update_chat_title(self):
        from database.user_manager import create_user
        from database.chat_manager import create_chat
        create_user("title@test.com", "Title User", "p")
        create_chat("title-chat", "title@test.com")
        response = self.client.put(
            "/api/chat/title-chat/title",
            json={"title": "Updated Title"}
        )
        assert response.status_code == 200

    def test_delete_chat_endpoint(self):
        from database.user_manager import create_user
        from database.chat_manager import create_chat
        create_user("del@test.com", "Del User", "p")
        create_chat("del-chat", "del@test.com")
        response = self.client.delete("/api/chat/del@test.com/del-chat")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"

    def test_list_files_empty(self):
        response = self.client.get("/api/files")
        assert response.status_code == 200
        data = response.json()
        assert "files" in data

    def test_upload_unsupported_file(self):
        """Upload an unsupported file type should return success=False"""
        response = self.client.post(
            "/api/upload",
            files={"file": ("test.txt", b"hello world", "text/plain")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    def test_register_missing_fields(self):
        """Missing required fields should fail"""
        response = self.client.post("/api/register", json={
            "email": "incomplete@test.com"
        })
        assert response.status_code == 422  # Validation error


# ===================================================================
# 9. PYDANTIC MODEL TESTS
# ===================================================================
class TestPydanticModels:
    """Test Pydantic request/response models"""

    def test_chat_request_model(self):
        from api_server import ChatRequest
        req = ChatRequest(message="hello", chat_id="c1", user_id="u1")
        assert req.message == "hello"
        assert req.chat_id == "c1"

    def test_user_register_model(self):
        from api_server import UserRegister
        reg = UserRegister(email="test@t.com", name="Test", password="pw")
        assert reg.email == "test@t.com"

    def test_user_login_model(self):
        from api_server import UserLogin
        login = UserLogin(email="test@t.com", password="pw")
        assert login.email == "test@t.com"

    def test_user_response_model(self):
        from api_server import UserResponse
        resp = UserResponse(email="test@t.com", name="Test")
        assert resp.token == "demo_token"

    def test_file_upload_response_model(self):
        from api_server import FileUploadResponse
        resp = FileUploadResponse(success=True, message="OK", file_hash="abc", document_count=5)
        assert resp.success is True
        assert resp.document_count == 5


# ===================================================================
# 10. INTEGRATION SANITY TESTS
# ===================================================================
class TestIntegrationSanity:
    """Cross-module integration sanity checks"""

    def test_database_package_exports(self):
        """Verify database __init__.py exports all expected names"""
        from database import (
            get_db_connection, init_database,
            create_user, get_user, verify_user,
            create_chat, get_user_chats, update_chat_title, delete_chat,
            add_message, get_chat_messages, get_recent_messages
        )
        # If all imports succeed, the exports are correct
        assert callable(init_database)
        assert callable(create_user)
        assert callable(create_chat)

    def test_src_package_exports(self):
        """Verify src package structure is importable"""
        from src.config.settings import MODEL_NAME
        from src.retrieval.dynamic_retrieval import DynamicRetrieval
        assert MODEL_NAME is not None
        assert DynamicRetrieval is not None

    def test_agent_prompt_template_has_placeholders(self):
        """Verify the ReAct prompt template has required placeholders"""
        from src.agents.langchain_react_agent import REACT_PROMPT_TEMPLATE
        assert "{tools}" in REACT_PROMPT_TEMPLATE
        assert "{tool_names}" in REACT_PROMPT_TEMPLATE
        assert "{input}" in REACT_PROMPT_TEMPLATE
        assert "{agent_scratchpad}" in REACT_PROMPT_TEMPLATE

    def test_greeting_patterns_valid_regex(self):
        """Verify all greeting regex patterns compile without error"""
        from src.agents.langchain_react_agent import GREETING_PATTERNS
        for pattern in GREETING_PATTERNS:
            compiled = re.compile(pattern, re.IGNORECASE)
            assert compiled is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
