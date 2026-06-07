from __future__ import annotations

from html import escape
from pathlib import Path

from schemas import AgentResult


WIDTH = 900
HEIGHT = 520
MARGIN = {"top": 64, "right": 48, "bottom": 92, "left": 86}


def _scale(value: float, src_min: float, src_max: float, dst_min: float, dst_max: float) -> float:
    if src_max == src_min:
        return (dst_min + dst_max) / 2
    return dst_min + (value - src_min) * (dst_max - dst_min) / (src_max - src_min)


def _write_svg(path: Path, body: str, title: str) -> None:
    path.write_text(
        f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  <rect width="100%" height="100%" fill="#fbfbf8"/>
  <text x="{WIDTH / 2}" y="34" text-anchor="middle" font-family="Arial, sans-serif" font-size="22" font-weight="700" fill="#1f2933">{escape(title)}</text>
  {body}
</svg>
""",
        encoding="utf-8",
    )


def _bar_chart(path: Path, rows: list[dict[str, object]], title: str, x_key: str = "group", y_key: str = "mean") -> None:
    rows = rows[:8]
    chart_w = WIDTH - MARGIN["left"] - MARGIN["right"]
    chart_h = HEIGHT - MARGIN["top"] - MARGIN["bottom"]
    max_y = max(float(row[y_key] or 0) for row in rows) if rows else 1
    max_y = max(max_y, 1)
    bar_gap = 18
    bar_w = (chart_w - bar_gap * (len(rows) - 1)) / max(len(rows), 1)
    colors = ["#2f6f73", "#c96f45", "#7567a8", "#d29d2b", "#4f7db8", "#8a6a43", "#65736d", "#b85b6b"]
    elements = [
        f'<line x1="{MARGIN["left"]}" y1="{HEIGHT - MARGIN["bottom"]}" x2="{WIDTH - MARGIN["right"]}" y2="{HEIGHT - MARGIN["bottom"]}" stroke="#9aa3a8" stroke-width="1"/>',
        f'<line x1="{MARGIN["left"]}" y1="{MARGIN["top"]}" x2="{MARGIN["left"]}" y2="{HEIGHT - MARGIN["bottom"]}" stroke="#9aa3a8" stroke-width="1"/>',
    ]
    for i, row in enumerate(rows):
        value = float(row[y_key] or 0)
        x = MARGIN["left"] + i * (bar_w + bar_gap)
        y = _scale(value, 0, max_y, HEIGHT - MARGIN["bottom"], MARGIN["top"])
        h = HEIGHT - MARGIN["bottom"] - y
        label = str(row[x_key])
        elements.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" fill="{colors[i % len(colors)]}" rx="3"/>')
        elements.append(f'<text x="{x + bar_w / 2:.1f}" y="{y - 8:.1f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#24323a">{value:.2f}</text>')
        elements.append(f'<text x="{x + bar_w / 2:.1f}" y="{HEIGHT - MARGIN["bottom"] + 26}" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="#24323a">{escape(label[:12])}</text>')
        elements.append(f'<text x="{x + bar_w / 2:.1f}" y="{HEIGHT - MARGIN["bottom"] + 45}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#6b7479">n={int(row.get("posts", 0))}</text>')
    elements.append(f'<text x="26" y="{MARGIN["top"] + 10}" font-family="Arial, sans-serif" font-size="13" fill="#56636a">均值</text>')
    _write_svg(path, "\n  ".join(elements), title)


def _line_chart(path: Path, rows: list[dict[str, object]], title: str) -> None:
    rows = rows[:]
    chart_w = WIDTH - MARGIN["left"] - MARGIN["right"]
    chart_h = HEIGHT - MARGIN["top"] - MARGIN["bottom"]
    values = [float(row.get("total_reposts", 0) or 0) for row in rows]
    max_y = max(values) if values else 1
    max_y = max(max_y, 1)
    elements = [
        f'<line x1="{MARGIN["left"]}" y1="{HEIGHT - MARGIN["bottom"]}" x2="{WIDTH - MARGIN["right"]}" y2="{HEIGHT - MARGIN["bottom"]}" stroke="#9aa3a8" stroke-width="1"/>',
        f'<line x1="{MARGIN["left"]}" y1="{MARGIN["top"]}" x2="{MARGIN["left"]}" y2="{HEIGHT - MARGIN["bottom"]}" stroke="#9aa3a8" stroke-width="1"/>',
    ]
    points = []
    for i, row in enumerate(rows):
        x = _scale(i, 0, max(len(rows) - 1, 1), MARGIN["left"], MARGIN["left"] + chart_w)
        y = _scale(float(row.get("total_reposts", 0) or 0), 0, max_y, HEIGHT - MARGIN["bottom"], MARGIN["top"])
        points.append(f"{x:.1f},{y:.1f}")
    if points:
        elements.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="#2f6f73" stroke-width="3"/>')
    for i, row in enumerate(rows):
        x = _scale(i, 0, max(len(rows) - 1, 1), MARGIN["left"], MARGIN["left"] + chart_w)
        y = _scale(float(row.get("total_reposts", 0) or 0), 0, max_y, HEIGHT - MARGIN["bottom"], MARGIN["top"])
        elements.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#c96f45"/>')
        if i % max(1, len(rows) // 6) == 0 or i == len(rows) - 1:
            elements.append(f'<text x="{x:.1f}" y="{HEIGHT - MARGIN["bottom"] + 26}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#24323a">{escape(str(row.get("date", ""))[5:])}</text>')
    elements.append(f'<text x="20" y="{MARGIN["top"] + 10}" font-family="Arial, sans-serif" font-size="13" fill="#56636a">总转发量</text>')
    _write_svg(path, "\n  ".join(elements), title)


def run(analysis: dict[str, object], output_dir: Path) -> AgentResult:
    chart_dir = output_dir / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)
    charts: list[dict[str, str]] = []
    metric = str(analysis.get("metric", "ln转发量"))

    chart_specs = [
        ("topic_mean_reposts.svg", analysis.get("topic_summary", []), f"不同主题类别的{metric}均值"),
        ("sentiment_mean_reposts.svg", analysis.get("sentiment_summary", []), f"不同情感极性的{metric}均值"),
        ("media_mean_reposts.svg", analysis.get("media_summary", []), f"官方媒体与非官方媒体的{metric}均值"),
    ]
    for filename, rows, title in chart_specs:
        if rows:
            path = chart_dir / filename
            _bar_chart(path, rows, title)
            charts.append({"title": title, "path": str(path)})

    daily = analysis.get("daily_summary", [])
    if daily:
        path = chart_dir / "daily_total_reposts.svg"
        _line_chart(path, daily, "每日总转发量趋势")
        charts.append({"title": "每日总转发量趋势", "path": str(path)})

    return AgentResult(
        agent="chart_agent",
        status="success",
        summary=f"生成 {len(charts)} 张 SVG 图表。",
        payload={"charts": charts},
    )
