"""
main.py

CareerVoice AI backend entry point (FastAPI).

Pipeline for POST /ask:
    Student text/voice-transcript
        -> profile_analyzer.extract_from_text()      (deterministic)
        -> career_engine.match_careers()              (deterministic)
        -> university_engine.match_universities()     (deterministic)
        -> admission_engine.get_admission_info()       (deterministic)
        -> admission_engine.compute_admission_readiness()
        -> action_plan.generate_action_plan()          (deterministic)
        -> _generate_ai_reply()                        (Gemini, with graceful fallback)
        -> structured JSON response

Deterministic engines never depend on Gemini being available. Gemini is used
only to phrase a friendly conversational reply; if it fails for any reason
(missing key, network error, rate limit) the API still returns full,
correct structured data plus a locally generated text reply.
"""

import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend import (
    action_plan,
    admission_engine,
    career_engine,
    career_knowledge,
    profile_analyzer,
    university_engine,
)

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="CareerVoice AI",
    description="Voice career & university counselor for Nigerian students.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory session store.
# For a production deployment this should be swapped for a real database or
# cache (e.g. Redis) so profiles persist across restarts and instances.
# ---------------------------------------------------------------------------
SESSIONS: Dict[str, Dict] = {}


def get_or_create_session(session_id: Optional[str]) -> str:
    if session_id and session_id in SESSIONS:
        return session_id
    new_id = session_id or str(uuid.uuid4())
    SESSIONS[new_id] = profile_analyzer.new_profile()
    return new_id


def get_profile(session_id: str) -> Dict:
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail=f"Unknown session_id '{session_id}'.")
    return SESSIONS[session_id]


# ---------------------------------------------------------------------------
# Gemini integration (optional generative layer).
# ---------------------------------------------------------------------------
_GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")


