"""
action_plan.py

Generates a personalized, ordered action plan for a student, adapting the
content of each step to their stream, career goal, and what is still
missing from their profile. Falls back to a sensible generic plan when the
profile is still mostly empty.
"""

from typing import Dict, List

from backend import admission_engine, career_knowledge, profile_analyzer, university_engine


def generate_action_plan(profile: Dict) -> List[Dict]:
    steps: List[Dict] = []
    step_no = 1

    def add(title: str, description: str):
        nonlocal step_no
        steps.append({"step": step_no, "title": title, "description": description})
        step_no += 1

    stream = profile.get("stream")
    career_id = profile.get("career_goal_id")
    career = career_knowledge.get_career(career_id) if career_id else None

    # Step 1: stream / career confirmation
    if not stream:
        add(
            "Confirm your academic stream",
            "Tell me whether you're a Science, Art/Humanities, or Commercial student so I can "
            "narrow down suitable careers for you.",
        )
    elif not career:
        add(
            "Explore career options",
            f"As a {stream} student, review the careers I've matched for you and pick one (or a "
            "shortlist) to focus on.",
        )
    else:
        add(
            "Confirm your preferred career",
            f"You're aiming for {career['name']}. If this still feels right, let's build the rest "
            "of your plan around it.",
        )

    # Step 2: WAEC/NECO subjects
    if career:
        subjects = ", ".join(career.get("waec_subjects", [])) or "the relevant subjects for your course"
        add(
            "Review required WAEC/NECO subjects",
            f"For {career['name']}, you'll typically need: {subjects}. Confirm you're offering "
            "all of these and are on track for credit passes.",
        )
    else:
        add(
            "Review your WAEC/NECO subject list",
            "Make sure your subject combination covers the core subjects for the stream you're "
            "leaning towards, plus English Language and Mathematics.",
        )

    # Step 3: UTME subject combination
    if career:
        jamb_subjects = ", ".join(career.get("jamb_subjects", []))
        add(
            "Review your UTME subject combination",
            f"The standard JAMB subjects for {career['name']} are: {jamb_subjects}. Double-check "
            "this against the current JAMB brochure before registration, since combinations are "
            "published fresh each year.",
        )
    else:
        add(
            "Learn the UTME subject combination for your target course",
            "Once you've picked a career, I can tell you exactly which four subjects to register "
            "for in JAMB.",
        )

    # Step 4: identify suitable universities
    if career:
        target_course = career.get("university_courses", [career.get("name")])[0]
        matches = university_engine.search_universities(course=target_course)
        names = ", ".join(u["short_name"] or u["name"] for u in matches[:4]) or "several Nigerian universities"
        add(
            "Identify suitable universities",
            f"Universities offering {target_course} include {names}. Compare federal, state and "
            "private options based on location, cost and admission requirements.",
        )
    else:
        add(
            "Shortlist universities once your career is set",
            "After choosing a career, I'll match you to universities that offer the right "
            "programme and fit your state and budget preferences.",
        )

    # Step 5: compare requirements
    add(
        "Compare university-specific requirements",
        "Admission requirements, O'Level subject rules, and cut-off marks vary by university "
        "even for the same course. Check each shortlisted university's admissions page directly.",
    )

    # Step 6: JAMB preparation
    add(
        "Prepare for JAMB/UTME",
        "Use past questions, JAMB CBT practice apps, and a study timetable that covers all four "
        "of your registered subjects. Focus extra time on your weakest subject.",
    )

    # Step 7: target score
    if career:
        info = admission_engine.get_admission_info(career_id, profile)
        add(
            "Set a target UTME score",
            info.get("target_score_guidance", "Aim as high as you reasonably can in JAMB."),
        )
    else:
        add(
            "Set a target UTME score",
            "A higher JAMB score gives you more course and university options — aim to comfortably "
            "beat the national benchmark.",
        )

    # Step 8: documents
    add(
        "Prepare required documents",
        "Gather your birth certificate/age declaration, passport photographs, WAEC/NECO result "
        "(or scratch card), local government identification, and JAMB result slip ahead of time.",
    )

    # Step 9: apply / admission process
    add(
        "Apply through the correct admission process",
        "Complete your JAMB CAPS choice, participate in Post-UTME/screening where required, and "
        "follow up on your chosen universities' admission portals.",
    )

    # Step 10: track progress
    add(
        "Track your admission progress",
        "Regularly check your JAMB CAPS status, university admission list, and email/SMS for "
        "updates. Keep your login details safe and respond quickly to any requests.",
    )

    return steps
