from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any


OUTPUT_DIR = Path("outputs/social_media_harness")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:,.{digits}f}".rstrip("0").rstrip(".")
    if isinstance(value, int):
        return f"{value:,}"
    return escape(str(value))


def _pct(value: Any) -> str:
    try:
        return f"{float(value):.1%}"
    except (TypeError, ValueError):
        return "-"


def _table(rows: list[dict[str, Any]], columns: list[tuple[str, str]], limit: int | None = None) -> str:
    if not rows:
        return '<p class="empty">暂无数据</p>'
    shown = rows if limit is None else rows[:limit]
    head = "".join(f"<th>{escape(label)}</th>" for _, label in columns)
    body_rows = []
    for row in shown:
        cells = "".join(f"<td>{_fmt(row.get(key))}</td>" for key, _ in columns)
        body_rows.append(f"<tr>{cells}</tr>")
    return f"""
    <div class="table-wrap">
      <table>
        <thead><tr>{head}</tr></thead>
        <tbody>{''.join(body_rows)}</tbody>
      </table>
    </div>
    """


def _agent_label(name: str) -> str:
    labels = {
        "reader_agent": "读数",
        "validator_agent": "核验",
        "analyst_agent": "分析",
        "chart_agent": "制图",
        "resolver_agent": "问题处理",
        "design_agent": "设计",
        "temp_control_agent": "温度控制",
    }
    return labels.get(name, name)


def _inline_svg(path: Path) -> str:
    if not path.exists():
        return '<p class="empty">图表文件缺失</p>'
    return path.read_text(encoding="utf-8")


