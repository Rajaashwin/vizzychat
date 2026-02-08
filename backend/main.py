"""
Vizzy Chat - AI Chat & Image Generation Backend
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import os
from datetime import datetime
import json
import httpx

app = FastAPI(title="Vizzy Chat API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session storage
sessions: Dict[str, List[dict]] = {}

class ChatRequest(BaseModel):
    message: str
    mode: str = "chat"
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    mode: str
    session_id: str
    timestamp: str


@app.get("/")
async def root():
    return {
        "message": "Vizzy Chat API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/chat (POST)",
            "health": "/health (GET)"
        }
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint that handles both text generation and image generation
    """
    
    # Validate inputs
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    if request.mode not in ["chat", "image"]:
        raise HTTPException(status_code=400, detail="Mode must be 'chat' or 'image'")
    
    session_id = request.session_id or f"session-{datetime.now().timestamp()}"
    
    # Initialize session if new
    if session_id not in sessions:
        sessions[session_id] = []
    
    try:
        if request.mode == "chat":
            response_text = await generate_text(request.message)
        else:
            response_text = await generate_image(request.message)
        
        # Store in session
        sessions[session_id].append({
            "timestamp": datetime.now().isoformat(),
            "mode": request.mode,
            "message": request.message,
            "response": response_text
        })
        
        return ChatResponse(
            response=response_text,
            mode=request.mode,
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def generate_text(prompt: str) -> str:
    """Generate text using OpenRouter API"""
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return f"Echo: {prompt}"  # Fallback
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "http://localhost",
                },
                json={
                    "model": "openai/gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        # Fallback response
        return f"Response to '{prompt}': I'm a demo AI assistant. Please configure API keys for real responses."


async def generate_image(prompt: str) -> str:
    """Generate image using fallback chain"""
    
    # Try HuggingFace first
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    if hf_token:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2",
                    headers={"Authorization": f"Bearer {hf_token}"},
                    content=json.dumps({"inputs": prompt}),
                    timeout=30.0
                )
                response.raise_for_status()
                # Response is image bytes
                import base64
                image_data = base64.b64encode(response.content).decode()
                return f"data:image/png;base64,{image_data}"
        except Exception as e:
            pass  # Continue to next option
    
    # Fallback: Return SVG placeholder
    import urllib.parse
    encoded_prompt = urllib.parse.quote(prompt[:50])
    return f"https://via.placeholder.com/500x500?text={encoded_prompt}"


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session history"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "history": sessions[session_id]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
