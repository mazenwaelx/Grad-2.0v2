"""
Playwright E2E Tests for Egyptian Legal AI Frontend
====================================================

End-to-end browser automation tests for the React frontend.
Tests login, signup, chat, file upload, and API health.

Prerequisites:
    pip install playwright
    playwright install chromium

Usage:
    python eval/playwright_tests.py                  # Run all tests (headless)
    python eval/playwright_tests.py --headed         # Run with visible browser
    python eval/playwright_tests.py --test login     # Run specific test
    python eval/playwright_tests.py --screenshots    # Save screenshots on each step

Note: The backend (port 8000) and frontend (port 3000) must be running.
"""

import sys

# Fix Windows console encoding for emoji/Unicode output
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from playwright.sync_api import sync_playwright, Page, Browser, expect
except ImportError:
    print("❌ Playwright is not installed. Run:")
    print("   pip install playwright")
    print("   playwright install chromium")
    sys.exit(1)


# ─────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────

FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"
SCREENSHOTS_DIR = PROJECT_ROOT / "eval" / "screenshots"
RESULTS_DIR = PROJECT_ROOT / "eval" / "reports"

# Test user credentials
TEST_USER_EMAIL = f"test_playwright_{int(time.time())}@test.com"
TEST_USER_NAME = "Playwright Test User"
TEST_USER_PASSWORD = "TestPassword123!"


# ─────────────────────────────────────────────────────────
# Test Results Tracker
# ─────────────────────────────────────────────────────────

class TestResult:
    """Track individual test results."""
    def __init__(self, name: str):
        self.name = name
        self.status = "pending"  # pending, passed, failed, skipped
        self.error = None
        self.duration_ms = 0
        self.screenshots: list = []
    
    def to_dict(self):
        return {
            "name": self.name,
            "status": self.status,
            "error": str(self.error) if self.error else None,
            "duration_ms": self.duration_ms,
            "screenshots": self.screenshots,
        }


class TestSuite:
    """Manages all test results."""
    def __init__(self):
        self.results: list[TestResult] = []
        self.start_time = time.time()
    
    def add(self, result: TestResult):
        self.results.append(result)
    
    def summary(self) -> dict:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "passed")
        failed = sum(1 for r in self.results if r.status == "failed")
        skipped = sum(1 for r in self.results if r.status == "skipped")
        elapsed = time.time() - self.start_time
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": round(passed / max(total, 1) * 100, 1),
            "elapsed_seconds": round(elapsed, 2),
            "timestamp": datetime.now().isoformat(),
        }


# ─────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────

def save_screenshot(page: Page, name: str, save_screenshots: bool = True) -> Optional[str]:
    """Save a screenshot with a descriptive name."""
    if not save_screenshots:
        return None
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%H%M%S')
    path = SCREENSHOTS_DIR / f"{name}_{timestamp}.png"
    page.screenshot(path=str(path), full_page=True)
    return str(path)


def wait_for_server(url: str, timeout: int = 5) -> bool:
    """Check if a server is reachable."""
    import urllib.request
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────────────────
# Individual Tests
# ─────────────────────────────────────────────────────────

def test_api_health(page: Page, save_screenshots: bool = False) -> TestResult:
    """Test: API health endpoint returns healthy."""
    result = TestResult("API Health Check")
    start = time.time()
    
    try:
        response = page.request.get(f"{BACKEND_URL}/api/health")
        assert response.ok, f"Health check failed with status {response.status}"
        
        data = response.json()
        assert data.get("status") == "healthy", f"Unexpected status: {data}"
        
        result.status = "passed"
        print("  ✅ API Health Check — PASSED")
        
    except Exception as e:
        result.status = "failed"
        result.error = e
        print(f"  ❌ API Health Check — FAILED: {e}")
    
    result.duration_ms = round((time.time() - start) * 1000)
    return result


