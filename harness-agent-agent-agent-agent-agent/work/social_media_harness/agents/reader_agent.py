from __future__ import annotations

from pathlib import Path

import pandas as pd

from schemas import AgentResult


TEXT_COLUMNS = {"发布博文", "文本", "发布者昵称", "发布者IP", "情感极性", "主题类别"}


def read_csv(path: Path) -> pd.DataFrame:
    """Read the source table with a small fallback for common Chinese CSV encodings."""
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path)


def _classify_columns(df: pd.DataFrame) -> dict[str, list[str]]:
    numeric = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    categorical = [
        col
        for col in df.columns
        if col not in numeric and col not in TEXT_COLUMNS and df[col].nunique(dropna=True) <= 30
    ]
    text = [col for col in df.columns if col in TEXT_COLUMNS]
    outcomes = [col for col in ["转发量", "ln转发量", "结构性病毒性", "ln结构性病毒性"] if col in df]
    predictors = [
        col
        for col in [
            "ln粉丝数",
            "发布者是否认证",
            "是否官方媒体",
            "是否受灾地IP",
            "是否北上广",
            "有无图片",
            "有无视频",
            "标签数量",
            "情感强度",
            "是否积极",
            "是否消极",
            "门槛和",
            "平均门槛",
            "0门槛占比",
        ]
        if col in df
    ]
    groups = [col for col in ["主题类别", "情感极性", "是否官方媒体", "有无富媒体", "有无图片"] if col in df]
    return {
        "numeric": numeric,
        "categorical": categorical,
        "text": text,
        "outcomes": outcomes,
        "candidate_predictors": predictors,
        "grouping_columns": groups,
    }


def run(path: Path) -> tuple[pd.DataFrame, AgentResult]:
    df = read_csv(path)
    parsed_time = pd.to_datetime(df["发布时间"], errors="coerce") if "发布时间" in df else None
    profile = {
        "source_path": str(path),
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
        "column_names": list(df.columns),
        "column_roles": _classify_columns(df),
        "missing_by_column": {col: int(count) for col, count in df.isna().sum().items()},
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
    }
    if parsed_time is not None:
        profile["time_range"] = {
            "min": str(parsed_time.min()),
            "max": str(parsed_time.max()),
            "invalid_count": int(parsed_time.isna().sum()),
        }
        df = df.copy()
        df["发布时间_parsed"] = parsed_time

    return df, AgentResult(
        agent="reader_agent",
        status="success",
        summary=f"读取 {len(df):,} 行、{df.shape[1]:,} 列，并完成字段角色识别。",
        payload=profile,
    )
