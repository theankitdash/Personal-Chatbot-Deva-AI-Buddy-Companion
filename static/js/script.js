const video = document.getElementById('liveVideo');

let mediaStream;

async function startMediaStream() {
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: true,
      audio: true
    });

    // Set the video stream
    video.srcObject = mediaStream;

    // Optional: play video
    await video.play();

    // Get audio track for processing (e.g., to send to Whisper or speech-to-text backend)
    const audioTracks = mediaStream.getAudioTracks();
    if (audioTracks.length > 0) {
      const audioStream = new MediaStream([audioTracks[0]]);
      
      // Pass audioStream to your LLM voice pipeline
      handleAudioStream(audioStream);
    }

  } catch (error) {
    console.error("Error accessing camera or microphone:", error);
  }
}

// Placeholder: your function to handle audio input
function handleAudioStream(audioStream) {
  console.log("Audio stream is ready for LLM processing");

  // Example: stream to Whisper or any STT backend
  // Then take transcription and send to LLM
  // Then use TTS to speak back the response

  // ⚠️ This part depends on your architecture (e.g., WebSocket to backend)
}

startMediaStream();
