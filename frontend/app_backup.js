/* =========================================================================
   CareerVoice AI — frontend application logic
   Talks to the FastAPI backend defined in backend/main.py.
   Adjust API_BASE if your backend runs on a different host/port.
   ========================================================================= */

const API_BASE = window.CAREERVOICE_API_BASE || "http://127.0.0.1:8000";
const SESSION_KEY = "careervoice_session_id";

const state = {
  sessionId: localStorage.getItem(SESSION_KEY) || null,
  careersCache: null,
  listening: false,
};

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

/* ---------------------------------------------------------------------- */
/* API helpers                                                             */
/* ---------------------------------------------------------------------- */

async function apiPost(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await safeJson(res);
    throw new Error(detail?.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const detail = await safeJson(res);
    throw new Error(detail?.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

async function safeJson(res) {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

/* ---------------------------------------------------------------------- */
/* Chat / voice interaction                                                */
/* ---------------------------------------------------------------------- */

function appendChatMessage(text, who) {
  const log = $("#chatLog");
  const bubble = document.createElement("div");
  bubble.className = `chat-msg ${who}`;
  bubble.textContent = text;
  log.appendChild(bubble);
  log.scrollTop = log.scrollHeight;
}

function speak(text) {
  if (!("speechSynthesis" in window) || !text) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.0;
  utterance.pitch = 1.0;
  window.speechSynthesis.speak(utterance);
}

async function sendMessage(text) {
  const trimmed = (text || "").trim();
  if (!trimmed) return;

  appendChatMessage(trimmed, "user");
  $("#textInput").value = "";
  $("#heroPrompt").textContent = "Thinking...";
  $("#sendBtn").disabled = true;

  try {
    const data = await apiPost("/ask", { session_id: state.sessionId, message: trimmed });
    state.sessionId = data.session_id;
    localStorage.setItem(SESSION_KEY, state.sessionId);

    appendChatMessage(data.reply, "ai");
    speak(data.reply);

    renderDashboardData(data);
  } catch (err) {
    appendChatMessage(`Sorry, something went wrong: ${err.message}`, "ai");
  } finally {
    $("#heroPrompt").textContent = "Tell me about your career goals";
    $("#sendBtn").disabled = false;
  }
}

function setupVoiceRecognition() {
  const SpeechRecognitionImpl = window.SpeechRecognition || window.webkitSpeechRecognition;
  const micBtn = $("#micBtn");
  const hint = $("#voiceHint");

  if (!SpeechRecognitionImpl) {
    hint.textContent = "Voice input isn't supported in this browser — please type instead.";
    micBtn.disabled = true;
    micBtn.style.opacity = 0.5;
    return;
  }

  const recognition = new SpeechRecognitionImpl();
  recognition.lang = "en-NG";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    state.listening = true;
    micBtn.classList.add("listening");
    micBtn.textContent = "🎙️ Listening...";
    hint.textContent = "Speak now — I'm listening.";
    $("#waveform").classList.remove("idle");
  };

  recognition.onerror = (event) => {
    hint.textContent = `Voice error: ${event.error}. You can type instead.`;
  };

  recognition.onend = () => {
    state.listening = false;
    micBtn.classList.remove("listening");
    micBtn.textContent = "🎤 Start talking";
    $("#waveform").classList.add("idle");
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    hint.textContent = `Heard: "${transcript}"`;
    sendMessage(transcript);
  };

  micBtn.addEventListener("click", () => {
    if (state.listening) {
      recognition.stop();
    } else {
      try {
        recognition.start();
      } catch (err) {
        hint.textContent = "Could not start the microphone. Please try again.";
      }
    }
  });
}

/* ---------------------------------------------------------------------- */
/* Dashboard rendering                                                     */
/* ---------------------------------------------------------------------- */

function renderDashboardData(data) {
  const profile = data.profile || {};
  const completeness = data.profile_completeness ?? 0;
  const careerMatches = data.career_matches || [];
  const uniMatches = data.university_matches || [];
  const readiness = data.admission_readiness || {};
  const nextQ = data.next_best_question;

  $("#greetingText").textContent = profile.name ? `Good day, ${profile.name} 👋` : "Good day 👋";

  $("#profilePercentVal").textContent = `${completeness}%`;
  $("#profilePercentNum").textContent = `${completeness}%`;
  const circumference = 150.8;
  const offset = circumference - (circumference * completeness) / 100;
  $("#profileRing").setAttribute("stroke-dashoffset", offset.toFixed(1));

  $("#profileFoot").innerHTML = `<b>Profile ${completeness}% complete</b><br>${
    completeness < 100 ? "Keep talking to sharpen your matches." : "Your profile looks complete!"
  }`;

  if (careerMatches.length) {
    $("#topCareerName").textContent = careerMatches[0].name;
    $("#topCareerPct").textContent = `${careerMatches[0].match_percent}% CareerVoice Match`;
  }
  if (uniMatches.length) {
    $("#topUniName").textContent = uniMatches[0].short_name || uniMatches[0].name;
    $("#topUniPct").textContent = `${uniMatches[0].match_percent}% CareerVoice Match`;
  }

  $("#readinessPct").textContent = `${readiness.readiness_percent ?? 0}%`;
  $("#readinessNote").textContent = readiness.career_name
    ? `For ${readiness.career_name}`
    : (readiness.message || "Set a career goal first");

  renderCareerDiscovery(careerMatches);
  renderUniversityFinder(uniMatches);
  renderNextQuestion(nextQ);
}

function renderCareerDiscovery(matches) {
  const container = $("#careerDiscoveryList");
  if (!matches.length) {
    container.innerHTML = `<div class="empty-state">Start the conversation to see your matches here.</div>`;
    return;
  }
  const icons = { Science: "🧪", "Art/Humanities": "🎭", Commercial: "💼" };
  container.innerHTML = matches
    .slice(0, 4)
    .map(
      (m, i) => `
      <div class="match-row">
        <div class="match-left"><div class="match-icon">${icons[m.stream] || "🎯"}</div> ${m.name}</div>
        <div class="match-score ${i === 0 ? "top" : ""}">${m.match_percent}%</div>
      </div>`
    )
    .join("");
}

function renderUniversityFinder(matches) {
  const container = $("#universityFinderList");
  if (!matches.length) {
    container.innerHTML = `<div class="empty-state">Your top university matches will appear here.</div>`;
    return;
  }
  container.innerHTML = matches
    .slice(0, 4)
    .map(
      (m, i) => `
      <div class="match-row">
        <div class="match-left"><div class="match-icon">🎓</div> ${m.short_name || m.name}</div>
        <div class="match-score ${i === 0 ? "top" : ""}">${m.match_percent}%</div>
      </div>`
    )
    .join("");
}

function renderNextQuestion(nextQ) {
  const panel = $("#nextQPanel");
  if (!nextQ) {
    panel.style.display = "none";
    return;
  }
  panel.style.display = "block";
  $("#nextQText").textContent = nextQ.question;
  $("#nextQChips").innerHTML = (nextQ.options || [])
    .map((opt) => `<div class="chip" data-answer="${opt}">${opt}</div>`)
    .join("");
  $$("#nextQChips .chip").forEach((chip) => {
    chip.addEventListener("click", () => sendMessage(chip.dataset.answer));
  });
}

/* ---------------------------------------------------------------------- */
/* Careers view                                                            */
/* ---------------------------------------------------------------------- */

async function loadCareersCache() {
  if (state.careersCache) return state.careersCache;
  try {
    const data = await apiGet("/careers");
    state.careersCache = data.careers || [];
  } catch (err) {
    state.careersCache = [];
  }
  return state.careersCache;
}

function renderCareersGrid(careers) {
  const grid = $("#careersGrid");
  if (!careers.length) {
    grid.innerHTML = `<div class="empty-state">No careers found.</div>`;
    return;
  }
  grid.innerHTML = careers
    .map(
      (c) => `
      <div class="info-card">
        <span class="tag">${c.stream}</span>
        <h3>${c.name}</h3>
        <p>${c.description}</p>
        <div class="meta">
          <span>UTME: ${(c.jamb_subjects || []).join(", ")}</span>
        </div>
      </div>`
    )
    .join("");
}

async function initCareersView() {
  const careers = await loadCareersCache();
  renderCareersGrid(careers);

  $$(".filter-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      $$(".filter-chip").forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      const stream = chip.dataset.stream;
      const filtered = stream ? careers.filter((c) => c.stream === stream) : careers;
      renderCareersGrid(filtered);
    });
  });
}

