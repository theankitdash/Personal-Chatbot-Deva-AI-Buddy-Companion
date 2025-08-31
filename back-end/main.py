import os
import time
import base64
import asyncio
import numpy as np
from io import BytesIO
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import traceback

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastrtc import Stream, AsyncAudioVideoStreamHandler, wait_for_item
import google.genai as genai
from pydantic import BaseModel
from PIL import Image

from db_connect import connect_db

from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# ---------- Helpers ----------
def encode_audio(data: np.ndarray) -> dict:
    return {
        "mime_type": "audio/pcm",
        "data": base64.b64encode(data.tobytes()).decode("UTF-8"),
    }

def encode_image(frame: np.ndarray) -> dict:
    with BytesIO() as output_bytes:
        pil_image = Image.fromarray(frame)
        pil_image.save(output_bytes, "JPEG")
        bytes_data = output_bytes.getvalue()
    return {
        "mime_type": "image/jpeg",
        "data": base64.b64encode(bytes_data).decode("utf-8")
    }

# ---------- Gemini Handler ----------
class GeminiHandler(AsyncAudioVideoStreamHandler):
    def __init__(self) -> None:
        super().__init__("mono", output_sample_rate=24000, input_sample_rate=16000)
        self.audio_queue = asyncio.Queue()
        self.video_queue = asyncio.Queue()
        self.session = None
        self.last_frame_time = 0
        self.quit = asyncio.Event()

    def copy(self):
        return GeminiHandler()

    async def start_up(self):
        client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
            http_options={"api_version": "v1alpha"}
        )
        config = {"response_modalities": ["AUDIO"]}
        async with client.aio.live.connect(
            model="gemini-2.0-flash-exp",
            config=config
        ) as session:
            self.session = session
            while not self.quit.is_set():
                turn = self.session.receive()
                try:
                    async for response in turn:
                        if data := response.data:
                            audio = np.frombuffer(data, dtype=np.int16).reshape(1, -1)
                            self.audio_queue.put_nowait(audio)
                except Exception:
                    break

    async def video_receive(self, frame: np.ndarray):
        """Receive video frames from client and send to Gemini every 1s"""
        self.video_queue.put_nowait(frame)
        if self.session and (time.time() - self.last_frame_time) > 1:
            self.last_frame_time = time.time()
            await self.session.send(input=encode_image(frame))

    async def video_emit(self):
        """Emit last received frame or placeholder"""
        frame = await wait_for_item(self.video_queue, 0.01)
        if frame is not None:
            return frame
        else:
            return np.zeros((100, 100, 3), dtype=np.uint8)

    async def receive(self, frame: tuple[int, np.ndarray]) -> None:
        """Receive audio from client and send to Gemini"""
        _, array = frame
        array = array.squeeze()
        if self.session:
            await self.session.send(input=encode_audio(array))

    async def emit(self):
        """Emit audio from Gemini to client"""
        array = await wait_for_item(self.audio_queue, 0.01)
        if array is not None:
            return (self.output_sample_rate, array)
        return array

    async def shutdown(self) -> None:
        if self.session:
            self.quit.set()
            await self.session.close()
            self.quit.clear()

# ---------- Stream ----------
stream = Stream(
    handler=GeminiHandler(),
    modality="audio-video",
    mode="send-receive"
)
stream.mount(app)

# Allow CORS for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- Models --------
class UserDetails(BaseModel):
    username: str
    name: str
    face_embedding: List[float]  # vector(512)

class Event(BaseModel):
    event_id: Optional[UUID]
    username: str
    type: str  # e.g., task, reminder, meeting
    description: str
    event_time: Optional[datetime] = None
    repeat_interval: Optional[str] = None
    priority: Optional[int] = 1
    status: Optional[str] = "pending"
    completed_at: Optional[datetime] = None

class UserKnowledge(BaseModel):
    knowledge_id: Optional[UUID]
    username: str
    fact: str
    category: Optional[str] = None
    importance: Optional[int] = 3

