document.addEventListener("DOMContentLoaded", () => {
  fetchTasksAndReminders();
  startLiveVideoFeed();
});

/** Fetch tasks and reminders from FastAPI backend */
async function fetchTasksAndReminders() {
  try {
    const response = await fetch("http://localhost:8000/api/tasks");
    if (!response.ok) throw new Error("Failed to fetch tasks");

    const data = await response.json();
    const taskListDiv = document.getElementById("taskList");
    taskListDiv.innerHTML = ""; // Clear existing

    data.tasks.forEach((task) => {
      const taskDiv = document.createElement("div");
      taskDiv.className = "task-item";
      taskDiv.textContent = `🔔 ${task.title} - ${task.time}`;
      taskListDiv.appendChild(taskDiv);
    });
  } catch (error) {
    console.error("Error fetching tasks:", error);
  }
}

/** Start live video feed using WebRTC (FastRTC signaling assumed) */
async function startLiveVideoFeed() {
  const video = document.getElementById("liveVideo");

  const peerConnection = new RTCPeerConnection();

  peerConnection.ontrack = (event) => {
    video.srcObject = event.streams[0];
  };

  try {
    // Fetch offer from FastRTC server
    const offerResponse = await fetch("http://localhost:8000/webrtc_offer");
    const offer = await offerResponse.json();

    await peerConnection.setRemoteDescription(new RTCSessionDescription(offer));

    // Create answer
    const answer = await peerConnection.createAnswer();
    await peerConnection.setLocalDescription(answer);

    // Send answer back to server
    await fetch("http://localhost:8000/webrtc_answer", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ answer: peerConnection.localDescription })
    });

    console.log("WebRTC connection established.");
  } catch (error) {
    console.error("Failed to start live video feed:", error);
  }
}
