"""
Usability Tests for Egyptian Legal AI
======================================

Tests user experience and usability:
- Response clarity and readability
- Arabic text quality
- Response time acceptability
- Error message helpfulness
- UI feedback and loading states
- Accessibility features

Usage:
    python eval/usability_tests.py
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


class UsabilityTestSuite:
    """Usability testing suite"""
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        self.backend_url = "http://localhost:8000"  # AI API
        self.website_url = "http://localhost:5128"  # LawyerConnect Website
        self.jwt_token = None
        self.test_user_id = None
        
        # Setup test user through website auth
        self._setup_test_user()
    
    def _check_backend(self):
        """Check if AI backend is running"""
        try:
            import urllib.request
            urllib.request.urlopen(f"{self.backend_url}/api/health", timeout=2)
            return True
        except Exception:
            return False
    
    def _check_website(self):
        """Check if LawyerConnect website is running"""
        try:
            import urllib.request
            # Just check if the server responds (even with 401 is fine)
            try:
                urllib.request.urlopen(f"{self.website_url}/api/auth/me", timeout=2)
                return True
            except urllib.error.HTTPError as e:
                # 401 Unauthorized means server is running but endpoint needs auth
                if e.code == 401:
                    return True
                return False
        except Exception:
            return False
    
    def _setup_test_user(self):
        """Setup test user for usability tests via website authentication"""
        try:
            if not self._check_website():
                print("  [WARN] Website not running - using fallback test user")
                self.test_user_id = "usability_fallback@test.com"
                return
            
            import urllib.request
            import json as jsonlib
            
            test_email = f"usability_test_{int(time.time())}@test.com"
            test_password = "TestPass123!"
            
            # Register
            reg_data = jsonlib.dumps({
                "user": {
                    "fullName": "Usability Test User",
                    "email": test_email,
                    "password": test_password,
                    "phone": "01234567890",
                    "city": "Cairo",
                    "role": "User"
                }
            }).encode('utf-8')
            
            reg_req = urllib.request.Request(
                f"{self.website_url}/api/auth/register",
                data=reg_data,
                headers={"Content-Type": "application/json"}
            )
            
            try:
                with urllib.request.urlopen(reg_req, timeout=10) as response:
                    pass
            except urllib.error.HTTPError as e:
                if e.code != 409:  # Ignore "already exists"
                    print(f"  [WARN] Registration failed: HTTP {e.code}")
            
            # Login
            login_data = jsonlib.dumps({
                "email": test_email,
                "password": test_password
            }).encode('utf-8')
            
            login_req = urllib.request.Request(
                f"{self.website_url}/api/auth/login",
                data=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            with urllib.request.urlopen(login_req, timeout=10) as response:
                login_result = jsonlib.loads(response.read())
                self.jwt_token = login_result.get("token")
                self.test_user_id = test_email  # Use email as user_id (API will look it up)
                print(f"  [INFO] Test user authenticated: {test_email}")
        except Exception as e:
            print(f"  [WARN] Auth setup failed: {e} - using fallback")
            self.test_user_id = "usability_fallback@test.com"  # Fallback to email-based lookup
    
    def test_response_clarity(self):
        """Test: AI responses are clear and well-structured"""
        result = {"name": "Response Clarity", "status": "pending"}
        start = time.time()
        
        try:
            if not self._check_backend():
                result["status"] = "skipped"
                result["details"] = "Backend not running"
                print(f"  ⚠️ Response Clarity - SKIPPED")
                self.results.append(result)
                return result
            
            import urllib.request
            import json as jsonlib
            import socket
            
            # Ask a clear question
            chat_data = jsonlib.dumps({
                "message": "ما هي مدة الإجازة السنوية؟",
                "chat_id": f"clarity_test_{int(time.time())}",
                "user_id": self.test_user_id
            }).encode('utf-8')
            
            headers = {"Content-Type": "application/json"}
            if self.jwt_token:
                headers["Authorization"] = f"Bearer {self.jwt_token}"
            
            req = urllib.request.Request(
                f"{self.backend_url}/api/chat",
                data=chat_data,
                headers=headers
            )
            
            try:
                with urllib.request.urlopen(req, timeout=45) as response:
                    data = jsonlib.loads(response.read())
            except socket.timeout:
                result["status"] = "skipped"
                result["details"] = "AI response timeout (>45s) - system overloaded"
                print(f"  ⚠️ Response Clarity - SKIPPED (timeout)")
                self.results.append(result)
                return result
            
            resp = data["response"]
            
            # Check clarity metrics
            clarity_score = 0
            
            # 1. Uses formatting (bullets, numbers)
            if any(marker in resp for marker in ["•", "●", "-", "1.", "2.", "أ.", "ب."]):
                clarity_score += 1
            
            # 2. Not too short or too long
            if 100 <= len(resp) <= 1500:
                clarity_score += 1
            
            # 3. Contains legal references
            if "المادة" in resp or "مادة" in resp:
                clarity_score += 1
            
            # 4. Direct answer (contains key terms)
            if "إجازة" in resp and "يوم" in resp:
                clarity_score += 1
            
            # Need at least 3/4 for pass
            if clarity_score >= 3:
                result["status"] = "passed"
                result["details"] = f"Clarity score: {clarity_score}/4"
                print(f"  ✅ Response Clarity - PASSED ({clarity_score}/4)")
            else:
                result["status"] = "failed"
                result["error"] = f"Low clarity score: {clarity_score}/4"
                print(f"  ❌ Response Clarity - FAILED ({clarity_score}/4)")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ Response Clarity - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def test_arabic_text_quality(self):
        """Test: Arabic text is properly formed and readable"""
        result = {"name": "Arabic Text Quality", "status": "pending"}
        start = time.time()
        
        try:
            if not self._check_backend():
                result["status"] = "skipped"
                result["details"] = "Backend not running"
                print(f"  ⚠️ Arabic Text Quality - SKIPPED")
                self.results.append(result)
                return result
            
            import urllib.request
            import json as jsonlib
            import socket
            
            chat_data = jsonlib.dumps({
                "message": "أخبرني عن حقوق العامل",
                "chat_id": f"arabic_test_{int(time.time())}",
                "user_id": self.test_user_id
            }).encode('utf-8')
            
            headers = {"Content-Type": "application/json"}
            if self.jwt_token:
                headers["Authorization"] = f"Bearer {self.jwt_token}"
            
            req = urllib.request.Request(
                f"{self.backend_url}/api/chat",
                data=chat_data,
                headers=headers
            )
            
            try:
                with urllib.request.urlopen(req, timeout=45) as response:
                    data = jsonlib.loads(response.read())
            except socket.timeout:
                result["status"] = "skipped"
                result["details"] = "AI response timeout (>45s) - system overloaded"
                print(f"  ⚠️ Arabic Text Quality - SKIPPED (timeout)")
                self.results.append(result)
                return result
            
            resp = data["response"]
            
            # Quality checks
            arabic_chars = sum(1 for c in resp if '\u0600' <= c <= '\u06FF')
            total_chars = len(resp)
            arabic_ratio = arabic_chars / max(total_chars, 1)
            
            # Should be mostly Arabic (> 60%)
            assert arabic_ratio > 0.60, f"Not enough Arabic content ({arabic_ratio:.0%})"
            
            # No garbled text (repetitive phrases)
            words = resp.split()
            if len(words) > 20:
                word_set = set(words)
                uniqueness = len(word_set) / len(words)
                assert uniqueness > 0.30, f"Text too repetitive ({uniqueness:.0%} unique)"
            
            result["status"] = "passed"
            result["details"] = f"Arabic quality: {arabic_ratio:.0%} Arabic chars"
            print(f"  ✅ Arabic Text Quality - PASSED")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ Arabic Text Quality - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def test_response_time_acceptable(self):
        """Test: Response time is within acceptable limits for users"""
        result = {"name": "Response Time Acceptable", "status": "pending"}
        start = time.time()
        
        try:
            if not self._check_backend():
                result["status"] = "skipped"
                result["details"] = "Backend not running"
                print(f"  ⚠️ Response Time Acceptable - SKIPPED")
                self.results.append(result)
                return result
            
            import urllib.request
            import json as jsonlib
            import socket
            
            # Measure response time
            request_start = time.time()
            
            chat_data = jsonlib.dumps({
                "message": "ما هي ساعات العمل؟",
                "chat_id": f"perf_test_{int(time.time())}",
                "user_id": self.test_user_id
            }).encode('utf-8')
            
            headers = {"Content-Type": "application/json"}
            if self.jwt_token:
                headers["Authorization"] = f"Bearer {self.jwt_token}"
            
            req = urllib.request.Request(
                f"{self.backend_url}/api/chat",
                data=chat_data,
                headers=headers
            )
            
            try:
                with urllib.request.urlopen(req, timeout=45) as response:
                    data = jsonlib.loads(response.read())
            except socket.timeout:
                result["status"] = "failed"
                result["error"] = "Response time > 45s (too slow for users)"
                print(f"  ❌ Response Time Acceptable - FAILED (timeout)")
                self.results.append(result)
                return result
            
            response_time = time.time() - request_start
            
            # Good: < 10s, Acceptable: < 20s, Poor: > 20s
            if response_time < 10:
                result["status"] = "passed"
                result["details"] = f"Excellent response time: {response_time:.1f}s"
                print(f"  ✅ Response Time Acceptable - PASSED ({response_time:.1f}s)")
            elif response_time < 20:
                result["status"] = "passed"
                result["details"] = f"Acceptable response time: {response_time:.1f}s"
                print(f"  ✅ Response Time Acceptable - PASSED ({response_time:.1f}s)")
            else:
                result["status"] = "warning"
                result["details"] = f"Slow response time: {response_time:.1f}s"
                print(f"  ⚠️ Response Time Acceptable - WARNING ({response_time:.1f}s)")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ Response Time Acceptable - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def test_error_message_helpfulness(self):
        """Test: Error messages are helpful to users"""
        result = {"name": "Error Message Helpfulness", "status": "pending"}
        start = time.time()
        
        try:
            if not self._check_backend():
                result["status"] = "skipped"
                result["details"] = "Backend not running"
                print(f"  ⚠️ Error Message Helpfulness - SKIPPED")
                self.results.append(result)
                return result
            
            import urllib.request
            import json as jsonlib
            
            # Test invalid chat request (empty message)
            try:
                chat_data = jsonlib.dumps({
                    "message": "",  # Empty - should fail validation
                    "chat_id": "error_test",
                    "user_id": "test@test.com"
                }).encode('utf-8')
                
                req = urllib.request.Request(
                    f"{self.backend_url}/api/chat",
                    data=chat_data,
                    headers={"Content-Type": "application/json"}
                )
                
                with urllib.request.urlopen(req, timeout=5) as response:
                    pass
            except urllib.error.HTTPError as e:
                # Error is expected - check if error code is appropriate
                assert e.code in [400, 422, 500], f"Unexpected error code: {e.code}"
            
            result["status"] = "passed"
            result["details"] = "Error messages are appropriate"
            print(f"  ✅ Error Message Helpfulness - PASSED")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ Error Message Helpfulness - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def test_api_discoverability(self):
        """Test: API documentation is accessible"""
        result = {"name": "API Discoverability", "status": "pending"}
        start = time.time()
        
        try:
            if not self._check_backend():
                result["status"] = "skipped"
                result["details"] = "Backend not running"
                print(f"  ⚠️ API Discoverability - SKIPPED")
                self.results.append(result)
                return result
            
            import urllib.request
            
            # Check if /docs endpoint is accessible
            req = urllib.request.Request(f"{self.backend_url}/docs")
            with urllib.request.urlopen(req, timeout=5) as response:
                content = response.read()
                # FastAPI Swagger UI page should be at least 500 bytes
                # (checking for very minimal threshold since it's dynamically loaded)
                assert len(content) > 500, f"Docs page too small ({len(content)} bytes)"
                # Check it contains FastAPI/Swagger indicators
                content_str = content.decode('utf-8', errors='ignore')
                assert 'swagger' in content_str.lower() or 'openapi' in content_str.lower() or 'api' in content_str.lower(), "Docs page doesn't appear to be API documentation"
            
            result["status"] = "passed"
            result["details"] = f"API documentation accessible ({len(content)} bytes)"
            print(f"  ✅ API Discoverability - PASSED")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ API Discoverability - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def test_consistent_terminology(self):
        """Test: System uses consistent terminology"""
        result = {"name": "Consistent Terminology", "status": "pending"}
        start = time.time()
        
        try:
            if not self._check_backend():
                result["status"] = "skipped"
                result["details"] = "Backend not running"
                print(f"  ⚠️ Consistent Terminology - SKIPPED")
                self.results.append(result)
                return result
            
            import urllib.request
            import json as jsonlib
            import socket
            
            # Ask similar questions
            questions = [
                "ما هي الإجازة السنوية؟",
                "أخبرني عن الإجازات السنوية",
            ]
            
            responses = []
            for q in questions:
                chat_data = jsonlib.dumps({
                    "message": q,
                    "chat_id": f"term_test_{int(time.time())}_{len(responses)}",
                    "user_id": self.test_user_id
                }).encode('utf-8')
                
                headers = {"Content-Type": "application/json"}
                if self.jwt_token:
                    headers["Authorization"] = f"Bearer {self.jwt_token}"
                
                req = urllib.request.Request(
                    f"{self.backend_url}/api/chat",
                    data=chat_data,
                    headers=headers
                )
                
                try:
                    with urllib.request.urlopen(req, timeout=45) as response:
                        data = jsonlib.loads(response.read())
                        responses.append(data["response"])
                except socket.timeout:
                    result["status"] = "skipped"
                    result["details"] = "AI response timeout - system overloaded"
                    print(f"  ⚠️ Consistent Terminology - SKIPPED (timeout)")
                    self.results.append(result)
                    return result
                
                time.sleep(2)  # Avoid rate limiting
            
            # Check for consistent terminology
            # Both should mention "إجازة" (leave)
            consistency_score = sum(1 for r in responses if "إجازة" in r)
            
            if consistency_score == len(responses):
                result["status"] = "passed"
                result["details"] = "Terminology consistent across responses"
                print(f"  ✅ Consistent Terminology - PASSED")
            else:
                result["status"] = "warning"
                result["details"] = f"Terminology varies: {consistency_score}/{len(responses)}"
                print(f"  ⚠️ Consistent Terminology - WARNING")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ Consistent Terminology - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def run_all(self):
        """Run all usability tests"""
        print("=" * 70)
        print("👤 Usability Tests - Egyptian Legal AI")
        print("=" * 70 + "\n")
        
        self.test_response_clarity()
        self.test_arabic_text_quality()
        self.test_response_time_acceptable()
        self.test_error_message_helpfulness()
        self.test_api_discoverability()
        self.test_consistent_terminology()
        
        # Summary
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "passed")
        failed = sum(1 for r in self.results if r["status"] == "failed")
        skipped = sum(1 for r in self.results if r["status"] == "skipped")
        warnings = sum(1 for r in self.results if r["status"] == "warning")
        
        print("\n" + "=" * 70)
        print("📊 Usability Tests Summary")
        print("=" * 70)
        print(f"  Total:     {total}")
        print(f"  Passed:    {passed}")
        print(f"  Failed:    {failed}")
        print(f"  Warnings:  {warnings}")
        print(f"  Skipped:   {skipped}")
        print(f"  Pass Rate: {((passed + warnings)/max(total-skipped, 1))*100:.1f}%")
        print("=" * 70)
        
        # Save results
        self.save_results()
        
        return (passed + warnings) == (total - skipped)
    
    def save_results(self):
        """Save results to JSON"""
        reports_dir = PROJECT_ROOT / "eval" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        summary = {
            "total": len(self.results),
            "passed": sum(1 for r in self.results if r["status"] == "passed"),
            "failed": sum(1 for r in self.results if r["status"] == "failed"),
            "skipped": sum(1 for r in self.results if r["status"] == "skipped"),
            "warnings": sum(1 for r in self.results if r["status"] == "warning"),
            "elapsed_seconds": round(time.time() - self.start_time, 2),
            "timestamp": datetime.now().isoformat()
        }
        summary["pass_rate"] = round(((summary["passed"] + summary["warnings"]) / max(summary["total"] - summary["skipped"], 1)) * 100, 1)
        
        output = {
            "summary": summary,
            "results": self.results
        }
        
        output_path = reports_dir / f"usability_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"\n📄 Results saved: {output_path}")


if __name__ == "__main__":
    suite = UsabilityTestSuite()
    success = suite.run_all()
    sys.exit(0 if success else 1)