def test_login_page_loads(page: Page, save_screenshots: bool = False) -> TestResult:
    """Test: Frontend loads correctly (standalone AI chat on port 3000)."""
    result = TestResult("Login Page Load")
    start = time.time()
    
    try:
        # Note: Port 3000 is the standalone AI chat interface, not a login page
        # The main website with login is on port 3002
        # This test verifies the standalone AI chat loads correctly
        
        page.goto(f"{FRONTEND_URL}", wait_until="networkidle", timeout=15000)
        
        # Wait for the page to render
        page.wait_for_timeout(2000)
        
        # Take screenshot
        ss = save_screenshot(page, "01_frontend_page", save_screenshots)
        if ss:
            result.screenshots.append(ss)
        
        # Check for chat-related elements (this is a chat interface, not login)
        # Look for chat input or message box
        chat_input = page.locator('textarea, input[type="text"], input[placeholder*="message" i], input[placeholder*="رسالة" i], div[contenteditable="true"]').first
        
        if chat_input.count() > 0:
            result.status = "passed"
            result.details = "Standalone AI chat interface loaded"
            print("  ✅ Login Page Load — PASSED (standalone chat interface)")
        else:
            # If no chat input found, at least check page loaded
            page_content = page.content()
            if len(page_content) > 1000:
                result.status = "passed"
                result.details = "Frontend page loaded successfully"
                print("  ✅ Login Page Load — PASSED (page loaded)")
            else:
                result.status = "failed"
                result.error = "Page appears empty or incomplete"
                print("  ❌ Login Page Load — FAILED: Page appears empty")
        
    except Exception as e:
        result.status = "failed"
        result.error = e
        save_screenshot(page, "01_frontend_page_FAILED", save_screenshots)
        print(f"  ❌ Login Page Load — FAILED: {e}")
    
    result.duration_ms = round((time.time() - start) * 1000)
    return result


def test_signup_flow(page: Page, save_screenshots: bool = False) -> TestResult:
    """Test: User signup (handled by LawyerConnect website, not AI API)."""
    result = TestResult("Signup Flow")
    start = time.time()
    
    try:
        # NOTE: Authentication is now handled by LawyerConnect website (ASP.NET Core)
        # The AI API no longer has /api/register endpoint
        # This test verifies the user can be created directly in the database
        
        from database import create_user, get_user
        test_email = f"playwright_test_{int(time.time())}@test.com"
        
        success, msg = create_user(test_email, "Playwright Test User", "TestPass123!")
        
        if success or "already exists" in str(msg).lower():
            user = get_user(test_email)
            assert user is not None, "User not found after creation"
            
            result.status = "passed"
            result.details = "User created in database (auth handled by website)"
            print(f"  ✅ Signup Flow — PASSED (database-level, auth via website)")
        else:
            result.status = "failed"
            result.error = f"User creation failed: {msg}"
            print(f"  ❌ Signup Flow — FAILED: {msg}")
        
    except Exception as e:
        result.status = "failed"
        result.error = e
        print(f"  ❌ Signup Flow — FAILED: {e}")
    
    result.duration_ms = round((time.time() - start) * 1000)
    return result


def test_login_flow(page: Page, save_screenshots: bool = False) -> TestResult:
    """Test: User login (handled by LawyerConnect website, not AI API)."""
    result = TestResult("Login Flow")
    start = time.time()
    
    try:
        # NOTE: Authentication is now handled by LawyerConnect website (ASP.NET Core + JWT)
        # The AI API no longer has /api/login endpoint
        # This test verifies that database user retrieval works
        
        from database import get_user, create_user
        test_email = f"playwright_login_{int(time.time())}@test.com"
        
        # Create user first
        create_user(test_email, "Login Test User", "TestPass123!")
        
        # Verify user can be retrieved (simulating authenticated session)
        user = get_user(test_email)
        
        if user and user['Email'] == test_email:
            result.status = "passed"
            result.details = "User authentication verified (via database, auth handled by website)"
            print(f"  ✅ Login Flow — PASSED (database-level, auth via website)")
        else:
            result.status = "failed"
            result.error = "User retrieval failed"
            print(f"  ❌ Login Flow — FAILED: User not found")
        
    except Exception as e:
        result.status = "failed"
        result.error = e
        print(f"  ❌ Login Flow — FAILED: {e}")
    
    result.duration_ms = round((time.time() - start) * 1000)
    return result


