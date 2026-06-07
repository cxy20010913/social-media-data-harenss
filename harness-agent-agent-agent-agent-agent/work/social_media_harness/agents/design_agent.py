from __future__ import annotations

from pathlib import Path

from schemas import AgentResult, HarnessState


def _markdown_table(rows: list[dict[str, object]], headers: list[tuple[str, str]], limit: int = 10) -> str:
    if not rows:
        return "暂无数据。\n"
    header_line = "| " + " | ".join(label for _, label in headers) + " |"
    sep_line = "| " + " | ".join("---" for _ in headers) + " |"
    body = []
    for row in rows[:limit]:
        body.append("| " + " | ".join(str(row.get(key, "")) for key, _ in headers) + " |")
    return "\n".join([header_line, sep_line] + body) + "\n"


def run(state: HarnessState, agent_results: list[AgentResult]) -> AgentResult:
    analysis = state.analysis
    validation = state.validation
    profile = state.data_profile
    resolver_results = [
        result.payload.get("actions", [])
        for result in agent_results
        if result.agent == "resolver_agent"
    ]
    actions = resolver_results[0] if resolver_results else []

    lines = [
        "# 社交媒体数据分析 Harness 报告",
        "",
        f"分析目标：{state.goal}",
        "",
        "## 1. 数据概览",
        "",
        f"- 数据源：`{state.source_path}`",
        f"- 样本量：{profile.get('rows')} 行",
        f"- 字段数：{profile.get('columns')} 列",
    ]
    time_range = profile.get("time_range", {})
    if time_range:
        lines.extend([
            f"- 发布时间范围：{time_range.get('min')} 至 {time_range.get('max')}",
            f"- 无法解析的时间：{time_range.get('invalid_count')} 条",
        ])

    lines.extend([
        "",
        "## 2. 数据核验",
        "",
        f"- 质量门禁：{validation.get('quality_gate')}",
        f"- 重复博文ID数量：{validation.get('duplicate_post_ids')}",
    ])
    if validation.get("duplicate_note"):
        lines.append(f"- 观测粒度提示：{validation.get('duplicate_note')}")
    high_missing = validation.get("high_missing", {})
    if high_missing:
        missing_text = "；".join(f"{k}: {v:.1%}" for k, v in high_missing.items())
        lines.append(f"- 高缺失字段：{missing_text}")
    else:
        lines.append("- 未发现高缺失字段。")

    lines.extend(["", "## 3. 关键发现", ""])
    for finding in analysis.get("findings", []):
        lines.append(f"- {finding}")

    lines.extend([
        "",
        "## 4. 分组表现",
        "",
        "### 主题类别",
        "",
        _markdown_table(
            analysis.get("topic_summary", []),
            [("group", "主题"), ("posts", "样本数"), ("mean", "均值"), ("median", "中位数"), ("total", "合计")],
        ),
        "### 情感极性",
        "",
        _markdown_table(
            analysis.get("sentiment_summary", []),
            [("group", "情感"), ("posts", "样本数"), ("mean", "均值"), ("median", "中位数"), ("total", "合计")],
        ),
        "### 官方媒体",
        "",
        _markdown_table(
            analysis.get("media_summary", []),
            [("group", "是否官方媒体"), ("posts", "样本数"), ("mean", "均值"), ("median", "中位数"), ("total", "合计")],
        ),
        "",
        "## 5. 相关性与轻量回归",
        "",
        "### 相关性 Top 10",
        "",
        _markdown_table(
            analysis.get("correlations", []),
            [("variable", "变量"), ("pearson_corr", "Pearson相关"), ("n", "样本数")],
            limit=10,
        ),
    ])

    ols = analysis.get("ols", {})
    if ols.get("status") == "success":
        lines.extend([
            f"- 模型目标变量：{ols.get('target')}",
            f"- 有效样本：{ols.get('n')}",
            f"- R²：{ols.get('r_squared')}",
            f"- 说明：{ols.get('note')}",
            "",
            _markdown_table(
                ols.get("coefficients", []),
                [("variable", "变量"), ("coef", "系数"), ("std_err", "标准误"), ("t", "t值")],
                limit=20,
            ),
        ])
    else:
        lines.append(f"- 回归未运行：{ols.get('reason')}")

    lines.extend(["", "## 6. 图表产物", ""])
    for chart in state.charts:
        chart_path = Path(chart["path"])
        rel = chart_path.relative_to(state.output_dir)
        lines.append(f"- [{chart['title']}](./{rel.as_posix()})")

    lines.extend(["", "## 7. 问题处理建议", ""])
    if actions:
        for action in actions:
            lines.append(f"- [{action.get('severity')}] {action.get('issue')}：{action.get('handling')}")
    else:
        lines.append("- 暂无需要额外处理的问题。")

    lines.extend(["", "## 8. Agent 运行记录", ""])
    for result in agent_results:
        lines.append(f"- {result.agent}: {result.summary}")
        for warning in result.warnings:
            lines.append(f"  - 警告：{warning}")

    output = state.output_dir / "social_media_analysis_report.md"
    output.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
    return AgentResult(
        agent="design_agent",
        status="success",
        summary="生成面向论文探索的中文 Markdown 报告。",
        payload={"report_path": str(output)},
    )
