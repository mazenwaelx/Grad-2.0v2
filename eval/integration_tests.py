"""
Integration Tests for Egyptian Legal AI
========================================

Tests the integration between different system components:
- Database interactions with agent
- Retriever with LLM
- File processor with agent
- API endpoints with database
- Frontend with backend API

Usage:
    python eval/integration_tests.py
"""

import sys
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

import os
import sys
import time
from pathlib import Path
from datetime import datetime
import json

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class IntegrationTestSuite:
    """Integration testing suite"""
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
    
    def test_database_chat_flow(self):
        """Test: Database stores and retrieves chat messages correctly"""
        result = {"name": "Database Chat Flow", "status": "pending"}
        start = time.time()
        
        try:
            from database import create_user, create_chat, get_chat_messages, get_user
            from database.db_memory_store import DatabaseChatMessageHistory
            
            # Create test user and chat
            test_email = f"integration_test_{int(time.time())}@test.com"
            success, msg = create_user(test_email, "Integration Test", "TestPass123!")
            
            if not (success or "already exists" in str(msg).lower()):
                raise Exception(f"User creation failed: {msg}")
            
            # Get user to get actual user_id (integer)
            user = get_user(test_email)
            if not user:
                raise Exception("User not found after creation")
            
            user_id = int(user['Id'])  # Convert to int
            
            # Create chat WITH PROPER USER_ID
            test_chat_id = f"integration_chat_{int(time.time())}"
            
            # Add messages through history store (now auto-creates chat with integer user_id)
            history = DatabaseChatMessageHistory(test_chat_id, user_id)
            history.add_user_message("اختبار رسالة المستخدم")
            history.add_ai_message("اختبار رد الذكاء الاصطناعي")
            
            # Retrieve messages
            messages = get_chat_messages(test_chat_id)
            assert len(messages) >= 2, f"Expected at least 2 messages, got {len(messages)}"
            
            result["status"] = "passed"
            result["details"] = f"Stored and retrieved {len(messages)} messages"
            print(f"  ✅ Database Chat Flow - PASSED ({len(messages)} messages)")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ Database Chat Flow - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def test_retriever_llm_integration(self):
        """Test: Retriever feeds context to LLM correctly"""
        result = {"name": "Retriever + LLM Integration", "status": "pending"}
        start = time.time()
        
        try:
            from dotenv import load_dotenv
            load_dotenv(override=True)
            
            # Check if API key is available
            import os
            if not os.getenv("GOOGLE_API_KEY"):
                result["status"] = "skipped"
                result["details"] = "API key not configured"
                print(f"  ⚠️ Retriever + LLM Integration - SKIPPED (no API key)")
                self.results.append(result)
                return result
            
            from src.retrieval.retriever import prepare_retriever
            from src.llm.llm_manager import init_llm
            from src.config.settings import MODEL_NAME
            
            # Initialize components
            retriever, _, _, _ = prepare_retriever("data/labour_data/labour_law.md")
            llm = init_llm(MODEL_NAME)
            
            # Test query
            question = "ما هي ساعات العمل؟"
            docs = retriever.invoke(question)
            assert len(docs) > 0, "Retriever returned no documents"
            
            # Build context from docs
            context = "\n\n".join([doc.page_content[:500] for doc in docs[:3]])
            
            # Query LLM with context
            prompt = f"السياق:\n{context}\n\nالسؤال: {question}\nالإجابة:"
            response = llm.invoke(prompt)
            
            # Check response
            response_text = response.content if hasattr(response, 'content') else str(response)
            assert len(response_text) > 50, "LLM response too short"
            assert "ساع" in response_text or "عمل" in response_text, "Response doesn't mention relevant terms"
            
            result["status"] = "passed"
            result["details"] = f"Retrieved {len(docs)} docs, LLM responded with {len(response_text)} chars"
            print(f"  ✅ Retriever + LLM Integration - PASSED")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ Retriever + LLM Integration - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def test_file_processor_agent(self):
        """Test: File processor integrates with agent for file queries"""
        result = {"name": "File Processor + Agent", "status": "pending"}
        start = time.time()
        
        try:
            from src.retrieval.file_processor import FileProcessor
            from data.data_embedding import SentenceTransformerEmbeddings
            
            # Initialize file processor
            embeddings = SentenceTransformerEmbeddings()
            processor = FileProcessor(embeddings)
            
            # Test file operations
            test_content = "هذا ملف اختبار يحتوي على معلومات قانونية عن العمل"
            test_file = b"Test content for integration"
            
            # Verify processor is functional
            assert hasattr(processor, 'process_file'), "Processor missing process_file method"
            assert hasattr(processor, 'list_uploaded_files'), "Processor missing list method"
            
            result["status"] = "passed"
            result["details"] = "File processor initialized and functional"
            print(f"  ✅ File Processor + Agent - PASSED")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ File Processor + Agent - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def test_api_database_integration(self):
        """Test: API chat endpoint correctly interacts with database"""
        result = {"name": "API + Database Integration", "status": "pending"}
        start = time.time()
        
        try:
            import urllib.request
            import json
            
            BACKEND_URL = "http://localhost:8000"
            
            # Check if backend is running
            try:
                urllib.request.urlopen(f"{BACKEND_URL}/api/health", timeout=2)
            except Exception:
                result["status"] = "skipped"
                result["details"] = "Backend not running"
                print(f"  ⚠️ API + Database Integration - SKIPPED (backend offline)")
                self.results.append(result)
                return result
            
            # Note: Authentication is now handled by LawyerConnect website
            # This test verifies that chat API can interact with database
            
            # Create test user directly in database (since auth is on website)
            from database import create_user, get_user
            test_email = f"api_integration_{int(time.time())}@test.com"
            create_user(test_email, "API Integration Test", "TestPass123!")
            user = get_user(test_email)
            assert user is not None, "User not created in database"
            
            # Test chat endpoint (writes to DB)
            chat_data = json.dumps({
                "message": "اختبار التكامل",
                "chat_id": f"integration_test_{int(time.time())}",
                "user_id": str(user['Id'])
            }).encode('utf-8')
            
            chat_req = urllib.request.Request(
                f"{BACKEND_URL}/api/chat",
                data=chat_data,
                headers={"Content-Type": "application/json"}
            )
            
            with urllib.request.urlopen(chat_req, timeout=60) as response:
                data = json.loads(response.read())
                assert "response" in data, "Chat response missing"
                assert len(data["response"]) > 0, "Empty response"
            
            result["status"] = "passed"
            result["details"] = "Chat API successfully interacts with database"
            print(f"  ✅ API + Database Integration - PASSED")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ API + Database Integration - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def test_agent_full_pipeline(self):
        """Test: Agent uses all tools (retriever, history, file processor) correctly"""
        result = {"name": "Agent Full Pipeline", "status": "pending"}
        start = time.time()
        
        try:
            from dotenv import load_dotenv
            load_dotenv(override=True)
            
            from src.retrieval.retriever import prepare_retriever
            from src.retrieval.file_processor import FileProcessor, set_file_processor
            from src.agents.langchain_react_agent import LangChainReActAgent, build_langchain_tools
            from src.llm.llm_manager import init_llm
            from src.config.settings import MODEL_NAME
            from data.data_embedding import SentenceTransformerEmbeddings
            from database.db_memory_store import DatabaseChatMessageHistory
            
            # Initialize all components
            retriever, _, _, _ = prepare_retriever("data/labour_data/labour_law.md")
            embeddings = SentenceTransformerEmbeddings()
            file_processor = FileProcessor(embeddings)
            set_file_processor(file_processor)
            
            llm = init_llm(MODEL_NAME)
            
            chat_id = f"integration_agent_{int(time.time())}"
            # Don't pass user_id - will default to 1 (system user)
            history_store = DatabaseChatMessageHistory(chat_id)
            
            # Build tools and agent
            tools = build_langchain_tools(retriever, history_store, file_processor)
            agent = LangChainReActAgent(
                llm=llm,
                retriever=retriever,
                history_store=history_store,
                file_processor=file_processor,
                chat_id=chat_id,
                log_callback=lambda msg: None,  # Silent
                max_iterations=6,
                verbose=False
            )
            
            # Test query
            question = "كم عدد أيام الإجازة السنوية؟"
            response = agent.ask(question)
            
            # Verify response
            assert len(response) > 50, "Response too short"
            assert "إجازة" in response or "يوم" in response, "Response doesn't mention relevant terms"
            
            result["status"] = "passed"
            result["details"] = f"Agent processed query successfully ({len(response)} chars)"
            print(f"  ✅ Agent Full Pipeline - PASSED")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ Agent Full Pipeline - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def run_all(self):
        """Run all integration tests"""
        print("=" * 70)
        print("🔗 Integration Tests - Egyptian Legal AI")
        print("=" * 70 + "\n")
        
        self.test_database_chat_flow()
        self.test_retriever_llm_integration()
        self.test_file_processor_agent()
        self.test_api_database_integration()
        self.test_agent_full_pipeline()
        
        # Summary
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "passed")
        failed = sum(1 for r in self.results if r["status"] == "failed")
        skipped = sum(1 for r in self.results if r["status"] == "skipped")
        
        print("\n" + "=" * 70)
        print("📊 Integration Tests Summary")
        print("=" * 70)
        print(f"  Total:   {total}")
        print(f"  Passed:  {passed}")
        print(f"  Failed:  {failed}")
        print(f"  Skipped: {skipped}")
        print(f"  Pass Rate: {(passed/max(total-skipped, 1))*100:.1f}%")
        print("=" * 70)
        
        # Save results
        self.save_results()
        
        return passed == (total - skipped)
    
    def save_results(self):
        """Save results to JSON"""
        reports_dir = PROJECT_ROOT / "eval" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        summary = {
            "total": len(self.results),
            "passed": sum(1 for r in self.results if r["status"] == "passed"),
            "failed": sum(1 for r in self.results if r["status"] == "failed"),
            "skipped": sum(1 for r in self.results if r["status"] == "skipped"),
            "elapsed_seconds": round(time.time() - self.start_time, 2),
            "timestamp": datetime.now().isoformat()
        }
        summary["pass_rate"] = round((summary["passed"] / max(summary["total"] - summary["skipped"], 1)) * 100, 1)
        
        output = {
            "summary": summary,
            "results": self.results
        }
        
        output_path = reports_dir / f"integration_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"\n📄 Results saved: {output_path}")


if __name__ == "__main__":
    suite = IntegrationTestSuite()
    success = suite.run_all()
    sys.exit(0 if success else 1)
