import os
import json
import asyncio
from typing import AsyncGenerator, List, Dict, Any, Optional
from dotenv import load_dotenv
import httpx

load_dotenv()

AVAILABLE_MODELS = [
    {
        "id": "gemini-3.5-flash-lite",
        "name": "Gemini 3.5 Flash Lite",
        "description": "Blazing fast, ultra-low latency and highly responsive for chat",
        "is_default": True,
    },
    {
        "id": "gemini-flash-lite-latest",
        "name": "Gemini Flash Lite (Latest)",
        "description": "Fast multimodal model with low latency",
        "is_default": False,
    },
    {
        "id": "gemini-3.8-flash",
        "name": "Gemini 3.8 Flash",
        "description": "Next-gen speed, deep comprehension, and advanced reasoning",
        "is_default": False,
    },
    {
        "id": "gemini-3.5-flash",
        "name": "Gemini 3.5 Flash",
        "description": "Versatile model for coding, analysis, and conversations",
        "is_default": False,
    },
]


def get_default_api_key() -> Optional[str]:
    """Retrieve Gemini API key from environment."""
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    return key if key and key != "your_gemini_api_key_here" else None


def is_gemini_configured(custom_key: Optional[str] = None) -> bool:
    """Check whether a valid API key is present."""
    key = (custom_key or "").strip() or get_default_api_key()
    return bool(key)


def _format_history_for_gemini(
    messages: List[Dict[str, Any]],
    current_prompt: str
) -> List[Dict[str, Any]]:
    """
    Format chat history for Gemini API.
    Gemini roles: 'user' and 'model'.
    Consecutive messages with the same role are grouped or alternated.
    """
    contents: List[Dict[str, Any]] = []

    for msg in messages:
        role = msg.get("role", "")
        content = (msg.get("content") or "").strip()
        if not content:
            continue

        gemini_role = "user" if role in ("user", "system") else "model"

        # If previous item has same role, append to parts; else new item
        if contents and contents[-1]["role"] == gemini_role:
            contents[-1]["parts"].append({"text": content})
        else:
            contents.append({
                "role": gemini_role,
                "parts": [{"text": content}]
            })

    # Ensure last message is current user prompt
    if current_prompt.strip():
        if contents and contents[-1]["role"] == "user":
            contents[-1]["parts"].append({"text": current_prompt.strip()})
        else:
            contents.append({
                "role": "user",
                "parts": [{"text": current_prompt.strip()}]
            })

    return contents


DEFAULT_SYSTEM_PROMPT = (
    "You are Encatesus, a highly capable, intelligent, and friendly AI assistant. "
    "Provide clear, accurate, and insightful responses with clean markdown formatting and code examples when requested."
)


async def _mock_stream_response(prompt: str, reason: str = "no_key") -> AsyncGenerator[str, None]:
    """
    Graceful fallback simulation when GEMINI_API_KEY is not configured or fails.
    Provides clear, helpful instructions and interactive sample response.
    """
    if reason == "no_key":
        header = (
            "✨ **Welcome to the Encatesus AI Chat interface!**\n\n"
            "> ⚠️ **Notice: Running in Demo / Mock Mode**\n"
            "> To unlock full Google Gemini AI capabilities:\n"
            "> 1. Get your free API key at **[Google AI Studio](https://aistudio.google.com/)**.\n"
            "> 2. Click the ⚙️ **Settings** button in the header and paste your API key, or set `GEMINI_API_KEY` in `backend/.env`.\n\n"
            "---\n\n"
        )
    else:
        header = (
            "⚠️ **Gemini API Error Notice**\n\n"
            f"> The API request encountered an error: *{reason}*.\n"
            "> Please verify your API key and network connection.\n\n"
            "---\n\n"
        )

    body = (
        f"**Echo Response to your prompt:**\n\n"
        f"You asked: *\"{prompt}\"*\n\n"
        f"Here is a simulated response from **Encatesus** demonstrating markdown rendering, code blocks, and streaming capability:\n\n"
        f"```python\n"
        f"# Example Python code snippet\n"
        f"def greet_user(name: str) -> str:\n"
        f"    return f'Hello, {{name}}! Welcome to Encatesus AI.'\n\n"
        f"print(greet_user('Explorer'))\n"
        f"```\n\n"
        f"### Features included:\n"
        f"- ⚡ Real-time SSE streaming responses\n"
        f"- 💬 Multi-turn chat persistence (SQLite)\n"
        f"- 🎨 Clean UI with dark/light themes & syntax highlighting\n"
        f"- 🔑 Easy custom API key configuration\n\n"
        f"Ready whenever you provide your Gemini API key!"
    )

    full_text = header + body
    # Stream in natural chunks with slight delay
    words = full_text.split(" ")
    buffer = ""
    for i, word in enumerate(words):
        buffer += (word + " ")
        if len(buffer) >= 12 or i == len(words) - 1:
            yield buffer
            buffer = ""
            await asyncio.sleep(0.02)


async def stream_gemini_response(
    messages: List[Dict[str, Any]],
    prompt: str,
    model: str = "gemini-3.5-flash-lite",
    system_prompt: Optional[str] = None,
    api_key: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """
    Stream Gemini response using REST API with SSE fallback or SDK.
    Supports multi-turn history and system instructions.
    """
    active_key = (api_key or "").strip() or get_default_api_key()

    if not active_key:
        async for chunk in _mock_stream_response(prompt, reason="no_key"):
            yield chunk
        return

    # Map model aliases if necessary
    model_name = model.strip() if model else "gemini-3.5-flash-lite"
    if model_name not in [m["id"] for m in AVAILABLE_MODELS]:
        model_name = "gemini-3.5-flash-lite"

    # Build Gemini REST payload
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:streamGenerateContent?alt=sse&key={active_key}"
    contents = _format_history_for_gemini(messages, prompt)

    payload: Dict[str, Any] = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 4096,
        }
    }

    instruction_text = (system_prompt or "").strip() or DEFAULT_SYSTEM_PROMPT
    if instruction_text:
        payload["systemInstruction"] = {
            "parts": [{"text": instruction_text}]
        }

    client_timeout = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)

    try:
        async with httpx.AsyncClient(timeout=client_timeout) as client:
            async with client.stream("POST", url, json=payload, headers={"Content-Type": "application/json"}) as response:
                if response.status_code != 200:
                    error_body = await response.aread()
                    error_text = error_body.decode(errors="replace")
                    try:
                        err_json = json.loads(error_text)
                        msg = err_json.get("error", {}).get("message", error_text)
                    except Exception:
                        msg = error_text
                    
                    async for chunk in _mock_stream_response(prompt, reason=f"Status {response.status_code}: {msg[:200]}"):
                        yield chunk
                    return

                # Parse SSE from Google API
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data:"):
                        raw_data = line[len("data:"):].strip()
                        if not raw_data or raw_data == "[DONE]":
                            continue
                        try:
                            data_obj = json.loads(raw_data)
                            candidates = data_obj.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for part in parts:
                                    text = part.get("text", "")
                                    if text:
                                        yield text
                        except json.JSONDecodeError:
                            continue

    except httpx.RequestError as exc:
        async for chunk in _mock_stream_response(prompt, reason=f"Network error: {str(exc)}"):
            yield chunk
    except Exception as exc:
        async for chunk in _mock_stream_response(prompt, reason=f"Unexpected error: {str(exc)}"):
            yield chunk
