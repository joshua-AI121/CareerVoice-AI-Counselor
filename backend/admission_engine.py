"""
admission_engine.py

Provides WAEC/NECO and JAMB/UTME guidance for a given career, plus a
personalized "Admission Readiness" score for a student profile.

Data-honesty rules:
  - Subject combinations come from the CareerVoice knowledge base.
  - Students are told to confirm current requirements against JAMB and
    the specific university.
  - Numeric JAMB values below are CareerVoice planning targets only.
  - They are NOT official university cut-offs and do NOT guarantee admission.
"""

from typing import Dict, List, Optional

from backend import career_knowledge, university_engine


# =========================================================
# COMPETITIVENESS
# =========================================================

COMPETITIVENESS = {
    "medicine": "very high",
    "dentistry": "very high",
    "law": "very high",
    "pharmacy": "high",
    "nursing": "high",
    "computer_science": "high",
    "software_engineering": "high",
    "accounting": "high",
    "mass_communication": "high",
    "cybersecurity": "medium-high",
    "data_science": "medium-high",
    "banking_finance": "medium-high",
    "economics_career": "medium-high",
    "engineering": "medium-high",
    "psychology": "medium",
    "political_science": "medium",
    "international_relations": "medium",
    "business_administration": "medium",
    "marketing": "medium",
    "architecture": "medium-high",
    "veterinary_medicine": "high",
    "medical_lab_science": "medium-high",
    "physiotherapy": "medium-high",
    "radiography": "medium",
}


TARGET_SCORE_BANDS = {
    "very high": (
        "Many candidates who gain admission in this field score well above "
        "the national average — treat 250+ as a target rather than a guarantee."
    ),
    "high": (
        "This field is competitive. A strong target is usually in the "
        "low-to-mid 200s and above."
    ),
    "medium-high": (
        "This field sees solid competition. Aim comfortably above the "
        "JAMB national benchmark."
    ),
    "medium": (
        "Requirements are moderate, but a good score still improves "
        "your options meaningfully."
    ),
    "default": (
        "Aim as high as you reasonably can — a higher score gives you "
        "more university and course options."
    ),
}


# =========================================================
# JAMB TARGETS
# =========================================================

JAMB_TARGETS = {
    "very high": (250, 300),
    "high": (230, 280),
    "medium-high": (210, 260),
    "medium": (190, 240),
    "unrated": (200, 250),
}


# =========================================================
# ADMISSION TARGET RESOLUTION
# =========================================================

def _resolve_admission_target(
    profile: Dict,
    career_id: Optional[str] = None
) -> Dict:
    """
    Resolve the student's broad career and specific course.

    The student's explicitly selected target_course always takes priority.
    """

    cid = career_id or profile.get("career_goal_id")

    if not cid:
        return {
            "career": None,
            "career_id": None,
            "target_course": profile.get("target_course"),
        }

    career = career_knowledge.get_career(cid)

    if not career:
        return {
            "career": None,
            "career_id": cid,
            "target_course": profile.get("target_course"),
        }

    # Always respect the student's explicitly selected course.
    target_course = profile.get("target_course")

    # If no specific course has been selected yet, use the first
    # course associated with the broad career as a planning fallback.
    if not target_course:
        courses = career.get("university_courses", [])

        target_course = (
            courses[0]
            if courses
            else career.get("name")
        )

    return {
        "career": career,
        "career_id": cid,
        "target_course": target_course,
    }


# =========================================================
# JAMB / UTME ANALYSIS
# =========================================================

