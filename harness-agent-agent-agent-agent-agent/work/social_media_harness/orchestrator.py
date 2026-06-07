from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from agents import analyst_agent, chart_agent, design_agent, reader_agent, resolver_agent, temp_control_agent, validator_agent
from html_dashboard import build_dashboard
from schemas import AgentResult, HarnessState
from skill_config import load_skill_cards


DEFAULT_SOURCE = Path(r"C:\Users\cxy\Desktop\个人资料\毕业论文\硕士论文\数据\计算博文表_用于回归.csv")
DEFAULT_GOAL = "社交媒体灾害信息传播数据的描述性分析、核验、图表生成和回归方向初筛"


def _to_jsonable(value):
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, AgentResult):
        return asdict(value)
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    return value


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(_to_jsonable(payload), ensure_ascii=False, indent=2), encoding="utf-8")


def run_harness(source_path: Path, output_dir: Path, goal: str = DEFAULT_GOAL) -> HarnessState:
    output_dir.mkdir(parents=True, exist_ok=True)
    state = HarnessState(goal=goal, source_path=source_path, output_dir=output_dir)
    state.skill_cards = load_skill_cards()
    results: list[AgentResult] = []

    results.append(temp_control_agent.run("reader_agent", state.skill_cards))
    df, reader_result = reader_agent.run(source_path)
    state.data_profile = reader_result.payload
    results.append(reader_result)

    results.append(temp_control_agent.run("validator_agent", state.skill_cards))
    validator_result = validator_agent.run(df)
    state.validation = validator_result.payload
    results.append(validator_result)

    results.append(temp_control_agent.run("analyst_agent", state.skill_cards))
    analyst_result = analyst_agent.run(df)
    state.analysis = analyst_result.payload
    results.append(analyst_result)

    results.append(temp_control_agent.run("chart_agent", state.skill_cards))
    chart_result = chart_agent.run(state.analysis, output_dir)
    state.charts = chart_result.payload["charts"]
    results.append(chart_result)

    results.append(temp_control_agent.run("resolver_agent", state.skill_cards))
    resolver_result = resolver_agent.run(state.validation, state.analysis)
    results.append(resolver_result)

    results.append(temp_control_agent.run("design_agent", state.skill_cards))
    design_result = design_agent.run(state, results)
    state.report_path = Path(design_result.payload["report_path"])
    results.append(design_result)

    _write_json(output_dir / "harness_state.json", asdict(state))
    _write_json(output_dir / "agent_results.json", {"results": results})
    _write_json(output_dir / "skill_cards.json", state.skill_cards)
    build_dashboard(output_dir)
    return state


def main() -> None:
    parser = argparse.ArgumentParser(description="Run social media data analysis harness.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=Path("outputs"))
    parser.add_argument("--goal", type=str, default=DEFAULT_GOAL)
    args = parser.parse_args()
    state = run_harness(args.source, args.output, args.goal)
    print(f"report={state.report_path}")
    print(f"charts={len(state.charts)}")
    print(f"html={args.output / 'social_media_analysis_dashboard.html'}")


if __name__ == "__main__":
    main()
