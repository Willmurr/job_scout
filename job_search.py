import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

def _get_secret(key):
    try:
        import streamlit as st
        return st.secrets[key]
    except Exception:
        return os.getenv(key)

CACHE_FILE = "job_cache.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def search_jobs(role, location, num_results=10):
    cache = load_cache()
    cache_key = f"{role}_{location}_{num_results}"

    if cache_key in cache:
        print("Loaded from cache.")
        return cache[cache_key]

    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "x-rapidapi-host": "jsearch.p.rapidapi.com",
        "x-rapidapi-key": _get_secret("RAPIDAPI_KEY")
    }
    params = {
        "query": f"{role} in {location}",
        "page": "1",
        "num_pages": "1",
        "date_posted": "all"
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    jobs = []
    for result in data.get("data", []):
        jobs.append({
            "title": result.get("job_title"),
            "company": result.get("employer_name"),
            "location": result.get("job_city") or result.get("job_country"),
            "description": result.get("job_description"),
            "url": result.get("job_apply_link"),
            "source": result.get("job_publisher"),
            "date_posted": result.get("job_posted_at_datetime_utc"),
        })

    if not jobs:
        print(f"WARNING: JSearch returned 0 results for '{role}' in '{location}'. Trying Adzuna fallback...")
        try:
            from adzuna_search import search_adzuna
            jobs = search_adzuna(role, location, num_results)
            if jobs:
                print(f"Adzuna returned {len(jobs)} results.")
            else:
                print("Adzuna also returned 0 results.")
                print("Try: London, New York, Sydney, Toronto, Dublin, Madrid, Barcelona, Paris, Berlin.")
        except Exception as e:
            print(f"Adzuna fallback failed: {e}")

    if jobs:
        cache[cache_key] = jobs
        save_cache(cache)

    return jobs

if __name__ == "__main__":
    jobs = search_jobs("credit analyst", "London")
    for job in jobs[:3]:
        print(f"\n{job['title']} at {job['company']}")
        print(f"Location: {job['location']}")
        print(f"Source: {job['source']}")
        print(f"URL: {job['url']}")