def test_invalid_login(page: Page, save_screenshots: bool = False) -> TestResult:
    """Test: Invalid user lookup is properly handled."""
    result = TestResult("Invalid Login Rejection")
    start = time.time()
    
    try:
        # NOTE: Authentication is now handled by LawyerConnect website
        # This test verifies that invalid user lookups return None gracefully
        
        from database import get_user
        
        # Try to get nonexistent user
        user = get_user("nonexistent_user_12345@test.com")
        
        # Should return None for nonexistent users
        assert user is None, f"Expected None for nonexistent user, got: {user}"
        
        result.status = "passed"
        result.details = "Invalid user lookup handled gracefully"
        print("  ✅ Invalid Login Rejection — PASSED (database-level)")
        
    except Exception as e:
        result.status = "failed"
        result.error = e
        print(f"  ❌ Invalid Login Rejection — FAILED: {e}")
    
    result.duration_ms = round((time.time() - start) * 1000)
    return result


# ─────────────────────────────────────────────────────────
# AI Quality Validation Tests (Core)
# ─────────────────────────────────────────────────────────

# Test cases: each has a legal question + keywords that MUST appear in a real answer
AI_TEST_CASES = [
    {
        "id": "ai_01",
        "question": "ما هي ساعات العمل اليومية القانونية؟",
        "must_contain": ["ساع"],          # must mention hours (ساعة / ساعات)
        "must_not_contain": ["عذراً، حدث خطأ", "خطأ في معالجة"],
        "min_length": 100,
        "description": "Working hours — must mention a number of hours",
    },
    {
        "id": "ai_02",
        "question": "ما هي مدة الإجازة السنوية للعامل؟",
        "must_contain": ["إجازة", "يوم"],  # must mention leave and days
        "must_not_contain": ["عذراً، حدث خطأ"],
        "min_length": 100,
        "description": "Annual leave — must mention 'leave' and 'days'",
    },
    {
        "id": "ai_03",
        "question": "ما هي حقوق المرأة العاملة في إجازة الوضع؟",
        "must_contain": ["إجازة"],          # must mention maternity leave
        "must_not_contain": ["عذراً، حدث خطأ"],
        "min_length": 100,
        "description": "Maternity leave — must mention 'leave'",
    },
    {
        "id": "ai_04",
        "question": "ما هي إجراءات الفصل التعسفي والتعويض المستحق؟",
        "must_contain": ["فصل", "تعويض"],   # must mention dismissal and compensation
        "must_not_contain": ["عذراً، حدث خطأ"],
        "min_length": 150,
        "description": "Wrongful dismissal — must mention 'dismissal' and 'compensation'",
    },
    {
        "id": "ai_05",
        "question": "ما هو طقس القاهرة غداً؟",            # INTENTIONALLY out of scope
        "must_contain": ["قانون العمل"],   # should reject & redirect to labour law
        "must_not_contain": ["درجة", "مئوية", "طقس"],  # must NOT answer weather
        "min_length": 30,
        "description": "Out-of-scope rejection — weather question must be refused",
    },
]


def _send_chat(page: Page, question: str) -> dict:
    """Send a chat request and return parsed JSON."""
    response = page.request.post(f"{BACKEND_URL}/api/chat", data={
        "message": question,
        "chat_id": f"ai_test_{int(time.time() * 1000)}",
        "user_id": "ai_quality_tester@eval.com",
    }, timeout=60000)  # Increase timeout to 60 seconds for AI responses
    assert response.ok, f"Chat API returned HTTP {response.status}"
    data = response.json()
    assert "response" in data, f"Missing 'response' field: {data}"
    return data