def _gemini_client():
    """Lazily construct a Gemini client. Returns None if unavailable."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai  # imported lazily so the app still runs without the package installed
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def _build_fallback_reply(
    profile: Dict,
    career_matches: List[Dict],
    university_matches: List[Dict],
    next_question: Optional[Dict],
) -> str:
    """Guided deterministic CareerVoice counselor flow."""

    name = profile.get("name")
    stream = profile.get("stream")
    subjects = profile.get("subjects", [])
    strong_subjects = profile.get("strongest_subjects", [])
    favorite_subjects = profile.get("favorite_subjects", [])
    career_goal = profile.get("career_goal")
    jamb_score = profile.get("jamb_score")
    stage = profile.get("conversation_stage")

    # 1. Start by identifying the student's class.
    if not profile.get("school_level"):
        return (
            f"Hello{', ' + name if name else ''}! I'm CareerVoice, your AI Career "
            "and University Counselor. First, what class are you currently in — "
            "SS1, SS2, or SS3?"
        )

    # 2. Identify the student's stream.
    if not stream:
        return (
            f"Great{', ' + name if name else ''}! What department or stream are you in? "
            "Are you a Science, Art/Humanities, or Commercial student?"
        )

    # 3. Ask the student which subjects they are good at.
    if stage == "subjects" and not strong_subjects:
        if next_question:
            return next_question["question"]

        return (
            "Here are the main subjects for your stream. "
            "Which ones are you good at? You can select as many as you want."
        )

    # 4. After strong subjects are selected, ask which ones they enjoy most.
    if stage == "favorite_subjects" and not favorite_subjects:
        if next_question:
            return next_question["question"]

        selected = ", ".join(strong_subjects)
        return (
            f"Great! I've noted that you're good at {selected}. "
            "Which of those subjects do you enjoy the most?"
        )

    # 5. Ask about career direction after favorite subjects.
    if not career_goal:
        if next_question:
            return next_question["question"]

        return (
            "Excellent. Now let's talk about your future. "
            "Do you already have a career in mind, or would you like me to "
            "suggest careers based on your subjects and interests?"
        )

    # 6. Ask about JAMB before moving deeply into university planning.
    if jamb_score is None:
        if next_question:
            return next_question["question"]

        return (
            f"That's helpful. A career path is starting to take shape around "
            f"{career_goal}. Have you written JAMB/UTME yet, and if so, what "
            "did you score?"
        )

    # 7. Once enough information is available, provide career guidance.
    response_parts = []

    response_parts.append(
        f"Thanks{', ' + name if name else ''}! "
        f"I've noted that you're a {stream} student."
    )

    if career_matches:
        top = career_matches[0]
        response_parts.append(
            f"Based on your profile, {top['name']} currently looks like one of "
            f"your strongest CareerVoice matches at {top['match_percent']}%."
        )

    # 8. University recommendation comes after the basic profile is established.
    if university_matches:
        top_uni = university_matches[0]
        response_parts.append(
            f"For university options, {top_uni['name']} currently appears to be "
            f"a strong personalized match at {top_uni['match_percent']}%."
        )

    # 9. Continue with the next useful question if one exists.
    if next_question:
        response_parts.append(next_question["question"])

    return " ".join(response_parts)


def _generate_ai_reply(
    profile: Dict,
    user_message: str,
    career_matches: List[Dict],
    university_matches: List[Dict],
    next_question: Optional[Dict],
) -> Dict:
    """Try Gemini first; fall back to a deterministic reply on any failure."""
    client = _gemini_client()

    fallback_text = _build_fallback_reply(
        profile,
        career_matches,
        university_matches,
        next_question,
    )

    if client is None:
        return {"text": fallback_text, "source": "local"}

    try:
        context_summary = (
            f"Student profile so far: "
            f"school_level={profile.get('school_level')}, "
            f"stream={profile.get('stream')}, "
            f"subjects={profile.get('subjects')}, "
            f"strongest_subjects={profile.get('strongest_subjects')}, "
            f"favorite_subjects={profile.get('favorite_subjects')}, "
            f"interests={profile.get('interests')}, "
            f"career_goal={profile.get('career_goal')}, "
            f"preferred_location={profile.get('preferred_location')}."
        )

        if next_question:
            next_question_text = next_question.get("question", "")
            next_question_options = next_question.get("options", [])
        else:
            next_question_text = ""
            next_question_options = []

        prompt = (
            "You are CareerVoice AI, a warm and encouraging voice career counselor "
            "for Nigerian secondary-school students.\n\n"

            "IMPORTANT RULES:\n"
            "1. Respond naturally to what the student just said.\n"
            "2. Follow the NEXT QUESTION provided below exactly.\n"
            "3. Do NOT skip ahead to another stage of the conversation.\n"
            "4. Do NOT ask a career question when the next question is about subjects.\n"
            "5. Do NOT treat subjects as interests unless the student explicitly says "
            "they like, enjoy, or are interested in them.\n"
            "6. Do NOT invent university rankings, cut-off marks, or admission guarantees.\n"
            "7. Keep the response short and suitable for voice conversation.\n"
            "8. If options are provided, mention that the student can choose from them "
            "or select multiple when appropriate.\n\n"

            f"CURRENT STUDENT PROFILE:\n{context_summary}\n\n"

            f"STUDENT JUST SAID:\n\"{user_message}\"\n\n"

            f"NEXT QUESTION:\n{next_question_text}\n\n"

            f"NEXT QUESTION OPTIONS:\n{next_question_options}\n\n"

            "Generate a short response that acknowledges the student's answer and then "
            "asks the NEXT QUESTION. Do not replace the next question with a different question."
        )

        response = client.models.generate_content(
            model=_GEMINI_MODEL,
            contents=prompt,
        )

        text = getattr(response, "text", None)

        if not text:
            return {"text": fallback_text, "source": "local"}

        return {
            "text": text.strip(),
            "source": "gemini",
        }

    except Exception:
        return {"text": fallback_text, "source": "local"}

# ---------------------------------------------------------------------------
# Pydantic request/response models
# ---------------------------------------------------------------------------
class AskRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="Existing session id, or omit to start a new one.")
    message: str = Field(..., min_length=1, description="Student's text or transcribed speech.")


class ProfileUpdateRequest(BaseModel):
    session_id: str
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    state: Optional[str] = None
    stream: Optional[str] = None
    school: Optional[str] = None
    subjects: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    hobbies: Optional[List[str]] = None
    career_goal_id: Optional[str] = None
    preferred_university: Optional[str] = None
    preferred_state: Optional[str] = None
    preferred_university_type: Optional[str] = None
    waec: Optional[str] = None
    neco: Optional[str] = None
    jamb_score: Optional[int] = None
    target_course: Optional[str] = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.post("/session")
def create_session():
    session_id = get_or_create_session(None)

    return {
        "session_id": session_id,
        "profile": SESSIONS[session_id],
    }


@app.get("/")
def root():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/app/")
def app_home():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/app/{file_name:path}")
def app_file(file_name: str):
    target = (FRONTEND_DIR / file_name).resolve()
    frontend_root = FRONTEND_DIR.resolve()

    # Prevent access outside the frontend folder
    if frontend_root not in target.parents:
        raise HTTPException(status_code=404, detail="File not found.")

    if not target.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    return FileResponse(target)

@app.get("/info")
def info():
    return {
        "name": "CareerVoice AI",
        "description": "Voice career & university counselor for Nigerian secondary-school students.",
        "streams_supported": profile_analyzer.STREAMS,
        "careers_in_database": len(career_knowledge.all_careers()),
        "universities_in_database": len(university_engine.all_universities()),
        "gemini_configured": bool(os.environ.get("GEMINI_API_KEY")),
    }


@app.post("/ask")
def ask(payload: AskRequest):
    if not payload.message or not payload.message.strip():
        raise HTTPException(status_code=400, detail="`message` must not be empty.")

    session_id = get_or_create_session(payload.session_id)
    profile = SESSIONS[session_id]

    try:
        profile_analyzer.extract_from_text(payload.message, profile)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to analyze message: {exc}")

    career_matches = career_engine.match_careers(profile)
    university_matches = university_engine.match_universities(profile)
    completeness = profile_analyzer.compute_completeness(profile)
    next_question = profile_analyzer.next_best_question(profile)
    admission_readiness = admission_engine.compute_admission_readiness(profile)
    plan = action_plan.generate_action_plan(profile)

    ai_reply = _generate_ai_reply(profile, payload.message, career_matches, university_matches, next_question)

    return {
        "session_id": session_id,
        "reply": ai_reply["text"],
        "reply_source": ai_reply["source"],
        "profile": profile,
        "profile_completeness": completeness,
        "career_matches": career_matches,
        "university_matches": university_matches,
        "admission_readiness": admission_readiness,
        "next_best_question": next_question,
        "action_plan": plan,
    }


@app.get("/session/{session_id}")
def get_session(session_id: str):
    profile = get_profile(session_id)
    career_matches = career_engine.match_careers(profile)
    university_matches = university_engine.match_universities(profile)
    return {
        "session_id": session_id,
        "profile": profile,
        "profile_completeness": profile_analyzer.compute_completeness(profile),
        "career_matches": career_matches,
        "university_matches": university_matches,
        "admission_readiness": admission_engine.compute_admission_readiness(profile),
        "next_best_question": profile_analyzer.next_best_question(profile),
    }


@app.post("/profile/update")
def update_profile(payload: ProfileUpdateRequest):
    session_id = get_or_create_session(payload.session_id)
    profile = SESSIONS[session_id]

    updates = payload.dict(exclude={"session_id"}, exclude_none=True)
    for key, value in updates.items():
        if key in ("subjects", "interests", "skills", "hobbies") and isinstance(value, list):
            existing = set(x.lower() for x in profile.get(key, []))
            for item in value:
                if item.lower() not in existing:
                    profile.setdefault(key, []).append(item)
                    existing.add(item.lower())
        else:
            profile[key] = value

    if payload.career_goal_id:
        career = career_knowledge.get_career(payload.career_goal_id)
        if career:
            profile["career_goal"] = career["name"]

    return {
        "session_id": session_id,
        "profile": profile,
        "profile_completeness": profile_analyzer.compute_completeness(profile),
    }


@app.get("/careers")
def list_careers(stream: Optional[str] = None):
    if stream:
        careers = career_knowledge.careers_by_stream(stream)
        if not careers and stream not in profile_analyzer.STREAMS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown stream '{stream}'. Must be one of {profile_analyzer.STREAMS}.",
            )
        return {"stream": stream, "careers": careers}
    return {"careers": career_knowledge.all_careers()}


@app.get("/careers/{career_id}")
def get_career(career_id: str):
    career = career_knowledge.get_career(career_id)
    if not career:
        raise HTTPException(status_code=404, detail=f"Unknown career id '{career_id}'.")
    return career


@app.get("/universities")
def list_universities():
    return {"universities": university_engine.all_universities()}


@app.get("/universities/search")
def search_universities(
    course: Optional[str] = None,
    state: Optional[str] = None,
    type: Optional[str] = None,
    q: Optional[str] = None,
):
    results = university_engine.search_universities(course=course, state=state, uni_type=type, query=q)
    return {"count": len(results), "universities": results}


@app.get("/admission")
def get_admission(career_id: Optional[str] = None, session_id: Optional[str] = None):
    cid = career_id
    profile = None
    if session_id:
        profile = get_profile(session_id)
        cid = cid or profile.get("career_goal_id")

    if not cid:
        raise HTTPException(
            status_code=400,
            detail="Provide `career_id`, or a `session_id` whose profile already has a career_goal_id.",
        )

    info_result = admission_engine.get_admission_info(cid, profile)
    if "error" in info_result:
        raise HTTPException(status_code=404, detail=info_result["error"])
    return info_result


@app.get("/action-plan")
def get_action_plan(session_id: str):
    profile = get_profile(session_id)
    return {"session_id": session_id, "action_plan": action_plan.generate_action_plan(profile)}
