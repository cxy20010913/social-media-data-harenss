from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_SKILL_CONFIG = Path(__file__).parent / "config" / "skill_cards.json"


def load_skill_cards(path: Path = DEFAULT_SKILL_CONFIG) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def temperature_policy(skill_cards: dict[str, Any]) -> dict[str, float]:
    skills = skill_cards.get("skills", {})
    policy: dict[str, float] = {}
    for agent_name, card in skills.items():
        try:
            policy[agent_name] = float(card.get("temperature", 0.3))
        except (TypeError, ValueError):
            policy[agent_name] = 0.3
    return policy


def skill_summary(skill_cards: dict[str, Any]) -> list[dict[str, str]]:
    rows = []
    for agent_name, card in skill_cards.get("skills", {}).items():
        rows.append({
            "agent": agent_name,
            "display_name": str(card.get("display_name", agent_name)),
            "agent_type": str(card.get("agent_type", "")),
            "temperature": str(card.get("temperature", "")),
        })
    return rows
