# Job Scout — Implementation Submission

**Author:** William Murray  
**Live App:** https://jobscout-fvs5f92lrdvtryjsu95zqv.streamlit.app  
**GitHub Repository:** https://github.com/Willmurr/job_scout

---

## What Job Scout Does

Job Scout is an AI-powered job matching tool. A user uploads their CV (PDF or Word), selects a location and either a specific role or a "find best fit" mode, and the app returns real job listings scored 0–100 against their profile. For every match it shows a radar chart breakdown, skill gap tips with actionable steps to close each gap, a one-click cover letter generator, and a CV improvement panel. Results can be exported to CSV and applications can be tracked per session.

---

## Architecture

```
app.py              ← Streamlit UI (sidebar search, results rendering)
cv_parser.py        ← Extracts structured profile from uploaded PDF/DOCX
job_search.py       ← JSearch API (primary) with Adzuna fallback
adzuna_search.py    ← Adzuna API client (European job coverage)
matcher.py          ← Parallel Claude scoring, role suggestions, CV tips
cover_letter.py     ← Cover letter generation
requirements.txt    ← Python dependencies
```

---

## AI Prompts

### 1. CV Parsing — `cv_parser.py:parse_cv_text()`

Extracts a structured profile from raw CV text. Returns a JSON object with `name`, `email`, `location`, `summary`, `skills`, `experience`, `education`, `languages`, `target_roles`, `target_industries`.

```
You are a CV parser. Extract the following information and return it as a JSON object:
- name, email, location, summary, skills, experience, education, languages, target_roles, target_industries
Return ONLY valid JSON, no additional text.
CV: {raw_text}
```

Model: `claude-haiku-4-5-20251001` | Max tokens: 2048

---

### 2. Job Scoring — `matcher.py:score_job()`

Assesses candidate-job fit across 4 dimensions (0–25 each). Produces `overall_score`, `breakdown`, `strengths`, `skill_gaps`, `gap_actions`, and a narrative `summary`.

```
You are a senior recruiter assessing candidate-job fit. Be precise and discriminating.

CANDIDATE PROFILE: {profile_json}

JOB LISTING:
Title: {job.title}
Company: {job.company}
Location: {job.location}
Description: {job.description[:1500]}

Score across four dimensions (0-25 each). overall_score MUST equal the exact sum.

SCORING RUBRIC:
role_alignment (0-25):     Job matches candidate's background, industry, and target roles
experience_match (0-25):   Seniority and years of experience appropriate for the role
skills_overlap (0-25):     Proportion of job's required skills the candidate has
location_fit (0-25):       Job location compatible with candidate's location/preferences

gap_actions: one concrete, specific action to close each skill gap

Return ONLY this JSON:
{
  "overall_score": <sum>,
  "breakdown": { "role_alignment", "experience_match", "skills_overlap", "location_fit" },
  "strengths": ["...", "...", "..."],
  "skill_gaps": ["...", "..."],
  "gap_actions": ["...", "..."],
  "summary": "..."
}
```

Model: `claude-haiku-4-5-20251001` | Max tokens: 1024 | Parallelism: `ThreadPoolExecutor(max_workers=10)`

---

### 3. Role Suggestions — `matcher.py:suggest_target_roles()`

Suggests 4 searchable job titles based on the candidate's CV profile.

```
You are a career advisor. Based on this candidate's profile, suggest exactly 4 specific job titles.
Rules:
- Standard, searchable titles (e.g. "Credit Analyst", not "Finance Professional")
- Match candidate's experience level — not too senior or junior
- Include obvious fit, 1-2 adjacent roles, one slightly aspirational role
- Return ONLY a JSON array of 4 strings
```

Model: `claude-haiku-4-5-20251001` | Max tokens: 256

---

### 4. CV Improvements — `matcher.py:suggest_cv_improvements()`

Generates 3 specific, actionable CV improvements based on the profile and top 3 job matches.

```
You are a career coach. Given a candidate's profile and their top 3 job matches, suggest exactly 3 specific, actionable CV improvements that would increase their chances of getting interviews.

CANDIDATE PROFILE: {profile_json}
TOP 3 MATCHED JOBS: {job_title} at {company}: {description[:400]}

Return ONLY a JSON array of exactly 3 strings.
```