/* ---------------------------------------------------------------------- */
/* Universities view                                                       */
/* ---------------------------------------------------------------------- */

function renderUniversitiesGrid(universities) {
  const grid = $("#universitiesGrid");
  if (!universities.length) {
    grid.innerHTML = `<div class="empty-state">No universities matched your search.</div>`;
    return;
  }
  grid.innerHTML = universities
    .map((u) => {
      const rankingText = (u.rankings || [])
        .map((r) => (r.organization && r.organization !== "Information requires verification"
          ? `${r.organization} ${r.year || ""}: ${r.position}`
          : r.position || "Ranking requires verification"))
        .join(" · ");
      return `
      <div class="info-card">
        <span class="tag">${u.type}</span>
        <h3>${u.name}</h3>
        <p>${u.location || u.state || ""}</p>
        <div class="meta">
          <span>Courses: ${(u.courses || []).slice(0, 4).join(", ")}${(u.courses || []).length > 4 ? "…" : ""}</span>
          <span>${rankingText}</span>
          ${u.website ? `<span><a href="${u.website}" target="_blank" rel="noopener">${u.website}</a></span>` : ""}
        </div>
      </div>`;
    })
    .join("");
}

async function initUniversitiesView() {
  try {
    const data = await apiGet("/universities");
    renderUniversitiesGrid(data.universities || []);
  } catch (err) {
    $("#universitiesGrid").innerHTML = `<div class="error-state">Couldn't load universities: ${err.message}</div>`;
  }

  $("#uniSearchBtn").addEventListener("click", async () => {
    const course = $("#uniCourseInput").value.trim();
    const stateVal = $("#uniStateInput").value.trim();
    const type = $("#uniTypeInput").value;
    const params = new URLSearchParams();
    if (course) params.set("course", course);
    if (stateVal) params.set("state", stateVal);
    if (type) params.set("type", type);

    $("#universitiesGrid").innerHTML = `<div class="empty-state">Searching...</div>`;
    try {
      const data = await apiGet(`/universities/search?${params.toString()}`);
      renderUniversitiesGrid(data.universities || []);
    } catch (err) {
      $("#universitiesGrid").innerHTML = `<div class="error-state">Search failed: ${err.message}</div>`;
    }
  });
}