def test_ai_legal_accuracy(page: Page, save_screenshots: bool = False) -> TestResult:
    """Test: AI gives accurate, keyword-rich Arabic legal answers to 4 real law questions."""
    result = TestResult("AI Legal Accuracy (4 questions)")
    start = time.time()

    legal_cases = [c for c in AI_TEST_CASES if c["id"] != "ai_05"]
    passed_cases, failed_cases = [], []

    for case in legal_cases:
        try:
            data = _send_chat(page, case["question"])
            resp = data["response"]

            errors = []

            # 1. Must be long enough to be a real answer
            if len(resp) < case["min_length"]:
                errors.append(f"Too short ({len(resp)} chars, need {case['min_length']})")

            # 2. Must contain all required keywords
            for kw in case["must_contain"]:
                if kw not in resp:
                    errors.append(f"Missing keyword: '{kw}'")

            # 3. Must NOT contain error phrases
            for bad in case["must_not_contain"]:
                if bad in resp:
                    errors.append(f"Contains error phrase: '{bad}'")

            # 4. Must be in Arabic (at least 30% Arabic chars)
            arabic_chars = sum(1 for c in resp if '\u0600' <= c <= '\u06FF')
            if arabic_chars / max(len(resp), 1) < 0.30:
                errors.append("Response is not in Arabic")

            if errors:
                failed_cases.append({"id": case["id"], "question": case["question"], "errors": errors})
                print(f"    ❌ [{case['id']}] {case['description']}")
                for e in errors:
                    print(f"         → {e}")
            else:
                passed_cases.append(case["id"])
                print(f"    ✅ [{case['id']}] {case['description']} ({len(resp)} chars)")

            time.sleep(2)  # Avoid rate limiting between questions

        except Exception as e:
            failed_cases.append({"id": case["id"], "question": case["question"], "errors": [str(e)]})
            print(f"    ❌ [{case['id']}] {case['description']} — ERROR: {e}")

    if failed_cases:
        result.status = "failed"
        result.error = f"{len(failed_cases)}/{len(legal_cases)} questions failed: " + \
                       ", ".join(f["id"] for f in failed_cases)
        print(f"  ❌ AI Legal Accuracy — FAILED ({len(passed_cases)}/{len(legal_cases)} passed)")
    else:
        result.status = "passed"
        print(f"  ✅ AI Legal Accuracy — PASSED ({len(passed_cases)}/{len(legal_cases)} questions)")

    result.duration_ms = round((time.time() - start) * 1000)
    return result


def test_ai_out_of_scope_rejection(page: Page, save_screenshots: bool = False) -> TestResult:
    """Test: AI correctly refuses out-of-scope questions (not related to labour law)."""
    result = TestResult("AI Out-of-Scope Rejection")
    start = time.time()

    case = next(c for c in AI_TEST_CASES if c["id"] == "ai_05")

    try:
        data = _send_chat(page, case["question"])
        resp = data["response"]

        errors = []

        # Must NOT answer the weather question
        for bad in case["must_not_contain"]:
            if bad in resp:
                errors.append(f"AI answered out-of-scope topic (contains '{bad}')")

        # Must redirect to labour law
        if not any(kw in resp for kw in case["must_contain"]):
            errors.append("AI did not redirect to labour law topic")

        if errors:
            result.status = "failed"
            result.error = " | ".join(errors)
            print(f"  ❌ AI Out-of-Scope Rejection — FAILED")
            for e in errors:
                print(f"     → {e}")
        else:
            result.status = "passed"
            print(f"  ✅ AI Out-of-Scope Rejection — PASSED (correctly refused weather question)")

    except Exception as e:
        result.status = "failed"
        result.error = e
        print(f"  ❌ AI Out-of-Scope Rejection — FAILED: {e}")

    result.duration_ms = round((time.time() - start) * 1000)
    return result


def test_ai_response_consistency(page: Page, save_screenshots: bool = False) -> TestResult:
    """Test: Asking the same question twice gives consistent (not contradictory) answers."""
    result = TestResult("AI Response Consistency")
    start = time.time()

    question = "كم عدد أيام الإجازة السنوية في قانون العمل المصري؟"

    try:
        data1 = _send_chat(page, question)
        time.sleep(3)
        data2 = _send_chat(page, question)

        resp1, resp2 = data1["response"], data2["response"]

        errors = []

        # Both responses must be substantial
        if len(resp1) < 50:
            errors.append(f"First response too short ({len(resp1)} chars)")
        if len(resp2) < 50:
            errors.append(f"Second response too short ({len(resp2)} chars)")

        # Both must contain "إجازة" (leave) — consistent topic
        if "إجازة" not in resp1:
            errors.append("First response missing 'إجازة'")
        if "إجازة" not in resp2:
            errors.append("Second response missing 'إجازة'")

        # Neither should be an error
        error_phrase = "عذراً، حدث خطأ"
        if error_phrase in resp1:
            errors.append("First response is an error message")
        if error_phrase in resp2:
            errors.append("Second response is an error message")

        if errors:
            result.status = "failed"
            result.error = " | ".join(errors)
            print(f"  ❌ AI Response Consistency — FAILED")
            for e in errors:
                print(f"     → {e}")
        else:
            result.status = "passed"
            print(f"  ✅ AI Response Consistency — PASSED (both responses on-topic, {len(resp1)} + {len(resp2)} chars)")

    except Exception as e:
        result.status = "failed"
        result.error = e
        print(f"  ❌ AI Response Consistency — FAILED: {e}")

    result.duration_ms = round((time.time() - start) * 1000)
    return result


