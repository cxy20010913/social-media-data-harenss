from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class HarnessState:
    goal: str
    source_path: Path
    output_dir: Path
    data_profile: dict[str, Any] = field(default_factory=dict)
    validation: dict[str, Any] = field(default_factory=dict)
    analysis: dict[str, Any] = field(default_factory=dict)
    charts: list[dict[str, str]] = field(default_factory=list)
    skill_cards: dict[str, Any] = field(default_factory=dict)
    report_path: Path | None = None


@dataclass
class AgentResult:
    agent: str
    status: str
    summary: str
    payload: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