def analyze_jamb_readiness(
    profile: Dict,
    career_id: Optional[str] = None
) -> Dict:
    """
    Analyze JAMB/UTME status for the selected career/course.

    Numeric values are CareerVoice planning targets only.
    They are not official university cut-offs.
    """

    resolved = _resolve_admission_target(
        profile,
        career_id
    )

    cid = resolved["career_id"]
    career = resolved["career"]
    target_course = resolved["target_course"]

    if not cid:
        return {
            "status": "no_career",
            "message": "Select a career first.",
        }

    if not career:
        return {
            "status": "unknown_career",
            "message": f"Unknown career id '{cid}'.",
        }

    competitiveness = COMPETITIVENESS.get(
        cid,
        "unrated"
    )

    target_low, target_high = JAMB_TARGETS.get(
        competitiveness,
        JAMB_TARGETS["unrated"]
    )

    jamb_status = profile.get("jamb_status")
    jamb_score = profile.get("jamb_score")

    # -----------------------------------------------------
    # JAMB NOT WRITTEN
    # -----------------------------------------------------

    if jamb_status in {
        "not_written",
        "not yet",
        "awaiting",
    }:
        return {
            "status": "not_written",
            "career_id": cid,
            "career_name": career.get("name"),
            "target_course": target_course,
            "competitiveness": competitiveness,
            "target_low": target_low,
            "target_high": target_high,
            "message": (
                f"You have not written JAMB yet. For {target_course}, "
                f"a sensible CareerVoice planning target is around "
                f"{target_low}-{target_high}. This is a preparation target, "
                "not an official university cut-off or admission guarantee."
            ),
            "official_cutoff_note": (
                "Always check the current JAMB policy and the specific "
                "university's current departmental admission requirements."
            ),
        }

    # -----------------------------------------------------
    # JAMB WRITTEN BUT SCORE MISSING
    # -----------------------------------------------------

    if jamb_status == "written" and jamb_score is None:
        return {
            "status": "score_missing",
            "career_id": cid,
            "career_name": career.get("name"),
            "target_course": target_course,
            "competitiveness": competitiveness,
            "target_low": target_low,
            "target_high": target_high,
            "message": (
                "Your JAMB status is recorded as written, "
                "but your score is missing."
            ),
        }

    # -----------------------------------------------------
    # JAMB SCORE EXISTS
    # -----------------------------------------------------

    if jamb_score is not None:

        try:
            score = float(jamb_score)
        except (TypeError, ValueError):
            return {
                "status": "invalid_score",
                "career_id": cid,
                "career_name": career.get("name"),
                "target_course": target_course,
                "message": (
                    "The JAMB score provided is not a valid number."
                ),
            }

        if score >= target_high:
            assessment = "strong"

            message = (
                f"Your JAMB score of {int(score)} is above the "
                f"CareerVoice planning target for {target_course}."
            )

        elif score >= target_low:
            assessment = "competitive"

            message = (
                f"Your JAMB score of {int(score)} is within the "
                f"CareerVoice planning target range for {target_course}."
            )

        else:
            assessment = "needs_improvement"

            message = (
                f"Your JAMB score of {int(score)} is below the "
                f"CareerVoice planning target for {target_course}. "
                "Consider improving your options and checking the "
                "specific university requirements."
            )

        return {
            "status": "scored",
            "career_id": cid,
            "career_name": career.get("name"),
            "target_course": target_course,
            "jamb_score": int(score),
            "competitiveness": competitiveness,
            "target_low": target_low,
            "target_high": target_high,
            "assessment": assessment,
            "message": message,
            "official_cutoff_note": (
                "CareerVoice targets are planning guidance only. "
                "They are not official university cut-offs and do not "
                "guarantee admission."
            ),
        }

    # -----------------------------------------------------
    # JAMB NOT PROVIDED
    # -----------------------------------------------------

    return {
        "status": "not_provided",
        "career_id": cid,
        "career_name": career.get("name"),
        "target_course": target_course,
        "competitiveness": competitiveness,
        "target_low": target_low,
        "target_high": target_high,
        "message": (
            "JAMB information has not been provided yet."
        ),
    }


# =========================================================
# ADMISSION INFORMATION
# =========================================================

def get_admission_info(
    career_id: str,
    profile: Optional[Dict] = None
) -> Dict:

    career = career_knowledge.get_career(
        career_id
    )

    if not career:
        return {
            "error": f"Unknown career id '{career_id}'."
        }

    target_course = (
        profile.get("target_course")
        if profile and profile.get("target_course")
        else (
            career.get(
                "university_courses",
                [career.get("name")]
            )[0]
        )
    )

    suitable_universities = (
        university_engine.search_universities(
            course=target_course
        )
    )

    competitiveness = COMPETITIVENESS.get(
        career_id,
        "unrated"
    )

    target_score_note = TARGET_SCORE_BANDS.get(
        competitiveness,
        TARGET_SCORE_BANDS["default"]
    )

    return {
        "career_id": career_id,
        "career_name": career["name"],
        "target_course": target_course,
        "stream": career["stream"],
        "waec_subjects": career.get(
            "waec_subjects",
            []
        ),
        "jamb_subjects": career.get(
            "jamb_subjects",
            []
        ),
        "university_courses": career.get(
            "university_courses",
            []
        ),
        "suitable_universities": [
            {
                "id": u["id"],
                "name": u["name"],
                "short_name": u.get("short_name"),
                "type": u.get("type"),
                "state": u.get("state"),
            }
            for u in suitable_universities
        ],
        "competitiveness": competitiveness,
        "target_score_guidance": target_score_note,
        "disclaimer": (
            "Subject combinations shown here reflect long-standing "
            "JAMB/WAEC patterns. Always confirm the exact requirements "
            "and cut-off marks for the current admission cycle on the "
            "official JAMB portal and the specific university's "
            "admissions page before registering."
        ),
    }


