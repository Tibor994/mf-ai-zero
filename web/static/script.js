const chatBox = document.getElementById("chat-box");
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const clearBtn = document.getElementById("clear-btn");
const temperatureSelect = document.getElementById("temperature-select");
const sentencesSelect = document.getElementById("sentences-select");
const typingIndicator = document.getElementById("typing-indicator");

function addMessage(text, sender, isError) {
  const row = document.createElement("div");
  row.className = "message " + sender + (isError ? " error" : "");

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  row.appendChild(bubble);
  chatBox.appendChild(row);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function setBusy(busy) {
  messageInput.disabled = busy;
  sendBtn.disabled = busy;
  typingIndicator.classList.toggle("hidden", !busy);
}

async function sendMessage() {
  const text = messageInput.value.trim();
  if (!text) {
    return;
  }

  addMessage(text, "user");
  messageInput.value = "";
  setBusy(true);

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        temperature: parseFloat(temperatureSelect.value),
        sentences: parseInt(sentencesSelect.value, 10),
      }),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      addMessage(errData.error || "Hiba történt a szerverrel.", "ai", true);
      return;
    }

    const data = await response.json();
    addMessage(data.reply, "ai");
  } catch (err) {
    addMessage("Nem sikerült elérni a szervert. Fut a python web/app.py?", "ai", true);
  } finally {
    setBusy(false);
    messageInput.focus();
  }
}

sendBtn.addEventListener("click", sendMessage);

messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
});

clearBtn.addEventListener("click", async () => {
  chatBox.innerHTML = "";
  addMessage(
    "Beszélgetés törölve. Kezdjünk újra!",
    "ai"
  );
  try {
    await fetch("/api/clear", { method: "POST" });
  } catch (err) {
    // a törlés a felületen akkor is működik, ha a naplózás nem sikerül
  }
});

messageInput.focus();
