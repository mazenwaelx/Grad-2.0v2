# Python AI Core (src)

This directory contains the core logic for the Egyptian Legal AI Assistant, including the LangChain agent, retrieval logic, and LLM configuration.

## 📁 Directory Structure

```text
src/
├── agents/              # LangChain ReAct Agent logic
│   ├── langchain_react_agent.py # Main agent class
│   ├── tool_builder.py          # Dynamic LangChain tool generation
│   ├── prompt_templates.py      # System prompts and templates
│   └── query_expansion.py       # Query expansion for better search
├── config/              # Configuration
│   └── settings.py      # Environment variables and constants
├── llm/                 # Language Model layer
│   └── llm_manager.py   # Google Gemini initialization
└── retrieval/           # RAG (Retrieval-Augmented Generation) layer
    ├── dynamic_retrieval.py # Intelligent document search
    ├── file_processor.py    # Handling uploaded user documents (PDF/DOCX)
    ├── retriever.py         # FAISS vector store integration
    └── ocr_strategies.py    # Image text extraction (Gemini Vision / Tesseract)
```

## 🚀 Usage

### Running the System

You do not run scripts inside this directory directly. The AI Core is imported and served via the main FastAPI backend.

To launch the AI backend and all other services:
```bash
# From the project root (Grad 2.0)
START_SERVERS.bat
```

### Extending the Agent

If you want to add new capabilities to the AI, you should:
1. Define a new tool inside `src/agents/tool_builder.py`.
2. Ensure the prompt handles it correctly in `src/agents/prompt_templates.py`.

### Dependencies

This module relies heavily on:
- `langchain` and `langchain-google-genai` for agent reasoning.
- `faiss-cpu` and `sentence-transformers` for document retrieval.
- `pytesseract` for local OCR capabilities.