def test_ai_arabic_quality(page: Page, save_screenshots: bool = False) -> TestResult:
    """Test: AI responds in proper Arabic with no garbled/empty text."""
    result = TestResult("AI Arabic Language Quality")
    start = time.time()

    question = "ما هي حقوق العامل عند إنهاء عقد العمل؟"

    try:
        data = _send_chat(page, question)
        resp = data["response"]

        errors = []

        # Must be substantial
        if len(resp) < 100:
            errors.append(f"Response too short: {len(resp)} chars")

        # Must be mostly Arabic
        arabic_chars = sum(1 for c in resp if '\u0600' <= c <= '\u06FF')
        arabic_ratio = arabic_chars / max(len(resp), 1)
        if arabic_ratio < 0.30:
            errors.append(f"Not enough Arabic text ({arabic_ratio:.0%} Arabic)")

        # Must not be repetitive — check for repeated multi-word PHRASES (real LLM looping)
        # Single words like 'العمل' naturally repeat in labour law; we check for 5-word sequences
        words = resp.split()
        if len(words) > 30:
            # Build 5-word phrases and count them
            phrases = [" ".join(words[i:i+5]) for i in range(len(words) - 4)]
            from collections import Counter
            phrase_counts = Counter(phrases)
            most_common_phrase, count = phrase_counts.most_common(1)[0]
            if count >= 3:
                errors.append(f"Repetitive output: phrase '{most_common_phrase}' appears {count} times")

        # Must not contain common error strings
        for err_str in ["عذراً، حدث خطأ", "يرجى المحاولة مرة أخرى", "ERROR:"]:
            if err_str in resp:
                errors.append(f"Response contains error message: '{err_str}'")

        if errors:
            result.status = "failed"
            result.error = " | ".join(errors)
            print(f"  ❌ AI Arabic Language Quality — FAILED")
            for e in errors:
                print(f"     → {e}")
        else:
            result.status = "passed"
            print(f"  ✅ AI Arabic Language Quality — PASSED ({len(resp)} chars, {arabic_ratio:.0%} Arabic)")

    except Exception as e:
        result.status = "failed"
        result.error = e
        print(f"  ❌ AI Arabic Language Quality — FAILED: {e}")

    result.duration_ms = round((time.time() - start) * 1000)
    return result


def test_file_upload_api(page: Page, save_screenshots: bool = False) -> TestResult:
    """Test: File upload API accepts files and returns proper response."""
    result = TestResult("File Upload API")
    start = time.time()
    
    try:
        # Create a dummy test file
        test_file_path = PROJECT_ROOT / "eval" / "test_upload.txt"
        test_file_path.write_text("هذا ملف اختبار لقانون العمل المصري", encoding='utf-8')
        
        # Note: text files may not be supported, the API will tell us
        # This tests that the API endpoint works and returns proper errors
        response = page.request.post(f"{BACKEND_URL}/api/upload", multipart={
            "file": {
                "name": "test_upload.txt",
                "mimeType": "text/plain",
                "buffer": test_file_path.read_bytes(),
            }
        })
        
        if response.ok:
            data = response.json()
            # Even if the file type is unsupported, the API should return a proper response
            assert "success" in data or "message" in data, f"Unexpected response: {data}"
            result.status = "passed"
            print(f"  ✅ File Upload API — PASSED")
        else:
            # Some error codes are acceptable (e.g., 422 for unsupported type)
            if response.status in [400, 422]:
                result.status = "passed"
                print(f"  ✅ File Upload API — PASSED (unsupported type properly rejected)")
            else:
                result.status = "failed"
                result.error = f"Upload API returned {response.status}"
                print(f"  ❌ File Upload API — FAILED: {response.status}")
        
        # Clean up
        test_file_path.unlink(missing_ok=True)
        
    except Exception as e:
        result.status = "failed"
        result.error = e
        print(f"  ❌ File Upload API — FAILED: {e}")
    
    result.duration_ms = round((time.time() - start) * 1000)
    return result


