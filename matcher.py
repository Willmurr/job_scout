import anthropic
import concurrent.futures
import json
import os
from dotenv import load_dotenv

load_dotenv()

def score_job(profile, job):
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    prompt = f"""You are a senior recruiter assessing candidate-job fit. Be precise and discriminating — most candidates are not a strong fit for any given role.

CANDIDATE PROFILE:
{json.dumps(profile, indent=2)}

JOB LISTING:
Title: {job['title']}
Company: {job['company']}
Location: {job['location']}
Description: {job['description'][:1500]}

Score the match across four dimensions (0-25 each). The overall_score MUST equal the exact sum of all four dimension scores.

SCORING RUBRIC:

role_alignment (0-25): Does this specific job match the candidate's background, industry, and target roles?
  0-5:   Completely different field or function (e.g. nurse applying for software engineering role)
  6-12:  Adjacent field — some transferable skills but significant industry or function mismatch
  13-18: Related role — meaningful overlap in function or industry, candidate could plausibly apply
  19-22: Strong match — job aligns directly with candidate's target roles and industry background
  23-25: Exceptional match — job is exactly what the candidate is targeting with deep relevant experience

experience_match (0-25): Is the seniority and years of experience appropriate for this role?
  0-5:   Severe over- or under-qualification (5+ year gap in seniority)
  6-12:  Noticeable seniority mismatch — candidate is clearly too junior or too senior
  13-18: Broadly appropriate level with some gaps in specific experience
  19-22: Good fit — experience level and tenure align well with role requirements
  23-25: Perfect seniority fit — years of experience and level match the role exactly

skills_overlap (0-25): What proportion of the job's required skills does the candidate demonstrably have?
  0-5:   Fewer than 20% of required skills present
  6-12:  20-40% of required skills present
  13-18: 40-60% of required skills present
  19-22: 60-80% of required skills present
  23-25: 80%+ of required skills present

location_fit (0-25): Is the job location compatible with the candidate's current location and preferences?
  0-5:   Different continent with no remote option indicated
  6-12:  Different country, relocation would be required
  13-18: Same country but different city, commuting or relocation needed
  19-22: Same city or region, or role is hybrid/remote-friendly
  23-25: Exact location match or fully remote role

gap_actions: one concrete, specific action the candidate can take to close each skill gap (e.g. course, certification, project, portfolio piece)

Return ONLY this JSON — overall_score must equal role_alignment + experience_match + skills_overlap + location_fit:
{{
  "overall_score": <sum of four dimensions>,
  "breakdown": {{
    "role_alignment": <0-25>,
    "experience_match": <0-25>,
    "skills_overlap": <0-25>,
    "location_fit": <0-25>
  }},
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "skill_gaps": ["<gap 1>", "<gap 2>"],
  "gap_actions": ["<one concrete action to address gap 1, e.g. 'Complete CFA Level 1'>", "<action for gap 2>"],
  "summary": "<one paragraph explaining the match>"
}}

Return ONLY valid JSON, no additional text.
"""

    import time
    for attempt in range(4):
        try:
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            break
        except anthropic.APIStatusError as e:
            if e.status_code == 529 and attempt < 3:
                wait = 10 * (attempt + 1)
                print(f"API overloaded, retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise

    response_text = message.content[0].text.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]

    return json.loads(response_text.strip())

def rank_jobs(profile, jobs):
    print(f"Scoring {len(jobs)} jobs in parallel...\n")

    def score_one(job):
        try:
            score = score_job(profile, job)
            print(f"[OK] Scored: {job['title']} at {job['company']} - {score['overall_score']}/100")
            return {"job": job, "score": score}
        except Exception as e:
            print(f"[FAIL] Failed to score {job['title']}: {e}")
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = list(executor.map(score_one, jobs))

    scored_jobs = [r for r in futures if r is not None]
    scored_jobs.sort(key=lambda x: x["score"]["overall_score"], reverse=True)
    return scored_jobs

def suggest_target_roles(profile) -> list:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    prompt = f"""You are a career advisor. Based on this candidate's profile, suggest exactly 4 specific job titles they should search for.

CANDIDATE PROFILE:
{json.dumps(profile, indent=2)}

Rules:
- Each title must be a standard, searchable job title (e.g. "Credit Analyst", not "Finance Professional")
- Match the candidate's experience level — do not suggest roles far above or below their seniority
- Include their most obvious fit, 1-2 adjacent roles, and one slightly aspirational role
- Return ONLY a JSON array of 4 strings

Example: ["Credit Analyst", "Financial Analyst", "Risk Manager", "Commercial Banker"]

Return ONLY valid JSON array, no other text."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}]
    )
    response_text = message.content[0].text.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
    return json.loads(response_text.strip())


def suggest_cv_improvements(profile, results):
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    top_jobs = [r["job"] for r in results[:3]]
    jobs_text = "\n".join([
        f"- {j.get('title')} at {j.get('company')}: {str(j.get('description',''))[:400]}"
        for j in top_jobs
    ])

    prompt = f"""You are a career coach. Given a candidate's profile and their top 3 job matches, suggest exactly 3 specific, actionable CV improvements that would increase their chances of getting interviews for these roles.

CANDIDATE PROFILE:
{json.dumps(profile, indent=2)}

TOP 3 MATCHED JOBS:
{jobs_text}

Return ONLY a JSON array of exactly 3 strings. Each string is one specific, actionable improvement.
Example: ["Add quantified achievements to each role (e.g. 'Reduced bad debt by 12%')", "Include CFA progress or relevant finance certifications", "Add a skills section listing Excel, Python, SQL, Bloomberg"]

Return ONLY valid JSON array, no other text."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )
    response_text = message.content[0].text.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
    return json.loads(response_text.strip())

if __name__ == "__main__":
    from cv_parser import parse_cv
    from job_search import search_jobs

    print("Parsing CV...")
    profile = parse_cv("William_Murray_CV.pdf")
    print("Searching for jobs...")
    jobs = search_jobs("credit analyst", "London")

    print("Ranking jobs...\n")
    results = rank_jobs(profile, jobs)

    print("\n--- TOP 3 MATCHES ---\n")
    for result in results[:3]:
        job = result["job"]
        score = result["score"]
        print(f"{job['title']} at {job['company']}")
        print(f"Overall Score: {score['overall_score']}/100")
        print(f"Strengths: {', '.join(score['strengths'])}")
        print(f"Skill Gaps: {', '.join(score['skill_gaps'])}")
        print(f"Summary: {score['summary']}")
        print(f"URL: {job['url']}")
        print()
