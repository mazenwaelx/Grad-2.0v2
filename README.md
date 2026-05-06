<div align="center">

# 🏛️ Egyptian Legal Assistant
### مساعد القانون المصري للعمل

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.3+-orange.svg)](https://langchain.com)
[![License](https://img.shields.io/badge/License-Educational-purple.svg)](#license)

An intelligent AI-powered legal assistant specialized in **Egyptian Labour Law (Law 12 of 2003)**, featuring advanced RAG (Retrieval-Augmented Generation) with a ReAct Agent architecture, multi-format document processing, and bilingual Arabic-English support.

[Features](#-features) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Architecture](#-system-architecture) • [API Reference](#-api-reference) • [Contributing](#-contributing)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Quick Start](#-quick-start)
- [API Reference](#-api-reference)
- [Frontend Interface](#-frontend-interface)
- [Database Schema](#-database-schema)
- [Data Pipeline](#-data-pipeline)
- [Usage Examples](#-usage-examples)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

The **Egyptian Legal Assistant** is a graduation project that provides an intelligent conversational interface for querying Egyptian Labour Law. Built with modern AI technologies, it combines:

- **Large Language Models (LLM)**: Google Gemini 2.0 Flash Lite for natural language understanding
- **Semantic Search**: FAISS vector store with BGE-M3 embeddings for accurate document retrieval
- **ReAct Agent**: Intelligent reasoning and action framework for complex query handling
- **Multi-format Support**: Process PDFs, Word documents, and Excel files

---

## ✨ Features

### Core Capabilities

| Feature | Description |
|---------|-------------|
| 🤖 **Intelligent ReAct Agent** | LLM-powered question analysis with tool-use capabilities |
| 🔍 **Smart Follow-up Detection** | Automatically detects conversation context to skip redundant retrieval |
| 📄 **Multi-format File Upload** | Upload and analyze PDF, DOCX, and Excel files |
| 🎯 **Intelligent Document Routing** | Prioritizes user-uploaded files when contextually relevant |
| 📚 **Rich Legal Metadata** | Articles categorized by book, chapter, and section |
| ✂️ **Adaptive Smart Chunking** | Dynamic chunking strategy based on article length |
| 💬 **Conversation Memory** | Extended context window (10+ message exchanges) |
| 🌐 **Bilingual Support** | Full Arabic RTL and English language support |
| 🔐 **User Authentication** | Secure login/signup with session management |
| 💾 **Chat Persistence** | Save and restore conversation history |

### Technical Highlights

- **Dynamic Retrieval**: Retrieves 2-6 documents based on query complexity
- **Response Caching**: Intelligent caching for repeated queries
- **Greeting Detection**: Specialized handling for conversational greetings
- **Multi-question Support**: Handle up to 3 questions in a single message
- **Source Attribution**: Clear indication of answer sources (uploaded file vs. legal database)

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │  Web Frontend │    │ Streamlit UI │    │  REST Client │                  │
│  │  (HTML/JS)   │    │  (Python)    │    │   (Any)      │                  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │
└─────────┼───────────────────┼───────────────────┼──────────────────────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     FastAPI Server (api_server.py)                   │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │   │
│  │  │ /api/chat   │  │ /api/upload │  │ /api/auth/* │  │ /api/chats │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INTELLIGENCE LAYER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                    LangChain ReAct Agent                               │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │  Question Analysis → Tool Selection → Action Execution → Response │ │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                        │ │
│  │  Tools:                                                                │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  │ │
│  │  │ legal_search │ │ smart_search │ │ file_search  │ │ follow_up    │  │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│   LLM SERVICE    │ │  RETRIEVAL LAYER │ │  DATABASE LAYER  │
├──────────────────┤ ├──────────────────┤ ├──────────────────┤
│ Google Gemini    │ │ FAISS Vector     │ │ SQL Server /     │
│ 2.0 Flash Lite   │ │ Store            │ │ SQLite           │
│                  │ │                  │ │                  │
│ BGE-M3           │ │ File Processor   │ │ Users, Chats,    │
│ Embeddings       │ │ (PDF/DOCX/Excel) │ │ Messages         │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

### ReAct Agent Flow

```
                    ┌─────────────────────┐
                    │   User Question     │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │  Greeting Check     │
                    └──────────┬──────────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
    ┌─────────────────┐               ┌─────────────────┐
    │   Is Greeting   │               │ Legal Question  │
    │                 │               │                 │
    │ Return Welcome  │               │ ReAct Analysis  │
    └─────────────────┘               └────────┬────────┘
                                               │
                          ┌────────────────────┼────────────────────┐
                          ▼                    ▼                    ▼
                ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
                │  New Question   │  │   Follow-up     │  │ Multiple Qs     │
                │                 │  │                 │  │                 │
                │ Retrieve 2-6   │  │ Use Memory &    │  │ Process Each    │
                │ Documents       │  │ Skip Retrieval  │  │ Separately      │
                └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
                         │                    │                    │
                         └────────────────────┼────────────────────┘
                                              ▼
                                   ┌─────────────────────┐
                                   │  Generate Response  │
                                   │  with Context       │
                                   └─────────────────────┘
```

---

## 📁 Project Structure

```
egyptian-legal-assistant/
│
├── 📄 api_server.py              # FastAPI REST API server
├── 📄 prepare_index.py           # FAISS vector index preparation script
├── 📄 labour_data_loader.py      # Data loading and preprocessing utilities
├── 📄 requirements.txt           # Python dependencies with version pinning
├── 📄 README.md                  # This documentation file
├── 📄 IMPLEMENTATION_GUIDE.md    # Detailed implementation guide
│
├── 📁 src/                       # Core application source code
│   ├── 📁 agents/                # ReAct Agent implementation
│   │   ├── __init__.py
│   │   └── langchain_react_agent.py  # Main agent with tools
│   │
│   ├── 📁 config/                # Application configuration
│   │   ├── __init__.py
│   │   └── settings.py           # Model settings, paths, constants
│   │
│   ├── 📁 llm/                   # LLM management
│   │   ├── __init__.py
│   │   └── llm_manager.py        # Gemini LLM initialization
│   │
│   ├── 📁 prompts/               # System prompts
│   │   ├── __init__.py
│   │   └── system_prompts.py     # Arabic legal assistant prompts
│   │
│   ├── 📁 retrieval/             # Document retrieval system
│   │   ├── __init__.py
│   │   ├── retriever.py          # FAISS retriever setup
│   │   ├── file_processor.py     # Multi-format file processor
│   │   └── dynamic_retrieval.py  # Dynamic document count logic
│   │
│   └── 📁 ui/                    # Streamlit interface
│       ├── __init__.py
│       └── streamlit_app.py      # Alternative Streamlit UI
│
├── 📁 data/                      # Data processing and storage
│   ├── __init__.py
│   ├── data_chunking.py          # Smart adaptive chunking
│   ├── data_embedding.py         # SentenceTransformer wrapper
│   ├── data_preprocessing.py     # Text preprocessing utilities
│   │
│   ├── 📁 labour_data/           # Egyptian Labour Law source data
│   │   ├── chunks_with_metadata.json
│   │   ├── labour_law_with_articles.csv
│   │   └── ...
│   │
│   ├── 📁 docstore/              # Document store cache
│   ├── 📁 merged_data/           # Processed merged documents
│   └── 📁 synthetic_data_QnA/    # Synthetic Q&A for testing
│
├── 📁 database/                  # Database layer
│   ├── __init__.py
│   ├── db_config.py              # Smart DB config (SQL Server/SQLite)
│   ├── user_manager.py           # User CRUD operations
│   ├── chat_manager.py           # Chat & message management
│   └── db_memory_store.py        # LangChain memory integration
│
├── 📁 Frontend/                  # Web interface
│   ├── chat.html                 # Main chat interface
│   ├── chat_api_script.js        # Frontend JavaScript logic
│   ├── login.html                # User login page
│   └── Signup.html               # User registration page
│
├── 📁 storage/                   # Persistent storage
│   ├── 📁 labour_faiss/          # FAISS vector index files
│   ├── 📁 chat_histories/        # File-based chat history backup
│   └── 📁 uploaded_files/        # Temporary uploaded file storage
│
└── 📁 grad_proj_env/             # Python virtual environment
```

---

## 🛠️ Installation

### Prerequisites

- **Python 3.10+** 
- **Git**
- **SQL Server** (optional - falls back to SQLite)
- **ODBC Driver 17 for SQL Server** (if using SQL Server)

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/egyptian-legal-assistant.git
cd egyptian-legal-assistant
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv grad_proj_env
grad_proj_env\Scripts\activate
source "/d/grad proj/New folder/Grad 2.0/grad_proj_env/Scripts/activate"
# Linux/macOS
python3 -m venv grad_proj_env
source grad_proj_env/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Verify Installation

```bash
pip check  # Check for dependency conflicts
python -c "import langchain; print(f'LangChain: {langchain.__version__}')"
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Required: Google AI API Key
GOOGLE_API_KEY=your_google_api_key_here

# Optional: Database Configuration (defaults to SQLite if not set)
DB_SERVER=(local)\SQLEXPRESS
DB_NAME=Labour_law_db
```

### Model Settings

Configuration is managed in [src/config/settings.py](src/config/settings.py):

| Setting | Default Value | Description |
|---------|---------------|-------------|
| `MODEL_NAME` | `models/gemini-2.0-flash-lite` | Google Gemini model |
| `CHUNK_SIZE` | `2000` | Document chunk size for embeddings |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `TOP_K_DOCUMENTS` | `6` | Default retrieval count |
| `MIN_DOCUMENTS` | `2` | Minimum dynamic retrieval |
| `MAX_DOCUMENTS` | `6` | Maximum dynamic retrieval |

### Embedding Model

The system uses **BAAI/bge-m3** multilingual embeddings, automatically detecting the best available device:

- **CUDA**: NVIDIA GPU acceleration
- **MPS**: Apple Silicon acceleration
- **CPU**: Fallback for all systems

---

## 🚀 Quick Start

### 1. Prepare the FAISS Index (First Time Only)

```bash
python prepare_index.py
```

This will:
- Load Egyptian Labour Law documents
- Create embeddings using BGE-M3
- Build and save the FAISS vector index

### 2. Initialize the Database

The database is automatically initialized on first run. It supports:
- **SQL Server**: If available and configured
- **SQLite**: Automatic fallback (no configuration needed)

### 3. Run the Application

#### Option A: FastAPI Server (Recommended)

```bash
python api_server.py
```

Access the web interface at: **http://localhost:8000/static/chat.html**

#### Option B: Streamlit UI

```bash
streamlit run src/ui/streamlit_app.py
```

Access at: **http://localhost:8501**

---

## 📡 API Reference

### Base URL
```
http://localhost:8000/api
```

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/register` | Register a new user |
| `POST` | `/login` | Authenticate user |

#### Register User
```json
POST /api/register
{
    "email": "user@example.com",
    "name": "John Doe",
    "password": "securepassword"
}
```

#### Login
```json
POST /api/login
{
    "email": "user@example.com",
    "password": "securepassword"
}
```

### Chat Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | Send a message and get AI response |
| `GET` | `/chats/{user_id}` | Get all user's chats |
| `GET` | `/chats/{chat_id}/messages` | Get chat messages |
| `PUT` | `/chats/{chat_id}/title` | Update chat title |
| `DELETE` | `/chats/{chat_id}` | Delete a chat |

#### Send Message
```json
POST /api/chat
{
    "message": "ما هي حقوق العامل في الإجازات؟",
    "chat_id": "chat_12345",
    "user_id": "user@example.com"
}
```

Response:
```json
{
    "response": "وفقاً لقانون العمل المصري...",
    "chat_id": "chat_12345"
}
```

### File Upload

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload` | Upload a document for analysis |
| `DELETE` | `/files/{file_hash}` | Remove uploaded file |

#### Upload File
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf" \
  -F "user_id=user@example.com" \
  -F "chat_id=chat_12345"
```

Response:
```json
{
    "success": true,
    "message": "File processed successfully",
    "file_hash": "abc123def456",
    "document_count": 15
}
```

---

## 🖥️ Frontend Interface

The web interface provides a modern, ChatGPT-style experience:

### Features

- **Real-time Chat**: Instant message streaming
- **File Upload**: Drag-and-drop or click to upload
- **Chat History**: Sidebar with conversation list
- **RTL Support**: Full Arabic language support
- **Responsive Design**: Works on desktop and mobile

### File Upload Card

When you upload a file, it appears as a visual card showing:
- File name and size
- Number of extracted text chunks
- Processing status

---

## 🗄️ Database Schema

### Users Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT | Primary key (auto-increment) |
| `email` | VARCHAR(255) | Unique user email |
| `name` | VARCHAR(255) | User display name |
| `password` | VARCHAR(255) | Hashed password |
| `created_at` | DATETIME | Registration timestamp |

### Chats Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT | Primary key (auto-increment) |
| `chat_id` | VARCHAR(255) | Unique chat identifier |
| `user_email` | VARCHAR(255) | Foreign key to users |
| `title` | VARCHAR(255) | Chat title |
| `created_at` | DATETIME | Creation timestamp |
| `updated_at` | DATETIME | Last update timestamp |

### Messages Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT | Primary key (auto-increment) |
| `chat_id` | VARCHAR(255) | Foreign key to chats |
| `role` | VARCHAR(50) | 'user' or 'assistant' |
| `content` | TEXT | Message content |
| `created_at` | DATETIME | Message timestamp |

---

## 📊 Data Pipeline

### Data Categorization

Each legal article includes rich metadata:

| Field | Arabic | Description |
|-------|--------|-------------|
| `article_number` | رقم المادة | Article number |
| `book` | الكتاب | Book section |
| `chapter` | الباب | Chapter |
| `section` | القسم | Section |
| `linked_definitions` | تعريفات مرتبطة | Related definitions |
| `linked_articles` | مواد مرتبطة | Related articles |

### Smart Chunking Strategy

Adaptive chunking based on article length:

| Article Size | Strategy | Result |
|--------------|----------|--------|
| ≤ 2,000 chars | Character-based (300 chars) | ~10-20 chunks |
| 2,001-4,000 chars | Word-based (÷2) | 2 chunks |
| 4,001-8,000 chars | Word-based (÷2) | 2 chunks |
| > 8,000 chars | Word-based (÷4) | 4 chunks |

### Data Statistics

| Metric | Value |
|--------|-------|
| Total Articles | 265 |
| Total Chunks | 510 |
| Average Article Size | 71 words |
| Largest Article | 340 words (المادة 1) |
| Embedding Dimensions | 1024 (BGE-M3) |

---

## 📝 Usage Examples

### Legal Questions (Arabic)

```
# Simple question
ما هي حقوق العامل في الإجازات؟

# Follow-up question (uses memory, skips retrieval)
هل يمكن للعامل رفض العمل في العطلات؟

# New topic question (triggers new retrieval)
ما هي عقوبة مخالفة قانون العمل؟
```

### File Analysis

```
# 1. Upload a document (PDF/DOCX/Excel)
# 2. Ask about its content:
ما المعلومات الموجودة في الملف؟
اشرح لي النقاط الرئيسية في المستند

# System indicates source:
# "هذه الإجابة مأخوذة من الملف الذي رفعته"
# OR
# "لم أجد معلومات ذات صلة في الملف، الإجابة من قاعدة بيانات قانون العمل"
```

### Multiple Questions

```
# Ask up to 3 questions at once:
1. ما هي مدة الإجازة السنوية؟
2. هل يمكن تجميع الإجازات؟
3. ما هي أجازة الوضع للمرأة العاملة؟
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. FAISS Index Not Found
```
Error: FAISS index not found
Solution: Run `python prepare_index.py`
```

#### 2. API Key Invalid
```
Error: Invalid API key
Solution: Check GOOGLE_API_KEY in .env file
```

#### 3. Database Connection Failed
```
Error: SQL Server connection failed
Solution: System will auto-fallback to SQLite. No action needed.
```

#### 4. Dependency Conflicts
```bash
# Check for conflicts
pip check

# Reinstall with clean environment
pip install --force-reinstall -r requirements.txt
```

#### 5. Embedding Model Download
```
First run may take time to download BGE-M3 model (~2GB)
Check internet connection and disk space
```

---

## 🚧 Future Enhancements

- [ ] Multi-document comparison analysis
- [ ] Export answers to PDF reports
- [ ] Voice input/output support
- [ ] Mobile-responsive progressive web app
- [ ] Advanced legal citation linking
- [ ] Integration with official legal databases
- [ ] Multi-language support beyond Arabic/English

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is developed for **educational purposes** as a graduation project.

---

## 👥 Contributors

Developed as a graduation project for the **Egyptian Legal AI Assistant**.

---

<div align="center">

**Made with ❤️ for the Egyptian Legal System**

مصنوع بحب لخدمة النظام القانوني المصري

</div>
