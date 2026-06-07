from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    output_dir = Path("outputs/social_media_harness")
    required = [
        output_dir / "social_media_analysis_report.md",
        output_dir / "social_media_analysis_dashboard.html",
        output_dir / "harness_state.json",
        output_dir / "agent_results.json",
        output_dir / "skill_cards.json",
        output_dir / "charts/topic_mean_reposts.svg",
        output_dir / "charts/sentiment_mean_reposts.svg",
        output_dir / "charts/media_mean_reposts.svg",
        output_dir / "charts/daily_total_reposts.svg",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("缺少产物：\n" + "\n".join(missing))

    state = json.loads((output_dir / "harness_state.json").read_text(encoding="utf-8"))
    if state["data_profile"]["rows"] <= 0:
        raise SystemExit("数据行数异常。")
    if not state["analysis"]["findings"]:
        raise SystemExit("未生成关键发现。")
    if len(state["charts"]) < 4:
        raise SystemExit("图表数量不足。")
    if len(state.get("skill_cards", {}).get("skills", {})) < 7:
        raise SystemExit("Skill 配置数量不足。")
    html = (output_dir / "social_media_analysis_dashboard.html").read_text(encoding="utf-8-sig")
    if html.count("<svg") < 4 or html.count("<table>") < 6:
        raise SystemExit("HTML 页面图表或表格数量不足。")

    print("self_check=pass")
    print(f"rows={state['data_profile']['rows']}")
    print(f"charts={len(state['charts'])}")
    print(f"report={state['report_path']}")
    print(f"html={output_dir / 'social_media_analysis_dashboard.html'}")
    print(f"skills={len(state['skill_cards']['skills'])}")


if __name__ == "__main__":
    main()
