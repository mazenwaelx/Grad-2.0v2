# Egyptian Legal AI - Test Suite Documentation

## Overview

Comprehensive testing framework covering all aspects of the Egyptian Legal AI system, from individual components to complete end-to-end workflows.

## Test Categories

### 1. Unit Tests (`unit_tests.py`)
**Purpose:** Test individual components in isolation

**Tests (8):**
- Embedding generation (1024-dim vectors)
- Text chunking with overlap
- Query expansion
- Document deduplication
- Arabic text normalization
- Cache management
- Prompt building
- Response validation

**Run:**
```bash
python eval/unit_tests.py
```

### 2. Integration Tests (`integration_tests.py`)
**Purpose:** Verify components work together correctly

**Tests (5):**
- Database + Agent integration
- Retriever + LLM pipeline
- File processor + Agent
- API + Database operations
- Complete agent pipeline

**Run:**
```bash
python eval/integration_tests.py
```

### 3. Mock Tests (`mock_tests.py`)
**Purpose:** Test with simulated dependencies

**Tests (8):**
- Mock LLM responses
- Mock database operations
- Mock retriever
- Mock file processor
- Mock API endpoints
- Mock embeddings
- Mock agent tools
- Mock chat history

**Run:**
```bash
python eval/mock_tests.py
```

### 4. Functional Tests (`functional_tests.py`)
**Purpose:** Verify specific feature requirements

**Tests (7):**
- User registration
- User authentication
- Chat creation
- Message storage and retrieval
- Search functionality
- Response generation
- Chat history management

**Run:**
```bash
python eval/functional_tests.py
```

### 5. System Tests (`system_tests.py`)
**Purpose:** End-to-end system workflows

**Tests (6):**
- Complete user journey (register → login → chat)
- Document upload and query flow
- Data persistence across sessions
- Concurrent user requests
- Error recovery
- System performance

**Run:**
```bash
python eval/system_tests.py
```

### 6. Security Tests (`security_tests.py`)
**Purpose:** Validate security measures

**Tests (7):**
- Password hashing (no plaintext storage)
- SQL injection prevention
- Authentication bypass prevention
- XSS protection
- Input validation
- CORS configuration
- Error message safety

**Run:**
```bash
python eval/security_tests.py
```

### 7. Usability Tests (`usability_tests.py`)
**Purpose:** Measure user experience

**Tests (6):**
- Response clarity and structure
- Arabic text quality
- Response time acceptability
- Error message helpfulness
- API documentation accessibility
- Consistent terminology

**Run:**
```bash
python eval/usability_tests.py
```

### 8. Playwright E2E Tests (`playwright_tests.py`)
**Purpose:** Browser automation testing

**Tests (13):**
- Infrastructure: API health, login page, docs
- Authentication: signup, login, invalid login
- File management: upload, list files
- UI: responsive design
- AI Quality: legal accuracy, out-of-scope rejection, consistency, Arabic quality

**Run:**
```bash
python eval/playwright_tests.py
python eval/playwright_tests.py --headed  # with visible browser
```

### 9. Deepchecks RAG Evaluation (`deepchecks_eval.py`)
**Purpose:** RAG quality evaluation

**Tests (15):**
- 15 legal questions across 7 topics
- 3 difficulty levels (simple, medium, complex)
- 5 quality dimensions per response
- Keyword coverage, completeness, legal references

**Run:**
```bash
python eval/deepchecks_eval.py
python eval/deepchecks_eval.py --live  # with real API calls
```

## Running All Tests

### Quick Run (All Tests)
```bash
python eval/run_all_tests.py
```

### Skip Slow Tests (No Playwright/Deepchecks)
```bash
python eval/run_all_tests.py --quick
```

### Specific Test Suites
```bash
python eval/run_all_tests.py --unit-only
python eval/run_all_tests.py --integration-only
python eval/run_all_tests.py --e2e-only
```

### Generate PDF Report
```bash
python eval/run_all_tests.py --generate-report
```

## Test Results

All test results are saved as JSON files in `eval/reports/`:
- `unit_results_YYYYMMDD_HHMMSS.json`
- `integration_results_YYYYMMDD_HHMMSS.json`
- `mock_results_YYYYMMDD_HHMMSS.json`
- `functional_results_YYYYMMDD_HHMMSS.json`
- `system_results_YYYYMMDD_HHMMSS.json`
- `security_results_YYYYMMDD_HHMMSS.json`
- `usability_results_YYYYMMDD_HHMMSS.json`
- `playwright_results_YYYYMMDD_HHMMSS.json`
- `deepchecks_results_YYYYMMDD_HHMMSS.json`

## Comprehensive PDF Report

Generate a complete PDF report with all test results:

```bash
python eval/generate_report.py
```

The report includes:
- Executive summary with overall statistics
- System architecture details
- Results from all 9 test categories
- Detailed per-test breakdowns
- Quality metrics and scoring
- Recommendations

Report saved to: `eval/reports/Egyptian_Legal_AI_Test_Report.pdf`

## Test Coverage Summary

| Category | Tests | Focus Area |
|----------|-------|------------|
| Unit | 8 | Component isolation |
| Integration | 5 | Component interaction |
| Mock | 8 | Dependency simulation |
| Functional | 7 | Feature verification |
| System | 6 | End-to-end workflows |
| Security | 7 | Vulnerability protection |
| Usability | 6 | User experience |
| Playwright E2E | 13 | Browser automation |
| Deepchecks RAG | 15 | AI quality evaluation |
| **TOTAL** | **75** | **Comprehensive coverage** |

## Prerequisites

### For All Tests
```bash
pip install -r requirements.txt
```

### For Playwright Tests Only
```bash
pip install playwright
playwright install chromium
```

### Backend Required
Some tests require the backend server running:
```bash
python api_server.py
```

Tests that need backend will skip automatically if it's not running.

## CI/CD Integration

Add to your CI pipeline:
```yaml
- name: Run Tests
  run: python eval/run_all_tests.py --quick

- name: Generate Report
  run: python eval/generate_report.py
  
- name: Upload Report
  uses: actions/upload-artifact@v2
  with:
    name: test-report
    path: eval/reports/Egyptian_Legal_AI_Test_Report.pdf
```

## Troubleshooting

### Backend Not Running
Tests requiring backend will skip automatically. Start backend:
```bash
python api_server.py
```

### Font Errors in PDF Generation
Ensure Tahoma and Arial fonts are installed (Windows includes them by default).

### Playwright Installation Issues
```bash
playwright install --with-deps chromium
```

### Database Connection Issues
Check SQL Server connection string in `.env` file.

## Contributing

When adding new tests:
1. Add test file to `eval/` directory
2. Follow naming convention: `{category}_tests.py`
3. Implement test suite class with `run_all()` and `save_results()` methods
4. Add to `run_all_tests.py`
5. Update `generate_report.py` to include results
6. Update this README

## License

Part of Egyptian Legal AI project.
