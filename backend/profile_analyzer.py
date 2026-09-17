"""
CareerVoice AI - Profile Analyzer

Handles:
- SS1, SS2, SS3 detection
- Science, Art/Humanities, Commercial streams
- Subject detection
- Strongest subjects
- Favorite subjects
- Career goals
- JAMB information
- WAEC information
- NECO information
- Conversation stages
- Profile completeness
- Next best question
"""

import re
from typing import Dict, List, Optional, Tuple


# ============================================================
# SUBJECT KNOWLEDGE
# ============================================================

SUBJECTS = {
    "Science": [
        "English Language",
        "Mathematics",
        "Biology",
        "Chemistry",
        "Physics",
        "Further Mathematics",
        "Agricultural Science",
        "Health Science",
        "Computer Science",
    ],
    "Art/Humanities": [
        "English Language",
        "Mathematics",
        "Literature in English",
        "Government",
        "History",
        "Christian Religious Studies",
        "Islamic Religious Studies",
        "Economics",
        "Geography",
        "Civic Education",
        "French",
        "Fine Arts",
        "Music",
    ],
    "Commercial": [
        "English Language",
        "Mathematics",
        "Economics",
        "Commerce",
        "Financial Accounting",
        "Government",
        "Geography",
        "Marketing",
        "Business Studies",
        "Civic Education",
        "Computer Science",
    ],
}


# ============================================================
# STREAM ALIASES
# ============================================================

STREAM_ALIASES = {
    "science": "Science",
    "science student": "Science",
    "science class": "Science",
    "science department": "Science",

    "art": "Art/Humanities",
    "arts": "Art/Humanities",
    "humanities": "Art/Humanities",
    "art student": "Art/Humanities",
    "arts student": "Art/Humanities",
    "humanities student": "Art/Humanities",

    "commercial": "Commercial",
    "commerce": "Commercial",
    "commercial student": "Commercial",
    "commercial class": "Commercial",
}


# ============================================================
# CAREER INTENT
# ============================================================

CAREER_INTENT_PATTERNS = [
    r"\bi want to study\b",
    r"\bi want to become\b",
    r"\bi want to be\b",
    r"\bi would like to study\b",
    r"\bi would like to become\b",
    r"\bi would like to be\b",
    r"\bmy dream career is\b",
    r"\bmy dream job is\b",
    r"\bmy career goal is\b",
    r"\bi am interested in\b",
    r"\bi'm interested in\b",
    r"\bi am interested\b",
    r"\bi'm interested\b",
    r"\bi want a career in\b",
    r"\bi want a job in\b",
]


# ============================================================
# JAMB PATTERNS
# ============================================================

JAMB_WRITTEN_PATTERNS = [
    r"\bi wrote jamb\b",
    r"\bi have written jamb\b",
    r"\bi already wrote jamb\b",
    r"\bi took jamb\b",
    r"\bi sat for jamb\b",
    r"\bi have taken jamb\b",
    r"\bi wrote utme\b",
    r"\bi have written utme\b",
]

JAMB_NOT_WRITTEN_PATTERNS = [
    r"\bi have not written jamb\b",
    r"\bi haven't written jamb\b",
    r"\bi did not write jamb\b",
    r"\bi didn't write jamb\b",
    r"\bi am yet to write jamb\b",
    r"\bi haven't taken jamb\b",
    r"\bi have not taken jamb\b",
    r"\bi am preparing for jamb\b",
    r"\bi will write jamb\b",
    r"\bi plan to write jamb\b",
]


# ============================================================
# O'LEVEL PATTERNS
# ============================================================

WAEC_PATTERNS = [
    r"\bwaec\b",
    r"\bwest african examination council\b",
]

NECO_PATTERNS = [
    r"\bneco\b",
    r"\bnational examination council\b",
]


# ============================================================
# BASIC HELPERS
# ============================================================

def _normalise(text: str) -> str:
    """Normalize user text for easier matching."""
    return re.sub(r"\s+", " ", text.strip().lower())


def _contains_any(text: str, patterns: List[str]) -> bool:
    """Return True if any regex pattern matches."""
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


# ============================================================
# CLASS DETECTION
# ============================================================

