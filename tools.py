from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scar_classifier import classify

RESOURCES       = Path(__file__).resolve().parent / "resources"
PROFILE_PATH    = RESOURCES / "profile.json"
STAGE_INFO_PATH = RESOURCES / "stage_info.json"

def classify_scar(image_path: str) -> dict[str, Any]:
    """Classify a scar image using the CNN model.
    Returns the predicted stage, confidence percentage, and all class probabilities."""
    result = classify(image_path)
    result["dangerous"] = result["class"] in {"infected", "dehiscence"}
    return result


def get_stage_info(stage: str) -> dict[str, Any]:
    """Return description, expected duration and care tips for a given healing stage."""
    stage_info = json.loads(STAGE_INFO_PATH.read_text(encoding="utf-8"))
    info = stage_info.get(stage)
    if info is None:
        return {"error": f"Unknown stage: '{stage}'. Valid stages: {list(stage_info.keys())}"}
    return {"stage": stage, **info}


def get_user_profile() -> dict[str, Any]:
    """Read the user's profile (name, operation type, operation date, current stage, notes)."""
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def update_user_profile(
    name:           str | None = None,
    operation:      str | None = None,
    operation_date: str | None = None,
    current_stage:  str | None = None,
    notes:          str | None = None,
) -> dict[str, Any]:
    """Update one or more fields in the user's profile."""
    profile = get_user_profile()

    if name           is not None: profile["name"]           = name
    if operation      is not None: profile["operation"]      = operation
    if operation_date is not None: profile["operation_date"] = operation_date
    if current_stage  is not None: profile["current_stage"]  = current_stage
    if notes          is not None: profile["notes"]          = notes

    PROFILE_PATH.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    return {"message": "Profile updated", "profile": profile}
