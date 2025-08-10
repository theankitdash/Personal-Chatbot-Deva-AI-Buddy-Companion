import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function AIBuddyDashboard() {
  return (
    <div className="grid grid-cols-3 gap-4 p-4 min-h-screen bg-gray-50">
      {/* Left Sidebar */}
      <div className="col-span-1 space-y-4">
        {/* User Details */}
        <Card>
          <CardContent className="flex items-center space-x-4 p-4">
            <Avatar>
              <img src="/avatar.png" alt="User" />
            </Avatar>
            <div>
              <p className="text-lg font-semibold text-black">Ankit Dash</p>
              <p className="text-sm text-gray-500">AI Enthusiast</p>
            </div>
          </CardContent>
        </Card>

        {/* Upcoming Tasks */}
        <Card>
          <CardContent className="p-4">
            <h2 className="text-md font-semibold mb-2 text-black">Upcoming Tasks</h2>
            <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
              <li>Finish AI model training</li>
              <li>Deploy FastAPI backend</li>
              <li>Write documentation</li>
            </ul>
          </CardContent>
        </Card>

        {/* Reminders */}
        <Card>
          <CardContent className="p-4">
            <h2 className="text-md font-semibold mb-2 text-black">Reminders</h2>
            <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
              <li>Call with client at 3 PM</li>
              <li>Submit demo by tonight</li>
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* Right Side - Live Feed */}
      <div className="col-span-2">
        <Card className="w-full h-full">
          <CardContent className="p-4 flex flex-col h-full">
            <h2 className="text-lg font-semibold mb-4 text-black">Talk to your AI Buddy</h2>
            <div className="flex-grow bg-black rounded-xl overflow-hidden mb-4">
              <video
                id="liveVideo"
                autoPlay
                muted
                playsInline
                className="w-full h-full object-cover"
              ></video>
            </div>
            <div className="flex gap-2">
              <Input placeholder="Type a message..." className="flex-grow" />
              <Button>Send</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
