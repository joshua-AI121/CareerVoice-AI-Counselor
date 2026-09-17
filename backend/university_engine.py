"""
university_engine.py

Loads the Nigerian university dataset (data/universities.json) and provides:
  - search_universities(): filter by course, state, or type
  - match_universities(): a personalized CareerVoice Match score per university
  - get_university(): direct lookup by id

IMPORTANT DISTINCTIONS (see project brief):
  - "ranking" in this dataset is an OFFICIAL third-party ranking (THE, QS,
    Webometrics, etc.). Where CareerVoice does not have a verified current
    value, it is explicitly marked "Information requires verification"
    rather than invented.
  - "CareerVoice Match" is our own personalized suitability score. It is
    never presented as an official ranking.
"""

import json
import os
from typing import Dict, List, Optional

from backend import career_knowledge

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
_UNIVERSITIES_PATH = os.path.join(_DATA_DIR, "universities.json")


def _load_universities() -> List[Dict]:
    try:
        with open(_UNIVERSITIES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


_UNIVERSITIES: List[Dict] = _load_universities()
_UNIVERSITIES_BY_ID: Dict[str, Dict] = {u["id"]: u for u in _UNIVERSITIES if "id" in u}


def reload_universities() -> None:
    global _UNIVERSITIES, _UNIVERSITIES_BY_ID
    _UNIVERSITIES = _load_universities()
    _UNIVERSITIES_BY_ID = {u["id"]: u for u in _UNIVERSITIES if "id" in u}


def all_universities() -> List[Dict]:
    return list(_UNIVERSITIES)


def get_university(university_id: str) -> Optional[Dict]:
    return _UNIVERSITIES_BY_ID.get(university_id)


def _course_matches(uni_courses: List[str], target_course: str) -> bool:
    target = target_course.strip().lower()
    for course in uni_courses:
        c = course.strip().lower()
        if target in c or c in target:
            return True
    return False


def search_universities(
    course: Optional[str] = None,
    state: Optional[str] = None,
    uni_type: Optional[str] = None,
    query: Optional[str] = None,
) -> List[Dict]:
    results = list(_UNIVERSITIES)

    if course:
        results = [u for u in results if _course_matches(u.get("courses", []), course)]
    if state:
        results = [u for u in results if u.get("state", "").lower() == state.strip().lower()]
    if uni_type:
        results = [u for u in results if u.get("type", "").lower() == uni_type.strip().lower()]
    if query:
        q = query.strip().lower()
        results = [
            u for u in results
            if q in u.get("name", "").lower()
            or q in u.get("short_name", "").lower()
            or any(q in c.lower() for c in u.get("courses", []))
        ]
    return results


def _target_course_for_profile(profile: Dict, career_id: Optional[str] = None) -> Optional[str]:
    # Always respect the student's explicitly selected specific course.
    selected_course = profile.get("target_course")
    if selected_course:
        return selected_course

    # Fall back to the career's first university course only when
    # the student has not selected a specific course yet.
    cid = career_id or profile.get("career_goal_id")

    if not cid:
        return None

    career = career_knowledge.get_career(cid)

    if not career:
        return None

    courses = career.get("university_courses", [])

    return courses[0] if courses else career.get("name")


def _score_university(profile: Dict, university: Dict, target_course: Optional[str]) -> Dict:
    score = 0.0
    max_score = 0.0
    reasons = []

    # --- Course availability ---
    max_score += 50
    if target_course:
        if _course_matches(university.get("courses", []), target_course):
            score += 50
            reasons.append(f"Offers {target_course}.")
        else:
            score += 10  # still a real university, just not an exact course match
    else:
        score += 25

    # --- Location preference ---
    max_score += 25
    preferred_state = profile.get("preferred_state") or profile.get("state")
    if preferred_state:
        if university.get("state", "").lower() == preferred_state.lower():
            score += 25
            reasons.append(f"Located in {university.get('state')}, matching your location preference.")
        else:
            score += 8
    else:
        score += 15

    # --- Type preference (federal/state/private) ---
    max_score += 15
    preferred_type = profile.get("preferred_university_type")
    if preferred_type:
        if university.get("type", "").lower() == preferred_type.lower():
            score += 15
            reasons.append(f"{university.get('type')} university, matching your preference.")
        else:
            score += 3
    else:
        score += 10

    # --- Explicit named preference ---
    max_score += 10
    preferred_name = (profile.get("preferred_university") or "").strip().lower()
    if preferred_name:
        if preferred_name in university.get("name", "").lower() or preferred_name in university.get("short_name", "").lower():
            score += 10
            reasons.append("This is the university you mentioned.")
    else:
        score += 5

    percent = round(100 * score / max_score) if max_score else 0
    percent = max(0, min(percent, 99))

    if not reasons:
        reasons.append("A reputable Nigerian university that may suit your profile.")

    return {
        "university_id": university["id"],
        "name": university["name"],
        "short_name": university.get("short_name"),
        "type": university.get("type"),
        "state": university.get("state"),
        "location": university.get("location"),
        "match_percent": percent,
        "reasons": reasons,
        "rankings": university.get("rankings", []),
        "website": university.get("website"),
        "admission_note": university.get("admission_note"),
    }


def match_universities(profile: Dict, career_id: Optional[str] = None, top_n: int = 6) -> List[Dict]:
    target_course = _target_course_for_profile(profile, career_id)
    scored = [_score_university(profile, u, target_course) for u in _UNIVERSITIES]
    scored.sort(key=lambda r: r["match_percent"], reverse=True)
    return scored[:top_n]

