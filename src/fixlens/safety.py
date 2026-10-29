from __future__ import annotations

HAZARD_RULES = {
    "Possible swollen or bulging battery": (
        "swollen battery", "battery swelling", "bulging battery", "puffed battery",
        "battery is swollen", "back cover lifting"
    ),
    "Smoke, flame, or burning smell": (
        "smoke", "flame", "on fire", "burning smell", "burnt smell", "sparking"
    ),
    "Possible dangerous overheating": (
        "too hot to touch", "extremely hot", "overheating", "overheated"
    ),
    "Possible electric shock or exposed live wiring": (
        "electric shock", "shocked me", "exposed live wire", "live wiring", "tingling when touching"
    ),
}

def detect_hazards(text: str) -> list[str]:
    """Conservative keyword screening; not a substitute for a full safety classifier."""
    normalized = (text or "").casefold()
    return [
        label for label, phrases in HAZARD_RULES.items()
        if any(phrase in normalized for phrase in phrases)
    ]
