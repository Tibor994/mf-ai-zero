const chatBox = document.getElementById("chat-box");
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const clearBtn = document.getElementById("clear-btn");
const temperatureSelect = document.getElementById("temperature-select");
const sentencesSelect = document.getElementById("sentences-select");
const typingIndicator = document.getElementById("typing-indicator");
const statusLine = document.getElementById("status-line");
const inputHint = document.getElementById("input-hint");

const MAX_MESSAGE_LENGTH = parseInt(messageInput.getAttribute("maxlength"), 10) || 500;

const INDICATOR_LABELS = {
  short_memory_used: "🧠 rövid memória",
  long_memory_used: "💾 hosszú memória",
  knowledge_used: "📚 tudásbázis",
  web_research_used: "🌐 weboldal olvasva",
  web_search_used: "🔎 webes keresés",
  conversation_context_used: "💬 beszélgetés-kontextus",
  input_normalized: "✏️ elírás javítva",
};

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

const knowledgeToggleBtn = document.getElementById("knowledge-toggle-btn");
const knowledgePanel = document.getElementById("knowledge-panel");
const knowledgeSearchInput = document.getElementById("knowledge-search-input");
const knowledgeCategoryFilter = document.getElementById("knowledge-category-filter");
const knowledgeSearchBtn = document.getElementById("knowledge-search-btn");
const knowledgeRefreshBtn = document.getElementById("knowledge-refresh-btn");
const knowledgeList = document.getElementById("knowledge-list");
const knowledgeSaveTitle = document.getElementById("knowledge-save-title");
const knowledgeSaveCategory = document.getElementById("knowledge-save-category");
const knowledgeSaveContent = document.getElementById("knowledge-save-content");
const knowledgeSaveTags = document.getElementById("knowledge-save-tags");
const knowledgeSaveBtn = document.getElementById("knowledge-save-btn");

const KNOWLEDGE_CATEGORY_LABELS = {
  ai_project: "AI-projekt",
  business: "Üzleti",
  training: "Tanítás",
  rules: "Szabály",
  technical: "Technikai",
  personal_notes: "Személyes jegyzet",
  other: "Egyéb",
};

function addMessage(text, sender, isError, indicators) {
  const row = document.createElement("div");
  row.className = "message " + sender + (isError ? " error" : "");

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  row.appendChild(bubble);

  const activeChips = Object.keys(INDICATOR_LABELS).filter((key) => indicators && indicators[key]);
  if (activeChips.length > 0) {
    const chipsRow = document.createElement("div");
    chipsRow.className = "indicator-chips";
    activeChips.forEach((key) => {
      const chip = document.createElement("span");
      chip.className = "indicator-chip";
      chip.textContent = INDICATOR_LABELS[key];
      chipsRow.appendChild(chip);
    });
    row.appendChild(chipsRow);
  }

  chatBox.appendChild(row);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function setBusy(busy) {
  messageInput.disabled = busy;
  sendBtn.disabled = busy;
  typingIndicator.classList.toggle("hidden", !busy);
}

function updateInputHint() {
  const remaining = MAX_MESSAGE_LENGTH - messageInput.value.length;
  inputHint.textContent = remaining <= 50 ? `${remaining} karakter maradt` : "";
  inputHint.classList.toggle("input-hint-warn", remaining <= 20);
}

messageInput.addEventListener("input", updateInputHint);

async function sendMessage() {
  const text = messageInput.value.trim();
  if (!text) {
    return;
  }
  if (text.length > MAX_MESSAGE_LENGTH) {
    addMessage(`Az üzenet túl hosszú (max. ${MAX_MESSAGE_LENGTH} karakter).`, "ai", true);
    return;
  }

  addMessage(text, "user");
  messageInput.value = "";
  updateInputHint();
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
      addMessage(errData.error || "Hiba történt a szerverrel. Próbáld újra.", "ai", true);
      return;
    }

    const data = await response.json();
    addMessage(data.reply, "ai", false, data.indicators);
  } catch (err) {
    addMessage("Nem sikerült elérni a szervert. Fut a python web/app.py, és van internet-/hálózati kapcsolat?", "ai", true);
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
updateInputHint();

// ---------------------------------------------------------------------------
// v1.5 healthcheck - egyszer, betöltéskor lekérdezi a szerver állapotát, és
// egy rövid, csendes státuszsorban jelzi (nem tolakodó, csak informatív).
// ---------------------------------------------------------------------------

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    if (!response.ok) {
      statusLine.textContent = "⚠️ A szerver állapota nem lekérdezhető.";
      statusLine.classList.add("status-warn");
      return;
    }
    const data = await response.json();
    const parts = [];
    if (data.guard_active) parts.push("guard aktív");
    if (data.long_memory_active) parts.push("hosszú memória aktív");
    if (data.knowledge_active) parts.push("tudásbázis aktív");
    if (data.web_research_active || data.web_search_active) parts.push("web aktív");
    statusLine.textContent = parts.length > 0 ? `✅ Kész — ${parts.join(", ")}` : "✅ Kész";
  } catch (err) {
    statusLine.textContent = "⚠️ Nem sikerült elérni a szervert.";
    statusLine.classList.add("status-warn");
  }
}

checkHealth();

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

