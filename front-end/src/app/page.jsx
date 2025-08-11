"use client";

import React, { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar } from "@/components/ui/avatar";

export default function AIBuddyDashboard() {
  const [user, setUser] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [transcript, setTranscript] = useState([]);

  useEffect(() => {
    fetch("/api/user").then(res => res.json()).then(setUser);
    fetch("/api/tasks").then(res => res.json()).then(setTasks);
    fetch("/api/reminders").then(res => res.json()).then(setReminders);
  }, []);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/rtc");
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "transcript") {
        setTranscript(prev => [...prev, { sender: data.sender, text: data.text }]);
      }
    };
    return () => ws.close();
  }, []);

  return (
    <div className="grid grid-cols-3 gap-4 p-4 min-h-screen bg-gray-50">
      {/* Left Sidebar */}
      <div className="col-span-1 space-y-4">
        <Card>
          <CardContent className="flex items-center space-x-4 p-4">
            <Avatar>
              <img src="/avatar.png" alt="User" />
            </Avatar>
            <div>
              <p className="text-lg font-semibold">{user?.name}</p>
              <p className="text-sm text-gray-500">{user?.role}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <h2 className="text-md font-semibold mb-2">Upcoming Tasks</h2>
            <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
              {tasks.map((task, idx) => <li key={idx}>{task}</li>)}
            </ul>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <h2 className="text-md font-semibold mb-2">Reminders</h2>
            <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
              {reminders.map((rem, idx) => <li key={idx}>{rem}</li>)}
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* Right Side - Live Feed with Transcript */}
      <div className="col-span-2 relative">
        <Card className="w-full h-full">
          <CardContent className="p-4 flex flex-col h-full relative">
            <h2 className="text-lg font-semibold mb-4">Talk to your AI Buddy</h2>
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
