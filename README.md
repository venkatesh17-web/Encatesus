# ⚡ Free Gemini AI Chat Interface (ChatGPT-Style)

A lightweight, responsive, and free AI chat web application powered by **FastAPI** and **Google Gemini API** (Free Tier), featuring real-time Server-Sent Events (SSE) token streaming, multi-turn conversation memory, SQLite persistence, and a modern ChatGPT-inspired dark mode interface.

---

## 🚀 Features

- 💬 **ChatGPT-Style Dark Mode Interface**: Modern UI with Tailwind CSS, Lucide icons, responsive sidebar, and auto-expanding input bar.
- ⚡ **Real-Time Token Streaming**: Server-Sent Events (SSE) streaming for typing effect.
- 🧠 **Google Gemini Free Tier Support**: Supports `gemini-2.5-flash`, `gemini-1.5-flash`, `gemini-1.5-pro`, and `gemini-2.0-flash`.
- 🗄️ **Zero-Configuration SQLite Persistence**: Conversations and messages automatically persist locally in `chat.db` with WAL mode.
- 📝 **Markdown & Code Highlighting**: Full Markdown support (tables, lists, blockquotes) and syntax-highlighted code blocks with a one-click **Copy Code** button.
- ⚙️ **Dual API Key Configuration**: Set `GEMINI_API_KEY` in `.env` OR enter your key directly in the browser Settings modal.
- 🛡️ **Interactive Fallback/Demo Mode**: Runs out-of-the-box even without an API key with built-in mock streaming for local testing.
- 💻 **Optimized for 8GB RAM / Windows**: Low memory footprint (~35MB RAM), async non-blocking I/O.

---

## 📁 Directory Structure

```
d:\trial_1\
├── backend/
│   ├── main.py              # FastAPI server, SSE stream handler, static file mount
│   ├── database.py          # SQLite database schema, WAL mode, CRUD methods
│   ├── gemini_service.py    # Gemini API client, SSE streaming, mock fallback
│   ├── requirements.txt     # Python dependencies
│   ├── run.py               # Uvicorn launcher
│   └── .env.example         # Environment template
├── frontend/
│   ├── index.html           # ChatGPT-style web interface
│   ├── css/
│   │   └── styles.css       # Dark mode theme, scrollbars, streaming animations
│   └── js/
│       └── app.js           # Client controller, SSE stream parser, markdown renderer
├── tests/
│   ├── test_api.py          # Integration and API route tests
│   ├── test_database.py     # SQLite database tests
│   ├── test_gemini_service.py # Gemini service & prompt formatting tests
│   └── conftest.py          # Pytest fixtures
├── .agents/
│   └── skills/
│       └── gemini-chat-app/
│           └── SKILL.md     # Project memory and architecture specifications
├── run_tests.py             # Automated test discovery and reporting runner
└── README.md                # Documentation and startup guide
```

---

## 🛠️ Quick Start Guide

### 1. (Optional) Configure Gemini API Key
You can get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

Create a `.env` file in `backend/` or in the project root:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```
> *Note: You can also enter the API key directly in the web UI Settings modal (`⚙️ Settings`), which saves it securely in your browser.*

### 2. Start the Local Server
Run from the project root (`d:\trial_1`):
```powershell
python backend/run.py
```
Or with uvicorn directly:
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Open the Web Application
Open your browser and navigate to:
👉 **[http://localhost:8000](http://localhost:8000)**

Swagger Interactive API Docs:
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## 🧪 Running Automated Tests

Run the test suite (33 tests covering health, models, CRUD, streaming, and frontend):
```powershell
python run_tests.py
```
Or using pytest:
```powershell
pytest
```

---

## ⌨️ Keyboard Shortcuts
- `Enter`: Send message
- `Shift + Enter`: Insert new line
- `Ctrl + N` / `Cmd + N`: Start new conversation
- `Ctrl + K` / `Cmd + K`: Focus conversation search