# =========================================================
# O'LEVEL ELIGIBILITY ENGINE
# =========================================================

OLEVEL_CREDIT_GRADES = {
    "A1",
    "B2",
    "B3",
    "C4",
    "C5",
    "C6",
}


SUBJECT_GROUPS = {

    "arts": {
        "literature-in-english",
        "government",
        "history",
        "christian religious studies",
        "islamic religious studies",
        "geography",
        "fine art",
        "visual art",
        "music",
        "french",
        "yoruba",
        "igbo",
        "hausa",
        "arabic",
    },

    "social_science": {
        "economics",
        "government",
        "geography",
        "commerce",
        "accounting",
        "financial accounting",
        "marketing",
        "insurance",
        "business studies",
    },

    "commercial": {
        "economics",
        "commerce",
        "accounting",
        "financial accounting",
        "marketing",
        "insurance",
        "business studies",
    },

    "science": {
        "biology",
        "chemistry",
        "physics",
        "agricultural science",
        "further mathematics",
        "computer studies",
        "computer science",
    },
}


def _normalize_subject(
    subject: str
) -> str:
    """
    Normalize subject names for reliable comparison.
    """

    if not subject:
        return ""

    value = str(subject).strip().lower()

    aliases = {
        "english": "english language",
        "english lang": "english language",

        "literature in english":
            "literature-in-english",

        "literature in english language":
            "literature-in-english",

        "lit in english":
            "literature-in-english",

        "crs":
            "christian religious studies",

        "christian religion":
            "christian religious studies",

        "christian religious knowledge":
            "christian religious studies",

        "crk":
            "christian religious studies",

        "irs":
            "islamic religious studies",

        "islamic religion":
            "islamic religious studies",

        "islamic religious knowledge":
            "islamic religious studies",

        "irk":
            "islamic religious studies",

        "financial accounting":
            "accounting",

        "math":
            "mathematics",

        "fmath":
            "further mathematics",

        "further math":
            "further mathematics",

        "agric":
            "agricultural science",

        "agriculture":
            "agricultural science",

        "civic":
            "civic education",

        "civic education":
            "civic education",
    }

    return aliases.get(
        value,
        value
    )


def _grade_is_credit(
    grade: str
) -> bool:

    if not grade:
        return False

    return (
        str(grade)
        .strip()
        .upper()
        in OLEVEL_CREDIT_GRADES
    )


def _has_olevel_credit(
    grades: Dict[str, str],
    subject: str
) -> bool:

    if not grades:
        return False

    target = _normalize_subject(
        subject
    )

    for student_subject, grade in grades.items():

        normalized_student_subject = (
            _normalize_subject(
                student_subject
            )
        )

        if normalized_student_subject == target:
            return _grade_is_credit(
                grade
            )

    return False


def _find_student_subject(
    grades: Dict[str, str],
    subject: str
) -> Optional[str]:

    target = _normalize_subject(
        subject
    )

    for student_subject in grades.keys():

        if (
            _normalize_subject(
                student_subject
            )
            == target
        ):
            return student_subject

    return None


def _get_credit_subjects(
    grades: Dict[str, str]
) -> List[str]:

    credits = []

    for subject, grade in grades.items():

        if _grade_is_credit(grade):

            normalized = _normalize_subject(
                subject
            )

            if normalized:
                credits.append(
                    normalized
                )

    return credits


def _subject_belongs_to_group(
    subject: str,
    group: str
) -> bool:

    normalized_subject = _normalize_subject(
        subject
    )

    normalized_group = (
        group.strip().lower()
    )

    subjects = SUBJECT_GROUPS.get(
        normalized_group,
        set()
    )

    return normalized_subject in subjects


