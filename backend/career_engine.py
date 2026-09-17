"""
career_engine.py

Deterministic, local career-matching logic. Given a student profile, this
module scores every career in the knowledge base and returns a ranked list
with a CareerVoice Match percentage and a human-readable explanation.

IMPORTANT: the "match percentage" is CareerVoice's own suitability estimate
based on the student's stated stream, subjects, interests, skills and goal.
It is NOT a university ranking and NOT an admission guarantee.
"""

from typing import Dict, List

from backend import career_knowledge


def _normalize(term: str) -> str:
    return term.strip().lower()


def _subject_overlap(profile_terms: List[str], career_terms: List[str]) -> List[str]:
    profile_set = {_normalize(t) for t in profile_terms}
    matches = []
    for term in career_terms:
        if _normalize(term) in profile_set:
            matches.append(term)
    return matches


def _score_career(profile: Dict, career: Dict) -> Dict:
    score = 0.0
    max_score = 0.0
    reasons = []

    # --- Stream alignment (heaviest single factor) ---
    max_score += 35
    student_stream = profile.get("stream")
    if student_stream:
        if career.get("stream") == student_stream:
            score += 35
        else:
            # cross-stream careers are still shown but scored low unless
            # the student explicitly asked for that specific career
            score += 5
    else:
        # unknown stream: don't penalize, but don't reward either
        score += 15

    # --- Explicit stated career goal ---
    max_score += 25
    if profile.get("career_goal_id") == career.get("id"):
        score += 25
        reasons.append("This matches the career goal you told me about.")

    # --- Subject overlap ---
    max_score += 20
    student_subjects = profile.get("subjects", [])
    career_subjects = career.get("required_subjects", [])
    subj_matches = _subject_overlap(student_subjects, career_subjects)
    if career_subjects:
        subj_ratio = len(subj_matches) / len(career_subjects)
        score += 20 * min(subj_ratio, 1.0)
    if subj_matches:
        reasons.append(f"You enjoy {', '.join(subj_matches)}, which lines up with this career.")

    # --- Interest / keyword overlap ---
    max_score += 15
    student_interests = profile.get("interests", []) + profile.get("subjects", [])
    career_keywords = career.get("keywords", [])
    interest_matches = _subject_overlap(student_interests, career_keywords)
    if career_keywords:
        interest_ratio = len(set(_normalize(m) for m in interest_matches)) / max(len(career_keywords), 1)
        score += 15 * min(interest_ratio * 2, 1.0)  # a couple of hits already counts strongly
    if interest_matches and not subj_matches:
        reasons.append(f"Your interest in {', '.join(sorted(set(interest_matches)))} fits this field.")

    # --- Skills overlap ---
    max_score += 5
    student_skills = profile.get("skills", [])
    career_skills = career.get("skills", [])
    skill_matches = _subject_overlap(student_skills, career_skills)
    if career_skills and student_skills:
        skill_ratio = len(skill_matches) / len(career_skills)
        score += 5 * min(skill_ratio, 1.0)
    if skill_matches:
        reasons.append(f"Your strength in {', '.join(skill_matches)} is valuable here.")

    percent = round(100 * score / max_score) if max_score else 0
    percent = max(0, min(percent, 99))  # never claim a "perfect" 100% match

    if not reasons:
        if student_stream and career.get("stream") == student_stream:
            reasons.append(f"This is a common and relevant path for {student_stream} students.")
        else:
            reasons.append("This is a general suggestion based on limited information so far.")

    return {
        "career_id": career["id"],
        "name": career["name"],
        "stream": career["stream"],
        "match_percent": percent,
        "reasons": reasons,
        "description": career.get("description", ""),
    }


def match_careers(profile: Dict, top_n: int = 6) -> List[Dict]:
    """Return the top N careers for this profile, ranked by match percentage."""
    careers = career_knowledge.all_careers()
    scored = [_score_career(profile, c) for c in careers]
    scored.sort(key=lambda r: r["match_percent"], reverse=True)
    return scored[:top_n]


def get_career_detail(career_id: str) -> Dict:
    career = career_knowledge.get_career(career_id)
    if not career:
        return {"error": f"Unknown career id '{career_id}'."}
    return career


def explain_match(profile: Dict, career_id: str) -> Dict:
    career = career_knowledge.get_career(career_id)
    if not career:
        return {"error": f"Unknown career id '{career_id}'."}
    return _score_career(profile, career)
