import anthropic
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def generate_cover_letter(profile, job, score):
    strengths = ", ".join(score.get("strengths", [])[:3])

    prompt = (
        "You are an expert career coach. Write a professional, tailored cover letter for this candidate applying to this job.\n\n"
        "CANDIDATE PROFILE:\n"
        + json.dumps(profile, indent=2)
        + "\n\nJOB LISTING:\n"
        + "Title: " + str(job["title"]) + "\n"
        + "Company: " + str(job["company"]) + "\n"
        + "Location: " + str(job["location"]) + "\n"
        + "Description: " + str(job["description"]) + "\n\n"
        + "KEY STRENGTHS FOR THIS ROLE:\n"
        + strengths + "\n\n"
        + "Instructions:\n"
        + "- Write 3 concise paragraphs\n"
        + "- Paragraph 1: Opening — why this role and company, referencing specific details from the job\n"
        + "- Paragraph 2: Core value — highlight 2-3 specific achievements from the CV that directly match the role requirements\n"
        + "- Paragraph 3: Closing — express enthusiasm and propose next steps\n"
        + "- Use a professional but direct tone\n"
        + "- Reference specific details from both the CV and job description\n"
        + "- Do NOT use generic phrases like 'I am writing to apply' or 'I believe I am the perfect candidate'\n"
        + "- Keep it under 350 words\n\n"
        + "Write the cover letter only, no additional commentary."
    )

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text.strip()

if __name__ == "__main__":
    from cv_parser import parse_cv
    from job_search import search_jobs
    from matcher import rank_jobs

    print("Loading profile and jobs from cache...\n")
    profile = parse_cv("William_Murray_CV.pdf")
    jobs = search_jobs("credit analyst", "London")
    results = rank_jobs(profile, jobs)

    top_match = results[0]
    job = top_match["job"]
    score = top_match["score"]

    print(f"Generating cover letter for: {job['title']} at {job['company']}\n")
    print("-" * 60)
    letter = generate_cover_letter(profile, job, score)
    print(letter)
    print("-" * 60)