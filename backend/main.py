import os
import json
import uuid
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Header, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import database as db
import gemini_service

app = FastAPI(
    title="Gemini AI Chat Backend",
    description="High-performance backend for Gemini AI Chat application",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Schemas
class CreateConversationRequest(BaseModel):
    title: Optional[str] = Field(default="New Chat", description="Title of the conversation")
    model: Optional[str] = Field(default="gemini-1.5-flash", description="Model ID")


class UpdateConversationRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Updated conversation title")


class ChatStreamRequest(BaseModel):
    conversation_id: Optional[str] = Field(default=None, description="Existing conversation ID or null for new")
    message: str = Field(..., min_length=1, description="User prompt message")
    model: Optional[str] = Field(default="gemini-1.5-flash", description="Model to use")
    system_prompt: Optional[str] = Field(default=None, description="Optional system instructions")
    api_key: Optional[str] = Field(default=None, description="Optional custom Gemini API key")


# API Routes
@app.get("/api/health")
async def health_check(x_gemini_api_key: Optional[str] = Header(None, alias="x-gemini-api-key")):
    """Check API server health and Gemini configuration status."""
    configured = gemini_service.is_gemini_configured(x_gemini_api_key)
    return {
        "status": "ok",
        "gemini_configured": configured,
        "models_count": len(gemini_service.AVAILABLE_MODELS),
    }


@app.get("/api/models")
async def get_models():
    """Return available Gemini models list."""
    return {"models": gemini_service.AVAILABLE_MODELS}


@app.get("/api/conversations")
async def list_conversations():
    """List all conversations ordered by recent activity."""
    conversations = db.list_conversations()
    return {"conversations": conversations}


@app.post("/api/conversations", status_code=status.HTTP_201_CREATED)
async def create_conversation(req: CreateConversationRequest):
    """Create a new conversation session."""
    conv = db.create_conversation(title=req.title or "New Chat", model=req.model or "gemini-1.5-flash")
    return conv


@app.get("/api/conversations/{conv_id}")
async def get_conversation(conv_id: str):
    """Get conversation details along with full message history."""
    conv = db.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@app.patch("/api/conversations/{conv_id}")
async def update_conversation(conv_id: str, req: UpdateConversationRequest):
    """Update conversation title."""
    updated = db.update_conversation_title(conv_id, req.title)
    if not updated:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return updated


@app.delete("/api/conversations/{conv_id}")
async def delete_conversation(conv_id: str):
    """Delete a conversation and all its messages."""
    deleted = db.delete_conversation(conv_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted", "id": conv_id}


@app.post("/api/chat/stream")
async def chat_stream(
    req: ChatStreamRequest,
    x_gemini_api_key: Optional[str] = Header(None, alias="x-gemini-api-key")
):
    """
    SSE Streaming endpoint for AI chat.
    Persists user message, streams chunks, and persists completed assistant response.
    """
    api_key = (req.api_key or "").strip() or (x_gemini_api_key or "").strip() or None

    conv_id = req.conversation_id
    is_new_chat = False

    # Check or initialize conversation
    if not conv_id:
        conv_id = str(uuid.uuid4())
        first_title = req.message[:35] + ("..." if len(req.message) > 35 else "")
        db.create_conversation(title=first_title, model=req.model or "gemini-1.5-flash", conversation_id=conv_id)
        is_new_chat = True
    else:
        existing = db.get_conversation(conv_id)
        if not existing:
            first_title = req.message[:35] + ("..." if len(req.message) > 35 else "")
            db.create_conversation(title=first_title, model=req.model or "gemini-1.5-flash", conversation_id=conv_id)
            is_new_chat = True

    # Get conversation history before adding current message
    existing_messages = db.get_messages(conv_id)

    # Save user message
    user_msg = db.add_message(
        conversation_id=conv_id,
        role="user",
        content=req.message
    )

    async def event_generator():
        # Yield metadata start event
        start_payload = {
            "type": "start",
            "conversation_id": conv_id,
            "user_message": user_msg,
            "is_new": is_new_chat,
        }
        yield f"data: {json.dumps(start_payload)}\n\n"

        assistant_chunks: List[str] = []
        try:
            async for chunk in gemini_service.stream_gemini_response(
                messages=existing_messages,
                prompt=req.message,
                model=req.model or "gemini-1.5-flash",
                system_prompt=req.system_prompt,
                api_key=api_key
            ):
                if chunk:
                    assistant_chunks.append(chunk)
                    chunk_payload = {
                        "type": "chunk",
                        "content": chunk
                    }
                    yield f"data: {json.dumps(chunk_payload)}\n\n"
        except Exception as exc:
            err_payload = {
                "type": "error",
                "error": str(exc)
            }
            yield f"data: {json.dumps(err_payload)}\n\n"

        # Save assistant message in DB
        full_assistant_content = "".join(assistant_chunks).strip() or "No response generated."
        asst_msg = db.add_message(
            conversation_id=conv_id,
            role="assistant",
            content=full_assistant_content
        )

        done_payload = {
            "type": "done",
            "conversation_id": conv_id,
            "message": asst_msg
        }
        yield f"data: {json.dumps(done_payload)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# Static Files / Frontend Serving
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Exclude /api paths from static routing
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        
        index_path = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        
        return JSONResponse(
            status_code=200,
            content={"message": "Gemini AI Chat Backend is running. Frontend directory is empty or index.html not found."}
        )
