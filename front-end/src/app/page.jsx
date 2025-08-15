"use client";

import React, { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar } from "@/components/ui/avatar";

export default function AIBuddyDashboard() {
  const [user, setUser] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [transcript, setTranscript] = useState([]);
  const username = "ankit";

  useEffect(() => {
    fetch(`/api/user_details/${username}`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch user details");
        return res.json();
      })
      .then((data) => setUser(data))
      .catch((err) => console.error(err));

    fetch(`/api/events/${username}`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch events");
        return res.json();
      })
      .then((data) => {
        const taskItems = data.filter((e) => e.type === "task").map((e) => e.description);
        const reminderItems = data.filter((e) => e.type === "reminder").map((e) => e.description);
        setTasks(taskItems);
        setReminders(reminderItems);
      })
      .catch((err) => console.error(err));

  }, [username]);


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
            <Avatar><img src="/avatar.png" alt="User" /></Avatar>
            <div>
              <p className="text-lg font-semibold text-black">{user?.name}</p>
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
