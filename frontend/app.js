let lastSummary = "";

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
      speak(data.summary);
    }
  } catch (error) {
    console.error("Could not fetch latest summary:", error);
  }
}

document.getElementById("startButton").addEventListener("click", () => {
  speak("SpeakEasy is now listening for Slack alerts.");
  setInterval(fetchLatestSummary, 3000);
});