def build_dashboard(output_dir: Path = OUTPUT_DIR) -> Path:
    state = _read_json(output_dir / "harness_state.json")
    agent_results = _read_json(output_dir / "agent_results.json")["results"]

    profile = state["data_profile"]
    validation = state["validation"]
    analysis = state["analysis"]
    charts = state.get("charts", [])
    skill_cards = state.get("skill_cards", {})
    time_range = profile.get("time_range", {})
    high_missing = validation.get("high_missing", {})
    ols = analysis.get("ols", {})

    agent_steps = [
        r for r in agent_results
        if r["agent"] != "temp_control_agent"
    ]
    temp_steps = [
        r for r in agent_results
        if r["agent"] == "temp_control_agent"
    ]
    resolver_actions = []
    for result in agent_results:
        if result["agent"] == "resolver_agent":
            resolver_actions = result["payload"].get("actions", [])

    skill_rows = []
    for agent_name, card in skill_cards.get("skills", {}).items():
        skill_rows.append({
            "agent": agent_name,
            "display_name": card.get("display_name", agent_name),
            "agent_type": card.get("agent_type", ""),
            "temperature": card.get("temperature", ""),
        })

    chart_cards = []
    for chart in charts:
        chart_path = Path(chart["path"])
        if not chart_path.is_absolute():
            chart_path = output_dir / chart_path.relative_to(output_dir) if str(chart_path).startswith(str(output_dir)) else chart_path
        chart_cards.append(f"""
        <section class="chart-panel">
          <h3>{escape(chart["title"])}</h3>
          <div class="svg-box">{_inline_svg(chart_path)}</div>
        </section>
        """)

    missing_items = "".join(
        f"<li><strong>{escape(col)}</strong><span>{_pct(rate)}</span></li>"
        for col, rate in high_missing.items()
    ) or "<li><strong>无高缺失字段</strong><span>pass</span></li>"

    findings = "".join(f"<li>{escape(item)}</li>" for item in analysis.get("findings", []))
    agents = "".join(
        f"""
        <li>
          <span class="agent-name">{escape(_agent_label(item["agent"]))}</span>
          <span class="agent-summary">{escape(item["summary"])}</span>
        </li>
        """
        for item in agent_steps
    )
    temp_policy = "".join(
        f"""
        <li>
          <span>{escape(item["payload"].get("target_agent", ""))}</span>
          <strong>{_fmt(item["payload"].get("temperature"))}</strong>
        </li>
        """
        for item in temp_steps
    )
    actions = "".join(
        f"""
        <li>
          <strong>{escape(action.get("issue", ""))}</strong>
          <span>{escape(action.get("handling", ""))}</span>
          <em>{escape(action.get("severity", ""))}</em>
        </li>
        """
        for action in resolver_actions
    ) or "<li><strong>暂无额外处理建议</strong><span>当前流程未发现需单独处理的问题。</span><em>low</em></li>"

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>社交媒体数据分析 Harness Dashboard</title>
  <style>
    :root {{
      --bg: #f7f6f1;
      --paper: #ffffff;
      --ink: #1f2933;
      --muted: #66727a;
      --line: #d9d7cd;
      --teal: #2f6f73;
      --rust: #c96f45;
      --violet: #7567a8;
      --gold: #d29d2b;
      --soft: #ece8dc;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", Arial, sans-serif;
      line-height: 1.55;
    }}
    main {{
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
      padding: 28px 0 56px;
    }}
    header {{
      border-bottom: 1px solid var(--line);
      padding: 18px 0 22px;
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: 34px;
      line-height: 1.18;
      letter-spacing: 0;
    }}
    h2 {{
      margin: 34px 0 14px;
      font-size: 22px;
      letter-spacing: 0;
    }}
    h3 {{
      margin: 0 0 12px;
      font-size: 17px;
      letter-spacing: 0;
    }}
    p {{ margin: 0; }}
    .subtitle {{
      max-width: 880px;
      color: var(--muted);
      font-size: 15px;
    }}
    .source {{
      margin-top: 10px;
      color: var(--muted);
      font-size: 13px;
      word-break: break-all;
    }}
    .kpis {{
      display: grid;
      grid-template-columns: repeat(6, minmax(130px, 1fr));
      gap: 10px;
      margin: 22px 0 6px;
    }}
    .kpi {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px 14px 12px;
      min-height: 92px;
    }}
    .kpi span {{
      display: block;
      color: var(--muted);
      font-size: 13px;
    }}
    .kpi strong {{
      display: block;
      margin-top: 8px;
      font-size: 24px;
      line-height: 1.1;
    }}
    .kpi.accent-a {{ border-top: 4px solid var(--teal); }}
    .kpi.accent-b {{ border-top: 4px solid var(--rust); }}
    .kpi.accent-c {{ border-top: 4px solid var(--violet); }}
    .kpi.accent-d {{ border-top: 4px solid var(--gold); }}
    .two-col {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(300px, 0.72fr);
      gap: 18px;
      align-items: start;
    }}
    .panel {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }}
    .finding-list {{
      margin: 0;
      padding-left: 20px;
    }}
    .finding-list li {{ margin: 8px 0; }}
    .warning-list, .agent-list, .action-list, .temp-list {{
      list-style: none;
      margin: 0;
      padding: 0;
    }}
    .warning-list li, .temp-list li {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      padding: 10px 0;
      border-bottom: 1px solid var(--soft);
    }}
    .warning-list li:last-child, .temp-list li:last-child {{ border-bottom: 0; }}
    .note {{
      margin-top: 14px;
      padding: 12px;
      background: #f4efe5;
      border-left: 4px solid var(--rust);
      color: #4f3c2f;
      border-radius: 4px;
    }}
    .chart-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
    }}
    .chart-panel {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      overflow: hidden;
    }}
    .svg-box {{
      width: 100%;
      overflow-x: auto;
    }}
    .svg-box svg {{
      display: block;
      width: 100%;
      height: auto;
      min-width: 540px;
    }}
    .table-wrap {{
      overflow-x: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--paper);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      min-width: 620px;
    }}
    th, td {{
      padding: 10px 12px;
      border-bottom: 1px solid var(--soft);
      text-align: left;
      vertical-align: top;
      font-size: 14px;
      white-space: nowrap;
    }}
    th {{
      background: #edeae1;
      font-weight: 700;
      color: #26343b;
    }}
    tr:last-child td {{ border-bottom: 0; }}
    .model-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin: 0 0 12px;
    }}
    .pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      min-height: 30px;
      padding: 4px 10px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: var(--paper);
      color: var(--muted);
      font-size: 13px;
    }}
    .pill strong {{ color: var(--ink); }}
    .action-list li, .agent-list li {{
      display: grid;
      grid-template-columns: 170px minmax(0, 1fr) 80px;
      gap: 12px;
      padding: 12px 0;
      border-bottom: 1px solid var(--soft);
      align-items: start;
    }}
    .agent-list li {{
      grid-template-columns: 120px minmax(0, 1fr);
    }}
    .action-list li:last-child, .agent-list li:last-child {{ border-bottom: 0; }}
    .agent-name {{
      font-weight: 700;
      color: var(--teal);
    }}
    .agent-summary, .action-list span {{
      color: var(--muted);
    }}
    .action-list em {{
      justify-self: end;
      font-style: normal;
      color: var(--rust);
      font-weight: 700;
    }}
    .empty {{
      color: var(--muted);
      padding: 12px 0;
    }}
    footer {{
      margin-top: 36px;
      padding-top: 18px;
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: 13px;
    }}
    @media (max-width: 920px) {{
      .kpis {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .two-col, .chart-grid {{ grid-template-columns: 1fr; }}
      .action-list li {{ grid-template-columns: 1fr; }}
      .action-list em {{ justify-self: start; }}
      h1 {{ font-size: 28px; }}
    }}
    @media (max-width: 560px) {{
      main {{ width: min(100% - 20px, 1180px); padding-top: 14px; }}
      .kpis {{ grid-template-columns: 1fr; }}
      .panel, .chart-panel {{ padding: 14px; }}
      th, td {{ padding: 8px 10px; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>社交媒体数据分析 Harness Dashboard</h1>
      <p class="subtitle">{escape(state["goal"])}</p>
      <p class="source">数据源：{escape(str(state["source_path"]))}</p>
    </header>

    <section class="kpis" aria-label="核心指标">
      <div class="kpi accent-a"><span>样本量</span><strong>{_fmt(profile.get("rows"))}</strong></div>
      <div class="kpi accent-b"><span>字段数</span><strong>{_fmt(profile.get("columns"))}</strong></div>
      <div class="kpi accent-c"><span>质量门禁</span><strong>{escape(str(validation.get("quality_gate", "-")))}</strong></div>
      <div class="kpi accent-d"><span>重复博文ID</span><strong>{_fmt(validation.get("duplicate_post_ids"))}</strong></div>
      <div class="kpi accent-a"><span>图表数量</span><strong>{_fmt(len(charts))}</strong></div>
      <div class="kpi accent-b"><span>分析目标变量</span><strong>{escape(str(analysis.get("metric", "-")))}</strong></div>
    </section>

    <section class="two-col">
      <div>
        <h2>关键发现</h2>
        <div class="panel">
          <ol class="finding-list">{findings}</ol>
        </div>
      </div>
      <div>
        <h2>数据核验</h2>
        <div class="panel">
          <ul class="warning-list">{missing_items}</ul>
          <p class="note">{escape(str(validation.get("duplicate_note", "无观测粒度提示。")))}</p>
          <p class="source">时间范围：{escape(str(time_range.get("min", "-")))} 至 {escape(str(time_range.get("max", "-")))}</p>
        </div>
      </div>
    </section>

    <h2>图表</h2>
    <div class="chart-grid">{''.join(chart_cards)}</div>

    <h2>分组表现</h2>
    <section class="two-col">
      <div class="panel">
        <h3>主题类别</h3>
        {_table(analysis.get("topic_summary", []), [("group", "主题"), ("posts", "样本数"), ("mean", "均值"), ("median", "中位数"), ("total", "合计")])}
      </div>
      <div class="panel">
        <h3>情感极性</h3>
        {_table(analysis.get("sentiment_summary", []), [("group", "情感"), ("posts", "样本数"), ("mean", "均值"), ("median", "中位数"), ("total", "合计")])}
      </div>
    </section>
    <section class="panel" style="margin-top: 18px;">
      <h3>官方媒体</h3>
      {_table(analysis.get("media_summary", []), [("group", "是否官方媒体"), ("posts", "样本数"), ("mean", "均值"), ("median", "中位数"), ("total", "合计")])}
    </section>

    <h2>相关性与轻量回归</h2>
    <section class="two-col">
      <div class="panel">
        <h3>相关性 Top 10</h3>
        {_table(analysis.get("correlations", []), [("variable", "变量"), ("pearson_corr", "Pearson相关"), ("n", "样本数")], limit=10)}
      </div>
      <div class="panel">
        <h3>模型摘要</h3>
        <div class="model-meta">
          <span class="pill">目标变量 <strong>{escape(str(ols.get("target", "-")))}</strong></span>
          <span class="pill">有效样本 <strong>{_fmt(ols.get("n"))}</strong></span>
          <span class="pill">R² <strong>{_fmt(ols.get("r_squared"), 4)}</strong></span>
        </div>
        <p class="note">{escape(str(ols.get("note", "当前模型仅用于探索方向。")))}</p>
      </div>
    </section>
    <section class="panel" style="margin-top: 18px;">
      <h3>回归系数</h3>
      {_table(ols.get("coefficients", []), [("variable", "变量"), ("coef", "系数"), ("std_err", "标准误"), ("t", "t值")], limit=20)}
    </section>

    <h2>问题处理建议</h2>
    <section class="panel">
      <ul class="action-list">{actions}</ul>
    </section>

    <h2>Agent 运行记录</h2>
    <section class="two-col">
      <div class="panel">
        <h3>主流程</h3>
        <ul class="agent-list">{agents}</ul>
      </div>
      <div class="panel">
        <h3>温度策略</h3>
        <ul class="temp-list">{temp_policy}</ul>
      </div>
    </section>

    <h2>Skill 配置摘要</h2>
    <section class="panel">
      {_table(skill_rows, [("display_name", "Skill"), ("agent", "Agent 文件"), ("agent_type", "类型"), ("temperature", "温度")])}
      <p class="source">完整配置见输出目录中的 skill_cards.json。</p>
    </section>

    <footer>
      由本地 Harness 自动生成。正式论文建模前，建议继续补充稳健标准误、固定效应、共线性检查和观测粒度确认。
    </footer>
  </main>
</body>
</html>
"""

    html_path = output_dir / "social_media_analysis_dashboard.html"
    html_path.write_text(html, encoding="utf-8-sig")
    return html_path


def main() -> None:
    html_path = build_dashboard()
    print(f"html={html_path}")


if __name__ == "__main__":
    main()
