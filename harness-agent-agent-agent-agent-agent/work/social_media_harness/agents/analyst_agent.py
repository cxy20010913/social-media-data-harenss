from __future__ import annotations

import math

import numpy as np
import pandas as pd

from schemas import AgentResult


def _round_float(value: float, digits: int = 4) -> float | None:
    if value is None or pd.isna(value) or math.isinf(float(value)):
        return None
    return round(float(value), digits)


def _group_summary(df: pd.DataFrame, group_col: str, metric: str) -> list[dict[str, object]]:
    if group_col not in df or metric not in df:
        return []
    grouped = (
        df.groupby(group_col, dropna=False)
        .agg(posts=(metric, "size"), mean=(metric, "mean"), median=(metric, "median"), total=(metric, "sum"))
        .reset_index()
        .sort_values("mean", ascending=False)
    )
    records = []
    for row in grouped.to_dict("records"):
        records.append({
            "group": str(row[group_col]),
            "posts": int(row["posts"]),
            "mean": _round_float(row["mean"], 3),
            "median": _round_float(row["median"], 3),
            "total": _round_float(row["total"], 3),
        })
    return records


def _safe_corr(df: pd.DataFrame, columns: list[str], target: str) -> list[dict[str, object]]:
    records = []
    for col in columns:
        if col == target or col not in df or target not in df:
            continue
        pair = df[[col, target]].dropna()
        if len(pair) < 5 or pair[col].nunique() <= 1:
            continue
        corr = pair[col].corr(pair[target])
        records.append({"variable": col, "pearson_corr": _round_float(corr, 4), "n": int(len(pair))})
    return sorted(records, key=lambda x: abs(x["pearson_corr"] or 0), reverse=True)


def _ols(df: pd.DataFrame, y_col: str, x_cols: list[str]) -> dict[str, object]:
    available = [col for col in x_cols if col in df]
    model_df = df[[y_col] + available].replace([np.inf, -np.inf], np.nan).dropna()
    model_df = model_df.loc[:, model_df.nunique() > 1]
    if y_col not in model_df or len(model_df) < len(model_df.columns) + 5:
        return {"status": "skipped", "reason": "有效样本不足或变量无变化。"}

    y = model_df[y_col].to_numpy(dtype=float)
    x_names = [col for col in model_df.columns if col != y_col]
    x = model_df[x_names].to_numpy(dtype=float)
    x = np.column_stack([np.ones(len(x)), x])
    names = ["截距"] + x_names

    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    fitted = x @ beta
    residual = y - fitted
    sse = float(np.sum(residual ** 2))
    sst = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - sse / sst if sst else 0
    n, k = x.shape
    dof = max(n - k, 1)
    sigma2 = sse / dof
    xtx_inv = np.linalg.pinv(x.T @ x)
    se = np.sqrt(np.diag(xtx_inv) * sigma2)
    t_values = np.divide(beta, se, out=np.zeros_like(beta), where=se != 0)

    coefficients = []
    for name, coef, std_err, t_value in zip(names, beta, se, t_values):
        coefficients.append({
            "variable": name,
            "coef": _round_float(coef, 4),
            "std_err": _round_float(std_err, 4),
            "t": _round_float(t_value, 3),
        })

    return {
        "status": "success",
        "target": y_col,
        "n": int(n),
        "r_squared": _round_float(r2, 4),
        "coefficients": coefficients,
        "note": "轻量 OLS 用于探索方向；正式论文建议用稳健标准误、固定效应或更完整模型复核。",
    }


def run(df: pd.DataFrame) -> AgentResult:
    metric = "ln转发量" if "ln转发量" in df else "转发量"
    raw_metric = "转发量" if "转发量" in df else metric
    findings = []

    topic_summary = _group_summary(df, "主题类别", metric)
    sentiment_summary = _group_summary(df, "情感极性", metric)
    media_summary = _group_summary(df, "是否官方媒体", metric)
    rich_media_summary = _group_summary(df, "有无富媒体", metric)

    if topic_summary:
        top = topic_summary[0]
        findings.append(f"按{metric}均值看，{top['group']}类内容传播表现最高，均值为 {top['mean']}。")
    if sentiment_summary:
        top = sentiment_summary[0]
        findings.append(f"按情感极性分组，{top['group']}内容的{metric}均值最高。")
    if "发布时间_parsed" in df:
        daily = (
            df.assign(date=df["发布时间_parsed"].dt.date.astype(str))
            .groupby("date")
            .agg(posts=("博文ID", "size"), mean_reposts=(raw_metric, "mean"), total_reposts=(raw_metric, "sum"))
            .reset_index()
            .sort_values("date")
        )
        peak = daily.sort_values("total_reposts", ascending=False).head(1).to_dict("records")
        if peak:
            findings.append(f"总转发量峰值出现在 {peak[0]['date']}，当天总转发量为 {int(peak[0]['total_reposts'])}。")
    else:
        daily = pd.DataFrame()

    corr_candidates = [
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
        "结构性病毒性",
        "门槛和",
        "平均门槛",
        "0门槛占比",
    ]
    correlations = _safe_corr(df, corr_candidates, metric)
    if correlations:
        best = correlations[0]
        findings.append(f"与{metric}相关性最高的变量是 {best['variable']}，相关系数 {best['pearson_corr']}。")

    model_x = [
        "ln粉丝数",
        "发布者是否认证",
        "是否官方媒体",
        "有无图片",
        "有无视频",
        "标签数量",
        "情感强度",
        "是否积极",
        "是否消极",
        "结构性病毒性",
        "门槛和",
        "平均门槛",
    ]
    model = _ols(df, metric, model_x)

    payload = {
        "metric": metric,
        "findings": findings,
        "topic_summary": topic_summary,
        "sentiment_summary": sentiment_summary,
        "media_summary": media_summary,
        "rich_media_summary": rich_media_summary,
        "daily_summary": daily.round(4).to_dict("records") if not daily.empty else [],
        "correlations": correlations,
        "ols": model,
    }
    return AgentResult(
        agent="analyst_agent",
        status="success",
        summary=f"围绕 {metric} 完成分组、趋势、相关性和轻量回归分析。",
        payload=payload,
        warnings=[] if model.get("status") == "success" else [str(model.get("reason"))],
    )
