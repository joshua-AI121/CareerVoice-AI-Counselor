"""
career_knowledge.py

Loads the structured career knowledge base (data/careers.json) and exposes
simple lookup / search helpers used by career_engine.py, admission_engine.py
and action_plan.py.

The dataset is loaded once at import time and cached in memory. If the file
is missing or malformed, the module falls back to an empty list rather than
crashing the whole application.
"""

import json
import os
from typing import Dict, List, Optional

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
_CAREERS_PATH = os.path.join(_DATA_DIR, "careers.json")


def _load_careers() -> List[Dict]:
    try:
        with open(_CAREERS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


_CAREERS: List[Dict] = _load_careers()
_CAREERS_BY_ID: Dict[str, Dict] = {c["id"]: c for c in _CAREERS if "id" in c}

VALID_STREAMS = ["Science", "Art/Humanities", "Commercial"]


def reload_careers() -> None:
    """Reload the careers dataset from disk. Useful after editing data/careers.json."""
    global _CAREERS, _CAREERS_BY_ID
    _CAREERS = _load_careers()
    _CAREERS_BY_ID = {c["id"]: c for c in _CAREERS if "id" in c}


def all_careers() -> List[Dict]:
    return list(_CAREERS)


def get_career(career_id: str) -> Optional[Dict]:
    return _CAREERS_BY_ID.get(career_id)


def find_career_by_name(name: str) -> Optional[Dict]:
    """Loose, case-insensitive match against a career's display name or id."""
    if not name:
        return None
    normalized = name.strip().lower()
    for career in _CAREERS:
        if career.get("name", "").lower() == normalized:
            return career
        if career.get("id", "").lower() == normalized:
            return career
    # partial match fallback
    for career in _CAREERS:
        if normalized in career.get("name", "").lower():
            return career
    return None


def careers_by_stream(stream: str) -> List[Dict]:
    if not stream:
        return []
    return [c for c in _CAREERS if c.get("stream", "").lower() == stream.lower()]


def search_careers(query: str) -> List[Dict]:
    """Keyword search across name, description and keywords fields."""
    if not query:
        return []
    q = query.strip().lower()
    results = []
    for career in _CAREERS:
        haystack = " ".join([
            career.get("name", ""),
            career.get("description", ""),
            " ".join(career.get("keywords", [])),
        ]).lower()
        if q in haystack:
            results.append(career)
    return results


def all_subjects_index() -> Dict[str, List[str]]:
    """Map each keyword/subject mentioned in the dataset to the list of career ids that use it.
    Useful for matching free-text student input to relevant careers."""
    index: Dict[str, List[str]] = {}
    for career in _CAREERS:
        terms = set(
            [s.lower() for s in career.get("required_subjects", [])]
            + [k.lower() for k in career.get("keywords", [])]
        )
        for term in terms:
            index.setdefault(term, []).append(career["id"])
    return index