def _find_group_credits(
    grades: Dict[str, str],
    group: str,
    excluded_subjects: Optional[List[str]] = None
) -> List[str]:

    excluded = {
        _normalize_subject(subject)
        for subject in (
            excluded_subjects or []
        )
    }

    matched = []

    for student_subject, grade in grades.items():

        normalized = _normalize_subject(
            student_subject
        )

        if normalized in excluded:
            continue

        if not _grade_is_credit(grade):
            continue

        if _subject_belongs_to_group(
            normalized,
            group
        ):
            matched.append(
                student_subject
            )

    return matched


def _count_other_credit_subjects(
    grades: Dict[str, str],
    excluded_subjects: Optional[List[str]] = None
) -> List[str]:

    excluded = {
        _normalize_subject(subject)
        for subject in (
            excluded_subjects or []
        )
    }

    results = []

    for student_subject, grade in grades.items():

        normalized = _normalize_subject(
            student_subject
        )

        if normalized in excluded:
            continue

        if _grade_is_credit(grade):
            results.append(
                student_subject
            )

    return results


def _check_broad_requirement(
    requirement: str,
    grades: Dict[str, str],
    already_required: Optional[List[str]] = None
) -> Optional[Dict]:

    text = requirement.strip().lower()

    excluded = already_required or []

    # -----------------------------------------------------
    # ANY TWO ARTS / SOCIAL SCIENCE
    # -----------------------------------------------------

    if (
        "any two arts/social science subjects"
        in text
    ):

        arts = _find_group_credits(
            grades,
            "arts",
            excluded
        )

        social = _find_group_credits(
            grades,
            "social_science",
            excluded
        )

        combined = []

        for subject in arts + social:

            if subject not in combined:
                combined.append(
                    subject
                )

        if len(combined) >= 2:

            return {
                "matched": True,
                "matched_subjects": combined[:2],
                "message": (
                    "Student has at least two credited "
                    "Arts/Social Science subjects."
                ),
            }

        return {
            "matched": False,
            "missing": requirement,
            "message": (
                "At least two credited Arts/Social Science "
                "subjects are required."
            ),
        }

    # -----------------------------------------------------
    # ANY TWO ARTS
    # -----------------------------------------------------

    if "any two arts subjects" in text:

        matched = _find_group_credits(
            grades,
            "arts",
            excluded
        )

        if len(matched) >= 2:

            return {
                "matched": True,
                "matched_subjects": matched[:2],
                "message": (
                    "Student has at least two credited "
                    "Arts subjects."
                ),
            }

        return {
            "matched": False,
            "missing": requirement,
            "message": (
                "At least two credited Arts subjects "
                "are required."
            ),
        }

    # -----------------------------------------------------
    # ANY TWO COMMERCIAL
    # -----------------------------------------------------

    if "any two commercial subjects" in text:

        matched = _find_group_credits(
            grades,
            "commercial",
            excluded
        )

        if len(matched) >= 2:

            return {
                "matched": True,
                "matched_subjects": matched[:2],
                "message": (
                    "Student has at least two credited "
                    "Commercial subjects."
                ),
            }

        return {
            "matched": False,
            "missing": requirement,
            "message": (
                "At least two credited Commercial "
                "subjects are required."
            ),
        }

    # -----------------------------------------------------
    # ANY OTHER ARTS
    # -----------------------------------------------------

    if "any other arts subject" in text:

        matched = _find_group_credits(
            grades,
            "arts",
            excluded
        )

        if matched:

            return {
                "matched": True,
                "matched_subjects": matched[:1],
                "message": (
                    "Student has another credited "
                    "Arts subject."
                ),
            }

        return {
            "matched": False,
            "missing": requirement,
            "message": (
                "At least one additional credited "
                "Arts subject is required."
            ),
        }

    # -----------------------------------------------------
    # ANY OTHER COMMERCIAL
    # -----------------------------------------------------

    if "any other commercial subject" in text:

        matched = _find_group_credits(
            grades,
            "commercial",
            excluded
        )

        if matched:

            return {
                "matched": True,
                "matched_subjects": matched[:1],
                "message": (
                    "Student has another credited "
                    "Commercial subject."
                ),
            }

        return {
            "matched": False,
            "missing": requirement,
            "message": (
                "At least one additional credited "
                "Commercial subject is required."
            ),
        }

    # -----------------------------------------------------
    # ANY OTHER ARTS / SOCIAL SCIENCE
    # -----------------------------------------------------

    if (
        "any other arts/social science subject"
        in text
    ):

        arts = _find_group_credits(
            grades,
            "arts",
            excluded
        )

        social = _find_group_credits(
            grades,
            "social_science",
            excluded
        )

        combined = []

        for subject in arts + social:

            if subject not in combined:
                combined.append(
                    subject
                )

        if combined:

            return {
                "matched": True,
                "matched_subjects": combined[:1],
                "message": (
                    "Student has an additional credited "
                    "Arts/Social Science subject."
                ),
            }

        return {
            "matched": False,
            "missing": requirement,
            "message": (
                "At least one additional credited "
                "Arts/Social Science subject is required."
            ),
        }

    # -----------------------------------------------------
    # ANY OTHER SUBJECT
    # -----------------------------------------------------

    if "any other subject" in text:

        matched = _count_other_credit_subjects(
            grades,
            excluded
        )

        if matched:

            return {
                "matched": True,
                "matched_subjects": matched[:1],
                "message": (
                    "Student has an additional credited "
                    "subject."
                ),
            }

        return {
            "matched": False,
            "missing": requirement,
            "message": (
                "At least one additional credited "
                "subject is required."
            ),
        }

    return None


