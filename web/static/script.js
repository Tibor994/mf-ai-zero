const chatBox = document.getElementById("chat-box");
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const clearBtn = document.getElementById("clear-btn");
const temperatureSelect = document.getElementById("temperature-select");
const sentencesSelect = document.getElementById("sentences-select");
const typingIndicator = document.getElementById("typing-indicator");

const memoryToggleBtn = document.getElementById("memory-toggle-btn");
const memoryPanel = document.getElementById("memory-panel");
const memorySearchInput = document.getElementById("memory-search-input");
const memoryCategoryFilter = document.getElementById("memory-category-filter");
const memorySearchBtn = document.getElementById("memory-search-btn");
const memoryRefreshBtn = document.getElementById("memory-refresh-btn");
const memoryList = document.getElementById("memory-list");
const memorySaveCategory = document.getElementById("memory-save-category");
const memorySaveText = document.getElementById("memory-save-text");
const memorySaveBtn = document.getElementById("memory-save-btn");

const MEMORY_CATEGORY_LABELS = {
  user_preference: "Kedvelés",
  user_fact: "Tény",
  project_fact: "Projekt-tény",
  current_goal: "Cél",
  correction: "Javítás",
};

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

// ---------------------------------------------------------------------------
// v1.0.1 memória-kezelő panel - listázás/keresés/törlés/kézi mentés.
// Semmi itt nem fut le automatikusan a chat közben - csak a felhasználó
// explicit kattintására (nyit/keres/töröl/ment).
// ---------------------------------------------------------------------------

function formatMemoryDate(value) {
  if (!value) return "";
  return value.slice(0, 16).replace("T", " ");
}

function renderMemories(memories, emptyText) {
  memoryList.innerHTML = "";
  if (!memories || memories.length === 0) {
    const empty = document.createElement("p");
    empty.className = "memory-empty";
    empty.textContent = emptyText || "Nincs találat.";
    memoryList.appendChild(empty);
    return;
  }

  memories.forEach((mem) => {
    const card = document.createElement("div");
    card.className = "memory-card" + (mem.active ? "" : " inactive");

    const meta = document.createElement("div");
    meta.className = "memory-meta";

    const catSpan = document.createElement("span");
    catSpan.className = "memory-category";
    catSpan.textContent = MEMORY_CATEGORY_LABELS[mem.category] || mem.category;
    meta.appendChild(catSpan);

    const statusSpan = document.createElement("span");
    statusSpan.className = "memory-status" + (mem.active ? " active" : " inactive");
    statusSpan.textContent = mem.active ? "aktív" : "inaktív";
    meta.appendChild(statusSpan);

    const text = document.createElement("div");
    text.className = "memory-text";
    text.textContent = mem.text;

    const footer = document.createElement("div");
    footer.className = "memory-footer";

    const date = document.createElement("span");
    date.className = "memory-date";
    date.textContent = formatMemoryDate(mem.updated_at || mem.created_at);
    footer.appendChild(date);

    if (mem.active) {
      const delBtn = document.createElement("button");
      delBtn.type = "button";
      delBtn.className = "btn btn-ghost btn-small";
      delBtn.textContent = "Deaktiválás";
      delBtn.addEventListener("click", () => deleteMemory(mem.id));
      footer.appendChild(delBtn);
    }

    card.appendChild(meta);
    card.appendChild(text);
    card.appendChild(footer);
    memoryList.appendChild(card);
  });
}

async function loadAllMemories() {
  memoryList.innerHTML = "<p class=\"memory-empty\">Betöltés...</p>";
  try {
    const category = memoryCategoryFilter.value;
    const url = "/api/memories" + (category ? `?category=${encodeURIComponent(category)}` : "");
    const response = await fetch(url);
    const data = await response.json();
    renderMemories(data.memories, "Még nincs mentett memória.");
  } catch (err) {
    memoryList.innerHTML = "<p class=\"memory-empty\">Nem sikerült betölteni a memóriákat.</p>";
  }
}

async function searchMemories() {
  const query = memorySearchInput.value.trim();
  if (!query) {
    loadAllMemories();
    return;
  }
  memoryList.innerHTML = "<p class=\"memory-empty\">Keresés...</p>";
  try {
    const response = await fetch("/api/memories/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        category: memoryCategoryFilter.value || null,
        limit: 10,
      }),
    });
    const data = await response.json();
    renderMemories(data.memories, "Nincs a keresésre illő memória.");
  } catch (err) {
    memoryList.innerHTML = "<p class=\"memory-empty\">Nem sikerült keresni.</p>";
  }
}

async function deleteMemory(id) {
  try {
    await fetch("/api/memories/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });
  } catch (err) {
    // a lista frissítés úgyis megmutatja, ha nem változott semmi
  } finally {
    if (memorySearchInput.value.trim()) {
      searchMemories();
    } else {
      loadAllMemories();
    }
  }
}

memoryToggleBtn.addEventListener("click", () => {
  const nowHidden = memoryPanel.classList.toggle("hidden");
  if (!nowHidden && memoryList.children.length === 0) {
    loadAllMemories();
  }
});

memorySearchBtn.addEventListener("click", searchMemories);
memoryRefreshBtn.addEventListener("click", () => {
  memorySearchInput.value = "";
  loadAllMemories();
});
memorySearchInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    searchMemories();
  }
});

memorySaveBtn.addEventListener("click", async () => {
  const text = memorySaveText.value.trim();
  if (!text) {
    return;
  }
  memorySaveBtn.disabled = true;
  try {
    await fetch("/api/memories/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        category: memorySaveCategory.value,
        text,
      }),
    });
    memorySaveText.value = "";
    loadAllMemories();
  } catch (err) {
    // -
  } finally {
    memorySaveBtn.disabled = false;
  }
});