/* ---------------------------------------------------------------------- */
/* Admission + JAMB views                                                  */
/* ---------------------------------------------------------------------- */

function renderAdmissionInfo(container, data) {
  container.innerHTML = `
    <div class="result-block">
      <h4>WAEC / NECO subjects</h4>
      <p>${(data.waec_subjects || []).join(", ") || "Not specified"}</p>
    </div>
    <div class="result-block">
      <h4>JAMB / UTME subjects</h4>
      <p>${(data.jamb_subjects || []).join(", ") || "Not specified"}</p>
    </div>
    <div class="result-block">
      <h4>Suitable universities</h4>
      <ul>${(data.suitable_universities || [])
        .map((u) => `<li>${u.name} (${u.type}, ${u.state})</li>`)
        .join("") || "<li>None found in the current dataset</li>"}</ul>
    </div>
    <div class="result-block">
      <h4>Target score guidance</h4>
      <p>${data.target_score_guidance}</p>
    </div>
    <div class="disclaimer">${data.disclaimer}</div>
  `;
}

async function populateCareerSelect(selectEl) {
  const careers = await loadCareersCache();
  selectEl.innerHTML = careers
    .map((c) => `<option value="${c.id}">${c.name} (${c.stream})</option>`)
    .join("");
}

async function initAdmissionView() {
  const select = $("#admissionCareerSelect");
  await populateCareerSelect(select);

  $("#admissionLoadBtn").addEventListener("click", async () => {
    const container = $("#admissionResult");
    container.innerHTML = `<div class="empty-state">Loading...</div>`;
    try {
      const data = await apiGet(`/admission?career_id=${encodeURIComponent(select.value)}`);
      renderAdmissionInfo(container, data);
    } catch (err) {
      container.innerHTML = `<div class="error-state">${err.message}</div>`;
    }
  });
}