def _check_olevel_requirements(
    required_subjects: List[str],
    grades: Dict[str, str]
) -> Dict:

    if not grades:

        return {
            "eligible": False,
            "required_subjects": required_subjects,
            "missing_subjects": list(
                required_subjects
            ),
            "weak_subjects": [],
            "matched_subjects": [],
        }

    matched = []
    missing = []
    weak = []

    explicit_required_subjects = []

    for requirement in required_subjects:

        requirement_text = str(
            requirement
        ).strip()

        if not requirement_text:
            continue

        lower_text = (
            requirement_text.lower()
        )

        # -------------------------------------------------
        # BROAD REQUIREMENT
        # -------------------------------------------------

        broad_result = _check_broad_requirement(
            requirement_text,
            grades,
            explicit_required_subjects
        )

        if broad_result is not None:

            if broad_result["matched"]:

                matched.append(
                    f"{requirement_text} "
                    f"({', '.join(broad_result.get('matched_subjects', []))})"
                )

            else:

                missing.append(
                    requirement_text
                )

            continue

        # -------------------------------------------------
        # ALTERNATIVE REQUIREMENT
        # -------------------------------------------------

        if " or " in lower_text:

            alternatives = [
                item.strip()
                for item in requirement_text.split(
                    " or ",
                    maxsplit=10
                )
            ]

            found_credit = False
            found_weak = []

            for alternative in alternatives:

                if _has_olevel_credit(
                    grades,
                    alternative
                ):

                    found_credit = True
                    break

                student_subject = (
                    _find_student_subject(
                        grades,
                        alternative
                    )
                )

                if student_subject:

                    grade = str(
                        grades[
                            student_subject
                        ]
                    ).strip().upper()

                    if not _grade_is_credit(
                        grade
                    ):

                        found_weak.append(
                            f"{alternative} ({grade})"
                        )

            if found_credit:

                matched.append(
                    requirement_text
                )

            elif found_weak:

                weak.append(
                    f"{requirement_text} "
                    f"[available but below credit: "
                    f"{', '.join(found_weak)}]"
                )

            else:

                missing.append(
                    requirement_text
                )

            continue

        # -------------------------------------------------
        # EXACT SUBJECT
        # -------------------------------------------------

        if _has_olevel_credit(
            grades,
            requirement_text
        ):

            matched.append(
                requirement_text
            )

            explicit_required_subjects.append(
                requirement_text
            )

        else:

            student_subject = (
                _find_student_subject(
                    grades,
                    requirement_text
                )
            )

            if student_subject:

                grade = str(
                    grades[
                        student_subject
                    ]
                ).strip().upper()

                if not _grade_is_credit(
                    grade
                ):

                    weak.append(
                        f"{requirement_text} ({grade})"
                    )

            else:

                missing.append(
                    requirement_text
                )

            explicit_required_subjects.append(
                requirement_text
            )

    eligible = (
        len(missing) == 0
        and len(weak) == 0
    )

    return {
        "eligible": eligible,
        "required_subjects": required_subjects,
        "missing_subjects": missing,
        "weak_subjects": weak,
        "matched_subjects": matched,
    }


# =========================================================
# O'LEVEL ANALYSIS
# =========================================================

