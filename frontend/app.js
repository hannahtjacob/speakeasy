let lastAlertTs = "";
let listeningInterval = null;

function speak(text, onFinished) {
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1;
  utterance.pitch = 1;
  if (onFinished) {
    let finished = false;
    const finishOnce = () => {
      if (!finished) {
        finished = true;
        onFinished();
      }
    };
    utterance.onend = finishOnce;
    utterance.onerror = finishOnce;
  }
  window.speechSynthesis.speak(utterance);
}

function presentAlert(alert) {
  const channelName = alert.channel_name || alert.channel || "Slack";
  const userName = alert.user_name || "Someone";
  const spokenChannel = channelName.replaceAll("-", " ");
  const alertList = document.getElementById("alertList");
  const alertItem = document.createElement("li");
  const alertSource = document.createElement("p");
  const alertMessage = document.createElement("p");

  alertItem.className = "alertItem";
  alertSource.className = "alertSource";
  alertMessage.className = "alertMessage";
  alertSource.textContent = `${userName} in #${channelName}`;
  alertMessage.textContent = alert.text;
  alertItem.append(alertSource, alertMessage);
  alertList.appendChild(alertItem);
  document.getElementById("emptyAlerts").hidden = true;

  speak(`From ${userName} in ${spokenChannel}. ${alert.text}`, () => {
    setTimeout(() => {
      alertItem.remove();
      document.getElementById("emptyAlerts").hidden = alertList.children.length > 0;
    }, 10000);
  });
}

async function fetchAlerts(speakNewAlerts = true) {
  try {
    const query = lastAlertTs ? `?after=${encodeURIComponent(lastAlertTs)}` : "";
    const response = await fetch(`http://localhost:3000/api/alerts${query}`);
    const data = await response.json();

    if (speakNewAlerts) {
      data.alerts.forEach(presentAlert);
    }
    lastAlertTs = data.latest_ts || lastAlertTs;
  } catch (error) {
    console.error("Could not fetch alerts:", error);
  }
}

async function loadChannels() {
  try {
    const response = await fetch("http://localhost:3000/api/channels");
    const data = await response.json();
    const channelSelect = document.getElementById("channelSelect");

    data.channels.forEach((channel) => {
      const option = document.createElement("option");
      option.value = channel.id;
      option.textContent = `#${channel.name}`;
      channelSelect.appendChild(option);
    });
  } catch (error) {
    console.error("Could not load channels:", error);
  }
}

async function askQuestion() {
  const askButton = document.getElementById("askButton");
  if (askButton.disabled) {
    return;
  }

  const channel = document.getElementById("channelSelect").value;
  const question = document.getElementById("questionInput").value.trim();
  const answerText = document.getElementById("answerText");

  if (!question) {
    answerText.textContent = "Enter a question.";
    return;
  }

  askButton.disabled = true;
  askButton.textContent = "Answering...";

  try {
    const response = await fetch("http://localhost:3000/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ channel, question })
    });
    const data = await response.json();

    answerText.textContent = data.answer;
    if (response.ok) {
      askButton.textContent = "Speaking...";
      speak(data.answer, () => {
        askButton.disabled = false;
        askButton.textContent = "Ask";
      });
    } else {
      askButton.disabled = false;
      askButton.textContent = "Ask";
    }
  } catch (error) {
    answerText.textContent = "SpeakEasy could not answer right now.";
    askButton.disabled = false;
    askButton.textContent = "Ask";
    console.error("Could not ask SpeakEasy:", error);
  }
}

document.getElementById("startButton").addEventListener("click", async (event) => {
  const button = event.currentTarget;

  if (listeningInterval) {
    clearInterval(listeningInterval);
    listeningInterval = null;
    window.speechSynthesis.cancel();
    button.textContent = "Start Listening";
    button.setAttribute("aria-pressed", "false");
    return;
  }

  button.disabled = true;
  await fetchAlerts(false);
  listeningInterval = setInterval(fetchAlerts, 1000);
  button.textContent = "Stop Listening";
  button.setAttribute("aria-pressed", "true");
  button.disabled = false;
  speak("SpeakEasy is now listening for Slack alerts.");
});

document.getElementById("askButton").addEventListener("click", askQuestion);
document.getElementById("questionInput").addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    askQuestion();
  }
});

loadChannels();
