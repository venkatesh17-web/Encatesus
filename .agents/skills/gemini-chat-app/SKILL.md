---
name: gemini-chat-app
description: >-
  Architecture, API integration logic, database schema, and frontend layout specifications
  for the free ChatGPT-like Gemini web application. Use when extending chat features,
  modifying API streaming, updating dark-mode UI, or debugging endpoints.
---

# Gemini AI Chat Application Specification & Architecture

This skill documents the complete system architecture, API connectivity, database structure, and frontend design guidelines for the ChatGPT-like AI chat application.

---

## 1. System Architecture Overview

```
d:\trial_1\
├── backend/
│   ├── main.py              # FastAPI application server, route handlers, SSE endpoints, static file mounting
│   ├── database.py          # SQLite database schema, WAL mode, indexing, thread-safe connection pooling & CRUD
│   ├── gemini_service.py    # Google Gemini API client (gemini-2.5-flash, gemini-1.5-flash, etc.), SSE streaming, fallback mock engine
│   ├── requirements.txt     # Backend dependencies (fastapi, uvicorn, pydantic, google-genai, httpx, python-dotenv)
│   ├── run.py               # Lightweight Uvicorn server launcher (port 8000)
│   └── .env.example         # Environment configuration template (GEMINI_API_KEY)
├── frontend/
│   ├── index.html           # Single-page ChatGPT-style responsive dark interface
│   ├── css/
│   │   └── styles.css       # Dark theme styles, code highlight wrappers, custom scrollbar, streaming animation
│   └── js/
│       └── app.js           # Client application controller, SSE stream parser, markdown renderer, chat state manager
├── tests/
│   └── test_api.py          # Automated test suite for health, models, CRUD, streaming, and static serving
├── .agents/
│   └── skills/
│       └── gemini-chat-app/
│           └── SKILL.md     # Agent skill documentation for future development cycles
└── README.md                # Quick start guide and server launch documentation
```

---

## 2. Backend Architecture & API Specifications

### 2.1 Technology Stack
- **Framework**: FastAPI (async Python 3.10+)
- **Server**: Uvicorn ASGI
- **Database**: SQLite3 (`chat.db`) with WAL (Write-Ahead Logging) mode and foreign keys enabled
- **AI SDK**: Google GenAI / Gemini Free Tier API (`gemini-2.5-flash`, `gemini-1.5-flash`, `gemini-1.5-pro`)

### 2.2 Database Schema
- **`conversations` Table**:
  - `id` (TEXT PRIMARY KEY) - UUID string
  - `title` (TEXT) - Auto-generated from initial prompt or user-edited
  - `model` (TEXT) - Gemini model identifier
  - `created_at` (TEXT) - ISO 8601 timestamp
  - `updated_at` (TEXT) - ISO 8601 timestamp
- **`messages` Table**:
  - `id` (TEXT PRIMARY KEY) - UUID string
  - `conversation_id` (TEXT FOREIGN KEY -> conversations.id ON DELETE CASCADE)
  - `role` (TEXT) - `'user'` | `'assistant'` | `'system'`
  - `content` (TEXT) - Message text content (Markdown formatted)
  - `timestamp` (TEXT) - ISO 8601 timestamp

### 2.3 REST & Streaming Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service status, database check, Gemini API key presence |
| `GET` | `/api/models` | List supported models (Gemini 2.5 Flash, 1.5 Flash, 1.5 Pro) |
| `GET` | `/api/conversations` | List conversation history summaries with message count and preview |
| `POST` | `/api/conversations` | Create a new conversation session |
| `GET` | `/api/conversations/{id}` | Retrieve single conversation metadata and full message history |
| `PATCH` | `/api/conversations/{id}` | Rename conversation title |
| `DELETE` | `/api/conversations/{id}` | Delete conversation and cascade delete all its messages |
| `POST` | `/api/chat/stream` | Server-Sent Events (SSE) endpoint: streams tokens in real-time, persists user and assistant messages |

### 2.4 Gemini Integration Logic
- **Stream Format**: EventStream with JSON payloads:
  - `data: {"type": "start", "conversation_id": "...", "message_id": "..."}`
  - `data: {"type": "chunk", "text": "token text"}`
  - `data: {"type": "done", "conversation_id": "...", "total_tokens": 120}`
  - `data: {"type": "error", "error": "details"}`
- **Fallback / Demo Mode**: If no `GEMINI_API_KEY` is provided, the backend falls back to an interactive local mock generator with clear instructions on how to obtain a free key from Google AI Studio.
- **Key Precedence**: Client Header (`x-gemini-api-key`) > Client Payload (`api_key`) > Server Environment (`GEMINI_API_KEY`).

---

## 3. Frontend Specifications & Layout Guidelines

### 3.1 Design System & Theme
- **Color Palette**:
  - Primary Background: `#0e1015` / `#15171e`
  - Sidebar Background: `#111318`
  - Card & Bubble Surface: `#1a1d26` (User), `#222632` (Assistant)
  - Accent / Primary Action: `#6366f1` / `#4f46e5` (Indigo gradient)
  - Text: High contrast `#f1f5f9` (Primary), `#94a3b8` (Muted)
  - Code Block Background: `#090b10` with custom header bar and syntax highlighting

### 3.2 Key UI Components
1. **Collapsible Sidebar**:
   - New Chat button (`Ctrl+N`)
   - Real-time search filter (`Ctrl+K`)
   - Chronological chat history grouping: *Today*, *Yesterday*, *Previous 7 Days*, *Older*
   - Active chat highlight with inline rename and delete controls
   - Bottom settings bar: Model switcher, API key modal trigger, Clear all chats
2. **Main Chat Canvas**:
   - Header with active model pill, status dot, sidebar toggle button, and quick new chat button
   - Empty-state welcome screen with 4 interactive starter suggestion cards
   - Scrollable message stream with markdown formatting (GFM tables, blockquotes, inline code, bold, links)
   - Code blocks with syntax badge (Python, JS, Bash, etc.) and instant copy button
   - Action toolbar beneath assistant replies: Copy Markdown, Retry prompt
3. **Smart Input Area**:
   - Auto-expanding textarea with max-height scroll
   - Send button transforming into dynamic "Stop Generating" button during active SSE stream
   - Typing indicator and streaming blinking cursor
   - Keyboard shortcuts: `Enter` to send, `Shift+Enter` for line break

---

## 4. Maintenance & Extension Runbook

### Adding New Models
1. Update model constants in `backend/gemini_service.py` (`AVAILABLE_MODELS`).
2. Add the model option in `frontend/index.html` model selector and `frontend/js/app.js`.

### Customizing System Prompts
- Default system instructions can be adjusted dynamically in the Settings modal or via `backend/gemini_service.py`.

### Performance on Low-Resource Devices (e.g. 8GB RAM / Dual-Core)
- Backend uses native Python `sqlite3` and lightweight `asyncio` without memory-heavy ORMs.
- Frontend uses lightweight CDN libraries (Tailwind, Marked, Highlight.js) without heavy Node build steps.
