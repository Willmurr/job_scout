import pdfplumber
from docx import Document
import anthropic
import json
import os
from dotenv import load_dotenv

load_dotenv()

def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extract_text_from_docx(file_path):
    doc = Document(file_path)
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    return text

def extract_cv_text(file_path):
    if file_path.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif file_path.endswith(".docx"):
        return extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file format. Please use PDF or DOCX.")

def parse_cv_text(raw_text: str) -> dict:
    prompt = (
        "You are a CV parser. Extract the following information and return it as a JSON object:\n\n"
        "- name: Full name\n"
        "- email: Email address\n"
        "- location: Current city/country\n"
        "- summary: Professional summary (2-3 sentences)\n"
        "- skills: List of technical and soft skills\n"
        "- experience: List of roles with company, title, duration, and key responsibilities\n"
        "- education: Institution, degree, and year\n"
        "- languages: Languages and proficiency levels\n"
        "- target_roles: What roles is this person targeting?\n"
        "- target_industries: What industries are they suited for?\n\n"
        "Return ONLY valid JSON, no additional text.\n\n"
        "CV:\n" + raw_text
    )

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    import time
    for attempt in range(4):
        try:
            print("Calling Claude API...")
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )
            print("Response received.")
            response_text = message.content[0].text.strip()
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            return json.loads(response_text[start:end])
        except anthropic.APIStatusError as e:
            if e.status_code == 529 and attempt < 3:
                wait = 10 * (attempt + 1)
                print(f"API overloaded, retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise


def parse_cv(file_path):
    cache_file = "cv_cache.json"
    if os.path.exists(cache_file):
        print("Loaded CV from cache.")
        with open(cache_file, "r") as f:
            return json.load(f)

    raw_text = extract_cv_text(file_path)
    profile = parse_cv_text(raw_text)

    with open(cache_file, "w") as f:
        json.dump(profile, f, indent=2)

    return profile

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        profile = parse_cv(sys.argv[1])
        print(json.dumps(profile, indent=2))
    else:
        print("Usage: python cv_parser.py your_cv.pdf")