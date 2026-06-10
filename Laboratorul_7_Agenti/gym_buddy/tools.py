from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

RESOURCES = Path(__file__).resolve().parent / "resources"
PROFILE_PATH = RESOURCES / "profile.json"
PLANS_DIR = RESOURCES / "plans"
WORKOUTS_DIR = RESOURCES / "workouts"
PROGRESS_DIR = RESOURCES / "progress"


def get_user_profile() -> dict[str, Any]:
    """Read user's profile from profile.json."""
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def update_user_profile(updates: dict[str, Any]) -> dict[str, Any]:
    profile = get_user_profile()
    profile.update(updates)
    PROFILE_PATH.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    return {"message": "Profile updated", "profile": profile}


def save_meal_plan(title: str, body: str) -> dict[str, Any]:
    PLANS_DIR.mkdir(parents=True, exist_ok=True)
    slug = title.lower().replace(" ", "-")
    path = PLANS_DIR / f"{slug}-{uuid.uuid4().hex[:6]}.md"
    path.write_text(f"# {title}\n\n{body.strip()}\n", encoding="utf-8")
    return {"message": "Meal plan saved", "path": str(path)}


def save_workout_plan(title: str, body: str) -> dict[str, Any]:
    WORKOUTS_DIR.mkdir(parents=True, exist_ok=True)
    slug = title.lower().replace(" ", "-")
    path = WORKOUTS_DIR / f"{slug}-{uuid.uuid4().hex[:6]}.md"
    path.write_text(f"# {title}\n\n{body.strip()}\n", encoding="utf-8")
    return {"message": "Workout plan saved", "path": str(path)}


def log_progress(
    weight_kg: float | None = None,
    exercises: dict[str, Any] | None = None,
    notes: str = "",
) -> dict[str, Any]:
    """Log a progress entry (weight and/or exercise performance)."""
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    entry = {
        "date": today,
        "weight_kg": weight_kg,
        "exercises": exercises or {},
        "notes": notes,
    }
    path = PROGRESS_DIR / f"{today}.json"
    path.write_text(json.dumps(entry, indent=2), encoding="utf-8")
    return {"message": "Progress logged", "entry": entry}


def read_progress() -> dict[str, Any]:
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    entries = []
    for file in sorted(PROGRESS_DIR.glob("*.json")):
        entries.append(json.loads(file.read_text(encoding="utf-8")))
    return {"count": len(entries), "entries": entries}


def get_exercise_tips(exercise_name: str) -> dict[str, Any]:
    """Search the web for form tips and common mistakes for an exercise."""
    query = f"{exercise_name} correct form tips common mistakes"
    response = requests.get(
        "https://www.bing.com/search",
        params={"q": query},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15,
    )
    import re, html
    raw_pairs = re.findall(r'<h2[^>]*><a[^>]+href="([^"]+)"[^>]*>(.*?)</a></h2>', response.text, re.S)
    results = []
    for href, title in raw_pairs[:5]:
        clean_title = re.sub(r"<[^>]+>", "", html.unescape(title)).strip()
        if clean_title:
            results.append({"title": clean_title, "url": html.unescape(href)})
    return {"exercise": exercise_name, "results": results}


def web_search(query: str, max_results: int = 5) -> dict[str, Any]:
    """Search the web for nutrition or fitness information."""
    import re, html
    response = requests.get(
        "https://www.bing.com/search",
        params={"q": query},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15,
    )
    raw_pairs = re.findall(r'<h2[^>]*><a[^>]+href="([^"]+)"[^>]*>(.*?)</a></h2>', response.text, re.S)
    results = []
    for href, title in raw_pairs[:max_results]:
        clean_title = re.sub(r"<[^>]+>", "", html.unescape(title)).strip()
        if clean_title:
            results.append({"title": clean_title, "url": html.unescape(href)})
    return {"query": query, "count": len(results), "results": results}
