# Source Code Structure

This directory contains the modular implementation of the Egyptian Legal Assistant.

## 📁 Directory Structure

```
src/
├── __init__.py
├── config/              # Configuration and settings
│   ├── __init__.py
│   └── settings.py      # Constants, paths, API key management
├── prompts/             # System prompts
│   ├── __init__.py
│   └── system_prompts.py # LLM system prompts
├── llm/                 # LLM management
│   ├── __init__.py
│   └── llm_manager.py   # LLM initialization
├── memory/              # Chat history management
│   ├── __init__.py
│   └── chat_history.py  # Session history functions
├── retrieval/           # Document retrieval
│   ├── __init__.py
│   ├── retriever.py     # FAISS retriever setup
│   └── dynamic_retrieval.py # Dynamic document retrieval
├── agents/              # LangChain ReAct Agent
│   ├── __init__.py
│   └── langchain_react_agent.py   # LangChainReActAgent class
└── ui/                  # User interface
    ├── __init__.py
    └── streamlit_app.py # Streamlit UI implementation
```

## 🔧 Module Descriptions

### config/
Configuration management for the application.
- `settings.py`: Application constants, paths, API key validation



### prompts/
LLM prompt templates.
- `system_prompts.py`: System prompt for the legal assistant

### llm/
Language model management.
- `llm_manager.py`: LLM initialization and configuration

### memory/
Chat history and conversation management.
- `chat_history.py`: Session history storage and retrieval

### retrieval/
Document retrieval and legal research tools.
- `retriever.py`: FAISS vector store initialization
- `dynamic_retrieval.py`: Dynamic document retrieval optimization

### agents/
LangChain ReAct Agent implementation.
- `langchain_react_agent.py`: Official LangChain ReAct Agent with:
  - Topic relevance checking
  - Follow-up question detection
  - Smart retrieval skipping
  - Context composition

### ui/
User interface implementation.
- `streamlit_app.py`: Streamlit web interface

## 🚀 Usage

### Running the Application

```bash
# From project root
streamlit run src/ui/streamlit_app.py
```

### Importing Modules

```python
# Configuration
from src.config import MODEL_NAME, DEFAULT_SESSION_ID



# LLM
from src.llm import init_llm

# Memory (now handled by database in API server)
# from src.memory import get_session_history, reset_history

# Retrieval
from src.retrieval import prepare_retriever

# Agent
from src.agents import LangChainReActAgent, build_langchain_tools

# Prompts
from src.prompts import SYSTEM_PROMPT

# UI
from src.ui import run_app
```

## 📝 Adding New Features

### Adding a New Tool

1. Edit `src/agents/langchain_react_agent.py`
2. Add your tool function in `build_langchain_tools()`
3. Add it to the returned tools list

### Modifying the Agent

1. Edit `src/agents/langchain_react_agent.py`
2. Add new methods to `LangChainReActAgent` class

### Changing Configuration

1. Edit `src/config/settings.py`
2. Update constants as needed

### Updating Prompts

1. Edit `src/prompts/system_prompts.py`
2. Modify `SYSTEM_PROMPT` constant

## 🧪 Testing

```bash
# Test imports
python -c "from src.agents import LangChainReActAgent; print('✓ Imports working')"

# Test configuration
python -c "from src.config import MODEL_NAME; print(f'Model: {MODEL_NAME}')"

# Compile check
python -m py_compile api_server.py
```

## 📦 Dependencies

All modules depend on:
- `langchain` - LLM framework
- `streamlit` - Web UI
- `sentence-transformers` - Embeddings
- `faiss-cpu` - Vector search

See `requirements.txt` in project root for full list.