Model: `claude-haiku-4-5-20251001` | Max tokens: 512

---

### 5. Cover Letter Generation — `cover_letter.py:generate_cover_letter()`

Writes a 3-paragraph cover letter tailored to the specific job.

```
You are an expert career coach. Write a professional, tailored cover letter.

CANDIDATE PROFILE: {profile_json}
JOB LISTING: Title / Company / Location / Description
KEY STRENGTHS: {strengths}

Instructions:
- Paragraph 1: Opening — why this role and company, referencing specific details
- Paragraph 2: Core value — 2-3 specific achievements matching role requirements
- Paragraph 3: Closing — enthusiasm and proposed next steps
- Professional but direct tone
- Do NOT use generic phrases like "I am writing to apply"
- Under 350 words
```

Model: `claude-haiku-4-5-20251001` | Max tokens: 1024

---

## APIs and Integrations

| Service | Purpose | Free tier |
|---------|---------|-----------|
| Anthropic Claude Haiku | CV parsing, scoring, suggestions, cover letters | Pay-per-token |
| JSearch via RapidAPI | Primary job source — English-speaking markets | 200 requests/month free |
| Adzuna | Fallback for European markets (ES, FR, DE, NL, IT, AU, CA) | Free developer tier |

### Job Search Flow (`job_search.py`)

1. Build cache key: `{role.lower()}_{location.lower()}_{num_results}`
2. Return cached result if present
3. Query JSearch API (`jsearch.p.rapidapi.com/search`)
4. If JSearch returns 0 results, fall back to Adzuna (`search_adzuna()`)
5. Cache non-empty results to `job_cache.json`

### Adzuna Country Routing (`adzuna_search.py`)

`infer_country_code(location)` maps 40+ cities and country names to 2-letter ISO codes. When the location is a country name (e.g. "Spain", "France"), the `where` parameter is omitted from the Adzuna API call — passing a country name as `where` when the endpoint already routes by country code causes 0 results.

---

## Key Technical Decisions

**API client initialization** — All 4 files (`cv_parser.py`, `matcher.py`, `adzuna_search.py`, `cover_letter.py`) use a `_get_secret()` helper that tries `st.secrets` first, then falls back to `os.getenv()`. Clients are instantiated inside functions, not at module level. This is required for Streamlit Community Cloud, where secrets are injected after import time.

**Parallel scoring** — `rank_jobs()` uses `ThreadPoolExecutor(max_workers=10)` to score all jobs simultaneously. A 10-job search completes in ~3s instead of ~20s.

**Best fit mode** — `suggest_target_roles()` returns 4 titles; the app searches each, deduplicates by URL, then ranks the combined list.

**Cache key normalisation** — Keys use `role.lower()_location.lower()_num_results` to prevent case-mismatch misses.

---

## Running Locally

```bash
git clone https://github.com/Willmurr/job_scout.git
cd job_scout
pip install -r requirements.txt
# Create .env with ANTHROPIC_API_KEY, RAPIDAPI_KEY, ADZUNA_APP_ID, ADZUNA_APP_KEY
streamlit run app.py
```

Or use `Start Job Scout.bat` (Windows) to open the browser and start the server in one click.

---

## Deployment

Hosted on Streamlit Community Cloud. API keys are stored in the app's Secrets panel (not committed to Git). The `.env` file and `job_cache.json` are both gitignored.

Config file: `.streamlit/config.toml` (theme, server settings if needed — defaults used here).

---

## File Index

| File | Purpose |
|------|---------|
| `app.py` | Streamlit UI — sidebar, search flow, results, export |
| `cv_parser.py` | CV text extraction (PDF/DOCX) + Claude parsing |
| `job_search.py` | JSearch API + caching + Adzuna fallback dispatch |
| `adzuna_search.py` | Adzuna API client + country code routing |
| `matcher.py` | Parallel scoring, role suggestions, CV improvement tips |
| `cover_letter.py` | Cover letter generation |
| `requirements.txt` | Python dependencies |
| `README.md` | Setup and deployment guide |
| `Start Job Scout.bat` | Windows one-click launcher |
| `.gitignore` | Excludes `.env`, caches, venv |
