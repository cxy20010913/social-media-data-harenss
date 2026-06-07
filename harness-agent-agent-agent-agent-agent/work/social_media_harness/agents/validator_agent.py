from __future__ import annotations

import pandas as pd

from schemas import AgentResult


def _rate(value: int, total: int) -> float:
    return round(value / total, 4) if total else 0.0


def run(df: pd.DataFrame) -> AgentResult:
    rows = len(df)
    warnings: list[str] = []
    missing_rates = {
        col: _rate(int(count), rows)
        for col, count in df.isna().sum().items()
        if count > 0
    }
    high_missing = {col: rate for col, rate in missing_rates.items() if rate >= 0.3}
    if high_missing:
        warnings.append(f"高缺失字段：{', '.join(high_missing.keys())}")

    duplicate_post_ids = int(df["博文ID"].duplicated().sum()) if "博文ID" in df else 0
    duplicate_note = None
    if duplicate_post_ids:
        duplicate_note = (
            "博文ID存在大量重复。结合结构性病毒性、门槛等字段判断，"
            "该表可能是一篇博文对应多条传播结构观测，重复不应直接删除。"
        )
        warnings.append("博文ID重复较多，后续分析需明确观测粒度。")

    impossible_counts = {}
    for col in ["点赞量", "评论量", "转发量", "发布者粉丝数", "发布者关注数"]:
        if col in df:
            impossible_counts[col] = int((df[col] < 0).sum())

    time_issues = {}
    if "发布时间_parsed" in df:
        time_issues = {
            "invalid_time_count": int(df["发布时间_parsed"].isna().sum()),
            "min_time": str(df["发布时间_parsed"].min()),
            "max_time": str(df["发布时间_parsed"].max()),
        }

    binary_columns = [
        col
        for col in df.columns
        if col.startswith("是否") or col.startswith("有无")
    ]
    binary_issues = {}
    for col in binary_columns:
        values = set(df[col].dropna().unique().tolist())
        bad = sorted(v for v in values if v not in {0, 1, 0.0, 1.0})
        if bad:
            binary_issues[col] = bad[:10]

    payload = {
        "row_count": rows,
        "missing_rates": missing_rates,
        "high_missing": high_missing,
        "duplicate_post_ids": duplicate_post_ids,
        "duplicate_note": duplicate_note,
        "negative_value_counts": impossible_counts,
        "time_issues": time_issues,
        "binary_issues": binary_issues,
        "quality_gate": "pass_with_warnings" if warnings else "pass",
    }

    return AgentResult(
        agent="validator_agent",
        status="success",
        summary="完成缺失、重复、取值范围和时间字段核验。",
        payload=payload,
        warnings=warnings,
    )
