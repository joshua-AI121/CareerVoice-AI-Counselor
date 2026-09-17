/* =========================================================================
   CareerVoice AI — frontend application logic

   Guided AI Counselor:

   SS1 / SS2 / SS3
          ↓
   Science / Art / Commercial
          ↓
   Subjects
          ↓
   Strongest Subjects
          ↓
   Favorite Subjects
          ↓
   Interests
          ↓
   Career
          ↓
   JAMB / UTME
          ↓
   JAMB Score (if written)
          ↓
   WAEC
          ↓
   WAEC Grades (if written)
          ↓
   NECO
          ↓
   NECO Grades (if written)
          ↓
   Admission Analysis
          ↓
   Recommendations

   The FastAPI backend is the authority for deciding
   which question comes next.
   ========================================================================= */


/* ---------------------------------------------------------------------- */
/* API CONFIGURATION                                                      */
/* ---------------------------------------------------------------------- */

const API_BASE =
  window.CAREERVOICE_API_BASE || "http://127.0.0.1:8000";

const SESSION_KEY =
  "careervoice_session_id";

const ONBOARDING_KEY =
  "careervoice_onboarding";


/* ---------------------------------------------------------------------- */
/* APPLICATION STATE                                                       */
/* ---------------------------------------------------------------------- */

const state = {
  sessionId:
    localStorage.getItem(SESSION_KEY) || null,

  careersCache: null,

  listening: false,

  aiStatus: "ready",

  profile: null,

  lastCounselorData: null,

  onboarding: {
    active: true,
    stage: "class",

    className: null,
    department: null,

    subjects: null,
    strengths: null,
    favoriteSubjects: null,

    interests: null,
    career: null,

    plansJamb: null,
    writtenJamb: null,
    jambScore: null,

    course: null,
    universityPreference: null,

    waecStatus: null,
    waecGrades: null,

    necoStatus: null,
    necoGrades: null,

    admissionAnalysis: null,
  },
};


/* ---------------------------------------------------------------------- */
/* DOM HELPERS                                                             */
/* ---------------------------------------------------------------------- */

const $ = (sel) =>
  document.querySelector(sel);

const $$ = (sel) =>
  Array.from(document.querySelectorAll(sel));


/* ---------------------------------------------------------------------- */
/* AI STATE                                                                */
/* ---------------------------------------------------------------------- */

function setAIState(status) {
  state.aiStatus = status;

  const statusPill =
    $("#statusPill");

  const heroPrompt =
    $("#heroPrompt");

  const waveform =
    $("#waveform");

  const stateLabels = {
    ready: "AI online",
    listening: "Listening...",
    thinking: "Thinking...",
    responding: "Responding...",
  };

  if (statusPill) {
    statusPill.innerHTML =
      `<span class="status-dot"></span> ${
        stateLabels[status] || "AI online"
      }`;
  }

  if (heroPrompt) {
    const prompts = {
      ready:
        "Tell me about your career goals",

      listening:
        "I'm listening to you...",

      thinking:
        "Analyzing your profile...",

      responding:
        "Building your career intelligence...",
    };

    heroPrompt.textContent =
      prompts[status] || prompts.ready;
  }

  if (waveform) {
    waveform.classList.remove(
      "state-ready",
      "state-listening",
      "state-thinking",
      "state-responding"
    );

    waveform.classList.add(
      `state-${status}`
    );
  }

  const aiStateLabel =
    $("#aiStateLabel");

  if (aiStateLabel) {
    aiStateLabel.textContent =
      (
        stateLabels[status] ||
        "AI online"
      ).toUpperCase();
  }

  const aiCore =
    $("#aiCore");

  if (aiCore) {
    aiCore.classList.remove(
      "core-ready",
      "core-listening",
      "core-thinking",
      "core-responding"
    );

    aiCore.classList.add(
      `core-${status}`
    );
  }

  const aiOrb =
    $("#aiOrb");

  if (aiOrb) {
    aiOrb.classList.remove(
      "orb-ready",
      "orb-listening",
      "orb-thinking",
      "orb-responding"
    );

    aiOrb.classList.add(
      `orb-${status}`
    );
  }
}


/* ---------------------------------------------------------------------- */
/* API HELPERS                                                             */
/* ---------------------------------------------------------------------- */

async function apiPost(path, body) {
  const res =
    await fetch(
      `${API_BASE}${path}`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",
        },

        body:
          JSON.stringify(body),
      }
    );

  if (!res.ok) {
    const detail =
      await safeJson(res);

    throw new Error(
      detail?.detail ||
      `Request failed (${res.status})`
    );
  }

  return res.json();
}


