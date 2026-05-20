# Job Scout

AI-powered job matching and cover letter generation. Upload your CV, search real job listings, and get every role scored against your skills, experience, and location.

## Features

- **CV parsing** — Upload a PDF or Word CV; Claude extracts your profile automatically
- **Specific role search** — Search any job title in 40+ cities or 16 countries
- **Best fit mode** — No role in mind? Claude suggests 4 roles based on your CV and searches all of them
- **Match scoring** — Every job scored 0–100 across role alignment, experience, skills, and location
- **Radar chart breakdown** — Visual score breakdown per job
- **Skill gap tips** — Actionable steps to close each gap
- **Cover letter generation** — One-click tailored cover letter per job
- **CV improvement suggestions** — 3 specific CV tweaks based on your top matches
- **Application tracker** — Mark jobs as applied; status persists across sessions
- **Export to CSV** — Download all results with scores and gaps

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Willmurr/job_scout.git
cd job_scout
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add API keys

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=your_anthropic_api_key
RAPIDAPI_KEY=your_rapidapi_key
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
```

| Key | Where to get it | Required |
|---|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) | Yes |
| `RAPIDAPI_KEY` | [rapidapi.com](https://rapidapi.com) — subscribe to JSearch | Yes |
| `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` | [developer.adzuna.com](https://developer.adzuna.com) | No (enables European job coverage) |

### 4. Run the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

## Deployment (Streamlit Community Cloud)

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
2. Click **New app** → select `Willmurr/job_scout` → branch `main` → main file `app.py`
3. Open **Advanced settings → Secrets** and paste your API keys in TOML format:

```toml
ANTHROPIC_API_KEY = "your_key"
RAPIDAPI_KEY = "your_key"
ADZUNA_APP_ID = "your_id"
ADZUNA_APP_KEY = "your_key"
```

4. Click **Deploy** — your app will be live at a public URL within a few minutes

## Location coverage

Job Scout searches via JSearch (RapidAPI) with automatic fallback to Adzuna for non-English markets.

**Cities:** Amsterdam, Auckland, Bangalore, Barcelona, Berlin, Birmingham, Boston, Brisbane, Cape Town, Chicago, Delhi, Dublin, Edinburgh, Florence, Hamburg, Johannesburg, London, Los Angeles, Lyon, Madrid, Manchester, Marseille, Melbourne, Milan, Montreal, Moscow, Mumbai, Munich, New York, Paris, Rome, Rotterdam, San Francisco, São Paulo, Seattle, Singapore, Sydney, Toronto, Valencia, Vancouver, Warsaw, Wellington

**Countries:** Australia, Brazil, Canada, France, Germany, India, Ireland, Italy, Netherlands, New Zealand, Poland, Russia, South Africa, Spain, United Kingdom, United States

## Tech stack

- **Frontend:** Streamlit
- **AI:** Anthropic Claude (Haiku for scoring/parsing, configurable)
- **Job data:** JSearch API (RapidAPI) + Adzuna fallback
- **Charts:** Plotly
