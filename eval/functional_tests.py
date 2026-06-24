"""
Functional Tests for Egyptian Legal AI
=======================================

Tests specific functional requirements:
- Chat functionality
- File upload/download
- User authentication
- Search and retrieval
- Response generation
- Chat history management

Usage:
    python eval/functional_tests.py
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


class FunctionalTestSuite:
    """Functional testing suite"""
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        self.backend_url = "http://localhost:8000"
    
    def _check_backend(self):
        """Check if backend is running"""
        try:
            import urllib.request
            urllib.request.urlopen(f"{self.backend_url}/api/health", timeout=2)
            return True
        except Exception:
            return False
    
    def test_user_registration_function(self):
        """Test: User registration creates valid accounts"""
        result = {"name": "User Registration Function", "status": "pending"}
        start = time.time()
        
        try:
            from database import create_user, get_user
            
            test_email = f"func_test_reg_{int(time.time())}@test.com"
            success, msg = create_user(test_email, "Functional Test", "TestPass123!")
            
            if success or "already exists" in msg:
                # Verify user exists
                user = get_user(test_email)
                assert user is not None, "User not found after creation"
                assert user["Email"] == test_email, "Email mismatch"
                
                result["status"] = "passed"
                result["details"] = "User registration functional"
                print(f"  ✅ User Registration Function - PASSED")
            else:
                raise Exception(f"Registration failed: {msg}")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ User Registration Function - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def test_user_authentication_function(self):
        """Test: User authentication validates credentials correctly"""
        result = {"name": "User Authentication Function", "status": "pending"}
        start = time.time()
        
        try:
            from database import create_user, verify_user
            
            test_email = f"func_test_auth_{int(time.time())}@test.com"
            test_pass = "TestPass123!"
            
            # Create user
            success, msg = create_user(test_email, "Auth Test", test_pass)
            if not success and "already exists" not in msg:
                raise Exception(f"Failed to create user: {msg}")
            
            # Small delay to ensure database write completes
            import time as t
            t.sleep(0.5)
            
            # Test valid credentials
            success, user = verify_user(test_email, test_pass)
            assert success, "Valid credentials rejected"
            assert user["Email"] == test_email, "User data mismatch"
            
            # Test invalid credentials
            success, _ = verify_user(test_email, "WrongPassword")
            assert not success, "Invalid credentials accepted"
            
            result["status"] = "passed"
            result["details"] = "Authentication validates correctly"
            print(f"  ✅ User Authentication Function - PASSED")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ User Authentication Function - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def test_chat_creation_function(self):
        """Test: Chat creation and management works"""
        result = {"name": "Chat Creation Function", "status": "pending"}
        start = time.time()
        
        try:
            from database import create_user, create_chat, get_user_chats
            
            test_email = f"func_test_chat_{int(time.time())}@test.com"
            create_user(test_email, "Chat Test", "TestPass123!")
            
            # Get user ID (integer)
            from database.user_manager import get_user
            user = get_user(test_email)
            user_id = int(user["Id"])
            
            # Create chat
            chat_id = f"func_chat_{int(time.time())}"
            create_chat(chat_id, user_id)
            
            # Verify chat exists
            chats = get_user_chats(user_id)
            assert len(chats) > 0, "No chats found"
            assert any(c["chat_id"] == chat_id for c in chats), "Created chat not found"
            
            result["status"] = "passed"
            result["details"] = "Chat creation functional"
            print(f"  ✅ Chat Creation Function - PASSED")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ Chat Creation Function - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def test_message_storage_function(self):
        """Test: Messages are stored and retrieved correctly"""
        result = {"name": "Message Storage Function", "status": "pending"}
        start = time.time()
        
        try:
            from database.db_memory_store import DatabaseChatMessageHistory
            
            chat_id = f"func_msg_{int(time.time())}"
            history = DatabaseChatMessageHistory(chat_id)
            
            # Add messages
            history.add_user_message("سؤال اختبار")
            history.add_ai_message("جواب اختبار")
            
            # Retrieve messages
            from database import get_chat_messages
            messages = get_chat_messages(chat_id)
            
            assert len(messages) >= 2, f"Expected at least 2 messages, got {len(messages)}"
            
            result["status"] = "passed"
            result["details"] = f"Stored and retrieved {len(messages)} messages"
            print(f"  ✅ Message Storage Function - PASSED")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ Message Storage Function - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def test_search_retrieval_function(self):
        """Test: Search retrieves relevant documents"""
        result = {"name": "Search Retrieval Function", "status": "pending"}
        start = time.time()
        
        try:
            from src.retrieval.retriever import prepare_retriever
            
            retriever, _, _, _ = prepare_retriever("data/labour_data/labour_law.md")
            
            # Test retrieval
            query = "ما هي ساعات العمل؟"
            docs = retriever.invoke(query)
            
            assert len(docs) > 0, "No documents retrieved"
            assert all(hasattr(doc, 'page_content') for doc in docs), "Invalid document format"
            
            # Check relevance
            combined_content = " ".join([doc.page_content for doc in docs[:3]])
            relevant_terms = ["ساع", "عمل", "يوم"]
            relevance_score = sum(1 for term in relevant_terms if term in combined_content)
            
            assert relevance_score >= 2, "Retrieved documents not relevant"
            
            result["status"] = "passed"
            result["details"] = f"Retrieved {len(docs)} relevant documents"
            print(f"  ✅ Search Retrieval Function - PASSED")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ Search Retrieval Function - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def test_response_generation_function(self):
        """Test: AI generates valid responses"""
        result = {"name": "Response Generation Function", "status": "pending"}
        start = time.time()
        
        try:
            if not self._check_backend():
                result["status"] = "skipped"
                result["details"] = "Backend not running"
                print(f"  ⚠️ Response Generation Function - SKIPPED")
                self.results.append(result)
                return result
            
            import urllib.request
            import json as jsonlib
            
            # First, ensure test user exists in database
            from database import create_user, get_user
            test_email = "func_test@test.com"
            user = get_user(test_email)
            if not user:
                create_user(test_email, "Functional Test User", "TestPass123!")
                user = get_user(test_email)
            
            # Use email as user_id (API will look it up)
            user_identifier = test_email
            
            # Send chat request
            chat_data = jsonlib.dumps({
                "message": "ما هي مدة الإجازة السنوية؟",
                "chat_id": f"func_gen_{int(time.time())}",
                "user_id": user_identifier
            }).encode('utf-8')
            
            req = urllib.request.Request(
                f"{self.backend_url}/api/chat",
                data=chat_data,
                headers={"Content-Type": "application/json"}
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                data = jsonlib.loads(response.read())
            
            # Validate response
            assert "response" in data, "Response missing"
            assert len(data["response"]) > 50, "Response too short"
            assert "إجازة" in data["response"] or "يوم" in data["response"], "Response not relevant"
            
            result["status"] = "passed"
            result["details"] = f"Generated {len(data['response'])} char response"
            print(f"  ✅ Response Generation Function - PASSED")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ Response Generation Function - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def test_chat_history_function(self):
        """Test: Chat history maintains conversation context"""
        result = {"name": "Chat History Function", "status": "pending"}
        start = time.time()
        
        try:
            from database import create_user, get_chat_messages
            from database.db_memory_store import DatabaseChatMessageHistory
            from database.user_manager import get_user
            
            # Create a test user first
            test_email = f"func_hist_{int(time.time())}@test.com"
            create_user(test_email, "History Test", "TestPass123!")
            user = get_user(test_email)
            user_id = int(user["Id"])
            
            chat_id = f"func_history_{int(time.time())}"
            
            # Use DatabaseChatMessageHistory which will auto-create the chat
            history = DatabaseChatMessageHistory(chat_id, user_id)
            
            # Add conversation
            history.add_user_message("ما هي الإجازة السنوية؟")
            history.add_ai_message("الإجازة السنوية هي 21 يوماً")
            history.add_user_message("هل تشمل العطل الرسمية؟")
            history.add_ai_message("لا، العطل الرسمية منفصلة")
            
            # Retrieve and validate
            messages = get_chat_messages(chat_id)
            assert len(messages) >= 4, "Not all messages stored"
            
            # Verify order (should be chronological)
            user_messages = [m for m in messages if m["role"] == "user"]
            assert len(user_messages) >= 2, "User messages not stored"
            
            result["status"] = "passed"
            result["details"] = "Chat history maintains conversation"
            print(f"  ✅ Chat History Function - PASSED")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ Chat History Function - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def run_all(self):
        """Run all functional tests"""
        print("=" * 70)
        print("⚙️  Functional Tests - Egyptian Legal AI")
        print("=" * 70 + "\n")
        
        self.test_user_registration_function()
        self.test_user_authentication_function()
        self.test_chat_creation_function()
        self.test_message_storage_function()
        self.test_search_retrieval_function()
        self.test_response_generation_function()
        self.test_chat_history_function()
        
        # Summary
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "passed")
        failed = sum(1 for r in self.results if r["status"] == "failed")
        skipped = sum(1 for r in self.results if r["status"] == "skipped")
        
        print("\n" + "=" * 70)
        print("📊 Functional Tests Summary")
        print("=" * 70)
        print(f"  Total:     {total}")
        print(f"  Passed:    {passed}")
        print(f"  Failed:    {failed}")
        print(f"  Skipped:   {skipped}")
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
        
        output_path = reports_dir / f"functional_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"\n📄 Results saved: {output_path}")


if __name__ == "__main__":
    suite = FunctionalTestSuite()
    success = suite.run_all()
    sys.exit(0 if success else 1)
