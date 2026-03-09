# 🦠 COVID-19 Global Dashboard

An interactive Streamlit web app that visualises COVID-19 time-series data from the
[Johns Hopkins University CSSE dataset](https://github.com/CSSEGISandData/COVID-19).

## Features

- **Multi-country comparison** — select any combination of countries
- **Metric toggle** — Confirmed Cases or Deaths
- **Count type** — Daily New or Cumulative totals
- **7-day rolling average** — smooth daily noise
- **Date range filter** — focus on any sub-period
- **Chart styles** — Line, Bar, or Area
- **Summary table** — totals + case-fatality rate per country

## Quick Start

```bash
git clone https://github.com/utkarshsharma19/covid-dashboard.git
cd covid-dashboard
pip install -r requirements.txt
streamlit run capstone.py
```

Then open <http://localhost:8501> in your browser.

## Data Source

Data is fetched live from the JHU CSSE GitHub repository at startup (cached for 1 hour):

- `time_series_covid19_confirmed_global.csv`
- `time_series_covid19_deaths_global.csv`

Province/State sub-rows are aggregated to country level. Daily counts are computed by
differencing consecutive cumulative values; negative corrections are clipped to zero.

## Project Files

| File | Purpose |
|------|---------|
| `capstone.py` | Main Streamlit application |
| `requirements.txt` | Python dependencies |
| `capstone.docx` | One-page project write-up |
| `make_docx.py` | Script that generated `capstone.docx` |

## Live App

> Link will be added after deploying to Streamlit Community Cloud.

## Presentation

> Link will be added after recording.

---

*Author: Harsimrat · Course Capstone 2024*
