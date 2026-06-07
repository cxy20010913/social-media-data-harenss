from __future__ import annotations

from schemas import AgentResult
from skill_config import temperature_policy


def run(agent_name: str, skill_cards: dict | None = None) -> AgentResult:
    policy = temperature_policy(skill_cards or {})
    temperature = policy.get(agent_name, 0.3)
    return AgentResult(
        agent="temp_control_agent",
        status="success",
        summary=f"为 {agent_name} 分配温度 {temperature}。",
        payload={
            "target_agent": agent_name,
            "temperature": temperature,
            "policy": policy,
        },
    )