async function apiGet(path) {
  const res =
    await fetch(
      `${API_BASE}${path}`
    );

  if (!res.ok) {
    const detail =
      await safeJson(res);

    throw new Error(
      detail?.detail ||
      `Request failed (${res.status})`
    );
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
/* CHAT                                                                    */
/* ---------------------------------------------------------------------- */

function appendChatMessage(text, who) {
  const log =
    $("#chatLog");

  if (!log) return;

  const bubble =
    document.createElement("div");

  bubble.className =
    `chat-msg ${who}`;

  bubble.textContent =
    text;

  log.appendChild(
    bubble
  );

  log.scrollTop =
    log.scrollHeight;
}


/* ---------------------------------------------------------------------- */
/* AI SPEECH                                                               */
/* ---------------------------------------------------------------------- */

let voiceActivated = false;


function speak(text) {
  if (
    !("speechSynthesis" in window) ||
    !text
  ) {
    return;
  }

  window.speechSynthesis.cancel();

  const speechText =
    text
      .replace(/WAEC/gi, "way ek")
      .replace(/NECO/gi, "neh koh")
      .replace(
        /[\p{Extended_Pictographic}]/gu,
        ""
      )
      .replace(/[*_#~`]/g, "")
      .replace(/\s+/g, " ")
      .trim();

  if (!speechText) return;

  const utterance =
    new SpeechSynthesisUtterance(
      speechText
    );

  utterance.rate = 0.95;
  utterance.pitch = 1.0;
  utterance.volume = 1.0;

  utterance.onstart = () => {
    setAIState("responding");
  };

  utterance.onend = () => {
    setAIState("ready");
  };

  utterance.onerror = () => {
    setAIState("ready");
  };

  window.speechSynthesis.speak(
    utterance
  );
}


/* ---------------------------------------------------------------------- */
/* GUIDED COUNSELOR QUESTIONS                                             */
/* ---------------------------------------------------------------------- */
const counselorQuestions = {

  class: {
    message:
      "Hello! 👋 I'm CareerVoice, your AI Career & University Counselor.\n\n" +
      "I'll ask you a few questions so I can understand your academic profile " +
      "and help you discover suitable careers, courses and universities.\n\n" +
      "What class are you presently in?",

    options: [
      "SS1",
      "SS2",
      "SS3",
    ],
  },


  department: {
    message:
      "Great! 🎓 What department are you in?",

    options: [
      "Science",
      "Art / Humanities",
      "Commercial",
    ],
  },


  subjects: {
    message:
      "Excellent! 📚 Here are the main subjects for your department.\n\n" +
      "Which ones are you good at? You can select as many as you want.",

    options: [],
  },


  strengths: {
    message:
      "Which subjects do you feel you are strongest in?",

    options: [],
  },


  favorite_subjects: {
    message:
      "Great! Which of those subjects do you enjoy the most?",

    options: [],
  },


  interests: {
    message:
      "Now let's learn about your interests.\n\n" +
      "What activities or areas do you enjoy doing?",

    options: [
      "Helping people",
      "Building or creating things",
      "Business and money",
      "Writing and media",
      "Technology",
      "Science and research",
    ],
  },


  career: {
    message:
      "What career are you currently interested in?\n\n" +
      "If you're not sure yet, just say \"I'm not sure\" and I'll help you discover one.",

    options: [],
  },


  jamb: {
    message:
      "Now let's talk about your university admission journey. 📝\n\n" +
      "Have you written JAMB / UTME yet?",

    options: [
      "Yes",
      "No",
    ],
  },


  jambScore: {
    message:
      "What was your JAMB / UTME score? You can enter a score from 0 to 400.",

    options: [],
  },


  waec: {
    message:
      "Have you written WAEC yet?",

    options: [
      "Yes",
      "No",
      "I'm awaiting my result",
    ],
  },


  waec_grades: {
    message:
      "Great. Please tell me your WAEC subjects and grades.\n\n" +
      "For example: English Language B2, Mathematics A1, Biology B3, Chemistry B2, Physics C6.",

    options: [],
  },


  neco: {
    message:
      "Have you written NECO yet?",

    options: [
      "Yes",
      "No",
      "I'm awaiting my result",
    ],
  },


  neco_grades: {
    message:
      "Great. Please tell me your NECO subjects and grades.\n\n" +
      "For example: English Language B2, Mathematics A1, Biology B3, Chemistry B2, Physics C6.",

    options: [],
  },


  admissionAnalysis: {
    message:
      "Thank you. I now have your JAMB and O'Level information. " +
      "I'll check your subjects and grades against your chosen course " +
      "and assess your admission readiness.",

    options: [],
  },


  recommendations: {
    message:
      "Your profile has been analyzed. Would you like me to show you your recommended careers, specific university courses, and suitable Nigerian universities?",

    options: [
      "Yes",
      "Show my recommendations",
    ],
  },
};


/* ---------------------------------------------------------------------- */
/* SAVE COUNSELOR STATE                                                   */
/* ---------------------------------------------------------------------- */

function saveOnboardingState() {
  try {
    localStorage.setItem(
      ONBOARDING_KEY,
      JSON.stringify(
        state.onboarding
      )
    );
  } catch {
    // Ignore localStorage errors.
  }
}


/* ---------------------------------------------------------------------- */
/* LOAD COUNSELOR STATE                                                   */
/* ---------------------------------------------------------------------- */

function loadOnboardingState() {
  try {
    const saved =
      localStorage.getItem(
        ONBOARDING_KEY
      );

    if (!saved) return;

    const parsed =
      JSON.parse(saved);

    if (
      parsed &&
      typeof parsed === "object"
    ) {
      state.onboarding = {
        ...state.onboarding,
        ...parsed,
      };
    }
  } catch {
    // Ignore invalid saved state.
  }
}


/* ---------------------------------------------------------------------- */
/* RESET COUNSELOR                                                        */
/* ---------------------------------------------------------------------- */

function resetCounselor() {

  state.onboarding = {
    active: true,
    stage: "class",

    className: null,
    department: null,

    subjects: null,
    strengths: null,
    favoriteSubjects: null,

    interests: null,
    career: null,

    plansJamb: null,
    writtenJamb: null,
    jambScore: null,

    course: null,
    universityPreference: null,

    waecStatus: null,
    waecGrades: null,

    necoStatus: null,
    necoGrades: null,

    admissionAnalysis: null,
  };

  localStorage.removeItem(
    ONBOARDING_KEY
  );

  const log =
    $("#chatLog");

  if (log) {
    log.innerHTML = "";
  }

  startCounselor();
}


/* ---------------------------------------------------------------------- */
/* DEPARTMENT MESSAGE                                                     */
/* ---------------------------------------------------------------------- */

function getDepartmentMessage(
  department
) {

  if (
    department === "Science"
  ) {
    return (
      "Excellent! 🧬 You're in the Science department.\n\n" +
      "Here are the main Science subjects. " +
      "Which ones are you good at? You can select as many as you want."
    );
  }

  if (
    department ===
    "Art / Humanities"
  ) {
    return (
      "Excellent! 📚 You're in the Art / Humanities department.\n\n" +
      "Here are the main Art / Humanities subjects. " +
      "Which ones are you good at? You can select as many as you want."
    );
  }

  if (
    department === "Commercial"
  ) {
    return (
      "Excellent! 💼 You're in the Commercial department.\n\n" +
      "Here are the main Commercial subjects. " +
      "Which ones are you good at? You can select as many as you want."
    );
  }

  return counselorQuestions
    .subjects
    .message;
}


/* ---------------------------------------------------------------------- */
/* SHOW COUNSELOR QUESTION                                                */
/* ---------------------------------------------------------------------- */

function showCounselorQuestion(
  stage,
  customMessage = null
) {

  const question =
    customMessage ||
    counselorQuestions[stage]?.message;

  /*
   * Important:
   * If the backend gives us a new field that the
   * frontend does not know yet, don't crash.
   */
  if (!question) {

    console.warn(
      "No counselor question found for stage:",
      stage
    );

    return;
  }


  appendChatMessage(
    question,
    "ai"
  );

  speak(question);


  const nextQText =
    $("#nextQText");

  if (nextQText) {
    nextQText.textContent =
      question.split("\n")[0];
  }


  const chips =
    $("#nextQChips");

  if (!chips) return;

  chips.innerHTML = "";


  let options =
    counselorQuestions[stage]?.options ||
    [];


  /* --------------------------------------------------------------- */
  /* DYNAMIC SUBJECTS                                                */
  /* --------------------------------------------------------------- */

  if (
    stage === "subjects"
  ) {

    const department =
      (
        state.onboarding.department ||
        ""
      )
        .toLowerCase()
        .replace(/\s+/g, " ")
        .trim();


    if (
      department.includes(
        "science"
      )
    ) {

      options = [
        "English Language",
        "Mathematics",
        "Biology",
        "Chemistry",
        "Physics",
        "Further Mathematics",
        "Agricultural Science",
        "Geography",
        "Health Science",
        "Computer Science",
        "Data Processing",
        "Technical Drawing",
        "Basic Technology",
      ];

    } else if (
      department.includes("art") ||
      department.includes(
        "humanities"
      )
    ) {

      options = [
        "English Language",
        "Literature-in-English",
        "Government",
        "History",
        "Economics",
        "Christian Religious Studies",
        "Islamic Religious Studies",
        "Civic Education",
        "French",
        "Yoruba",
        "Igbo",
        "Hausa",
        "Fine Art",
        "Music",
        "Cultural and Creative Arts",
      ];

    } else if (
      department.includes(
        "commercial"
      )
    ) {

      options = [
        "English Language",
        "Mathematics",
        "Economics",
        "Accounting",
        "Financial Accounting",
        "Commerce",
        "Office Practice",
        "Insurance",
        "Marketing",
        "Data Processing",
        "Business Studies",
        "Entrepreneurship",
      ];
    }
  }


  /* --------------------------------------------------------------- */
  /* FAVORITE SUBJECTS                                               */
  /* --------------------------------------------------------------- */

  if (
    stage === "favorite_subjects"
  ) {

    const strongest =
      state.onboarding
        .strengths || "";

    const subjectList =
      strongest
        .split(",")
        .map(
          (item) =>
            item.trim()
        )
        .filter(Boolean);

    if (
      subjectList.length
    ) {
      options =
        subjectList;
    }
  }


  /* --------------------------------------------------------------- */
  /* MULTI-SELECT SUBJECTS                                           */
  /* --------------------------------------------------------------- */

  if (
    stage === "subjects"
  ) {

    const selectedSubjects =
      new Set();


    options.forEach(
      (option) => {

        const chip =
          document.createElement(
            "div"
          );

        chip.className =
          "chip";

        chip.textContent =
          option;

        chip.dataset.answer =
          option;


        chip.addEventListener(
          "click",
          () => {

            if (
              selectedSubjects.has(
                option
              )
            ) {

              selectedSubjects.delete(
                option
              );

              chip.classList.remove(
                "selected"
              );

            } else {

              selectedSubjects.add(
                option
              );

              chip.classList.add(
                "selected"
              );
            }
          }
        );


        chips.appendChild(
          chip
        );
      }
    );


    const continueButton =
      document.createElement(
        "button"
      );

    continueButton.type =
      "button";

    continueButton.className =
      "subject-continue-btn";

    continueButton.textContent =
      "CONTINUE →";


    continueButton.addEventListener(
      "click",
      () => {

        if (
          selectedSubjects.size ===
          0
        ) {
          return;
        }

        const selected =
          Array.from(
            selectedSubjects
          );

        handleCounselorAnswer(
          selected.join(", ")
        );
      }
    );


    chips.appendChild(
      continueButton
    );

    return;
  }


  /* --------------------------------------------------------------- */
  /* NORMAL OPTIONS                                                  */
  /* --------------------------------------------------------------- */

  options.forEach(
    (option) => {

      const chip =
        document.createElement(
          "div"
        );

      chip.className =
        "chip";

      chip.textContent =
        option;

      chip.dataset.answer =
        option;


      chip.addEventListener(
        "click",
        () =>
          handleCounselorAnswer(
            option
          )
      );


      chips.appendChild(
        chip
      );
    }
  );
}


/* ---------------------------------------------------------------------- */
/* SEND PROFILE MESSAGE TO BACKEND                                        */
/* ---------------------------------------------------------------------- */

async function sendProfileMessage(
  message
) {

  const data =
    await apiPost(
      "/ask",
      {
        session_id:
          state.sessionId,

        message:
          message,
      }
    );


  state.sessionId =
    data.session_id;


  localStorage.setItem(
    SESSION_KEY,
    state.sessionId
  );


  if (data.profile) {
    state.profile =
      data.profile;
  }


  renderDashboardData(
    data
  );


  return data;
}


/* ---------------------------------------------------------------------- */
/* BUILD BACKEND-FRIENDLY PROFILE MESSAGE                                 */
/* ---------------------------------------------------------------------- */

function buildProfileMessage(stage, value) {

  const o = state.onboarding;

  if (stage === "class") {
    return (
      `I am currently in ${value}. ` +
      `I am a Nigerian secondary school student.`
    );
  }

  if (stage === "department") {
    return (
      `I am in ${o.className} ` +
      `and my department is ${value}.`
    );
  }

  if (stage === "subjects") {
    return (
      `I am a ${o.className} ${o.department} student. ` +
      `The subjects I enjoy most are ${value}.`
    );
  }

  if (stage === "strengths") {
    return `I am strongest in these subjects: ${value}.`;
  }

  if (stage === "favorite_subjects") {
    return `My favorite subjects are ${value}.`;
  }

  if (stage === "interests") {
    return `My interests include ${value}.`;
  }

  if (stage === "career") {

    const normalized =
      /^(no|not sure|i don't know|i dont know|none)$/i.test(
        value.trim()
      )
        ? "I'm not sure"
        : value.trim();

    return `My current career interest is ${normalized}.`;
  }

  if (stage === "jamb") {
    return `I have written JAMB / UTME: ${value}.`;
  }

  if (stage === "jambScore") {
    return `My JAMB / UTME score was ${value}.`;
  }

  if (stage === "waec") {
    return `I have written WAEC: ${value}.`;
  }

  if (stage === "waec_grades") {
    return `My WAEC subjects and grades are: ${value}.`;
  }

  if (stage === "neco") {
    return `I have written NECO: ${value}.`;
  }

  if (stage === "neco_grades") {
    return `My NECO subjects and grades are: ${value}.`;
  }

  if (stage === "admissionAnalysis") {
    return (
      "Please complete my admission analysis using my student profile."
    );
  }

  return value;
}
/* ---------------------------------------------------------------------- */
/* MAP BACKEND FIELD TO FRONTEND STAGE                                    */
/* ---------------------------------------------------------------------- */

function mapBackendStage(backendStage) {

  const stageMap = {

    class:
      "class",

    stream:
      "department",

    department:
      "department",

    subjects:
      "subjects",

    strengths:
      "favorite_subjects",

    favorite_subjects:
      "favorite_subjects",

    interests:
      "interests",

    career_goal:
      "career",

    career:
      "career",

    jamb_status:
      "jamb",

    jamb:
      "jamb",

    jamb_score:
      "jambScore",

    waec_status:
      "waec",

    waec:
      "waec",

    waec_grades:
      "waec_grades",

    neco_status:
      "neco",

    neco:
      "neco",

    neco_grades:
      "neco_grades",

    admission_analysis:
      "admissionAnalysis",

    recommendations:
      "recommendations",
  };

  return (
    stageMap[backendStage] ||
    backendStage
  );
}


/* ---------------------------------------------------------------------- */
/* HANDLE GUIDED COUNSELOR ANSWER                                         */
/* ---------------------------------------------------------------------- */

async function handleCounselorAnswer(answer) {

  const stage =
    state.onboarding.stage;

  console.log(
    "CURRENT ONBOARDING STAGE:",
    stage
  );

  if (
    !answer ||
    !answer.trim()
  ) {
    return;
  }

  appendChatMessage(
    answer,
    "user"
  );

  setAIState(
    "thinking"
  );


  /* --------------------------------------------------------------- */
  /* FINAL RECOMMENDATION STAGE                                     */
  /* --------------------------------------------------------------- */

  if (
    stage === "recommendations"
  ) {

    state.onboarding.active =
      false;

    saveOnboardingState();

    /*
     * Do NOT call /ask again here.
     * The backend has already generated
     * the recommendations.
     */

    if (
      state.lastCounselorData
    ) {

      renderDashboardData(
        state.lastCounselorData
      );
    }

    appendChatMessage(
      "Your recommendations are now available on your dashboard.",
      "ai"
    );

    setAIState(
      "ready"
    );

    return;
  }


  /* --------------------------------------------------------------- */
  /* SAVE ANSWER LOCALLY                                             */
  /* --------------------------------------------------------------- */

  switch (stage) {

    case "class":
      state.onboarding.className =
        answer;
      break;

    case "department":
      state.onboarding.department =
        answer;
      break;

    case "subjects":
      state.onboarding.subjects =
        answer;
      break;

    case "strengths":
      state.onboarding.strengths =
        answer;
      break;

    case "favorite_subjects":
      state.onboarding.favoriteSubjects =
        answer;
      break;

    case "interests":
      state.onboarding.interests =
        answer;
      break;

    case "career":
      state.onboarding.career =
        answer;
      break;

    case "jamb":
      state.onboarding.plansJamb =
        answer;
      break;

    case "jambScore":
      state.onboarding.jambScore =
        answer;
      break;

    case "waec":
      state.onboarding.waecStatus =
        answer;
      break;

    case "waec_grades":
      state.onboarding.waecGrades =
        answer;
      break;

    case "neco":
      state.onboarding.necoStatus =
        answer;
      break;

    case "neco_grades":
      state.onboarding.necoGrades =
        answer;
      break;

    case "admissionAnalysis":
      state.onboarding.admissionAnalysis =
        answer;
      break;
  }


  saveOnboardingState();


  /* --------------------------------------------------------------- */
  /* SEND EXACTLY ONE REQUEST TO BACKEND                             */
  /* --------------------------------------------------------------- */

  const backendMessage =
    buildProfileMessage(
      stage,
      answer
    );

  let data;

  try {

    data =
      await sendProfileMessage(
        backendMessage
      );

  } catch (error) {

    console.error(
      "Failed to send counselor answer:",
      error
    );

    appendChatMessage(
      "Sorry, I couldn't process that answer. Please try again.",
      "ai"
    );

    setAIState(
      "ready"
    );

    return;
  }


  if (!data) {

    setAIState(
      "ready"
    );

    return;
  }


  /*
   * Save the latest backend response.
   * This is useful when the student reaches
   * the recommendation stage.
   */

  state.lastCounselorData =
    data;


  /* --------------------------------------------------------------- */
  /* BACKEND DECIDES THE NEXT QUESTION                              */
  /* --------------------------------------------------------------- */

  const nextQuestion =
    data.next_best_question;


  if (
    !nextQuestion ||
    !nextQuestion.field
  ) {

    state.onboarding.active =
      false;

    saveOnboardingState();

    appendChatMessage(
      "Your CareerVoice profile is complete. Your recommendations are available on the dashboard.",
      "ai"
    );

    setAIState(
      "ready"
    );

    return;
  }


  const nextStage =
    mapBackendStage(
      nextQuestion.field
    );


  console.log(
    "BACKEND NEXT FIELD:",
    nextQuestion.field
  );

  console.log(
    "FRONTEND NEXT STAGE:",
    nextStage
  );


  state.onboarding.stage =
    nextStage;

  state.onboarding.active =
    true;

  saveOnboardingState();


  /* --------------------------------------------------------------- */
  /* SHOW ONLY ONE NEXT QUESTION                                    */
  /* --------------------------------------------------------------- */

  showCounselorQuestion(
    nextStage,
    nextQuestion.question ||
    null
  );

  setAIState(
    "ready"
  );
}


/* ---------------------------------------------------------------------- */
/* SEND NORMAL AI CHAT                                                    */
/* ---------------------------------------------------------------------- */

async function sendMessage(
  text
) {

  const trimmed =
    (text || "").trim();


  if (!trimmed) {
    return;
  }


  /*
   * Guided counselor mode.
   */

  if (
    state.onboarding.active
  ) {

    await handleCounselorAnswer(
      trimmed
    );


    if (
      $("#textInput")
    ) {
      $("#textInput").value =
        "";
    }


    return;
  }


  /*
   * Normal AI chat mode.
   */

  appendChatMessage(
    trimmed,
    "user"
  );


  if (
    $("#textInput")
  ) {
    $("#textInput").value =
      "";
  }


  if (
    $("#sendBtn")
  ) {
    $("#sendBtn").disabled =
      true;
  }


  setAIState(
    "thinking"
  );


  try {

    const data =
      await apiPost(
        "/ask",
        {
          session_id:
            state.sessionId,

          message:
            trimmed,
        }
      );


    state.sessionId =
      data.session_id;


    localStorage.setItem(
      SESSION_KEY,
      state.sessionId
    );


    appendChatMessage(
      data.reply,
      "ai"
    );


    setAIState(
      "responding"
    );


    speak(
      data.reply
    );


    renderDashboardData(
      data
    );

  } catch (err) {

    appendChatMessage(
      `Sorry, something went wrong: ${err.message}`,
      "ai"
    );

  } finally {

    setAIState(
      "ready"
    );


    if (
      $("#sendBtn")
    ) {
      $("#sendBtn").disabled =
        false;
    }
  }
}


/* ---------------------------------------------------------------------- */
/* VOICE RECOGNITION                                                       */
/* ---------------------------------------------------------------------- */

function setupVoiceRecognition() {

  const SpeechRecognitionImpl =
    window.SpeechRecognition ||
    window.webkitSpeechRecognition;


  const micBtn =
    $("#micBtn");


  const hint =
    $("#voiceHint");


  if (!micBtn) {
    return;
  }


  if (!SpeechRecognitionImpl) {

    if (hint) {
      hint.textContent =
        "Voice input isn't supported in this browser — please type instead.";
    }


    micBtn.disabled =
      true;

    micBtn.style.opacity =
      0.5;


    return;
  }


  const recognition =
    new SpeechRecognitionImpl();


  recognition.lang =
    "en-NG";


  recognition.interimResults =
    false;


  recognition.maxAlternatives =
    1;


  recognition.onstart =
    () => {

      state.listening =
        true;


      setAIState(
        "listening"
      );


      micBtn.classList.add(
        "listening"
      );


      micBtn.textContent =
        "🎙️ Listening...";


      if (hint) {
        hint.textContent =
          "Speak now — I'm listening.";
      }


      if (
        $("#waveform")
      ) {
        $("#waveform")
          .classList.remove(
            "idle"
          );
      }
    };


  recognition.onerror =
    (event) => {

      if (hint) {
        hint.textContent =
          `Voice error: ${event.error}. You can type instead.`;
      }


      setAIState(
        "ready"
      );
    };


  recognition.onend =
    () => {

      state.listening =
        false;


      if (
        state.aiStatus ===
        "listening"
      ) {

        setAIState(
          "ready"
        );
      }


      micBtn.classList.remove(
        "listening"
      );


      micBtn.textContent =
        "🎤 Start talking";


      if (
        $("#waveform")
      ) {

        $("#waveform")
          .classList.add(
            "idle"
          );
      }
    };


  recognition.onresult =
    (event) => {

      const transcript =
        event.results[0][0]
          .transcript;


      if (hint) {

        hint.textContent =
          `Heard: "${transcript}"`;
      }


      sendMessage(
        transcript
      );
    };


  micBtn.addEventListener(
    "click",
    () => {

      if (
        state.listening
      ) {

        recognition.stop();

      } else {

        try {

          recognition.start();

        } catch (err) {

          if (hint) {

            hint.textContent =
              "Could not start the microphone. Please try again.";
          }
        }
      }
    }
  );
}


/* ---------------------------------------------------------------------- */
/* DASHBOARD INTELLIGENCE                                                 */
/* ---------------------------------------------------------------------- */

function updateDashboardIntelligence(
  data
) {

  const profile =
    data.profile || {};


  const careers =
    data.career_matches || [];


  const universities =
    data.university_matches || [];


  const readiness =
    data.admission_readiness || {};


  const intelligenceStatus =
    $("#aiIntelligenceStatus");


  if (
    intelligenceStatus
  ) {

    if (
      careers.length ||
      universities.length
    ) {

      intelligenceStatus.textContent =
        "PROFILE INTELLIGENCE ACTIVE";

    } else {

      intelligenceStatus.textContent =
        "AWAITING PROFILE DATA";
    }
  }


  const careerSignal =
    $("#careerSignal");


  if (
    careerSignal
  ) {

    careerSignal.textContent =
      careers.length
        ? careers[0].name
        : "Scanning...";
  }


  const universitySignal =
    $("#universitySignal");


  if (
    universitySignal
  ) {

    universitySignal.textContent =
      universities.length
        ? (
            universities[0]
              .short_name ||
            universities[0].name ||
            "Scanning..."
          )
        : "Scanning...";
  }


  const admissionSignal =
    $("#admissionSignal");


  if (
    admissionSignal
  ) {

    admissionSignal.textContent =
      `${readiness.readiness_percent ?? 0}%`;
  }


  const profileSignal =
    $("#profileSignal");


  if (
    profileSignal
  ) {

    profileSignal.textContent =
      profile.name ||
      "Student profile";
  }


  /* Career DNA */

  const dnaContainer =
    $("#careerDNA");


  if (
    dnaContainer &&
    careers.length
  ) {

    dnaContainer.innerHTML =
      careers
        .slice(0, 5)
        .map(
          (career, index) => {

            const score =
              Number(
                career.match_percent ||
                0
              );


            return `
              <div class="dna-row">

                <div class="dna-name">

                  <span class="dna-index">
                    ${String(
                      index + 1
                    ).padStart(2, "0")}
                  </span>

                  <span>
                    ${career.name}
                  </span>

                </div>


                <div class="dna-track">

                  <div
                    class="dna-fill"
                    style="width:${Math.max(
                      0,
                      Math.min(
                        score,
                        100
                      )
                    )}%"
                  ></div>

                </div>


                <div class="dna-score">
                  ${score}%
                </div>

              </div>
            `;
          }
        )
        .join("");
  }


  /* University Intelligence */

  const uniIntel =
    $("#universityIntelligence");


  if (
    uniIntel &&
    universities.length
  ) {

    uniIntel.innerHTML =
      universities
        .slice(0, 5)
        .map(
          (uni, index) => `

            <div class="intel-row">

              <div class="intel-rank">
                ${String(
                  index + 1
                ).padStart(2, "0")}
              </div>


              <div class="intel-main">

                <strong>
                  ${
                    uni.short_name ||
                    uni.name
                  }
                </strong>

                <span>
                  ${
                    uni.state ||
                    uni.location ||
                    "Nigeria"
                  }
                </span>

              </div>


              <div class="intel-match">
                ${
                  uni.match_percent ??
                  0
                }%
              </div>

            </div>
          `
        )
        .join("");
  }


  /* Timestamp */

  const lastUpdated =
    $("#dashboardUpdated");


  if (
    lastUpdated
  ) {

    lastUpdated.textContent =
      `Updated ${new Date().toLocaleTimeString(
        [],
        {
          hour:
            "2-digit",

          minute:
            "2-digit",
        }
      )}`;
  }
}


/* ---------------------------------------------------------------------- */
/* DASHBOARD RENDERING                                                    */
/* ---------------------------------------------------------------------- */

function renderDashboardData(
  data
) {

  updateDashboardIntelligence(
    data
  );


  const profile =
    data.profile || {};


  const completeness =
    data.profile_completeness ?? 0;


  const careerMatches =
    data.career_matches || [];


  const uniMatches =
    data.university_matches || [];


  const readiness =
    data.admission_readiness || {};


  const nextQ =
    data.next_best_question;


  if (
    $("#greetingText")
  ) {

    $("#greetingText").textContent =
      profile.name
        ? `Good day, ${profile.name} 👋`
        : "Good day 👋";
  }


  if (
    $("#profilePercentVal")
  ) {

    $("#profilePercentVal")
      .textContent =
      `${completeness}%`;
  }


  if (
    $("#profilePercentNum")
  ) {

    $("#profilePercentNum")
      .textContent =
      `${completeness}%`;
  }


  const circumference =
    263.9;


  const offset =
    circumference -
    (
      circumference *
      completeness
    ) / 100;


  if (
    $("#profileRing")
  ) {

    $("#profileRing")
      .setAttribute(
        "stroke-dasharray",
        circumference
      );


    $("#profileRing")
      .setAttribute(
        "stroke-dashoffset",
        offset.toFixed(1)
      );
  }


  if (
    $("#profileFoot")
  ) {

    $("#profileFoot").innerHTML =
      `<b>Profile ${completeness}% complete</b><br>${
        completeness < 100
          ? "Keep talking to sharpen your matches."
          : "Your profile looks complete!"
      }`;
  }


  if (
    careerMatches.length &&
    $("#topCareerName") &&
    $("#topCareerPct")
  ) {

    $("#topCareerName")
      .textContent =
      careerMatches[0].name;


    $("#topCareerPct")
      .textContent =
      `${careerMatches[0].match_percent}% CareerVoice Match`;
  }


  if (
    uniMatches.length &&
    $("#topUniName") &&
    $("#topUniPct")
  ) {

    $("#topUniName")
      .textContent =
      uniMatches[0]
        .short_name ||
      uniMatches[0]
        .name;


    $("#topUniPct")
      .textContent =
      `${uniMatches[0].match_percent}% CareerVoice Match`;
  }


  if (
    $("#readinessPct")
  ) {

    $("#readinessPct")
      .textContent =
      `${readiness.readiness_percent ?? 0}%`;
  }


  if (
    $("#readinessNote")
  ) {

    $("#readinessNote")
      .textContent =
      readiness.career_name
        ? `For ${readiness.career_name}`
        : (
            readiness.message ||
            "Set a career goal first"
          );
  }


  const readinessFill =
    $("#readinessFill");


  if (
    readinessFill
  ) {

    readinessFill.style.width =
      `${Math.max(
        0,
        Math.min(
          Number(
            readiness.readiness_percent ||
            0
          ),
          100
        )
      )}%`;
  }


  renderCareerDiscovery(
    careerMatches
  );


  renderUniversityFinder(
    uniMatches
  );


  /*
   * During guided onboarding,
   * handleCounselorAnswer()
   * controls the next question.
   */

  if (
    !state.onboarding.active
  ) {

    renderNextQuestion(
      nextQ
    );
  }
}


/* ---------------------------------------------------------------------- */
/* CAREER DISCOVERY                                                        */
/* ---------------------------------------------------------------------- */

function renderCareerDiscovery(
  matches
) {

  const container =
    $("#careerDiscoveryList");


  if (!container) {
    return;
  }


  if (
    !matches.length
  ) {

    container.innerHTML =
      `
        <div class="empty-state">
          Start the conversation to see your matches here.
        </div>
      `;

    return;
  }


  const icons = {
    Science: "🧪",
    "Art/Humanities": "🎭",
    Commercial: "💼",
  };


  container.innerHTML =
    matches
      .slice(0, 4)
      .map(
        (m, i) => `

          <div class="match-row">

            <div class="match-left">

              <div class="match-icon">
                ${
                  icons[m.stream] ||
                  "🎯"
                }
              </div>

              ${m.name}

            </div>


            <div
              class="match-score ${
                i === 0
                  ? "top"
                  : ""
              }"
            >
              ${m.match_percent}%
            </div>

          </div>
        `
      )
      .join("");
}


/* ---------------------------------------------------------------------- */
/* UNIVERSITY FINDER                                                       */
/* ---------------------------------------------------------------------- */

function renderUniversityFinder(
  matches
) {

  const container =
    $("#universityFinderList");


  if (!container) {
    return;
  }


  if (
    !matches.length
  ) {

    container.innerHTML =
      `
        <div class="empty-state">
          Your top university matches will appear here.
        </div>
      `;

    return;
  }


  container.innerHTML =
    matches
      .slice(0, 4)
      .map(
        (m, i) => `

          <div class="match-row">

            <div class="match-left">

              <div class="match-icon">
                🎓
              </div>

              ${
                m.short_name ||
                m.name
              }

            </div>


            <div
              class="match-score ${
                i === 0
                  ? "top"
                  : ""
              }"
            >
              ${m.match_percent}%
            </div>

          </div>
        `
      )
      .join("");
}


/* ---------------------------------------------------------------------- */
/* NEXT QUESTION PANEL                                                     */
/* ---------------------------------------------------------------------- */

function renderNextQuestion(
  nextQ
) {

  const panel =
    $("#nextQPanel");


  if (!panel) {
    return;
  }


  if (!nextQ) {

    panel.style.display =
      "none";

    return;
  }


  panel.style.display =
    "block";


  if (
    $("#nextQText")
  ) {

    $("#nextQText")
      .textContent =
      nextQ.question;
  }


  if (
    $("#nextQChips")
  ) {

    $("#nextQChips")
      .innerHTML = "";


    (nextQ.options || [])
      .forEach(
        (opt) => {

          const chip =
            document.createElement(
              "div"
            );

          chip.className =
            "chip";

          chip.dataset.answer =
            opt;

          chip.textContent =
            opt;


          chip.addEventListener(
            "click",
            () => {

              sendMessage(
                opt
              );
            }
          );


          $("#nextQChips")
            .appendChild(
              chip
            );
        }
      );
  }
}


/* ---------------------------------------------------------------------- */
/* CAREERS CACHE                                                           */
/* ---------------------------------------------------------------------- */

async function loadCareersCache() {

  if (
    state.careersCache
  ) {

    return state.careersCache;
  }


  try {

    const data =
      await apiGet(
        "/careers"
      );


    state.careersCache =
      data.careers || [];

  } catch (err) {

    console.error(
      "Failed to load careers:",
      err
    );


    state.careersCache =
      [];
  }


  return state.careersCache;
}


/* ---------------------------------------------------------------------- */
/* COURSE SELECTION                                                        */
/* ---------------------------------------------------------------------- */

function showCourseSelection(
  career
) {

  const panel =
    $("#courseSelectionPanel");


  const options =
    $("#courseOptions");


  const description =
    $("#courseSelectionDescription");


  const status =
    $("#courseSelectionStatus");


  if (
    !panel ||
    !options
  ) {

    console.warn(
      "Course selection panel not found."
    );

    return;
  }


  const courses =
    career.university_courses ||
    [];


  if (
    !courses.length
  ) {

    panel.style.display =
      "none";

    return;
  }


  description.textContent =
    `You selected ${career.name}. Choose the specific course you would like to study.`;


  options.innerHTML =
    courses
      .map(
        (course) => `

          <button
            type="button"
            class="course-option-card"
            data-course="${course}"
          >
            ${course}
          </button>
        `
      )
      .join("");


  if (status) {
    status.textContent =
      "";
  }


  panel.style.display =
    "block";


  $$("#courseOptions .course-option-card")
    .forEach(
      (button) => {

        button.addEventListener(
          "click",
          async () => {

            const selectedCourse =
              button.dataset.course;


            if (
              !selectedCourse
            ) {
              return;
            }


            try {

              const data =
                await apiPost(
                  "/profile/update",
                  {
                    session_id:
                      state.sessionId,

                    target_course:
                      selectedCourse,
                  }
                );


              if (
                data &&
                data.profile
              ) {

                state.profile =
                  data.profile;
              }


              $$("#courseOptions .course-option-card")
                .forEach(
                  (item) => {

                    item.classList.remove(
                      "selected-course"
                    );
                  }
                );


              button.classList.add(
                "selected-course"
              );


              if (status) {

                status.textContent =
                  `Selected course: ${selectedCourse}`;
              }


              console.log(
                "Course selected:",
                selectedCourse
              );


              const sessionData =
                await apiGet(
                  `/session/${state.sessionId}`
                );


              renderDashboardData(
                sessionData
              );

            } catch (error) {

              console.error(
                "Failed to select course:",
                error
              );


              if (status) {

                status.textContent =
                  "Unable to save the course selection. Please try again.";
              }
            }
          }
        );
      }
    );
}


/* ---------------------------------------------------------------------- */
/* CAREERS GRID                                                            */
/* ---------------------------------------------------------------------- */

function renderCareersGrid(
  careers
) {

  const grid =
    $("#careersGrid");


  if (!grid) {
    return;
  }


  if (
    !careers.length
  ) {

    grid.innerHTML =
      `
        <div class="empty-state">
          No careers found.
        </div>
      `;

    return;
  }


  grid.innerHTML =
    careers
      .map(
        (c) => `

          <div
            class="info-card career-select-card"
            data-career-id="${c.id}"
            style="cursor:pointer;"
          >

            <span class="tag">
              ${c.stream}
            </span>


            <h3>
              ${c.name}
            </h3>


            <p>
              ${c.description}
            </p>


            <div class="meta">

              <span>
                UTME:
                ${
                  (
                    c.jamb_subjects ||
                    []
                  ).join(", ")
                }
              </span>

            </div>


            <div class="career-select-label">
              Select this career
            </div>

          </div>
        `
      )
      .join("");


  $$("#careersGrid .career-select-card")
    .forEach(
      (card) => {

        card.addEventListener(
          "click",
          async () => {

            const careerId =
              card.dataset.careerId;


            console.log(
              "SESSION ID:",
              state.sessionId
            );


            console.log(
              "CAREER ID:",
              careerId
            );


            if (!careerId) {
              return;
            }


            const career =
              careers.find(
                (c) =>
                  c.id ===
                  careerId
              );


            if (!career) {
              return;
            }


            try {

              const data =
                await apiPost(
                  "/profile/update",
                  {
                    session_id:
                      state.sessionId,

                    career_goal_id:
                      careerId,
                  }
                );


              if (
                data &&
                data.profile
              ) {

                state.profile =
                  data.profile;
              }


              $$("#careersGrid .career-select-card")
                .forEach(
                  (item) => {

                    item.classList.remove(
                      "selected-career"
                    );
                  }
                );


              card.classList.add(
                "selected-career"
              );


              console.log(
                "Career selected:",
                career.name,
                careerId
              );


              showCourseSelection(
                career
              );


              if (
                state.sessionId
              ) {

                const sessionData =
                  await apiGet(
                    `/session/${state.sessionId}`
                  );


                renderDashboardData(
                  sessionData
                );
              }

            } catch (error) {

              console.error(
                "Failed to select career:",
                error
              );
            }
          }
        );
      }
    );
}


/* ---------------------------------------------------------------------- */
/* CAREERS VIEW                                                            */
/* ---------------------------------------------------------------------- */

async function initCareersView() {

  const careers =
    await loadCareersCache();


  renderCareersGrid(
    careers
  );


  const filters =
    $(
      ".filter-chip, .filter-btn"
    );


  filters.forEach(
    (chip) => {

      chip.addEventListener(
        "click",
        () => {

          filters.forEach(
            (c) =>
              c.classList.remove(
                "active"
              )
          );


          chip.classList.add(
            "active"
          );


          const stream =
            chip.dataset.stream ||
            chip.dataset.filter;


          const filtered =
            !stream ||
            stream === "All"
              ? careers
              : careers.filter(
                  (c) =>
                    c.stream ===
                    stream
                );


          renderCareersGrid(
            filtered
          );
        }
      );
    }
  );
}


/* ---------------------------------------------------------------------- */
/* UNIVERSITIES                                                            */
/* ---------------------------------------------------------------------- */

function renderUniversitiesGrid(
  universities
) {

  const grid =
    $("#universitiesGrid");


  if (!grid) {
    return;
  }


  if (
    !universities.length
  ) {

    grid.innerHTML =
      `
        <div class="empty-state">
          No universities matched your search.
        </div>
      `;

    return;
  }


  grid.innerHTML =
    universities
      .map(
        (u) => {

          const rankingText =
            (u.rankings || [])
              .map(
                (r) =>
                  (
                    r.organization &&
                    r.organization !==
                      "Information requires verification"
                  )
                    ? `${r.organization} ${
                        r.year || ""
                      }: ${
                        r.position
                      }`
                    : (
                        r.position ||
                        "Ranking requires verification"
                      )
              )
              .join(" · ");


          return `

            <div class="info-card">

              <span class="tag">
                ${u.type}
              </span>


              <h3>
                ${u.name}
              </h3>


              <p>
                ${
                  u.location ||
                  u.state ||
                  ""
                }
              </p>


              <div class="meta">

                <span>
                  Courses:
                  ${
                    (
                      u.courses ||
                      []
                    )
                      .slice(0, 4)
                      .join(", ")
                  }

                  ${
                    (
                      u.courses ||
                      []
                    ).length > 4
                      ? "…"
                      : ""
                  }
                </span>


                <span>
                  ${rankingText}
                </span>


                ${
                  u.website
                    ? `
                      <span>
                        <a
                          href="${u.website}"
                          target="_blank"
                          rel="noopener"
                        >
                          ${u.website}
                        </a>
                      </span>
                    `
                    : ""
                }

              </div>

            </div>
          `;
        }
      )
      .join("");
}


/* ---------------------------------------------------------------------- */
/* UNIVERSITIES VIEW                                                       */
/* ---------------------------------------------------------------------- */

async function initUniversitiesView() {

  try {

    const data =
      await apiGet(
        "/universities"
      );


    renderUniversitiesGrid(
      data.universities || []
    );

  } catch (err) {

    if (
      $("#universitiesGrid")
    ) {

      $("#universitiesGrid").innerHTML =
        `
          <div class="error-state">
            Couldn't load universities:
            ${err.message}
          </div>
        `;
    }
  }


  const searchBtn =
    $("#uniSearchBtn");


  if (!searchBtn) {
    return;
  }


  searchBtn.addEventListener(
    "click",
    async () => {

      const course =
        $("#uniCourseInput")
          ?.value
          .trim() || "";


      const stateVal =
        $("#uniStateInput")
          ?.value
          .trim() || "";


      const type =
        $("#uniTypeInput")
          ?.value || "";


      const params =
        new URLSearchParams();


      if (course) {
        params.set(
          "course",
          course
        );
      }


      if (stateVal) {
        params.set(
          "state",
          stateVal
        );
      }


      if (type) {
        params.set(
          "type",
          type
        );
      }


      if (
        $("#universitiesGrid")
      ) {

        $("#universitiesGrid").innerHTML =
          `
            <div class="empty-state">
              Searching...
            </div>
          `;
      }


      try {

        const data =
          await apiGet(
            `/universities/search?${params.toString()}`
          );


        renderUniversitiesGrid(
          data.universities || []
        );

      } catch (err) {

        if (
          $("#universitiesGrid")
        ) {

          $("#universitiesGrid").innerHTML =
            `
              <div class="error-state">
                Search failed:
                ${err.message}
              </div>
            `;
        }
      }
    }
  );
}


/* ---------------------------------------------------------------------- */
/* ADMISSION INFO                                                          */
/* ---------------------------------------------------------------------- */

function renderAdmissionInfo(
  container,
  data
) {

  container.innerHTML = `

    <div class="result-block">

      <h4>
        Target course
      </h4>

      <p>
        ${
          data.target_course ||
          "Not specified"
        }
      </p>

    </div>


    <div class="result-block">

      <h4>
        WAEC / NECO subjects
      </h4>

      <p>
        ${
          (
            data.waec_subjects ||
            []
          ).join(", ") ||
          "Not specified"
        }
      </p>

    </div>


    <div class="result-block">

      <h4>
        JAMB / UTME subjects
      </h4>

      <p>
        ${
          (
            data.jamb_subjects ||
            []
          ).join(", ") ||
          "Not specified"
        }
      </p>

    </div>


    <div class="result-block">

      <h4>
        Suitable universities
      </h4>

      <ul>

        ${
          (
            data.suitable_universities ||
            []
          )
            .map(
              (u) =>
                `<li>
                  ${u.name}
                  (${u.type}, ${u.state})
                </li>`
            )
            .join("") ||
          "<li>None found in the current dataset</li>"
        }

      </ul>

    </div>


    <div class="result-block">

      <h4>
        Target score guidance
      </h4>

      <p>
        ${
          data.target_score_guidance ||
          "Not specified"
        }
      </p>

    </div>


    <div class="disclaimer">
      ${
        data.disclaimer ||
        ""
      }
    </div>
  `;
}


/* ---------------------------------------------------------------------- */
/* CAREER SELECT                                                           */
/* ---------------------------------------------------------------------- */

async function populateCareerSelect(
  selectEl
) {

  if (!selectEl) {
    return;
  }


  const careers =
    await loadCareersCache();


  selectEl.innerHTML =
    careers
      .map(
        (c) =>
          `<option value="${c.id}">
            ${c.name} (${c.stream})
          </option>`
      )
      .join("");
}


/* ---------------------------------------------------------------------- */
/* ADMISSION VIEW                                                          */
/* ---------------------------------------------------------------------- */

async function initAdmissionView() {

  const select =
    $("#admissionCareerSelect");


  if (!select) {
    return;
  }


  await populateCareerSelect(
    select
  );


  const button =
    $("#admissionLoadBtn");


  if (!button) {
    return;
  }


  button.addEventListener(
    "click",
    async () => {

      const container =
        $("#admissionResult");


      if (!container) {
        return;
      }


      container.innerHTML =
        `
          <div class="empty-state">
            Loading...
          </div>
        `;


      try {

        const data =
          await apiGet(
            `/admission?career_id=${encodeURIComponent(
              select.value
            )}`
          );


        renderAdmissionInfo(
          container,
          data
        );

      } catch (err) {

        container.innerHTML =
          `
            <div class="error-state">
              ${err.message}
            </div>
          `;
      }
    }
  );
}


/* ---------------------------------------------------------------------- */
/* JAMB VIEW                                                               */
/* ---------------------------------------------------------------------- */

async function initJambView() {

  const select =
    $("#jambCareerSelect");


  if (!select) {
    return;
  }


  await populateCareerSelect(
    select
  );


  const button =
    $("#jambLoadBtn");


  if (!button) {
    return;
  }


  button.addEventListener(
    "click",
    async () => {

      const container =
        $("#jambResult");


      if (!container) {
        return;
      }


      container.innerHTML =
        `
          <div class="empty-state">
            Loading...
          </div>
        `;


      try {

        const data =
          await apiGet(
            `/admission?career_id=${encodeURIComponent(
              select.value
            )}`
          );


        container.innerHTML = `

          <div class="result-block">

            <h4>
              Target course
            </h4>

            <p>
              ${
                data.target_course ||
                "Not specified"
              }
            </p>

          </div>


          <div class="result-block">

            <h4>
              UTME subject combination
            </h4>

            <p>
              ${
                (
                  data.jamb_subjects ||
                  []
                ).join(", ")
              }
            </p>

          </div>


          <div class="result-block">

            <h4>
              Competitiveness
            </h4>

            <p>
              ${
                data.competitiveness ||
                "Not specified"
              }
            </p>

          </div>


          <div class="result-block">

            <h4>
              Target score guidance
            </h4>

            <p>
              ${
                data.target_score_guidance ||
                "Not specified"
              }
            </p>

          </div>


          <div class="disclaimer">
            ${
              data.disclaimer ||
              ""
            }
          </div>

        `;

      } catch (err) {

        container.innerHTML =
          `
            <div class="error-state">
              ${err.message}
            </div>
          `;
      }
    }
  );
}


/* ---------------------------------------------------------------------- */
/* ACTION PLAN                                                             */
/* ---------------------------------------------------------------------- */

function renderActionPlan(
  steps
) {

  const container =
    $("#actionPlanList");


  if (!container) {
    return;
  }


  if (
    !steps ||
    !steps.length
  ) {

    container.innerHTML =
      `
        <div class="empty-state">
          Start a conversation on the dashboard first,
          then come back for your plan.
        </div>
      `;

    return;
  }


  container.innerHTML =
    steps
      .map(
        (s) => `

          <div class="plan-step">

            <div class="num">
              ${s.step}
            </div>


            <div>

              <h4>
                ${s.title}
              </h4>


              <p>
                ${s.description}
              </p>

            </div>

          </div>
        `
      )
      .join("");
}


/* ---------------------------------------------------------------------- */
/* ACTION PLAN VIEW                                                        */
/* ---------------------------------------------------------------------- */

async function initActionPlanView() {

  const button =
    $("#refreshPlanBtn");


  if (!button) {
    return;
  }


  button.addEventListener(
    "click",
    async () => {

      if (
        !state.sessionId
      ) {

        renderActionPlan(
          []
        );

        return;
      }


      if (
        $("#actionPlanList")
      ) {

        $("#actionPlanList").innerHTML =
          `
            <div class="empty-state">
              Building your plan...
            </div>
          `;
      }


      try {

        const data =
          await apiGet(
            `/action-plan?session_id=${encodeURIComponent(
              state.sessionId
            )}`
          );


        renderActionPlan(
          data.action_plan
        );

      } catch (err) {

        if (
          $("#actionPlanList")
        ) {

          $("#actionPlanList").innerHTML =
            `
              <div class="error-state">
                ${err.message}
              </div>
            `;
        }
      }
    }
  );
}


/* ---------------------------------------------------------------------- */
/* SMART SEARCH                                                            */
/* ---------------------------------------------------------------------- */

async function runSmartSearch(
  query
) {

  const container =
    $("#smartSearchResults");


  if (!container) {
    return;
  }


  if (!query.trim()) {

    container.innerHTML =
      "";

    return;
  }


  container.innerHTML =
    `
      <div class="empty-state">
        Searching...
      </div>
    `;


  const careers =
    await loadCareersCache();


  const q =
    query.toLowerCase();


  const careerMatches =
    careers.filter(
      (c) =>
        c.name
          .toLowerCase()
          .includes(q) ||

        c.description
          .toLowerCase()
          .includes(q) ||

        (
          c.keywords ||
          []
        ).some(
          (k) =>
            k
              .toLowerCase()
              .includes(q)
        )
    );


  let uniMatches =
    [];


  try {

    const data =
      await apiGet(
        `/universities/search?q=${encodeURIComponent(
          query
        )}`
      );


    uniMatches =
      data.universities ||
      [];

  } catch (err) {

    uniMatches =
      [];
  }


  if (
    !careerMatches.length &&
    !uniMatches.length
  ) {

    container.innerHTML =
      `
        <div class="empty-state">
          No matches found for "${query}".
        </div>
      `;

    return;
  }


  container.innerHTML = `

    ${
      careerMatches.length
        ? `

          <div
            class="panel"
            style="margin-bottom:16px;"
          >

            <div class="panel-head">

              <div class="panel-title">
                Careers
              </div>

            </div>


            <div class="cards-grid">

              ${
                careerMatches
                  .map(
                    (c) => `

                      <div class="info-card">

                        <span class="tag">
                          ${c.stream}
                        </span>


                        <h3>
                          ${c.name}
                        </h3>


                        <p>
                          ${c.description}
                        </p>

                      </div>
                    `
                  )
                  .join("")
              }

            </div>

          </div>

        `
        : ""
    }


    ${
      uniMatches.length
        ? `

          <div class="panel">

            <div class="panel-head">

              <div class="panel-title">
                Universities
              </div>

            </div>


            <div class="cards-grid">

              ${
                uniMatches
                  .map(
                    (u) => `

                      <div class="info-card">

                        <span class="tag">
                          ${u.type}
                        </span>


                        <h3>
                          ${u.name}
                        </h3>


                        <p>
                          ${
                            u.location ||
                            u.state ||
                            ""
                          }
                        </p>

                      </div>
                    `
                  )
                  .join("")
              }

            </div>

          </div>

        `
        : ""
    }

  `;
}


/* ---------------------------------------------------------------------- */
/* SMART SEARCH INITIALIZATION                                            */
/* ---------------------------------------------------------------------- */

function initSmartSearchView() {

  const button =
    $("#smartSearchBtn");


  const input =
    $("#smartSearchInput");


  if (
    !button ||
    !input
  ) {
    return;
  }


  button.addEventListener(
    "click",
    () =>
      runSmartSearch(
        input.value
      )
  );


  input.addEventListener(
    "keydown",
    (e) => {

      if (
        e.key ===
        "Enter"
      ) {

        runSmartSearch(
          input.value
        );
      }
    }
  );
}


/* ---------------------------------------------------------------------- */
/* NAVIGATION                                                              */
/* ---------------------------------------------------------------------- */

function initNavigation() {

  $$(".nav-item")
    .forEach(
      (item) => {

        item.addEventListener(
          "click",
          () =>
            switchView(
              item.dataset.view
            )
        );
      }
    );


  $$("[data-goto]")
    .forEach(
      (el) => {

        el.addEventListener(
          "click",
          () =>
            switchView(
              el.dataset.goto
            )
        );
      }
    );
}


/* ---------------------------------------------------------------------- */
/* SWITCH VIEW                                                             */
/* ---------------------------------------------------------------------- */

function switchView(
  view
) {

  $$(".nav-item")
    .forEach(
      (i) =>
        i.classList.toggle(
          "active",
          i.dataset.view ===
          view
        )
    );


  $$(".view")
    .forEach(
      (v) =>
        v.classList.toggle(
          "active",
          v.dataset.view ===
          view
        )
    );
}


/* ---------------------------------------------------------------------- */
/* WAVEFORM                                                                */
/* ---------------------------------------------------------------------- */

function buildWaveform() {

  const wf =
    $("#waveform");


  if (!wf) {
    return;
  }


  wf.innerHTML =
    "";


  const heights = [
    14, 24, 34, 20, 40,
    28, 16, 36, 22, 30,
    18, 38, 26, 16, 32
  ];


  heights.forEach(
    (h, i) => {

      const bar =
        document.createElement(
          "span"
        );


      bar.style.height =
        `${h}px`;


      bar.style.animationDelay =
        `${i * 0.06}s`;


      wf.appendChild(
        bar
      );
    }
  );


  wf.classList.add(
    "idle"
  );
}


/* ---------------------------------------------------------------------- */
/* LOAD EXISTING SESSION                                                   */
/* ---------------------------------------------------------------------- */

async function loadExistingSession() {

  /*
   * Create a session if one does not exist.
   */

  if (
    !state.sessionId
  ) {

    try {

      const session =
        await apiPost(
          "/session",
          {}
        );


      state.sessionId =
        session.session_id;


      localStorage.setItem(
        SESSION_KEY,
        state.sessionId
      );


      console.log(
        "New CareerVoice session created:",
        state.sessionId
      );

    } catch (err) {

      console.error(
        "Failed to create CareerVoice session:",
        err
      );


      return;
    }
  }


  try {

    const data =
      await apiGet(
        `/session/${encodeURIComponent(
          state.sessionId
        )}`
      );


    if (
      data.profile
    ) {

      state.profile =
        data.profile;
    }


    renderDashboardData({

      profile:
        data.profile,

      profile_completeness:
        data.profile_completeness,

      career_matches:
        data.career_matches,

      university_matches:
        data.university_matches,

      admission_readiness:
        data.admission_readiness,

      next_best_question:
        data.next_best_question,

    });


    /*
     * Load saved counselor state ONCE.
     */

    loadOnboardingState();


    if (
      !state.onboarding.stage
    ) {

      state.onboarding.stage =
        "class";
    }


  } catch (err) {

    console.error(
      "Failed to load CareerVoice session:",
      err
    );


    state.sessionId =
      null;


    localStorage.removeItem(
      SESSION_KEY
    );
  }
}


/* ---------------------------------------------------------------------- */
/* BACKEND STATUS                                                          */
/* ---------------------------------------------------------------------- */

async function checkBackendStatus() {

  try {

    await apiGet(
      "/info"
    );


    if (
      $("#statusPill")
    ) {

      $("#statusPill").innerHTML =
        `<span class="status-dot"></span> AI online`;
    }

  } catch (err) {

    if (
      $("#statusPill")
    ) {

      $("#statusPill").innerHTML =
        `
          <span
            class="status-dot"
            style="background:var(--bad);"
          ></span>

          Backend offline
        `;


      $("#statusPill").style.borderColor =
        "rgba(248,113,113,0.35)";


      $("#statusPill").style.background =
        "rgba(248,113,113,0.07)";


      $("#statusPill").style.color =
        "var(--bad)";
    }
  }
}


/* ---------------------------------------------------------------------- */
/* START COUNSELOR                                                         */
/* ---------------------------------------------------------------------- */

function startCounselor() {

  if (
    !$("#chatLog")
  ) {
    return;
  }


  const stage =
    state.onboarding.stage ||
    "class";


  /*
   * Do not start a completed counselor.
   */

  if (
    !state.onboarding.active
  ) {
    return;
  }


  /*
   * If the student is already in the
   * department stage, preserve the
   * previous class.
   */

  if (
    stage === "department" &&
    state.onboarding.className
  ) {

    showCounselorQuestion(
      "department"
    );

    return;
  }


  /*
   * Subjects need the stream-specific
   * message.
   */

  if (
    stage === "subjects"
  ) {

    const message =
      getDepartmentMessage(
        state.onboarding.department
      );


    showCounselorQuestion(
      "subjects",
      message
    );


    return;
  }


  showCounselorQuestion(
    stage
  );
}


/* ---------------------------------------------------------------------- */
/* INITIALIZE GUIDED COUNSELOR                                             */
/* ---------------------------------------------------------------------- */

function initializeGuidedCounselor() {

  loadOnboardingState();


  /*
   * If counselor has already been completed,
   * do not restart it.
   */

  if (
    !state.onboarding.active
  ) {
    return;
  }


  /*
   * Start from the saved stage.
   */

  startCounselor();
}


/* ---------------------------------------------------------------------- */
/* BOOTSTRAPPING                                                           */
/* ---------------------------------------------------------------------- */

document.addEventListener(
  "DOMContentLoaded",
  () => {

    buildWaveform();


    setAIState(
      "ready"
    );


    initNavigation();


    setupVoiceRecognition();


    const sendBtn =
      $("#sendBtn");


    const textInput =
      $("#textInput");


    if (
      sendBtn
    ) {

      sendBtn.addEventListener(
        "click",
        () =>
          sendMessage(
            textInput?.value ||
            ""
          )
      );
    }


    if (
      textInput
    ) {

      textInput.addEventListener(
        "keydown",
        (e) => {

          if (
            e.key ===
            "Enter"
          ) {

            e.preventDefault();

            sendMessage(
              textInput.value
            );
          }
        }
      );
    }


    checkBackendStatus();


    /*
     * Load the backend session.
     */

    loadExistingSession();


    /*
     * Initialize other application
     * views.
     */

    initCareersView();

    initUniversitiesView();

    initAdmissionView();

    initJambView();

    initActionPlanView();

    initSmartSearchView();


    /*
     * Start counselor once the page
     * has loaded.
     *
     * We deliberately DO NOT call
     * showCounselorQuestion("class")
     * from another button handler.
     */

    window.addEventListener(
      "load",
      () => {

        setTimeout(
          () => {

            initializeGuidedCounselor();

          },
          1000
        );
      }
    );


    /*
     * Optional voice activation button.
     *
     * It no longer creates a second
     * counselor flow.
     */

    const activateVoiceBtn =
      $("#activateVoiceBtn");


    const voiceActivation =
      $("#voiceActivation");


    if (
      activateVoiceBtn
    ) {

      activateVoiceBtn.addEventListener(
        "click",
        () => {

          voiceActivated =
            true;


          if (
            voiceActivation
          ) {

            voiceActivation.style.display =
              "none";
          }


          /*
           * Only start the counselor
           * if it is not already running.
           */

          if (
            !state.onboarding.active
          ) {

            state.onboarding.active =
              true;

            state.onboarding.stage =
              "class";

            saveOnboardingState();

            startCounselor();

          } else {

            /*
             * If the counselor is already
             * active, do not display another
             * question.
             */

            console.log(
              "CareerVoice counselor is already active."
            );
          }
        }
      );
    }

  }
);