// ---------------------------------------------------------------------------
// v1.1 saját tudásbázis panel - listázás/keresés/törlés/kézi mentés. KÜLÖN
// mechanizmus a memóriától (lásd src/knowledge_base.py) - semmi itt sem fut
// le automatikusan a chat közben, csak a felhasználó explicit kattintására.
// ---------------------------------------------------------------------------

function renderKnowledge(items, emptyText) {
  knowledgeList.innerHTML = "";
  if (!items || items.length === 0) {
    const empty = document.createElement("p");
    empty.className = "memory-empty";
    empty.textContent = emptyText || "Nincs találat.";
    knowledgeList.appendChild(empty);
    return;
  }

  items.forEach((item) => {
    const card = document.createElement("div");
    card.className = "memory-card" + (item.active ? "" : " inactive");

    const meta = document.createElement("div");
    meta.className = "memory-meta";

    const catSpan = document.createElement("span");
    catSpan.className = "memory-category";
    catSpan.textContent = KNOWLEDGE_CATEGORY_LABELS[item.category] || item.category;
    meta.appendChild(catSpan);

    const statusSpan = document.createElement("span");
    statusSpan.className = "memory-status" + (item.active ? " active" : " inactive");
    statusSpan.textContent = item.active ? "aktív" : "inaktív";
    meta.appendChild(statusSpan);

    if (item.tags && item.tags.length > 0) {
      const tagsSpan = document.createElement("span");
      tagsSpan.className = "memory-tags";
      tagsSpan.textContent = item.tags.join(", ");
      meta.appendChild(tagsSpan);
    }

    const title = document.createElement("div");
    title.className = "memory-title";
    title.textContent = item.title;

    const text = document.createElement("div");
    text.className = "memory-text";
    text.textContent = item.content;

    const footer = document.createElement("div");
    footer.className = "memory-footer";

    const date = document.createElement("span");
    date.className = "memory-date";
    date.textContent = formatMemoryDate(item.updated_at || item.created_at);
    footer.appendChild(date);

    if (item.active) {
      const delBtn = document.createElement("button");
      delBtn.type = "button";
      delBtn.className = "btn btn-ghost btn-small";
      delBtn.textContent = "Deaktiválás";
      delBtn.addEventListener("click", () => deleteKnowledge(item.id));
      footer.appendChild(delBtn);
    }

    card.appendChild(meta);
    card.appendChild(title);
    card.appendChild(text);
    card.appendChild(footer);
    knowledgeList.appendChild(card);
  });
}

async function loadAllKnowledge() {
  knowledgeList.innerHTML = "<p class=\"memory-empty\">Betöltés...</p>";
  try {
    const category = knowledgeCategoryFilter.value;
    const url = "/api/knowledge" + (category ? `?category=${encodeURIComponent(category)}` : "");
    const response = await fetch(url);
    const data = await response.json();
    renderKnowledge(data.items, "Még nincs mentett tudáselem.");
  } catch (err) {
    knowledgeList.innerHTML = "<p class=\"memory-empty\">Nem sikerült betölteni a tudásbázist.</p>";
  }
}

async function searchKnowledge() {
  const query = knowledgeSearchInput.value.trim();
  if (!query) {
    loadAllKnowledge();
    return;
  }
  knowledgeList.innerHTML = "<p class=\"memory-empty\">Keresés...</p>";
  try {
    const response = await fetch("/api/knowledge/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        category: knowledgeCategoryFilter.value || null,
        limit: 10,
      }),
    });
    const data = await response.json();
    renderKnowledge(data.items, "Nincs a keresésre illő tudáselem.");
  } catch (err) {
    knowledgeList.innerHTML = "<p class=\"memory-empty\">Nem sikerült keresni.</p>";
  }
}

async function deleteKnowledge(id) {
  try {
    await fetch("/api/knowledge/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });
  } catch (err) {
    // a lista frissítés úgyis megmutatja, ha nem változott semmi
  } finally {
    if (knowledgeSearchInput.value.trim()) {
      searchKnowledge();
    } else {
      loadAllKnowledge();
    }
  }
}

knowledgeToggleBtn.addEventListener("click", () => {
  const nowHidden = knowledgePanel.classList.toggle("hidden");
  if (!nowHidden && knowledgeList.children.length === 0) {
    loadAllKnowledge();
  }
});

knowledgeSearchBtn.addEventListener("click", searchKnowledge);
knowledgeRefreshBtn.addEventListener("click", () => {
  knowledgeSearchInput.value = "";
  loadAllKnowledge();
});
knowledgeSearchInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    searchKnowledge();
  }
});

knowledgeSaveBtn.addEventListener("click", async () => {
  const content = knowledgeSaveContent.value.trim();
  if (!content) {
    return;
  }
  knowledgeSaveBtn.disabled = true;
  try {
    await fetch("/api/knowledge/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: knowledgeSaveTitle.value.trim(),
        content,
        category: knowledgeSaveCategory.value,
        tags: knowledgeSaveTags.value.trim(),
      }),
    });
    knowledgeSaveTitle.value = "";
    knowledgeSaveContent.value = "";
    knowledgeSaveTags.value = "";
    loadAllKnowledge();
  } catch (err) {
    // -
  } finally {
    knowledgeSaveBtn.disabled = false;
  }
});