def analyze_olevel_eligibility(
    profile: Dict,
    career_id: Optional[str] = None
) -> Dict:
    """
    Analyze WAEC and NECO independently.

    The selected target course is carried through the result,
    while requirements are currently taken from the broad career
    knowledge base.
    """

    resolved = _resolve_admission_target(
        profile,
        career_id
    )

    cid = resolved["career_id"]
    career = resolved["career"]
    target_course = resolved["target_course"]

    if not cid:

        return {
            "status": "no_career",
            "message": "Select a career/course first.",
        }

    if not career:

        return {
            "status": "unknown_career",
            "message": (
                f"Unknown career id '{cid}'."
            ),
        }

    required_subjects = career.get(
        "waec_subjects",
        []
    )

    waec_grades = (
        profile.get(
            "waec_grades",
            {}
        )
        or {}
    )

    neco_grades = (
        profile.get(
            "neco_grades",
            {}
        )
        or {}
    )

    waec_status = profile.get(
        "waec_status"
    )

    neco_status = profile.get(
        "neco_status"
    )

    waec_analysis = (
        _check_olevel_requirements(
            required_subjects,
            waec_grades
        )
    )

    neco_analysis = (
        _check_olevel_requirements(
            required_subjects,
            neco_grades
        )
    )

    return {
        "career_id": cid,
        "career_name": career.get(
            "name"
        ),
        "target_course": target_course,
        "required_subjects": required_subjects,

        "waec": {
            "status": waec_status,
            "grades": waec_grades,
            "analysis": waec_analysis,
        },

        "neco": {
            "status": neco_status,
            "grades": neco_grades,
            "analysis": neco_analysis,
        },
    }


# =========================================================
# RESULT STATUS HELPER
# =========================================================

def _is_result_available(
    status: Optional[str]
) -> bool:

    if not status:
        return False

    return (
        str(status)
        .strip()
        .lower()
        in {
            "written",
            "completed",
            "complete",
            "available",
        }
    )


# =========================================================
# COMBINED ADMISSION INTELLIGENCE
# =========================================================

