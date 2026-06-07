# Social Media Analysis Harness

A lightweight multi-agent data analysis harness for social media propagation research.

This project turns a raw social media dataset into a reproducible analysis pipeline with data profiling, validation, statistical summaries, chart generation, structured agent outputs, skill-card configuration, Markdown reports, and an offline HTML dashboard.

## What It Does

The harness coordinates several specialized agents:

- **Reader Agent**: loads CSV data, detects field roles, parses time fields, and profiles the dataset.
- **Validator Agent**: checks missing values, duplicated post IDs, binary fields, time validity, and abnormal numeric values.
- **Analyst Agent**: produces descriptive summaries, grouped comparisons, correlations, and a lightweight OLS exploration.
- **Chart Agent**: generates SVG charts from analysis outputs.
- **Design Agent**: assembles a readable Markdown report and dashboard-ready narrative structure.
- **Temperature Control Agent**: records model-temperature policy for each agent.
- **Resolver Agent**: converts data quality warnings into handling recommendations.

## Current Use Case

The current implementation is configured for social media disaster communication data, especially datasets containing fields such as:

- post ID and publishing time
- repost, like, and comment counts
- publisher attributes
- sentiment scores and sentiment polarity
- topic category
- rich media indicators
- structural virality metrics

The default analysis focuses on log-transformed repost count as the main propagation-performance metric.

## Project Structure

```text
social_media_harness/
  orchestrator.py                 # Main pipeline controller
  schemas.py                      # Shared state and result schemas
  skill_config.py                 # Skill-card loader
  html_dashboard.py               # Offline HTML dashboard generator
  self_check.py                   # Output validation script
  config/
    skill_cards.json              # Agent skill definitions and prompt protocols
  agents/
    reader_agent.py               # Data loading and profiling
    validator_agent.py            # Data quality validation
    analyst_agent.py              # Statistical analysis
    chart_agent.py                # SVG chart generation
    design_agent.py               # Markdown report assembly
    temp_control_agent.py         # Temperature policy controller
    resolver_agent.py             # Issue handling recommendations
```

## Skill Cards

Agent behavior is configured in:

```text
config/skill_cards.json
```

Each skill card includes:

- `display_name`
- `agent_type`
- `temperature`
- `trigger_conditions`
- `input_contract`
- `processing_steps`
- `output_contract`
- `quality_checks`
- `exception_handling`
- `prompt_protocol`

The `prompt_protocol` field follows a structured prompt format:

```text
role
task
constraints
data_output / input
insight_output
output_format
self_check
```

The config also includes `sales_skill_template_reference`, a reusable reference for adapting the harness to sales analytics workflows with:

- extract skill
- chart skill
- design skill

## Installation

Create a Python environment with:

```bash
pip install pandas numpy
```

No plotting library is required. Charts are generated as standalone SVG files.

## Usage

Run the full pipeline:

```bash
python orchestrator.py --source path/to/your_data.csv --output outputs/social_media_harness
```

Run output validation:

```bash
python self_check.py
```

## Outputs

The pipeline writes the following files to the output directory:

```text
social_media_analysis_report.md        # Markdown report
social_media_analysis_dashboard.html   # Offline HTML dashboard
harness_state.json                     # Full pipeline state
agent_results.json                     # Structured outputs from each agent
skill_cards.json                       # Skill config used for this run
charts/*.svg                           # Generated SVG charts
```

## Example Findings

On the current social media dataset, the harness produced findings such as:

- Help-seeking posts had the highest average log repost count.
- Negative sentiment posts had the highest average log repost count among sentiment groups.
- The total repost peak occurred on a specific date in the observation window.
- Structural virality had the strongest correlation with log repost count.

These findings are generated from the data and written into both the Markdown report and the HTML dashboard.

## Design Principles

- **Agent separation**: each agent owns one stage of the workflow.
- **Config-first behavior**: skill definitions are stored in JSON rather than hidden in code.
- **Traceable outputs**: reports, charts, state files, and agent results are all persisted.
- **Validation before interpretation**: data quality warnings are surfaced before conclusions.
- **Offline-friendly reporting**: the dashboard is a static HTML file with embedded SVG charts.

## Notes

The lightweight OLS module is intended for exploratory analysis. For formal academic or production modeling, consider adding:

- robust standard errors
- fixed effects
- multicollinearity checks
- model comparison tables
- richer missing-data treatment
