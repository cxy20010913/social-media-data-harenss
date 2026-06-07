from __future__ import annotations

from schemas import AgentResult


def run(validation: dict[str, object], analysis: dict[str, object]) -> AgentResult:
    actions: list[dict[str, str]] = []
    high_missing = validation.get("high_missing", {})
    if isinstance(high_missing, dict):
        for column, rate in high_missing.items():
            actions.append({
                "issue": f"{column} 缺失率较高",
                "handling": "默认不进入核心模型；若论文需要该变量，应单独说明缺失机制或改用缺失指示变量。",
                "severity": "medium" if float(rate) < 0.9 else "high",
            })

    if validation.get("duplicate_post_ids"):
        actions.append({
            "issue": "博文ID大量重复",
            "handling": "将观测粒度标记为传播结构观测；正式建模前需决定是否聚合到博文层级。",
            "severity": "high",
        })

    ols = analysis.get("ols", {})
    if isinstance(ols, dict) and ols.get("status") == "success":
        actions.append({
            "issue": "当前回归为轻量 OLS",
            "handling": "用于方向初筛；论文结果建议增加稳健标准误、控制变量、固定效应和共线性检查。",
            "severity": "medium",
        })

    return AgentResult(
        agent="resolver_agent",
        status="success",
        summary=f"生成 {len(actions)} 条问题处理建议。",
        payload={"actions": actions},
    )