def _detect_class(text: str) -> Optional[str]:
    """
    Detect Nigerian senior secondary school level.

    Supports:
    SS1, SS2, SS3
    SSS1, SSS2, SSS3
    Senior Secondary 1/2/3
    """
    text_lower = _normalise(text)

    patterns = [
        (r"\bss1\b", "SS1"),
        (r"\bss2\b", "SS2"),
        (r"\bss3\b", "SS3"),
        (r"\bsss1\b", "SS1"),
        (r"\bsss2\b", "SS2"),
        (r"\bsss3\b", "SS3"),
        (r"\bsenior secondary 1\b", "SS1"),
        (r"\bsenior secondary 2\b", "SS2"),
        (r"\bsenior secondary 3\b", "SS3"),
        (r"\bsenior secondary one\b", "SS1"),
        (r"\bsenior secondary two\b", "SS2"),
        (r"\bsenior secondary three\b", "SS3"),
    ]

    for pattern, value in patterns:
        if re.search(pattern, text_lower):
            return value

    return None


# ============================================================
# STREAM DETECTION
# ============================================================

def _detect_stream(text: str) -> Optional[str]:
    """Detect Science, Art/Humanities, or Commercial."""
    text_lower = _normalise(text)

    # Check longer phrases first.
    for alias, stream in sorted(
        STREAM_ALIASES.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        if re.search(rf"\b{re.escape(alias)}\b", text_lower):
            return stream

    return None


# ============================================================
# SUBJECT DETECTION
# ============================================================

SUBJECT_ALIASES = {
    "english": "English Language",
    "english language": "English Language",

    "math": "Mathematics",
    "maths": "Mathematics",
    "mathematics": "Mathematics",

    "biology": "Biology",
    "bio": "Biology",

    "chemistry": "Chemistry",
    "chem": "Chemistry",

    "physics": "Physics",
    "phys": "Physics",

    "further mathematics": "Further Mathematics",
    "further maths": "Further Mathematics",
    "further math": "Further Mathematics",

    "agric": "Agricultural Science",
    "agriculture": "Agricultural Science",
    "agricultural science": "Agricultural Science",

    "health science": "Health Science",

    "computer science": "Computer Science",
    "computer": "Computer Science",
    "computing": "Computer Science",

    "literature": "Literature in English",
    "literature in english": "Literature in English",

    "government": "Government",

    "history": "History",

    "crs": "Christian Religious Studies",
    "crk": "Christian Religious Studies",
    "christian religious studies": "Christian Religious Studies",

    "irs": "Islamic Religious Studies",
    "irk": "Islamic Religious Studies",
    "islamic religious studies": "Islamic Religious Studies",

    "economics": "Economics",
    "economy": "Economics",

    "geography": "Geography",
    "geo": "Geography",

    "civic": "Civic Education",
    "civic education": "Civic Education",

    "french": "French",

    "fine arts": "Fine Arts",
    "fine art": "Fine Arts",
    "art": "Fine Arts",

    "music": "Music",

    "commerce": "Commerce",

    "financial accounting": "Financial Accounting",
    "accounting": "Financial Accounting",

    "marketing": "Marketing",

    "business studies": "Business Studies",
}


def _detect_subjects(
    text: str,
    stream: Optional[str] = None,
) -> List[str]:
    """
    Detect subjects mentioned in text.

    If a stream is supplied, only subjects available for that
    stream are returned.
    """
    text_lower = _normalise(text)

    allowed_subjects = None

    if stream and stream in SUBJECTS:
        allowed_subjects = set(SUBJECTS[stream])

    detected = []

    # Longest aliases first prevents partial matches.
    for alias, subject in sorted(
        SUBJECT_ALIASES.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        if not re.search(rf"\b{re.escape(alias)}\b", text_lower):
            continue

        if allowed_subjects is not None and subject not in allowed_subjects:
            continue

        if subject not in detected:
            detected.append(subject)

    return detected


# ============================================================
# PROFILE CREATION
# ============================================================

def create_empty_profile() -> Dict:
    """Create a fresh CareerVoice student profile."""
    return {
        "school_level": None,
        "stream": None,

        "subjects": [],
        "favorite_subjects": [],
        "strongest_subjects": [],

        "interests": [],
        "skills": [],
        "strengths": [],
        "personality": [],
        "work_preferences": [],

        "career_interests": [],
        "career_goals": [],

        "career_goal_id": None,
        "target_course": None,

        "preferred_location": None,
        "university_preferences": [],
        "budget_preferences": [],

        "jamb_status": None,
        "jamb_score": None,

        "waec_status": None,
        "waec_grades": {},

        "neco_status": None,
        "neco_grades": {},

        "additional_information": None,

        "conversation_stage": "class",

        "last_user_message": None,
    }

def new_profile() -> Dict:
    """Backward-compatible alias used by backend.main."""
    return create_empty_profile()
# ============================================================
# CAREER GOAL EXTRACTION
# ============================================================

def _extract_career_text(text: str) -> Optional[str]:
    """
    Extract a career/course intention from a sentence.

    This is deliberately lightweight. The career engine performs
    the actual career matching.
    """
    clean = text.strip()

    for pattern in CAREER_INTENT_PATTERNS:
        match = re.search(
            pattern + r"\s+(.+)",
            clean,
            re.IGNORECASE,
        )

        if match:
            value = match.group(1).strip(" .,!?:;")
            if value:
                return value

    return None


# ============================================================
# JAMB EXTRACTION
# ============================================================

def _extract_jamb_score(text: str) -> Optional[int]:
    """
    Extract a plausible JAMB/UTME score from the message.

    Only scores between 0 and 400 are accepted.
    """
    patterns = [
        r"\bjamb(?:\s+score)?\s*(?:is|was|of)?\s*(\d{1,3})\b",
        r"\butme(?:\s+score)?\s*(?:is|was|of)?\s*(\d{1,3})\b",
        r"\bscore(?:d)?\s*(\d{1,3})\s*(?:in\s+)?(?:jamb|utme)\b",
        r"\b(\d{1,3})\s*(?:in\s+)?(?:jamb|utme)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            try:
                score = int(match.group(1))
            except ValueError:
                continue

            if 0 <= score <= 400:
                return score

    return None


# ============================================================
# MAIN PROFILE EXTRACTION
# ============================================================

def extract_from_text(
    text: str,
    profile: Dict,
) -> Dict:
    """
    Extract useful information from one student message.

    The extraction is stage-aware so a Biology mention during
    a career discussion does not automatically overwrite the
    student's strongest/favorite subjects.
    """
    if not isinstance(profile, dict):
        raise TypeError("profile must be a dictionary")

    if not text or not text.strip():
        return profile

    raw_text = text.strip()
    text_lower = _normalise(raw_text)

    # Always store the latest message.
    profile["last_user_message"] = raw_text

    # --------------------------------------------------------
    # IMPORTANT: capture the current stage BEFORE changing it
    # --------------------------------------------------------
    current_stage = profile.get("conversation_stage")

    # --------------------------------------------------------
    # CLASS
    # --------------------------------------------------------
    detected_class = _detect_class(raw_text)

    if detected_class:
        profile["school_level"] = detected_class

        if current_stage == "class":
            profile["conversation_stage"] = "stream"

    # --------------------------------------------------------
    # STREAM
    # --------------------------------------------------------
    detected_stream = _detect_stream(raw_text)

    if detected_stream:
        profile["stream"] = detected_stream

        if current_stage in {"class", "stream"}:
            profile["conversation_stage"] = "subjects"

    # --------------------------------------------------------
    # SUBJECTS
    # --------------------------------------------------------
    #
    # Subjects are intentionally processed mainly during the
    # subject-related stages.
    #
    # This prevents a later message such as:
    # "I want to become a medical doctor"
    #
    # from accidentally being treated as a subject response.
    # --------------------------------------------------------
    if current_stage in {
        "subjects",
        "strongest_subjects",
        "favorite_subjects",
    }:
        detected_subjects = _detect_subjects(
            raw_text,
            profile.get("stream"),
        )

        if detected_subjects:
            existing_subjects = profile.get("subjects", [])

            for subject in detected_subjects:
                if subject not in existing_subjects:
                    existing_subjects.append(subject)

            profile["subjects"] = existing_subjects

            if current_stage in {"subjects", "strongest_subjects"}:
                strongest = profile.get("strongest_subjects", [])

                for subject in detected_subjects:
                    if subject not in strongest:
                        strongest.append(subject)

                profile["strongest_subjects"] = strongest

                profile["conversation_stage"] = "favorite_subjects"

    # --------------------------------------------------------
    # FAVORITE SUBJECTS
    # --------------------------------------------------------
    if current_stage == "favorite_subjects":
        detected_favorite_subjects = _detect_subjects(
            raw_text,
            profile.get("stream"),
        )

        if detected_favorite_subjects:
            favorites = profile.get("favorite_subjects", [])

            for subject in detected_favorite_subjects:
                if subject not in favorites:
                    favorites.append(subject)

            profile["favorite_subjects"] = favorites

            profile["conversation_stage"] = "career_goal"

    # --------------------------------------------------------
    # CAREER GOAL
    # --------------------------------------------------------
    if current_stage in {
        "career_goal",
        "career",
        "career_interest",
    }:
        career_text = _extract_career_text(raw_text)

        # Handle direct career answers such as:
        # "Medicine"
        # "Engineering"
        # "Law"
        # "Accounting"
        if not career_text:
            simple_answer = raw_text.strip(" .,!?:;")

            if len(simple_answer.split()) <= 8:
                career_text = simple_answer

        if career_text:
            previous_career_id = profile.get("career_goal_id")

            profile["career_goals"] = [career_text]
            profile["career_interests"] = [career_text]

            # Career ID is resolved by career_engine.
            # Clear it here if the student changed their career.
            profile["career_goal_id"] = None

            # IMPORTANT:
            # A new broad career must not keep an old course.
            if previous_career_id is not None:
                profile["target_course"] = None

            profile["conversation_stage"] = "jamb"

    # --------------------------------------------------------
    # JAMB
    # --------------------------------------------------------
    jamb_score = _extract_jamb_score(raw_text)

    if jamb_score is not None:
        profile["jamb_score"] = jamb_score
        profile["jamb_status"] = "written"

        if current_stage in {"jamb", "jamb_score"}:
            profile["conversation_stage"] = "waec"

    elif _contains_any(text_lower, JAMB_NOT_WRITTEN_PATTERNS):
        profile["jamb_status"] = "not_written"

        if current_stage in {"jamb", "jamb_score"}:
            profile["conversation_stage"] = "waec"

    elif _contains_any(text_lower, JAMB_WRITTEN_PATTERNS):
        profile["jamb_status"] = "written"

        if current_stage == "jamb":
            profile["conversation_stage"] = "jamb_score"

    # --------------------------------------------------------
    # WAEC
    # --------------------------------------------------------
    if _contains_any(text_lower, WAEC_PATTERNS):
        if any(
            phrase in text_lower
            for phrase in [
                "awaiting",
                "waiting",
                "not yet",
                "pending",
            ]
        ):
            profile["waec_status"] = "awaiting"
        else:
            profile["waec_status"] = "mentioned"

        if current_stage == "waec":
            profile["conversation_stage"] = "neco"

    # --------------------------------------------------------
    # NECO
    # --------------------------------------------------------
    if _contains_any(text_lower, NECO_PATTERNS):
        if any(
            phrase in text_lower
            for phrase in [
                "awaiting",
                "waiting",
                "not yet",
                "pending",
            ]
        ):
            profile["neco_status"] = "awaiting"
        else:
            profile["neco_status"] = "mentioned"

        if current_stage == "neco":
            profile["conversation_stage"] = "admission"

    # --------------------------------------------------------
    # Additional interests / information
    # --------------------------------------------------------
    if current_stage in {
        "interests",
        "skills",
        "strengths",
        "personality",
        "work_preferences",
    }:
        profile["additional_information"] = raw_text

    return profile


# ============================================================
# NEXT BEST QUESTION
# ============================================================

def next_best_question(profile: Dict) -> Dict:
    """
    Determine the next question CareerVoice should ask.

    The flow is:

    SS1/SS2/SS3
        ↓
    Stream
        ↓
    Strongest subjects
        ↓
    Favorite subjects
        ↓
    Career goal
        ↓
    JAMB
        ↓
    JAMB score
        ↓
    WAEC
        ↓
    NECO
        ↓
    Admission analysis
    """

    school_level = profile.get("school_level")
    stream = profile.get("stream")
    strongest_subjects = profile.get("strongest_subjects", [])
    favorite_subjects = profile.get("favorite_subjects", [])
    career_goals = profile.get("career_goals", [])
    jamb_status = profile.get("jamb_status")
    jamb_score = profile.get("jamb_score")
    waec_status = profile.get("waec_status")
    neco_status = profile.get("neco_status")

    # --------------------------------------------------------
    # CLASS
    # --------------------------------------------------------
    if not school_level:
        profile["conversation_stage"] = "class"

        return {
            "field": "class",
            "question": "What class are you currently in? For example, SS1, SS2, or SS3.",
            "options": ["SS1", "SS2", "SS3"],
        }

    # --------------------------------------------------------
    # STREAM
    # --------------------------------------------------------
    if not stream:
        profile["conversation_stage"] = "stream"

        return {
            "field": "stream",
            "question": (
                "What department or stream are you in? "
                "Are you a Science, Art/Humanities, or Commercial student?"
            ),
            "options": [
                "Science",
                "Art/Humanities",
                "Commercial",
            ],
        }

    # --------------------------------------------------------
    # STRONGEST SUBJECTS
    # --------------------------------------------------------
    if not strongest_subjects:
        profile["conversation_stage"] = "subjects"

        options = SUBJECTS.get(stream, [])

        return {
            "field": "subjects",
            "question": (
                f"Here are the main {stream} subjects. "
                "Which ones are you good at? You can select as many as you want."
            ),
            "options": options,
        }

    # --------------------------------------------------------
    # FAVORITE SUBJECTS
    # --------------------------------------------------------
    if not favorite_subjects:
        profile["conversation_stage"] = "favorite_subjects"

        return {
            "field": "favorite_subjects",
            "question": (
                "Which of those subjects do you enjoy the most? "
                "You can select more than one."
            ),
            "options": strongest_subjects,
        }

    # --------------------------------------------------------
    # CAREER
    # --------------------------------------------------------
    if not career_goals:
        profile["conversation_stage"] = "career_goal"

        return {
            "field": "career_goal",
            "question": (
                "Do you already have a career or course in mind, "
                "or would you like me to recommend careers based on your profile?"
            ),
            "options": [
                "I have a career in mind",
                "Recommend careers for me",
                "I'm not sure yet",
            ],
        }

    # --------------------------------------------------------
    # JAMB STATUS
    # --------------------------------------------------------
    if jamb_status is None:
        profile["conversation_stage"] = "jamb"

        return {
            "field": "jamb",
            "question": (
                "Have you written JAMB/UTME yet?"
            ),
            "options": [
                "Yes, I have written JAMB",
                "No, I have not written JAMB",
                "I am preparing for JAMB",
            ],
        }

    # --------------------------------------------------------
    # JAMB SCORE
    # --------------------------------------------------------
    if jamb_status == "written" and jamb_score is None:
        profile["conversation_stage"] = "jamb_score"

        return {
            "field": "jamb_score",
            "question": (
                "What JAMB/UTME score did you get?"
            ),
            "options": [],
        }

    # --------------------------------------------------------
    # WAEC
    # --------------------------------------------------------
    if waec_status is None:
        profile["conversation_stage"] = "waec"

        return {
            "field": "waec",
            "question": (
                "What is your WAEC status? "
                "Have you written it, or are you still awaiting it?"
            ),
            "options": [
                "Written",
                "Awaiting",
                "Not yet written",
            ],
        }

    # --------------------------------------------------------
    # NECO
    # --------------------------------------------------------
    if neco_status is None:
        profile["conversation_stage"] = "neco"

        return {
            "field": "neco",
            "question": (
                "What is your NECO status? "
                "Have you written it, or are you still awaiting it?"
            ),
            "options": [
                "Written",
                "Awaiting",
                "Not yet written",
            ],
        }

    # --------------------------------------------------------
    # ADMISSION
    # --------------------------------------------------------
    profile["conversation_stage"] = "admission"

    return {
        "field": "admission",
        "question": (
            "Great. I now have enough information to analyze "
            "your career, course, university options, and admission readiness."
        ),
        "options": [],
    }


# ============================================================
# PROFILE COMPLETENESS
# ============================================================

def compute_completeness(profile: Dict) -> int:
    """
    Calculate profile completeness.

    Total = 100
    """

    score = 0

    if profile.get("school_level"):
        score += 10

    if profile.get("stream"):
        score += 10

    if profile.get("subjects") or profile.get("strongest_subjects"):
        score += 10

    if profile.get("interests") or profile.get("favorite_subjects"):
        score += 10

    if profile.get("career_goals") or profile.get("career_goal_id"):
        score += 15

    if profile.get("target_course"):
        score += 10

    if profile.get("jamb_status") is not None:
        score += 10

    if profile.get("jamb_score") is not None:
        score += 5

    if profile.get("waec_status") is not None:
        score += 5

    if profile.get("neco_status") is not None:
        score += 5

    return min(score, 100)


# ============================================================
# PROFILE SUMMARY
# ============================================================

def summarize_profile(profile: Dict) -> Dict:
    """Return a clean summary for the frontend/debugging."""

    return {
        "school_level": profile.get("school_level"),
        "stream": profile.get("stream"),

        "subjects": profile.get("subjects", []),
        "strongest_subjects": profile.get(
            "strongest_subjects",
            [],
        ),
        "favorite_subjects": profile.get(
            "favorite_subjects",
            [],
        ),

        "career_goals": profile.get(
            "career_goals",
            [],
        ),
        "career_goal_id": profile.get(
            "career_goal_id"
        ),
        "target_course": profile.get(
            "target_course"
        ),

        "jamb_status": profile.get(
            "jamb_status"
        ),
        "jamb_score": profile.get(
            "jamb_score"
        ),

        "waec_status": profile.get(
            "waec_status"
        ),
        "neco_status": profile.get(
            "neco_status"
        ),

        "conversation_stage": profile.get(
            "conversation_stage"
        ),

        "profile_completeness": compute_completeness(
            profile
        ),
    }