from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from db_connect import connect_db
from uuid import UUID
from datetime import datetime

# -------- App Init --------
app = FastAPI()

# -------- Models --------
class UserDetails(BaseModel):
    username: str
    name: str
    face_embedding: List[float]  # vector(512)

class Memory(BaseModel):
    memory_id: Optional[UUID]
    username: str  # link to user
    memory_type: str
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = []
    importance: Optional[int] = 1
    embedding: Optional[List[float]] = None  # vector for FAISS
    memory_time: Optional[datetime] = None
    remind_at: Optional[datetime] = None
    repeat_interval: Optional[str] = None
    completed: Optional[bool] = False
    priority: Optional[int] = 1

# -------- User Endpoints --------
@app.get("/api/users")
async def get_users():
    conn = await connect_db()
    try:
        rows = await conn.fetch("SELECT username, name, face_embedding FROM user_details")
        return {
            "users": [
                {
                    "username": r["username"],
                    "name": r["name"],
                    "face_embedding": list(r["face_embedding"]) if r["face_embedding"] else None
                }
                for r in rows
            ]
        }
    finally:
        await conn.close()

@app.post("/api/users")
async def add_user(user: UserDetails):
    conn = await connect_db()
    try:
        await conn.execute("""
            INSERT INTO user_details (username, name, face_embedding)
            VALUES ($1, $2, $3)
            ON CONFLICT (username) DO UPDATE
            SET name = EXCLUDED.name,
                face_embedding = EXCLUDED.face_embedding
        """, user.username, user.name, user.face_embedding)
        return {"status": "success"}
    finally:
        await conn.close()

# -------- Memory Endpoints --------
@app.get("/api/memory")
async def get_all_memories():
    conn = await connect_db()
    try:
        rows = await conn.fetch("SELECT * FROM memory ORDER BY timestamp DESC")
        return {"memory": [dict(r) for r in rows]}
    finally:
        await conn.close()

@app.get("/api/memory/{memory_id}")
async def get_memory(memory_id: UUID):
    conn = await connect_db()
    try:
        row = await conn.fetchrow("SELECT * FROM memory WHERE memory_id = $1", memory_id)
        if not row:
            raise HTTPException(status_code=404, detail="Memory not found")
        return dict(row)
    finally:
        await conn.close()

@app.post("/api/memory")
async def add_memory(memory: Memory):
    conn = await connect_db()
    try:
        await conn.execute("""
            INSERT INTO memory (
                username, memory_type, title, content, tags, importance,
                embedding, memory_time, remind_at, repeat_interval, completed, priority
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        """, memory.username, memory.memory_type, memory.title, memory.content, memory.tags,
            memory.importance, memory.embedding, memory.memory_time,
            memory.remind_at, memory.repeat_interval, memory.completed, memory.priority)
        return {"status": "success"}
    finally:
        await conn.close()

@app.put("/api/memory/{memory_id}")
async def update_memory(memory_id: UUID, memory: Memory):
    conn = await connect_db()
    try:
        await conn.execute("""
            UPDATE memory
            SET memory_type = $1, title = $2, content = $3, tags = $4,
                importance = $5, embedding = $6, memory_time = $7,
                remind_at = $8, repeat_interval = $9, completed = $10, 
                priority = $11, updated_at = CURRENT_TIMESTAMP
            WHERE memory_id = $12
        """, memory.memory_type, memory.title, memory.content, memory.tags,
            memory.importance, memory.embedding, memory.memory_time, memory.remind_at, 
            memory.repeat_interval, memory.completed, memory.priority, memory_id)
        return {"status": "success"}
    finally:
        await conn.close()

@app.delete("/api/memory/{memory_id}")
async def delete_memory(memory_id: UUID):
    conn = await connect_db()
    try:
        await conn.execute("DELETE FROM memory WHERE memory_id = $1", memory_id)
        return {"status": "deleted"}
    finally:
        await conn.close()

# -------- WebRTC Signaling Placeholder --------
offer_sdp = None

@app.get("/api/webrtc_offer")
async def get_offer():
    global offer_sdp
    return offer_sdp or {"sdp": "", "type": "offer"}

class WebRTCAnswer(BaseModel):
    answer: dict

@app.post("/api/webrtc_answer")
async def receive_answer(answer: WebRTCAnswer):
    print("Received WebRTC answer:", answer.answer)
    return {"status": "received"}


# Run the application using uvicorn main:app --reload