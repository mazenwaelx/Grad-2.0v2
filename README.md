# LawyerConnect - Egyptian Legal AI Platform

A comprehensive platform connecting clients with lawyers and providing AI-powered legal assistance for Egyptian Labour Law.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Deployment](#deployment)

---

## Overview

LawyerConnect is a full-stack legal technology platform that combines:

- **Client-Lawyer Marketplace**: Book consultations, chat with lawyers, manage appointments
- **AI Legal Assistant**: Specialized chatbot for Egyptian Labour Law queries
- **Document Processing**: Upload and analyze legal documents (PDF, DOCX, Excel)
- **Secure Authentication**: JWT-based auth with refresh tokens

### Technology Stack

**Frontend:**
- React 18 + TypeScript (Main website)
- React 18 + JavaScript (Standalone AI chat)
- Tailwind CSS, Framer Motion

**Backend:**
- .NET 8.0 (C#) - Main API
- Python 3.11 + FastAPI - AI services
- SQL Server (Azure-ready)

**AI/ML:**
- Google Gemini 2.0 Flash Lite
- LangChain ReAct Agent
- FAISS vector store (BGE-M3 embeddings)
- OCR support (Tesseract + Gemini Vision)

---

## Architecture

```
┌─────────────────┐      ┌─────────────────┐
│  Website (3002) │◄────►│ .NET API (5128) │
│  React + TS     │      │  Auth, Lawyers  │
└────────┬────────┘      └─────────────────┘
         │                        │
         │                        ▼
         │               ┌─────────────────┐
         │               │  SQL Server DB  │
         │               │  LawyerConnectDB│
         │               └─────────────────┘
         │
         ▼
┌─────────────────┐      ┌─────────────────┐
│ AI Chat (3000)  │◄────►│ Python API      │
│  React + JS     │      │  FastAPI (8000) │
└─────────────────┘      └────────┬────────┘
                                  │
                         ┌────────┴────────┐
                         │  AI Components  │
                         │  - LangChain    │
                         │  - FAISS Index  │
                         │  - Gemini LLM   │
                         └─────────────────┘
```

---

## Features

### Client Features
- Browse lawyer profiles by specialization
- Book consultations and appointments
- Real-time chat with lawyers
- Payment integration
- Review and rating system
- AI legal assistant with document analysis

### Lawyer Features
- Professional profile management
- Availability scheduling
- Client interaction management
- Earnings dashboard
- Consultation history

### AI Assistant
- Natural language Q&A for Egyptian Labour Law
- Multi-turn conversations with context
- Document upload and analysis
- Bilingual support (Arabic/English)
- Smart follow-up detection
- Response caching

---

## Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- **.NET SDK** 8.0+
- **SQL Server** (LocalDB/Express/Azure)
- **Git**

**Optional:**
- Tesseract OCR (for image text extraction)
- CUDA-capable GPU (for faster embeddings)

---

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd "Grad 2.0"
```

### 2. Backend Setup (.NET)

```bash
cd LawyerConnect-main
dotnet restore
dotnet build

# Run migrations
dotnet ef database update
```

### 3. Frontend Setup (Website)

```bash
cd LawyerConnect-main/FrontEnd
npm install
```

### 4. Frontend Setup (Standalone AI Chat)

```bash
cd react-frontend
npm install
```

### 5. Python AI Setup

```bash
# Create virtual environment
python -m venv grad_proj_env
grad_proj_env\Scripts\activate  # Windows
source grad_proj_env/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Prepare FAISS index (first time only)
python -c "from src.retrieval.retriever import get_retriever; get_retriever()"
```

---

## Configuration

### 1. Database Connection

Edit `LawyerConnect-main/appsettings.json`:

```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Server=(local)\\SQLEXPRESS;Database=LawyerConnectDB;Trusted_Connection=True;TrustServerCertificate=True"
  },
  "Jwt": {
    "Key": "your-secret-key-min-32-characters",
    "Issuer": "LawyerConnectAPI",
    "Audience": "LawyerConnectClients",
    "ExpirationMinutes": 30
  },
  "App": {
    "BaseUrl": "http://localhost:3002"
  }
}
```

### 2. Python AI Configuration

Create `.env` file in root:

```env
# Required
GEMINI_API_KEY=your_google_api_key

# Optional (defaults to SQL Server if available)
DB_SERVER=(local)\SQLEXPRESS
DB_NAME=LawyerConnectDB
```

### 3. Frontend Configuration

Create `LawyerConnect-main/FrontEnd/.env.local`:

```env
VITE_API_URL=http://localhost:5128/api
VITE_AI_API_URL=http://localhost:8000
```

---

## Running the Application

### Quick Start (All Servers)

```bash
START_SERVERS.bat
```

This starts:
1. Python AI Backend (port 8000)
2. .NET Backend (port 5128)
3. Standalone AI Chat (port 3000)
4. Main Website (port 3002)

### Manual Start

**Python AI Backend:**
```bash
python api_server.py
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

**.NET Backend:**
```bash
cd LawyerConnect-main
dotnet run
# API: http://localhost:5128
```

**Website Frontend:**
```bash
cd LawyerConnect-main/FrontEnd
npm run dev
# App: http://localhost:3002
```

**Standalone AI Chat:**
```bash
cd react-frontend
npm start
# App: http://localhost:3000
```

### Stop All Servers

```bash
STOP_SERVERS.bat
```

### Check Server Status

```bash
CHECK_SERVERS.bat
```

---

## Project Structure