async function initJambView() {
  const select = $("#jambCareerSelect");
  await populateCareerSelect(select);

  $("#jambLoadBtn").addEventListener("click", async () => {
    const container = $("#jambResult");
    container.innerHTML = `<div class="empty-state">Loading...</div>`;
    try {
      const data = await apiGet(`/admission?career_id=${encodeURIComponent(select.value)}`);
      container.innerHTML = `
        <div class="result-block">
          <h4>UTME subject combination</h4>
          <p>${(data.jamb_subjects || []).join(", ")}</p>
        </div>
        <div class="result-block">
          <h4>Competitiveness</h4>
          <p>${data.competitiveness}</p>
        </div>
        <div class="result-block">
          <h4>Target score guidance</h4>
          <p>${data.target_score_guidance}</p>
        </div>
        <div class="disclaimer">${data.disclaimer}</div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="error-state">${err.message}</div>`;
    }
  });
}

/* ---------------------------------------------------------------------- */
/* Action plan view                                                        */
/* ---------------------------------------------------------------------- */

function renderActionPlan(steps) {
  const container = $("#actionPlanList");
  if (!steps || !steps.length) {
    container.innerHTML = `<div class="empty-state">Start a conversation on the dashboard first, then come back for your plan.</div>`;
    return;
  }
  container.innerHTML = steps
    .map(
      (s) => `
      <div class="plan-step">
        <div class="num">${s.step}</div>
        <div>
          <h4>${s.title}</h4>
          <p>${s.description}</p>
        </div>
      </div>`
    )
    .join("");
}

async function initActionPlanView() {
  $("#refreshPlanBtn").addEventListener("click", async () => {
    if (!state.sessionId) {
      renderActionPlan([]);
      return;
    }
    $("#actionPlanList").innerHTML = `<div class="empty-state">Building your plan...</div>`;
    try {
      const data = await apiGet(`/action-plan?session_id=${encodeURIComponent(state.sessionId)}`);
      renderActionPlan(data.action_plan);
    } catch (err) {
      $("#actionPlanList").innerHTML = `<div class="error-state">${err.message}</div>`;
    }
  });
}

/* ---------------------------------------------------------------------- */
/* Smart search view                                                       */
/* ---------------------------------------------------------------------- */

async function runSmartSearch(query) {
  const container = $("#smartSearchResults");
  if (!query.trim()) {
    container.innerHTML = "";
    return;
  }
  container.innerHTML = `<div class="empty-state">Searching...</div>`;

  const careers = await loadCareersCache();
  const q = query.toLowerCase();
  const careerMatches = careers.filter(
    (c) =>
      c.name.toLowerCase().includes(q) ||
      c.description.toLowerCase().includes(q) ||
      (c.keywords || []).some((k) => k.toLowerCase().includes(q))
  );

  let uniMatches = [];
  try {
    const data = await apiGet(`/universities/search?q=${encodeURIComponent(query)}`);
    uniMatches = data.universities || [];
  } catch (err) {
    uniMatches = [];
  }

  if (!careerMatches.length && !uniMatches.length) {
    container.innerHTML = `<div class="empty-state">No matches found for "${query}".</div>`;
    return;
  }

  container.innerHTML = `
    ${
      careerMatches.length
        ? `<div class="panel" style="margin-bottom:16px;">
            <div class="panel-head"><div class="panel-title">Careers</div></div>
            <div class="cards-grid">${careerMatches
              .map((c) => `<div class="info-card"><span class="tag">${c.stream}</span><h3>${c.name}</h3><p>${c.description}</p></div>`)
              .join("")}</div>
          </div>`
        : ""
    }
    ${
      uniMatches.length
        ? `<div class="panel">
            <div class="panel-head"><div class="panel-title">Universities</div></div>
            <div class="cards-grid">${uniMatches
              .map((u) => `<div class="info-card"><span class="tag">${u.type}</span><h3>${u.name}</h3><p>${u.location || u.state || ""}</p></div>`)
              .join("")}</div>
          </div>`
        : ""
    }
  `;
}

