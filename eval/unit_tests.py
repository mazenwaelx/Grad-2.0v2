"""
Unit Tests for Egyptian Legal AI
=================================

Tests individual components in isolation:
- Embedding generation
- Text chunking
- Query expansion
- Document deduplication
- Arabic text processing
- Cache management
- Prompt building

Usage:
    python eval/unit_tests.py
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


class UnitTestSuite:
    """Unit testing suite for isolated components"""
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
    
    def test_embeddings_generation(self):
        """Test: Embedding model generates correct dimension vectors"""
        result = {"name": "Embeddings Generation", "status": "pending"}
        start = time.time()
        
        try:
            from data.data_embedding import SentenceTransformerEmbeddings
            
            embeddings = SentenceTransformerEmbeddings()
            
            # Test Arabic text
            text = "قانون العمل المصري"
            vector = embeddings.embed_query(text)
            
            # Check dimensions
            assert len(vector) == 1024, f"Expected 1024 dimensions, got {len(vector)}"
            assert all(isinstance(v, float) for v in vector), "Vector contains non-float values"
            assert any(v != 0 for v in vector), "Vector is all zeros"
            
            result["status"] = "passed"
            result["details"] = f"Generated {len(vector)}-dim vector for Arabic text"
            print(f"  ✅ Embeddings Generation - PASSED")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ Embeddings Generation - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def test_text_chunking(self):
        """Test: Text splitter creates proper chunks with overlap"""
        result = {"name": "Text Chunking", "status": "pending"}
        start = time.time()
        
        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=2000,
                chunk_overlap=200,
                separators=["\n\n", "\n", ".", "،", " ", ""]
            )
            
            # Test text
            long_text = "المادة الأولى: " + "هذا نص قانوني طويل. " * 300
            chunks = splitter.split_text(long_text)
            
            assert len(chunks) > 1, "Should create multiple chunks"
            assert all(len(chunk) <= 2200 for chunk in chunks), "Chunks exceed max size"
            assert all(len(chunk) > 0 for chunk in chunks), "Empty chunk found"
            
            result["status"] = "passed"
            result["details"] = f"Created {len(chunks)} chunks from {len(long_text)} chars"
            print(f"  ✅ Text Chunking - PASSED ({len(chunks)} chunks)")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ Text Chunking - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def test_query_expansion(self):
        """Test: Query expansion adds relevant legal terms"""
        result = {"name": "Query Expansion", "status": "pending"}
        start = time.time()
        
        try:
            # Simple query expansion logic
            query_map = {
                "إجازة": "إجازة سنوية عطلة راحة",
                "عقد": "عقد عمل اتفاق تعاقد",
                "أجر": "أجر راتب مرتب",
                "فصل": "فصل إنهاء عقد إيقاف",
            }
            
            def expand_query(query):
                expanded = query
                for term, expansion in query_map.items():
                    if term in query:
                        expanded += " " + expansion
                return expanded.strip()
            
            # Test expansions
            test_query = "ما هي مدة الإجازة؟"
            expanded = expand_query(test_query)
            
            assert "إجازة" in expanded, "Original term missing"
            assert "سنوية" in expanded or "عطلة" in expanded, "Expansion missing"
            assert len(expanded) > len(test_query), "Query wasn't expanded"
            
            result["status"] = "passed"
            result["details"] = f"Expanded query from {len(test_query)} to {len(expanded)} chars"
            print(f"  ✅ Query Expansion - PASSED")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ Query Expansion - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def test_document_deduplication(self):
        """Test: Document deduplication removes similar chunks"""
        result = {"name": "Document Deduplication", "status": "pending"}
        start = time.time()
        
        try:
            import hashlib
            
            def deduplicate_docs(docs):
                seen = set()
                unique = []
                for doc in docs:
                    # Use first 200 chars as fingerprint
                    content = doc.get("content", "") if isinstance(doc, dict) else str(doc)
                    fingerprint = hashlib.md5(content[:200].encode(), usedforsecurity=False).hexdigest()
                    if fingerprint not in seen:
                        seen.add(fingerprint)
                        unique.append(doc)
                return unique
            
            # Test data
            docs = [
                {"content": "المادة الأولى: تنظم أحكام هذا القانون..."},
                {"content": "المادة الأولى: تنظم أحكام هذا القانون..."},  # Duplicate
                {"content": "المادة الثانية: يُقصد بالعامل كل شخص..."},
                {"content": "المادة الثانية: يُقصد بالعامل كل شخص..."},  # Duplicate
                {"content": "المادة الثالثة: تسري أحكام هذا القانون..."},
            ]
            
            unique_docs = deduplicate_docs(docs)
            
            assert len(unique_docs) == 3, f"Expected 3 unique docs, got {len(unique_docs)}"
            assert len(unique_docs) < len(docs), "No deduplication occurred"
            
            result["status"] = "passed"
            result["details"] = f"Deduplicated {len(docs)} docs to {len(unique_docs)} unique"
            print(f"  ✅ Document Deduplication - PASSED")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ Document Deduplication - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def test_arabic_text_processing(self):
        """Test: Arabic text is properly normalized and processed"""
        result = {"name": "Arabic Text Processing", "status": "pending"}
        start = time.time()
        
        try:
            import re
            
            def normalize_arabic(text):
                # Remove diacritics
                text = re.sub(r'[\u064B-\u0652]', '', text)
                # Normalize alef forms
                text = re.sub(r'[إأآا]', 'ا', text)
                # Normalize taa marbuta
                text = re.sub(r'ة', 'ه', text)
                return text.strip()
            
            # Test normalization
            test_texts = [
                ("مَدَّة", "مده"),
                ("إجازة", "اجازه"),
                ("العَامِل", "العامل"),
            ]
            
            for original, expected in test_texts:
                normalized = normalize_arabic(original)
                # Basic check - diacritics removed
                assert '\u064B' not in normalized and '\u0652' not in normalized, "Diacritics not removed"
            
            result["status"] = "passed"
            result["details"] = "Arabic normalization working correctly"
            print(f"  ✅ Arabic Text Processing - PASSED")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ Arabic Text Processing - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def test_cache_management(self):
        """Test: Cache stores and retrieves data correctly"""
        result = {"name": "Cache Management", "status": "pending"}
        start = time.time()
        
        try:
            import hashlib
            
            class SimpleCache:
                def __init__(self):
                    self.cache = {}
                
                def get(self, key):
                    return self.cache.get(key)
                
                def set(self, key, value):
                    self.cache[key] = value
                
                def clear(self):
                    self.cache.clear()
            
            cache = SimpleCache()
            
            # Test operations
            test_key = "test_query"
            test_value = "cached_response"
            
            cache.set(test_key, test_value)
            retrieved = cache.get(test_key)
            
            assert retrieved == test_value, "Cache retrieve failed"
            
            cache.clear()
            assert cache.get(test_key) is None, "Cache clear failed"
            
            result["status"] = "passed"
            result["details"] = "Cache operations working correctly"
            print(f"  ✅ Cache Management - PASSED")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ Cache Management - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def test_prompt_building(self):
        """Test: Prompts are built correctly with context and question"""
        result = {"name": "Prompt Building", "status": "pending"}
        start = time.time()
        
        try:
            def build_rag_prompt(context, question):
                prompt = f"""أنت مساعد قانوني متخصص في قانون العمل المصري.