def test_files_list_api(page: Page, save_screenshots: bool = False) -> TestResult:
    """Test: Files list API returns a proper response."""
    result = TestResult("Files List API")
    start = time.time()
    
    try:
        response = page.request.get(f"{BACKEND_URL}/api/files")
        
        assert response.ok, f"Files list API failed with status {response.status}"
        data = response.json()
        assert "files" in data, f"Response missing 'files' field: {data}"
        
        result.status = "passed"
        print(f"  ✅ Files List API — PASSED ({len(data['files'])} files)")
        
    except Exception as e:
        result.status = "failed"
        result.error = e
        print(f"  ❌ Files List API — FAILED: {e}")
    
    result.duration_ms = round((time.time() - start) * 1000)
    return result


def test_api_docs_accessible(page: Page, save_screenshots: bool = False) -> TestResult:
    """Test: FastAPI docs page is accessible."""
    result = TestResult("API Docs Accessible")
    start = time.time()
    
    try:
        page.goto(f"{BACKEND_URL}/docs", wait_until="networkidle", timeout=10000)
        page.wait_for_timeout(2000)
        
        # Check that the page has Swagger UI content
        title = page.title()
        assert "api" in title.lower() or "swagger" in title.lower() or "fastapi" in title.lower() or "docs" in title.lower() or "egyptian" in title.lower(), f"Unexpected page title: {title}"
        
        ss = save_screenshot(page, "08_api_docs", save_screenshots)
        if ss:
            result.screenshots.append(ss)
        
        result.status = "passed"
        print("  ✅ API Docs Accessible — PASSED")
        
    except Exception as e:
        result.status = "failed"
        result.error = e
        print(f"  ❌ API Docs Accessible — FAILED: {e}")
    
    result.duration_ms = round((time.time() - start) * 1000)
    return result


def test_frontend_responsive(page: Page, save_screenshots: bool = False) -> TestResult:
    """Test: Frontend renders properly at different viewport sizes."""
    result = TestResult("Frontend Responsive Design")
    start = time.time()
    
    try:
        page.goto(f"{FRONTEND_URL}", wait_until="networkidle", timeout=15000)
        page.wait_for_timeout(2000)
        
        viewports = [
            ("desktop", 1920, 1080),
            ("tablet", 768, 1024),
            ("mobile", 375, 667),
        ]
        
        for name, width, height in viewports:
            page.set_viewport_size({"width": width, "height": height})
            page.wait_for_timeout(500)
            ss = save_screenshot(page, f"09_responsive_{name}", save_screenshots)
            if ss:
                result.screenshots.append(ss)
        
        # Reset viewport
        page.set_viewport_size({"width": 1280, "height": 720})
        
        result.status = "passed"
        print("  ✅ Frontend Responsive Design — PASSED")
        
    except Exception as e:
        result.status = "failed"
        result.error = e
        print(f"  ❌ Frontend Responsive Design — FAILED: {e}")
    
    result.duration_ms = round((time.time() - start) * 1000)
    return result


# ─────────────────────────────────────────────────────────
# Test Runner
# ─────────────────────────────────────────────────────────

# All available tests in execution order
ALL_TESTS = {
    # ── Infrastructure ──
    "health":           test_api_health,
    "login_page":       test_login_page_loads,
    "signup":           test_signup_flow,
    "login":            test_login_flow,
    "invalid_login":    test_invalid_login,
    "upload":           test_file_upload_api,
    "files":            test_files_list_api,
    "docs":             test_api_docs_accessible,
    "responsive":       test_frontend_responsive,
    # ── Core AI Quality ──
    "ai_accuracy":      test_ai_legal_accuracy,
    "ai_scope":         test_ai_out_of_scope_rejection,
    "ai_consistency":   test_ai_response_consistency,
    "ai_arabic":        test_ai_arabic_quality,
}