function initSmartSearchView() {
  $("#smartSearchBtn").addEventListener("click", () => runSmartSearch($("#smartSearchInput").value));
  $("#smartSearchInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter") runSmartSearch($("#smartSearchInput").value);
  });
}

/* ---------------------------------------------------------------------- */
/* Navigation                                                              */
/* ---------------------------------------------------------------------- */

function initNavigation() {
  $$(".nav-item").forEach((item) => {
    item.addEventListener("click", () => switchView(item.dataset.view));
  });
  $$("[data-goto]").forEach((el) => {
    el.addEventListener("click", () => switchView(el.dataset.goto));
  });
}

function switchView(view) {
  $$(".nav-item").forEach((i) => i.classList.toggle("active", i.dataset.view === view));
  $$(".view").forEach((v) => v.classList.toggle("active", v.dataset.view === view));
}

/* ---------------------------------------------------------------------- */
/* Waveform bars                                                           */
/* ---------------------------------------------------------------------- */

function buildWaveform() {
  const wf = $("#waveform");
  const heights = [14, 24, 34, 20, 40, 28, 16, 36, 22, 30, 18, 38, 26, 16, 32];
  heights.forEach((h, i) => {
    const bar = document.createElement("span");
    bar.style.height = `${h}px`;
    bar.style.animationDelay = `${i * 0.06}s`;
    wf.appendChild(bar);
  });
  wf.classList.add("idle");
}

/* ---------------------------------------------------------------------- */
/* Bootstrapping                                                           */
/* ---------------------------------------------------------------------- */

async function loadExistingSession() {
  if (!state.sessionId) return;
  try {
    const data = await apiGet(`/session/${encodeURIComponent(state.sessionId)}`);
    renderDashboardData({
      profile: data.profile,
      profile_completeness: data.profile_completeness,
      career_matches: data.career_matches,
      university_matches: data.university_matches,
      admission_readiness: data.admission_readiness,
      next_best_question: data.next_best_question,
    });
  } catch (err) {
    // session may have expired if the backend restarted; start fresh silently
    state.sessionId = null;
    localStorage.removeItem(SESSION_KEY);
  }
}

async function checkBackendStatus() {
  try {
    await apiGet("/info");
    $("#statusPill").innerHTML = `<span class="status-dot"></span> AI online`;
  } catch (err) {
    $("#statusPill").innerHTML = `<span class="status-dot" style="background:var(--bad);"></span> Backend offline`;
    $("#statusPill").style.borderColor = "rgba(248,113,113,0.35)";
    $("#statusPill").style.background = "rgba(248,113,113,0.07)";
    $("#statusPill").style.color = "var(--bad)";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  buildWaveform();
  initNavigation();
  setupVoiceRecognition();

  $("#sendBtn").addEventListener("click", () => sendMessage($("#textInput").value));
  $("#textInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage($("#textInput").value);
  });

  checkBackendStatus();
  loadExistingSession();
  initCareersView();
  initUniversitiesView();
  initAdmissionView();
  initJambView();
  initActionPlanView();
  initSmartSearchView();
});
