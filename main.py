from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Serve static files (HTML, JS, CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ----- Task Reminder Endpoint -----
class Task(BaseModel):
    title: str
    time: str


@app.get("/api/tasks")
async def get_tasks():
    tasks = [
        {"title": "Morning Walk", "time": "6:30 AM"},
        {"title": "Team Meeting", "time": "10:00 AM"},
        {"title": "Lunch", "time": "1:00 PM"},
        {"title": "Call Mom", "time": "8:00 PM"}
    ]
    return {"tasks": tasks}


# ----- WebRTC Signaling -----
# Simulating FastRTC endpoints for frontend

offer_sdp = None

@app.get("/webrtc_offer")
async def get_offer():
    global offer_sdp
    # In real FastRTC, this would generate a real offer
    return offer_sdp or {"sdp": "", "type": "offer"}


class WebRTCAnswer(BaseModel):
    answer: dict


@app.post("/webrtc_answer")
async def receive_answer(answer: WebRTCAnswer):
    # Save or forward answer SDP for FastRTC
    print("Received WebRTC answer:", answer.answer)
    return {"status": "received"}


# ----- Home route -----
@app.get("/")
async def serve_home():
    return FileResponse("static/index.html")