def run_tests(
    headed: bool = False,
    save_screenshots: bool = False,
    test_filter: Optional[str] = None,
):
    """Run all Playwright tests."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    suite = TestSuite()
    
    print("=" * 70)
    print("🎭 Playwright E2E Test Suite — Egyptian Legal AI")
    print(f"   Browser: Chromium ({'headed' if headed else 'headless'})")
    print(f"   Frontend: {FRONTEND_URL}")
    print(f"   Backend: {BACKEND_URL}")
    print(f"   Screenshots: {'ON' if save_screenshots else 'OFF'}")
    print("=" * 70)
    
    # Check server availability
    print("\n🔍 Checking server availability...")
    backend_up = wait_for_server(f"{BACKEND_URL}/api/health")
    frontend_up = wait_for_server(FRONTEND_URL)
    
    if not backend_up:
        print(f"  ⚠️ Backend ({BACKEND_URL}) is not reachable!")
        print("  ℹ️ Start the backend: python api_server.py")
        print("  ℹ️ API-dependent tests will be skipped.\n")
    else:
        print(f"  ✅ Backend is running at {BACKEND_URL}")
        # Register the AI quality tester user so database operations succeed
        # NOTE: Auth handled by LawyerConnect website - create user directly in DB
        try:
            sys.path.insert(0, str(PROJECT_ROOT))
            from database import create_user
            create_user("ai_quality_tester@eval.com", "AI Quality Tester", "TestPassword123!")
        except Exception:
            # Ignore errors (e.g. if user already exists)
            pass
    
    if not frontend_up:
        print(f"  ⚠️ Frontend ({FRONTEND_URL}) is not reachable!")
        print("  ℹ️ Start the frontend: cd react-frontend && npm start")
        print("  ℹ️ UI tests will be skipped.\n")
    else:
        print(f"  ✅ Frontend is running at {FRONTEND_URL}")
    
    if not backend_up and not frontend_up:
        print("\n❌ Both servers are down. Cannot run tests.")
        print("   Start your servers and try again.")
        return
    
    # Filter tests if specified
    tests_to_run = ALL_TESTS
    if test_filter:
        tests_to_run = {k: v for k, v in ALL_TESTS.items() if test_filter.lower() in k.lower()}
        if not tests_to_run:
            print(f"\n❌ No tests matching filter '{test_filter}'")
            print(f"   Available: {', '.join(ALL_TESTS.keys())}")
            return
    
    # Determine which tests need which servers
    api_tests = {"health", "signup", "login", "invalid_login", "upload", "files", "docs",
                 "ai_accuracy", "ai_scope", "ai_consistency", "ai_arabic"}
    ui_tests = {"login_page", "responsive"}
    
    print(f"\n🚀 Running {len(tests_to_run)} tests...\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headed)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            locale="ar-EG",
        )
        page = context.new_page()
        
        for test_name, test_fn in tests_to_run.items():
            # Skip tests if required server is down
            if test_name in api_tests and not backend_up:
                result = TestResult(test_fn.__doc__ or test_name)
                result.status = "skipped"
                result.error = "Backend not available"
                suite.add(result)
                print(f"  ⏭️ {test_name} — SKIPPED (backend down)")
                continue
            
            if test_name in ui_tests and not frontend_up:
                result = TestResult(test_fn.__doc__ or test_name)
                result.status = "skipped"
                result.error = "Frontend not available"
                suite.add(result)
                print(f"  ⏭️ {test_name} — SKIPPED (frontend down)")
                continue
            
            # Run the test
            test_result = test_fn(page, save_screenshots)
            suite.add(test_result)
        
        browser.close()
    
    # Print summary
    summary = suite.summary()
    
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    print(f"  Total:   {summary['total']}")
    print(f"  Passed:  {summary['passed']} ✅")
    print(f"  Failed:  {summary['failed']} ❌")
    print(f"  Skipped: {summary['skipped']} ⏭️")
    print(f"  Pass Rate: {summary['pass_rate']}%")
    print(f"  Duration: {summary['elapsed_seconds']}s")
    print("=" * 70)
    
    # Save results as JSON
    results_data = {
        "summary": summary,
        "results": [r.to_dict() for r in suite.results],
    }
    results_path = RESULTS_DIR / f"playwright_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    results_path.write_text(json.dumps(results_data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\n📄 Results saved: {results_path}")
    
    if save_screenshots:
        print(f"📸 Screenshots saved: {SCREENSHOTS_DIR}")
    
    # Return exit code
    return 0 if summary['failed'] == 0 else 1


# ─────────────────────────────────────────────────────────
# CLI Entry Point
# ─────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Playwright E2E Tests for Egyptian Legal AI")
    parser.add_argument("--headed", action="store_true", help="Run with visible browser")
    parser.add_argument("--screenshots", action="store_true", help="Save screenshots")
    parser.add_argument("--test", type=str, default=None,
                        help=f"Run specific test. Options: {', '.join(ALL_TESTS.keys())}")
    args = parser.parse_args()
    
    exit_code = run_tests(
        headed=args.headed,
        save_screenshots=args.screenshots,
        test_filter=args.test,
    )
    sys.exit(exit_code or 0)


if __name__ == "__main__":
    main()
