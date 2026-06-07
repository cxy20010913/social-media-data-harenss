社交媒体分析框架
这是一个专为社交媒体传播研究设计的轻量级多智能体（multi-agent）数据分析框架。

该项目将原始社交媒体数据集转化为一个可复现的分析流水线，涵盖数据概览（profiling）、验证、统计摘要、图表生成、结构化智能体输出、技能卡配置、Markdown 报告以及离线 HTML 仪表盘。

功能概述
该框架协调多个专用智能体协同工作：

读取智能体（Reader Agent）：加载 CSV 数据，识别字段角色，解析时间字段，并生成数据集概览。
验证智能体（Validator Agent）：检查缺失值、重复的帖子 ID、二元字段、时间有效性及异常数值。
分析智能体（Analyst Agent）：生成描述性统计摘要、分组比较、相关性分析以及轻量级 OLS（普通最小二乘法）探索性分析。
图表智能体（Chart Agent）：根据分析结果生成 SVG 图表。
设计智能体（Design Agent）：整合生成易读的 Markdown 报告及适合仪表盘展示的叙述结构。
温度控制智能体（Temperature Control Agent）：记录每个智能体的模型“温度”（temperature）策略。
解析智能体（Resolver Agent）：将数据质量警告转化为具体的处理建议。

当前应用场景
目前的实现配置针对社交媒体灾害传播数据，特别是包含以下字段的数据集：

帖子 ID 与发布时间
转发、点赞与评论数量
发布者属性
情感得分与情感极性
主题类别
富媒体指标
结构化病毒式传播指标
默认分析侧重于将“经对数变换后的转发量”作为衡量传播效果的主要指标。项目结构
social_media_harness/
orchestrator.py                 # 主流水线控制器
schemas.py                      # 共享状态与结果的数据模式（Schema）
skill_config.py                 # 技能卡（Skill-card）加载器
html_dashboard.py               # 离线 HTML 仪表盘生成器
self_check.py                   # 输出验证脚本
config/
skill_cards.json              # 智能体技能定义与提示词（Prompt）协议
agents/
reader_agent.py               # 数据加载与概况分析
validator_agent.py            # 数据质量验证
analyst_agent.py              # 统计分析
chart_agent.py                # SVG 图表生成
design_agent.py               # Markdown 报告组装
temp_control_agent.py         # 温度（Temperature）策略控制器
resolver_agent.py             # 问题处理建议
技能卡
智能体行为配置于：

config/skill_cards.json
每张技能卡包含：

display_name（显示名称）
agent_type（智能体类型）
temperature（温度参数）
trigger_conditions（触发条件）
input_contract（输入契约）
processing_steps（处理步骤）
output_contract（输出契约）
quality_checks（质量检查）
exception_handling（异常处理）
prompt_protocol（提示词协议）
prompt_protocol 字段遵循结构化提示词格式：

role（角色）
task（任务）
constraints（约束条件）
data_output / input（数据输出/输入）
insight_output（洞察输出）
output_format（输出格式）
self_check（自检）
该配置还包含 sales_skill_template_reference，这是一个可复用的参考配置，用于将该框架适配到销售分析工作流中，涵盖：

提取技能（extract skill）
图表技能（chart skill）
设计技能（design skill）
安装
创建 Python 环境并安装：

pip install pandas numpy
无需绘图库。图表将生成为独立的 SVG 文件。使用方法
运行完整流水线：

python orchestrator.py --source path/to/your_data.csv --output outputs/social_media_harness
运行输出验证：

python self_check.py
输出结果
流水线会将以下文件写入输出目录：

social_media_analysis_report.md        # Markdown 格式报告
social_media_analysis_dashboard.html   # 离线 HTML 仪表盘
harness_state.json                     # 完整流水线状态
agent_results.json                     # 各个智能体（agent）的结构化输出
skill_cards.json                       # 本次运行使用的技能配置
charts/*.svg                           # 生成的 SVG 图表
分析发现示例
针对当前的社交媒体数据集，该系统得出了以下发现：

“寻求帮助”类帖子的平均转发量（对数尺度）最高。
在不同情感类别中，负面情感帖子的平均转发量（对数尺度）最高。
总转发量峰值出现在观测期内的特定日期。
“结构化病毒式传播”指标与转发量（对数尺度）的相关性最强。
这些发现基于数据生成，并同时写入 Markdown 报告和 HTML 仪表盘中。

设计原则
智能体分离：每个智能体负责工作流中的一个阶段。
配置优先：技能定义存储在 JSON 文件中，而非硬编码在程序逻辑内。
输出可追溯：报告、图表、状态文件及智能体结果均进行持久化存储。
先验证后解读：在得出结论前，先提示数据质量相关的警告信息。
支持离线查看：仪表盘为包含嵌入式 SVG 图表的静态 HTML 文件。
注意事项
轻量级 OLS（普通最小二乘法）模块旨在用于探索性分析。若需进行正式学术研究或生产环境建模，建议增加以下内容：

稳健标准误（robust standard errors）
固定效应（fixed effects）
多重共线性检查
模型比较表
更完善的缺失数据处理方案
