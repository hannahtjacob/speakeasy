let lastSummary = "";
let drivingModeOn = true;

function speak(text) {
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1;
  utterance.pitch = 1;
  window.speechSynthesis.speak(utterance);
}

async function fetchLatestSummary() {
  try {
    const response = await fetch("http://localhost:3000/api/latest-summary");
    const data = await response.json();

    if (data.summary && data.summary !== lastSummary) {
      lastSummary = data.summary;
      document.getElementById("summaryText").textContent = data.summary;

      if (!drivingModeOn) {
        return;
      }

      if (data.priority) {
        speak("Priority alert. " + data.summary);
      } else {
        speak(data.summary);
      }
    }
  } catch (error) {
    console.error("Could not fetch latest summary:", error);
  }
}

document.getElementById("startButton").addEventListener("click", () => {
  speak("SpeakEasy is now listening for Slack alerts.");
  setInterval(fetchLatestSummary, 3000);
});

const drivingModeButton = document.getElementById("drivingModeButton");

drivingModeButton.addEventListener("click", () => {
  drivingModeOn = !drivingModeOn;
  drivingModeButton.textContent = `Driving Mode: ${drivingModeOn ? "ON" : "OFF"}`;
  drivingModeButton.classList.toggle("off", !drivingModeOn);
});

async function askQuestion() {
  const question = document.getElementById("questionInput").value;

  const response = await fetch("http://localhost:3000/api/ask", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ question })
  });

  const data = await response.json();
  document.getElementById("answerText").textContent = data.answer;
  speak(data.answer);
}

document.getElementById("askButton").addEventListener("click", askQuestion);