def analyze_admission(
    profile: Dict,
    career_id: Optional[str] = None
) -> Dict:
    """
    Produce combined admission analysis:

        JAMB
          +
        WAEC / NECO
          ↓
        Course eligibility
          ↓
        Admission readiness
          ↓
        Recommendations
    """

    resolved = _resolve_admission_target(
        profile,
        career_id
    )

    cid = resolved["career_id"]
    career = resolved["career"]
    target_course = resolved["target_course"]

    if not cid:

        return {
            "status": "no_career",
            "message": (
                "Select a career/course first."
            ),
        }

    if not career:

        return {
            "status": "unknown_career",
            "message": (
                f"Unknown career id '{cid}'."
            ),
        }

    jamb = analyze_jamb_readiness(
        profile,
        cid
    )

    olevel = analyze_olevel_eligibility(
        profile,
        cid
    )

    recommendations = []
    eligibility_status = "pending"

    waec_analysis = (
        olevel["waec"]["analysis"]
    )

    neco_analysis = (
        olevel["neco"]["analysis"]
    )

    waec_status = (
        olevel["waec"]["status"]
    )

    neco_status = (
        olevel["neco"]["status"]
    )

    # -----------------------------------------------------
    # JAMB
    # -----------------------------------------------------

    if jamb["status"] == "not_written":

        recommendations.append(
            f"Prepare toward a JAMB score of approximately "
            f"{jamb['target_low']}-{jamb['target_high']} for "
            f"{target_course} as a CareerVoice planning target."
        )

    elif jamb["status"] == "scored":

        if jamb["assessment"] == "needs_improvement":

            recommendations.append(
                "Your JAMB score is below the current "
                "CareerVoice planning target for this field. "
                "Review your university choices and consider "
                "ways to strengthen your admission options."
            )

    elif jamb["status"] == "score_missing":

        recommendations.append(
            "Your JAMB result is marked as written, "
            "but the actual score has not been provided."
        )

    elif jamb["status"] == "invalid_score":

        recommendations.append(
            "Your JAMB score needs to be corrected before "
            "admission readiness can be calculated accurately."
        )

    else:

        recommendations.append(
            "Provide your JAMB status so your admission "
            "readiness can be assessed."
        )

    # -----------------------------------------------------
    # WAEC
    # -----------------------------------------------------

    if _is_result_available(
        waec_status
    ):

        if waec_analysis["eligible"]:

            recommendations.append(
                "Your WAEC subjects currently satisfy the "
                "required course subjects represented in "
                "the CareerVoice database."
            )

        else:

            if waec_analysis[
                "missing_subjects"
            ]:

                recommendations.append(
                    "Your WAEC result is missing these "
                    "required subjects: "
                    + ", ".join(
                        waec_analysis[
                            "missing_subjects"
                        ]
                    )
                    + "."
                )

            if waec_analysis[
                "weak_subjects"
            ]:

                recommendations.append(
                    "These WAEC subjects do not currently "
                    "have credit grades: "
                    + ", ".join(
                        waec_analysis[
                            "weak_subjects"
                        ]
                    )
                    + "."
                )

    elif waec_status == "awaiting":

        recommendations.append(
            "Your WAEC result is awaiting. Once available, "
            "enter the subject-by-subject grades so course "
            "eligibility can be checked."
        )

    elif waec_status == "not_written":

        recommendations.append(
            "You have not written WAEC yet. Aim for at "
            "least the required credit grades in the "
            "course's required O'Level subjects."
        )

    else:

        recommendations.append(
            "Provide your WAEC status and subject grades "
            "when available."
        )

    # -----------------------------------------------------
    # NECO
    # -----------------------------------------------------

    if _is_result_available(
        neco_status
    ):

        if neco_analysis["eligible"]:

            recommendations.append(
                "Your NECO subjects currently satisfy the "
                "required course subjects represented in "
                "the CareerVoice database."
            )

        else:

            if neco_analysis[
                "missing_subjects"
            ]:

                recommendations.append(
                    "Your NECO result is missing these "
                    "required subjects: "
                    + ", ".join(
                        neco_analysis[
                            "missing_subjects"
                        ]
                    )
                    + "."
                )

            if neco_analysis[
                "weak_subjects"
            ]:

                recommendations.append(
                    "These NECO subjects do not currently "
                    "have credit grades: "
                    + ", ".join(
                        neco_analysis[
                            "weak_subjects"
                        ]
                    )
                    + "."
                )

    elif neco_status == "awaiting":

        recommendations.append(
            "Your NECO result is awaiting. Once available, "
            "enter the subject-by-subject grades so course "
            "eligibility can be checked."
        )

    elif neco_status == "not_written":

        recommendations.append(
            "You have not written NECO yet. Your WAEC "
            "result can still be evaluated separately "
            "when available."
        )

    else:

        recommendations.append(
            "Provide your NECO status and subject grades "
            "when available."
        )

    # -----------------------------------------------------
    # OVERALL O'LEVEL ELIGIBILITY
    # -----------------------------------------------------

    if (
        (
            _is_result_available(
                waec_status
            )
            and waec_analysis["eligible"]
        )
        or
        (
            _is_result_available(
                neco_status
            )
            and neco_analysis["eligible"]
        )
    ):

        eligibility_status = (
            "eligible_on_olevel"
        )

    elif (
        waec_status in {
            "awaiting",
            None,
        }
        or
        neco_status in {
            "awaiting",
            None,
        }
    ):

        eligibility_status = (
            "pending_olevel"
        )

    else:

        eligibility_status = (
            "needs_attention"
        )

    # -----------------------------------------------------
    # FINAL RESULT
    # -----------------------------------------------------

    return {
        "status": "analyzed",
        "career_id": cid,
        "career_name": career.get(
            "name"
        ),
        "target_course": target_course,
        "stream": career.get(
            "stream"
        ),

        "jamb": jamb,

        "olevel": olevel,

        "course_eligibility": {
            "status": eligibility_status,
            "waec_eligible": (
                waec_analysis["eligible"]
            ),
            "neco_eligible": (
                neco_analysis["eligible"]
            ),
        },

        "recommendations": recommendations,

        "disclaimer": (
            "This analysis is personalized planning "
            "guidance based on the requirements represented "
            "in CareerVoice's knowledge base. It is not an "
            "admission guarantee. Always verify the current "
            "JAMB requirements and the specific university's "
            "requirements before applying."
        ),
    }


# =========================================================
# ADMISSION READINESS
# =========================================================