```
Grad 2.0/
├── LawyerConnect-main/          # .NET backend + website frontend
│   ├── Controllers/             # API controllers
│   ├── Services/                # Business logic
│   ├── Repositories/            # Data access
│   ├── Models/                  # Entity models
│   ├── DTOs/                    # Data transfer objects
│   ├── Migrations/              # EF Core migrations
│   ├── FrontEnd/                # React website
│   │   └── src/
│   │       ├── components/      # React components
│   │       ├── pages/           # Page components
│   │       └── services/        # API clients
│   └── LawyerConnect.Tests/     # Unit tests
│
├── react-frontend/              # Standalone AI chat app
│   └── src/
│       ├── pages/Chat/          # Chat interface
│       ├── components/          # Reusable components
│       └── context/             # React context
│
├── src/                         # Python AI core
│   ├── agents/                  # LangChain ReAct agent
│   ├── retrieval/               # FAISS retriever + file processor
│   ├── llm/                     # LLM initialization
│   └── config/                  # Settings
│
├── data/                        # Legal data
│   └── labour_data/             # Egyptian Labour Law
│
├── database/                    # Python DB layer
│   ├── chat_manager.py          # Chat CRUD
│   ├── user_manager.py          # User CRUD
│   └── db_memory_store.py       # LangChain memory
│
├── storage/                     # Runtime storage
│   ├── labour_faiss/            # Vector index
│   └── uploaded_files/          # User uploads
│
├── eval/                        # Testing & evaluation
│   ├── deepchecks_eval.py       # AI quality tests
│   ├── mlflow_tracking.py       # Experiment tracking
│   └── playwright_tests.py      # E2E tests
│
├── api_server.py                # FastAPI server
├── requirements.txt             # Python dependencies
├── START_SERVERS.bat            # Launch all servers
└── README.md                    # This file
```

---

## API Documentation

### .NET API (Port 5128)

**Authentication:**
- `POST /api/auth/register` - Register user/lawyer
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Refresh token
- `POST /api/auth/logout` - Logout

**Lawyers:**
- `GET /api/lawyers` - List lawyers (with filters)
- `GET /api/lawyers/{id}` - Get lawyer details
- `PUT /api/lawyers/{id}` - Update profile
- `GET /api/lawyers/{id}/availability` - Get schedule

**Bookings:**
- `POST /api/bookings` - Create booking
- `GET /api/bookings/user/{userId}` - User's bookings
- `GET /api/bookings/lawyer/{lawyerId}` - Lawyer's bookings
- `PUT /api/bookings/{id}/status` - Update status

**Chat:**
- `GET /api/chat/rooms/{userId}` - Get chat rooms
- `POST /api/chat/send` - Send message
- `GET /api/chat/messages/{roomId}` - Get messages

**Reviews:**
- `POST /api/reviews` - Create review
- `GET /api/reviews/lawyer/{lawyerId}` - Get reviews

### Python AI API (Port 8000)

Full docs: http://localhost:8000/docs

**AI Chat:**
- `POST /api/chat` - Send message to AI
  ```json
  {
    "message": "ما هي حقوق العامل؟",
    "user_id": "user@email.com",
    "chat_id": "chat_123"
  }
  ```

**File Upload:**
- `POST /api/upload` - Upload document
- `GET /api/files` - List uploaded files
- `DELETE /api/files/{hash}` - Remove file

**Chat Management:**
- `GET /api/chats/{user_email}` - Get user chats
- `GET /api/messages/{chat_id}` - Get messages
- `DELETE /api/chat/{user_id}/{chat_id}` - Delete chat

---

## Testing

### .NET Tests

```bash
cd LawyerConnect-main
dotnet test
```

### AI Evaluation

```bash
# Quality tests
python eval/deepchecks_eval.py

# E2E tests
python eval/playwright_tests.py

# Experiment tracking
python eval/mlflow_tracking.py --ui
```

### Manual Testing

1. Start all servers: `START_SERVERS.bat`
2. Open http://localhost:3002
3. Register an account
4. Test features:
   - Browse lawyers
   - Book consultation
   - Use AI chat (click AI icon in header)
   - Upload document in AI chat
   - Go fullscreen to standalone app

---

## Deployment

### Database

**SQL Server:**
- Use connection string in `appsettings.json`
- Run migrations: `dotnet ef database update`

**Azure SQL:**
```json
"DefaultConnection": "Server=tcp:yourserver.database.windows.net,1433;Initial Catalog=LawyerConnectDB;Persist Security Info=False;User ID=admin;Password=yourpassword;MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;"
```

### .NET Backend

```bash
dotnet publish -c Release -o ./publish
# Deploy to IIS, Azure App Service, or container
```

### Python AI

```bash
# Production server
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api_server:app
```

### Frontend

```bash
# Website
cd LawyerConnect-main/FrontEnd
npm run build
# Deploy dist/ folder to static hosting

# Standalone AI
cd react-frontend
npm run build
# Deploy build/ folder
```

### Environment Variables (Production)

- Set `GEMINI_API_KEY` securely
- Update `VITE_API_URL` to production URLs
- Use strong JWT secret keys
- Enable HTTPS
- Configure CORS properly

---

## Maintenance

### Cleanup

```bash
CLEANUP_PROJECT.bat  # Remove cache, old reports, build artifacts
```

### Update Dependencies

```bash
# Python
pip install --upgrade -r requirements.txt

# .NET
dotnet restore

# Frontend
npm update
```

### Database Backup

```bash
# SQL Server
sqlcmd -S (local)\SQLEXPRESS -Q "BACKUP DATABASE LawyerConnectDB TO DISK='backup.bak'"
```

---

## Support

For issues or questions:
- Check `SERVER_GUIDE.md` for server management
- Check `FILES_TO_DELETE.md` for cleanup guidance
- Review API docs at http://localhost:8000/docs

---

## License

Educational project for graduation requirements.
