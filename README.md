# CareerVoice AI

**Voice Career & University Counselor for Nigerian Students**

CareerVoice AI helps Nigerian secondary-school students — across **Science**,
**Art/Humanities**, and **Commercial** streams — discover suitable careers,
find matching universities, understand WAEC/JAMB requirements, and get a
personalized action plan. Students can interact by typing or speaking.

---

## Architecture

```
Student
  → Text / Voice input
  → Speech recognition (browser)
  → FastAPI backend (/ask)
      → profile_analyzer   (extract stream, subjects, interests, goals)
      → career_engine      (career match %, with reasons)
      → university_engine  (university match %, verified rankings only)
      → admission_engine   (WAEC/JAMB subjects, admission readiness)
      → action_plan        (personalized 10-step plan)
      → Gemini (optional)  (conversational phrasing, with local fallback)
  → Structured JSON response
  → Dashboard UI updates + optional voice output (browser TTS)
```

All matching, profiling, and planning logic is **deterministic and local** —
it works fully even without a Gemini API key. Gemini is used only to make the
reply text sound more natural; if it's unavailable, unset, or errors out, the
app automatically falls back to a locally generated reply built from the same
structured data.

---

## Project structure

```
CareerVoice_AI/
├── backend/
│   ├── main.py               FastAPI app & routes
│   ├── profile_analyzer.py   Extracts stream/subjects/interests, tracks profile
│   ├── career_engine.py      Career matching & scoring
│   ├── career_knowledge.py   Loads/queries data/careers.json
│   ├── university_engine.py  University matching, filtering, search
│   ├── admission_engine.py   WAEC/JAMB info + admission readiness score
│   └── action_plan.py        Personalized step-by-step plan generator
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js                 Talks to the backend, handles voice I/O
├── data/
│   ├── careers.json           47 careers across all 3 streams
│   └── universities.json      22 Nigerian universities
├── .env / .env.example
├── requirements.txt
└── README.md
```

---

## Setup (Windows PowerShell)

```powershell
cd CareerVoice_AI

# 1. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your Gemini key (optional but recommended)
copy .env.example .env
# then open .env and paste your key from https://aistudio.google.com/app/apikey

# 4. Run the backend
uvicorn backend.main:app --reload
```

The API will be live at `http://127.0.0.1:8000` (interactive docs at
`http://127.0.0.1:8000/docs`).

### Running the frontend

The frontend is plain HTML/CSS/JS with no build step. Serve it with any
static server, e.g.:

```powershell
cd frontend
python -m http.server 5500
```

Then open `http://127.0.0.1:5500` in your browser. If your backend runs on a
different host/port, set it before `app.js` loads:

```html
<script>window.CAREERVOICE_API_BASE = "http://127.0.0.1:8000";</script>
<script src="app.js"></script>
```

Voice input uses the browser's built-in Web Speech API (best support in
Chrome/Edge). If unsupported, the mic button is disabled and text input still
works fully.

---

## API endpoints

| Method | Path                     | Purpose                                            |
|--------|--------------------------|-----------------------------------------------------|
| GET    | `/info`                  | System status, counts, whether Gemini is configured |
| POST   | `/ask`                   | Main conversational endpoint (text or transcript)   |
| GET    | `/session/{session_id}`  | Retrieve current profile + matches for a session    |
| POST   | `/profile/update`        | Manually set/append profile fields                  |
| GET    | `/careers`               | List all careers, optionally filtered by `?stream=` |
| GET    | `/careers/{career_id}`   | Full detail for one career                          |
| GET    | `/universities`          | List all universities                                |
| GET    | `/universities/search`   | Filter by `course`, `state`, `type`, or free text `q`|
| GET    | `/admission`             | WAEC/JAMB info for a career (`career_id` or `session_id`) |
| GET    | `/action-plan`           | Personalized action plan for a session               |

---

## Important distinctions the system always keeps separate

- **Career Match %** — how well a career fits the student's stream, subjects, and stated interests.
- **University Match %** — how suitable a university is for *this student's* target course, state and type preferences.
- **University Ranking** — only shown when a verified ranking organization + year is available; otherwise the system explicitly says ranking information requires verification. Rankings are never invented.
- **Admission Readiness %** — how prepared the student's profile currently is (JAMB score, WAEC/NECO status, subjects) relative to what their target career typically needs.
- **Profile Completeness %** — how much of the student's profile has been filled in.

## Data honesty

- WAEC/JAMB subject guidance reflects standard, widely published subject
  combinations, but the app always reminds students to confirm current
  cut-off marks and faculty-specific requirements with JAMB and the
  university directly.
- University rankings are never fabricated. Each university record either
  cites a real organization + year, or is marked as requiring verification.
- The AI counselor is instructed never to promise "guaranteed admission" —
  only "target score" language is used.

## Extending the data

`data/careers.json` and `data/universities.json` are plain JSON arrays —
add a new object following the existing shape to expand either database.
No code changes are required for new entries to appear in matching, search,
or admission lookups.