@app.post("/api/register_user")
async def register_user(
    username: str = Form(...),
    name: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        conn = await connect_db()
        image_bytes = await file.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        encodings = face_recognition.face_encodings(img)
        if not encodings:
            raise HTTPException(status_code=400, detail="No face detected")
        
        face_embedding = encodings[0].tolist()

        await conn.execute(
            """
            INSERT INTO user_details (username, name, face_embedding)
            VALUES ($1, $2, $3)
            ON CONFLICT (username)
            DO UPDATE SET name = EXCLUDED.name, face_embedding = EXCLUDED.face_embedding;
            """,
            username, name, face_embedding
        )
        await conn.close()

        return {"message": "User registered successfully", "username": username}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/verify_face")
async def verify_face(file: UploadFile = File(...)):
    try:
        conn = await connect_db()
        image_bytes = await file.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        encodings = face_recognition.face_encodings(img)
        if not encodings:
            raise HTTPException(status_code=400, detail="No face detected")
        
        face_embedding = np.array(encodings[0])

        # Get all users
        rows = await conn.fetch("SELECT username, face_embedding FROM user_details")
        await conn.close()

        for row in rows:
            db_embedding = np.array(row["face_embedding"])
            match = face_recognition.compare_faces([db_embedding], face_embedding)[0]
            if match:
                return {"message": "Login successful", "username": row["username"]}

        raise HTTPException(status_code=401, detail="No matching face found")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user_details/")
async def add_user(details: UserDetails):
    
    try:
        conn = await connect_db()
        await conn.execute(
            """
            INSERT INTO user_details (username, name, face_embedding)
            VALUES ($1, $2, $3)
            ON CONFLICT (username) 
            DO UPDATE SET 
                name = EXCLUDED.name, 
                face_embedding = EXCLUDED.face_embedding;
            """, 
            details.username, details.name, details.face_embedding
        )

        await conn.close()

        return {"message": "User details saved successfully"}
    except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail="Failed to save personal details.") 
    
@app.post("/api/events/")
async def add_event(event: Event):
    try:
        conn = await connect_db()
        await conn.execute(
            """
            INSERT INTO events (
                username, type, description, event_time,
                repeat_interval, priority, status, completed_at
            )
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
            """,
            event.username, event.type, event.description,
            event.event_time, event.repeat_interval,
            event.priority, event.status, event.completed_at
        )
        await conn.close()
        return {"message": "Event saved successfully"}
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to save event.")
    
@app.post("/api/user_knowledge/")
async def add_knowledge(knowledge: UserKnowledge):
    try:
        conn = await connect_db()
        await conn.execute(
            """
            INSERT INTO user_knowledge (username, fact, category, importance)
            VALUES ($1,$2,$3,$4)
            """,
            knowledge.username, knowledge.fact, knowledge.category, knowledge.importance
        )
        await conn.close()
        return {"message": "Knowledge saved successfully"}
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to save knowledge.")    

@app.get("/api/user_details/{username}")
async def get_user_details(username: str):
    try:
        conn = await connect_db()
        user = await conn.fetchrow(
            "SELECT username, name, face_embedding FROM user_details WHERE username=$1",
            username
        )
        await conn.close()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return dict(user)

    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Error fetching user details.")

@app.get("/api/events/{username}")
async def get_events(username: str):
    try:
        conn = await connect_db()
        events = await conn.fetch(
            "SELECT * FROM events WHERE username=$1 ORDER BY event_time DESC",
            username
        )
        await conn.close()

        return [dict(e) for e in events]

    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Error fetching events.")

@app.get("/api/user_knowledge/{username}")
async def get_knowledge(username: str):
    try:
        conn = await connect_db()
        knowledge = await conn.fetch(
            "SELECT * FROM user_knowledge WHERE username=$1 ORDER BY importance DESC",
            username
        )
        await conn.close()

        return [dict(k) for k in knowledge]

    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Error fetching knowledge.")

@app.delete("/api/events/{event_id}")
async def delete_event(event_id: UUID):
    try:
        conn = await connect_db()
        result = await conn.execute("DELETE FROM events WHERE event_id=$1", event_id)
        await conn.close()

        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Event not found")

        return {"message": "Event deleted successfully"}
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to delete event.")
    
# Run the application using uvicorn main:app --reload