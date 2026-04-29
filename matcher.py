import anthropic
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def score_job(profile, job):
    prompt = f"""You are an expert recruiter. Score how well this candidate matches the job listing.

CANDIDATE PROFILE:
{json.dumps(profile, indent=2)}

JOB LISTING:
Title: {job['title']}
Company: {job['company']}
Location: {job['location']}
Description: {job['description']}

Evaluate the match across four dimensions and return a JSON object with exactly this structure:

{{
  "overall_score": <0-100>,
  "breakdown": {{
    "role_alignment": <0-25>,
    "experience_match": <0-25>,
    "skills_overlap": <0-25>,
    "location_fit": <0-25>
  }},
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "skill_gaps": ["<gap 1>", "<gap 2>"],
  "summary": "<one paragraph explaining the match>"
}}

Scoring guide:
- role_alignment: Does the job match the candidate's target roles and career direction?
- experience_match: Is the seniority and experience level appropriate?
- skills_overlap: How many required skills does the candidate have?
- location_fit: Is the location suitable given the candidate's profile?

Return ONLY valid JSON, no additional text.
"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]

    return json.loads(response_text.strip())

def rank_jobs(profile, jobs):
    print(f"Scoring {len(jobs)} jobs...\n")
    scored_jobs = []

    for job in jobs:
        try:
            score = score_job(profile, job)
            scored_jobs.append({
                "job": job,
                "score": score
            })
            print(f"✓ Scored: {job['title']} at {job['company']} — {score['overall_score']}/100")
        except Exception as e:
            print(f"✗ Failed to score {job['title']}: {e}")

    scored_jobs.sort(key=lambda x: x["score"]["overall_score"], reverse=True)
    return scored_jobs

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