def compute_admission_readiness(
    profile: Dict,
    career_id: Optional[str] = None
) -> Dict:
    """
    Calculate a personalized admission-readiness score.

    Current scoring:
        Required subjects = 40 points
        JAMB = 30 points
        WAEC/NECO = 20 points

    The selected target course is included in the result.
    """

    resolved = _resolve_admission_target(
        profile,
        career_id
    )

    cid = resolved["career_id"]
    career = resolved["career"]
    target_course = resolved["target_course"]

    if not cid:

        return {
            "readiness_percent": 0,
            "message": (
                "Set a career goal first so I can assess "
                "your admission readiness for it."
            ),
        }

    if not career:

        return {
            "readiness_percent": 0,
            "message": (
                f"Unknown career id '{cid}'."
            ),
        }

    score = 0.0
    max_score = 0.0

    notes: List[str] = []

    # =====================================================
    # REQUIRED SUBJECTS
    # =====================================================

    max_score += 40

    required = {
        str(subject).lower()
        for subject in career.get(
            "required_subjects",
            []
        )
    }

    have = {
        str(subject).lower()
        for subject in profile.get(
            "subjects",
            []
        )
    }

    if required:

        ratio = (
            len(required & have)
            / len(required)
        )

        score += 40 * ratio

        if ratio < 1.0:

            missing = [
                subject
                for subject in career.get(
                    "required_subjects",
                    []
                )
                if str(subject).lower()
                not in have
            ]

            if missing:

                notes.append(
                    "Still needs to confirm these subjects: "
                    + ", ".join(missing)
                    + "."
                )

    else:

        score += 20

    # =====================================================
    # JAMB
    # =====================================================

    max_score += 30

    jamb_score = profile.get(
        "jamb_score"
    )

    if jamb_score is not None:

        try:
            numeric_jamb_score = float(
                jamb_score
            )
        except (
            TypeError,
            ValueError
        ):

            numeric_jamb_score = None

        if numeric_jamb_score is not None:

            competitiveness = (
                COMPETITIVENESS.get(
                    cid,
                    "medium"
                )
            )

            thresholds = {
                "very high": 250,
                "high": 220,
                "medium-high": 200,
                "medium": 180,
                "unrated": 180,
            }

            threshold = thresholds.get(
                competitiveness,
                180
            )

            if (
                numeric_jamb_score
                >= threshold
            ):

                score += 30

                notes.append(
                    f"Your JAMB score "
                    f"({int(numeric_jamb_score)}) "
                    f"is in a competitive range for "
                    f"{target_course}."
                )

            else:

                partial = (
                    30
                    * max(
                        numeric_jamb_score
                        / threshold,
                        0.3
                    )
                )

                score += partial

                notes.append(
                    f"Your JAMB score "
                    f"({int(numeric_jamb_score)}) "
                    f"may be below the typical "
                    f"competitive range for "
                    f"{target_course}; check the "
                    "current cut-off for your target "
                    "universities."
                )

        else:

            notes.append(
                "The JAMB score on file is invalid."
            )

    else:

        notes.append(
            "No JAMB score on file yet."
        )

    # =====================================================
    # WAEC / NECO
    # =====================================================

    max_score += 20

    waec_status = profile.get(
        "waec_status"
    )

    neco_status = profile.get(
        "neco_status"
    )

    waec_grades = (
        profile.get(
            "waec_grades",
            {}
        )
        or {}
    )

    neco_grades = (
        profile.get(
            "neco_grades",
            {}
        )
        or {}
    )

    # -----------------------------------------------------
    # WAEC
    # -----------------------------------------------------

    if (
        _is_result_available(
            waec_status
        )
        and waec_grades
    ):

        score += 10

        notes.append(
            "WAEC result information is on file."
        )

    elif waec_status == "awaiting":

        score += 5

        notes.append(
            "WAEC result is awaiting release."
        )

    elif waec_status == "not_written":

        notes.append(
            "WAEC has not been written yet."
        )

    else:

        notes.append(
            "WAEC result status not yet provided."
        )

    # -----------------------------------------------------
    # NECO
    # -----------------------------------------------------

    if (
        _is_result_available(
            neco_status
        )
        and neco_grades
    ):

        score += 10

        notes.append(
            "NECO result information is on file."
        )

    elif neco_status == "awaiting":

        score += 5

        notes.append(
            "NECO result is awaiting release."
        )

    elif neco_status == "not_written":

        notes.append(
            "NECO has not been written yet."
        )

    else:

        notes.append(
            "NECO result status not yet provided."
        )

    # =====================================================
    # FINAL SCORE
    # =====================================================

    percent = (
        round(
            100 * score / max_score
        )
        if max_score
        else 0
    )

    # Keep 99 as the maximum because the system should not
    # imply that admission is guaranteed.
    percent = max(
        0,
        min(
            percent,
            99
        )
    )

    return {
        "career_id": cid,
        "career_name": career["name"],
        "target_course": target_course,
        "readiness_percent": percent,
        "notes": notes,
    }