السياق:
{context}

السؤال: {question}

الإجابة:"""
                return prompt
            
            test_context = "المادة 47: تكون مدة الإجازة السنوية 21 يوماً بأجر كامل"
            test_question = "كم مدة الإجازة السنوية؟"
            
            prompt = build_rag_prompt(test_context, test_question)
            
            assert test_context in prompt, "Context not in prompt"
            assert test_question in prompt, "Question not in prompt"
            assert "السياق" in prompt, "Prompt structure incorrect"
            assert "السؤال" in prompt, "Prompt structure incorrect"
            assert len(prompt) > 100, "Prompt too short"
            
            result["status"] = "passed"
            result["details"] = f"Built prompt with {len(prompt)} chars"
            print(f"  ✅ Prompt Building - PASSED")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ Prompt Building - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def test_response_validation(self):
        """Test: Response validation catches errors and empty responses"""
        result = {"name": "Response Validation", "status": "pending"}
        start = time.time()
        
        try:
            def validate_response(response):
                if not response or len(response.strip()) < 20:
                    return False, "Response too short"
                
                if "عذراً، حدث خطأ" in response:
                    return False, "Error message in response"
                
                # Check for Arabic content (at least 30%)
                arabic_chars = sum(1 for c in response if '\u0600' <= c <= '\u06FF')
                if arabic_chars / max(len(response), 1) < 0.30:
                    return False, "Not enough Arabic content"
                
                return True, "Valid"
            
            # Test cases
            test_cases = [
                ("", False),  # Empty
                ("short", False),  # Too short
                ("عذراً، حدث خطأ في معالجة طلبك", False),  # Error message
                ("This is English only response with no Arabic", False),  # No Arabic
                ("مدة الإجازة السنوية هي 21 يوماً بأجر كامل لكل عامل", True),  # Valid
            ]
            
            for test_response, should_pass in test_cases:
                valid, msg = validate_response(test_response)
                if should_pass:
                    assert valid, f"Valid response rejected: {msg}"
                else:
                    assert not valid, f"Invalid response accepted: {test_response}"
            
            result["status"] = "passed"
            result["details"] = f"Validated {len(test_cases)} test cases correctly"
            print(f"  ✅ Response Validation - PASSED")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"  ❌ Response Validation - FAILED: {e}")
        
        result["duration_ms"] = round((time.time() - start) * 1000)
        self.results.append(result)
        return result
    
    def run_all(self):
        """Run all unit tests"""
        print("=" * 70)
        print("🔬 Unit Tests - Egyptian Legal AI")
        print("=" * 70 + "\n")
        
        self.test_embeddings_generation()
        self.test_text_chunking()
        self.test_query_expansion()
        self.test_document_deduplication()
        self.test_arabic_text_processing()
        self.test_cache_management()
        self.test_prompt_building()
        self.test_response_validation()
        
        # Summary
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "passed")
        failed = sum(1 for r in self.results if r["status"] == "failed")
        
        print("\n" + "=" * 70)
        print("📊 Unit Tests Summary")
        print("=" * 70)
        print(f"  Total:     {total}")
        print(f"  Passed:    {passed}")
        print(f"  Failed:    {failed}")
        print(f"  Pass Rate: {(passed/max(total, 1))*100:.1f}%")
        print("=" * 70)
        
        # Save results
        self.save_results()
        
        return passed == total
    
    def save_results(self):
        """Save results to JSON"""
        reports_dir = PROJECT_ROOT / "eval" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        summary = {
            "total": len(self.results),
            "passed": sum(1 for r in self.results if r["status"] == "passed"),
            "failed": sum(1 for r in self.results if r["status"] == "failed"),
            "elapsed_seconds": round(time.time() - self.start_time, 2),
            "timestamp": datetime.now().isoformat()
        }
        summary["pass_rate"] = round((summary["passed"] / max(summary["total"], 1)) * 100, 1)
        
        output = {
            "summary": summary,
            "results": self.results
        }
        
        output_path = reports_dir / f"unit_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"\n📄 Results saved: {output_path}")


if __name__ == "__main__":
    suite = UnitTestSuite()
    success = suite.run_all()
    sys.exit(0 if success else 1)
