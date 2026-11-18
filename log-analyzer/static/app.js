const state = {
  sessions: [],
  activeSessionId: null,
  logs: [],
  counts: {},
  searchTimer: null,
};

const els = {
  fileInput: document.getElementById("fileInput"),
  uploadBtn: document.getElementById("uploadBtn"),
  sampleBtn: document.getElementById("sampleBtn"),
  sessionList: document.getElementById("sessionList"),
  noSessions: document.getElementById("noSessions"),
  emptyState: document.getElementById("emptyState"),
  dashboard: document.getElementById("dashboard"),
  statTotal: document.getElementById("statTotal"),
  statError: document.getElementById("statError"),
  statWarning: document.getElementById("statWarning"),
  statInfo: document.getElementById("statInfo"),
  levelFilter: document.getElementById("levelFilter"),
  searchInput: document.getElementById("searchInput"),
  resultCount: document.getElementById("resultCount"),
  logBody: document.getElementById("logBody"),
  toast: document.getElementById("toast"),
};

function showToast(message, kind = "success") {
  els.toast.textContent = message;
  els.toast.className = `toast ${kind}`;
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => els.toast.classList.add("hidden"), 3500);
}

async function api(path, options = {}) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch (_) {}
    throw new Error(detail);
  }
  return res.json();
}

async function refreshSessions() {
  state.sessions = await api("/api/sessions");
  renderSessions();
}

function renderSessions() {
  els.sessionList.innerHTML = "";
  els.noSessions.classList.toggle("hidden", state.sessions.length > 0);

  for (const s of state.sessions) {
    const li = document.createElement("li");
    li.className = "session-item" + (s.id === state.activeSessionId ? " active" : "");
    li.innerHTML = `
      <div>
        <div class="name"></div>
        <div class="meta">${s.entry_count} entries · ${s.created_at}</div>
      </div>
      <button class="btn-danger" title="Delete session">&times;</button>
    `;
    li.querySelector(".name").textContent = s.filename;
    li.addEventListener("click", (e) => {
      if (e.target.closest(".btn-danger")) return;
      selectSession(s.id);
    });
    li.querySelector(".btn-danger").addEventListener("click", async (e) => {
      e.stopPropagation();
      try {
        await api(`/api/sessions/${s.id}`, { method: "DELETE" });
        if (state.activeSessionId === s.id) {
          state.activeSessionId = null;
          els.dashboard.classList.add("hidden");
          els.emptyState.classList.remove("hidden");
        }
        await refreshSessions();
        showToast("Session deleted");
      } catch (err) {
        showToast(err.message, "error");
      }
    });
    els.sessionList.appendChild(li);
  }
}

async function selectSession(id) {
  state.activeSessionId = id;
  renderSessions();
  await loadLogs();
}

async function loadLogs() {
  if (!state.activeSessionId) return;
  const params = new URLSearchParams();
  const level = els.levelFilter.value;
  const q = els.searchInput.value.trim();
  if (level !== "ALL") params.set("level", level);
  if (q) params.set("q", q);

  const data = await api(`/api/logs/${state.activeSessionId}?${params}`);
  state.logs = data.logs;
  state.counts = data.counts;

  els.statTotal.textContent = state.counts.TOTAL ?? 0;
  els.statError.textContent = state.counts.ERROR ?? 0;
  els.statWarning.textContent = state.counts.WARNING ?? 0;
  els.statInfo.textContent = state.counts.INFO ?? 0;
  els.resultCount.textContent = `${state.logs.length} shown`;

  els.emptyState.classList.add("hidden");
  els.dashboard.classList.remove("hidden");
  renderLogs();
}

function renderLogs() {
  els.logBody.innerHTML = "";
  const frag = document.createDocumentFragment();
  for (const log of state.logs) {
    const tr = document.createElement("tr");
    const ts = document.createElement("td");
    ts.className = "timestamp";
    ts.textContent = log.timestamp;
    const lv = document.createElement("td");
    const badge = document.createElement("span");
    badge.className = `badge ${log.level}`;
    badge.textContent = log.level;
    lv.appendChild(badge);
    const msg = document.createElement("td");
    msg.className = "message";
    msg.textContent = log.message;
    tr.append(ts, lv, msg);
    frag.appendChild(tr);
  }
  els.logBody.appendChild(frag);
}

async function uploadFiles(files) {
  for (const file of files) {
    const form = new FormData();
    form.append("file", file);
    try {
      const result = await api("/api/upload", { method: "POST", body: form });
      showToast(`Uploaded ${result.filename}: ${result.entries} entries`);
      state.activeSessionId = result.session_id;
    } catch (err) {
      showToast(`${file.name}: ${err.message}`, "error");
    }
  }
  await refreshSessions();
  if (state.activeSessionId) await loadLogs();
}

els.uploadBtn.addEventListener("click", () => els.fileInput.click());
els.fileInput.addEventListener("change", (e) => {
  if (e.target.files.length) uploadFiles(e.target.files);
  e.target.value = "";
});

els.sampleBtn.addEventListener("click", async () => {
  els.sampleBtn.disabled = true;
  try {
    const result = await api("/api/sample", { method: "POST" });
    state.activeSessionId = result.session_id;
    showToast(`Loaded ${result.entries} sample entries`);
    await refreshSessions();
    await loadLogs();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    els.sampleBtn.disabled = false;
  }
});

els.levelFilter.addEventListener("change", loadLogs);
els.searchInput.addEventListener("input", () => {
  clearTimeout(state.searchTimer);
  state.searchTimer = setTimeout(loadLogs, 250);
});

refreshSessions().then(() => {
  if (state.sessions.length) selectSession(state.sessions[0].id);
});
