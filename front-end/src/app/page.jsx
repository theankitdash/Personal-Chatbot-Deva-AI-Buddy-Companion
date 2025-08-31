"use client";

import React, { useState, useEffect, useRef } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar } from "@/components/ui/avatar";

export default function FaceAuthAIBuddy() {
  const [mode, setMode] = useState("login"); // "login" or "register"
  const [username, setUsername] = useState("");
  const [name, setName] = useState("");
  const [verifiedUser, setVerifiedUser] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [transcript, setTranscript] = useState([]);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const videoRef = useRef();

  // Start camera
  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ video: true })
      .then(stream => { videoRef.current.srcObject = stream; })
      .catch(() => setMsg("❌ Camera access denied"));
  }, []);

  // Capture current frame from webcam
  const captureFrame = async () => {
    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(videoRef.current, 0, 0);
    return new Promise(resolve => canvas.toBlob(resolve, "image/jpeg"));
  };

  // Handle registration
  const registerUser = async () => {
    if (!username.trim() || !name.trim()) {
      setMsg("⚠ Please enter username and name");
      return;
    }
    setLoading(true);
    setMsg("");

    const blob = await captureFrame();
    const formData = new FormData();
    formData.append("username", username);
    formData.append("name", name);
    formData.append("file", blob, "face.jpg");

    try {
      const res = await fetch("/api/register_user", {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Registration failed");
      setMsg("✅ Registration successful! Please switch to login.");
    } catch (err) {
      setMsg("❌ " + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Handle login
  const verifyFace = async () => {
    setLoading(true);
    setMsg("");

    const blob = await captureFrame();
    const formData = new FormData();
    formData.append("file", blob, "face.jpg");

    try {
      const res = await fetch("/api/verify_face", {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Face not recognized");
      setVerifiedUser(data.username);
      setMsg("");
    } catch (err) {
      setMsg("❌ " + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Fetch user data after login
  useEffect(() => {
    if (!verifiedUser) return;

    fetch(`/api/user_details/${verifiedUser}`)
      .then(res => res.json())
      .then(data => setName(data.name))
      .catch(console.error);

    fetch(`/api/events/${verifiedUser}`)
      .then(res => res.json())
      .then(data => {
        setTasks(data.filter(e => e.type === "task").map(e => e.description));
        setReminders(data.filter(e => e.type === "reminder").map(e => e.description));
      })
      .catch(console.error);

    const ws = new WebSocket("ws://localhost:8000/ws/rtc");
    ws.onmessage = event => {
      const data = JSON.parse(event.data);
      if (data.type === "transcript") {
        setTranscript(prev => [...prev, { sender: data.sender, text: data.text }]);
      }
    };
    return () => ws.close();
  }, [verifiedUser]);

  // If verified, show AI Buddy Dashboard
  if (verifiedUser) {
    return (
      <div className="grid grid-cols-3 gap-4 p-4 min-h-screen bg-gray-50">
        {/* Left Sidebar */}
        <div className="col-span-1 space-y-4">
          <Card>
            <CardContent className="flex items-center space-x-4 p-4">
              <Avatar><img src="/avatar.png" alt="User" /></Avatar>
              <div>
                <p className="text-lg font-semibold text-black">{name}</p>
                <p className="text-sm text-gray-500 text-black">AI Buddy User</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <h2 className="text-md font-semibold mb-2 text-black">Upcoming Tasks</h2>
              <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                {tasks.length > 0 ? tasks.map((task, idx) => <li key={idx}>{task}</li>) : <li>No tasks found</li>}
              </ul>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <h2 className="text-md font-semibold mb-2 text-black">Reminders</h2>
              <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                {reminders.length > 0 ? reminders.map((rem, idx) => <li key={idx}>{rem}</li>) : <li>No reminders found</li>}
              </ul>
            </CardContent>
          </Card>
        </div>

        {/* Right Side - Live Feed with Transcript */}
        <div className="col-span-2 relative">
          <Card className="w-full h-full flex flex-col">
            <CardContent className="p-4 flex flex-col h-full relative flex-grow">
              <h2 className="text-lg font-semibold mb-4 text-black">Talk to your AI Buddy</h2>
              <div className="flex-grow bg-black rounded-xl overflow-hidden mb-4 relative">
                <video id="liveVideo" autoPlay muted playsInline className="w-full h-full object-cover"></video>
                {/* Transcript Overlay */}
                <div className="absolute bottom-2 right-2 bg-white/80 p-2 rounded-md max-w-xs text-sm overflow-y-auto max-h-48">
                  {transcript.map((line, idx) => (
                    <div key={idx} className={line.sender === "user" ? "text-blue-600" : "text-green-600"}>
                      <strong>{line.sender === "user" ? "You:" : "AI:"}</strong> {line.text}
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // If not verified, show login/register screen
  return (
    <div className="flex flex-col items-center justify-center min-h-screen space-y-4">
      <video ref={videoRef} autoPlay playsInline className="rounded-lg border w-80" />
      {mode === "register" && (
        <>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={e => setUsername(e.target.value)}
            className="border p-2 w-80"
          />
          <input
            type="text"
            placeholder="Full Name"
            value={name}
            onChange={e => setName(e.target.value)}
            className="border p-2 w-80"
          />
        </>
      )}
      <button
        onClick={mode === "register" ? registerUser : verifyFace}
        disabled={loading}
        className="bg-blue-600 text-white px-4 py-2 rounded-lg w-80"
      >
        {loading ? "Processing..." : mode === "register" ? "Register" : "Login"}
      </button>
      <button
        onClick={() => setMode(mode === "register" ? "login" : "register")}
        className="text-blue-500 underline"
      >
        {mode === "register" ? "Already have an account? Login" : "New user? Register"}
      </button>
      {msg && <p className="text-center text-sm mt-2">{msg}</p>}
    </div>
  );
}
