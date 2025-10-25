from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timedelta
import asyncio
import os

app = FastAPI(title="Stateless Anonymous Chat Proxy (with static frontend)")

# Serve built frontend from ./frontend/dist (SPA). Ensure you build frontend into this folder.
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path), name="static")

# Config
RATE_LIMIT_WINDOW = timedelta(minutes=1)
MAX_REQUESTS_PER_WINDOW = int(os.getenv("MAX_REQ_PER_MIN", "40"))
_rate_table = {}  # ip -> {"count": int, "window_start": datetime}

class MessageIn(BaseModel):
    message: str

class MessageOut(BaseModel):
    reply: str

def _cleanup_rate_table():
    now = datetime.utcnow()
    to_delete = []
    for ip, info in list(_rate_table.items()):
        if info["window_start"] + RATE_LIMIT_WINDOW < now:
            to_delete.append(ip)
    for ip in to_delete:
        del _rate_table[ip]

@app.on_event("startup")
async def start_cleanup_loop():
    async def loop():
        while True:
            _cleanup_rate_table()
            await asyncio.sleep(30)
    asyncio.create_task(loop())

def moderation_check(text: str) -> bool:
    """
    Базовый модератор — замените или расширьте.
    """
    if not text or not text.strip():
        return False
    low = text.lower()
    blocked = [
        "how to kill", "bomb", "explode", "manufacture weapon",
        "детонац", "взорв", "как убить"
    ]
    for b in blocked:
        if b in low:
            return False
    return True

async def call_model(user_message: str) -> str:
    """
    Замените на вызов вашей локальной GPT4All / LLM.
    Важно: не логировать содержимое сообщений при необходимости приватности.
    """
    # Заглушка — эхо
    await asyncio.sleep(0.02)
    return f"(placeholder) {user_message}"

def _check_rate_limit(client_ip: str):
    now = datetime.utcnow()
    info = _rate_table.get(client_ip)
    if info is None or info["window_start"] + RATE_LIMIT_WINDOW < now:
        _rate_table[client_ip] = {"count": 1, "window_start": now}
        return
    if info["count"] + 1 > MAX_REQUESTS_PER_WINDOW:
        raise HTTPException(status_code=429, detail="Too many requests")
    info["count"] += 1

def _get_client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

@app.post("/api/message", response_model=MessageOut)
async def message_endpoint(req: Request, payload: MessageIn):
    client_ip = _get_client_ip(req)
    _check_rate_limit(client_ip)

    if not moderation_check(payload.message):
        raise HTTPException(status_code=400, detail="Message failed moderation")

    reply = await call_model(payload.message)
    return MessageOut(reply=reply)

# If frontend exists, let SPA handle routing: fallback to index.html for unknown GET paths
@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path, media_type="text/html")
    return JSONResponse({"detail": "Not found"}, status_code=404)