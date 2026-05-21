import requests
import os
from dotenv import load_dotenv

load_dotenv()

def _get_secret(key):
    try:
        import streamlit as st
        return st.secrets[key]
    except Exception:
        return os.getenv(key)

COUNTRY_CODE_MAP = {
    "united kingdom": "gb", "uk": "gb", "england": "gb", "london": "gb",
    "manchester": "gb", "birmingham": "gb", "edinburgh": "gb",
    "united states": "us", "usa": "us", "new york": "us", "san francisco": "us",
    "chicago": "us", "los angeles": "us", "boston": "us", "seattle": "us",
    "australia": "au", "sydney": "au", "melbourne": "au", "brisbane": "au",
    "canada": "ca", "toronto": "ca", "vancouver": "ca", "montreal": "ca",
    "spain": "es", "madrid": "es", "barcelona": "es", "valencia": "es",
    "germany": "de", "berlin": "de", "munich": "de", "hamburg": "de",
    "france": "fr", "paris": "fr", "lyon": "fr", "marseille": "fr",
    "netherlands": "nl", "amsterdam": "nl", "rotterdam": "nl",
    "italy": "it", "rome": "it", "milan": "it", "florence": "it",
    "ireland": "ie", "dublin": "ie",
    "new zealand": "nz", "auckland": "nz", "wellington": "nz",
    "india": "in", "mumbai": "in", "bangalore": "in", "delhi": "in",
    "brazil": "br", "sao paulo": "br", "rio de janeiro": "br",
    "poland": "pl", "warsaw": "pl", "krakow": "pl",
    "russia": "ru", "moscow": "ru",
    "singapore": "sg",
    "south africa": "za", "cape town": "za", "johannesburg": "za",
}


def infer_country_code(location: str) -> str:
    """Infer Adzuna country code from a location string."""
    loc_lower = location.strip().lower()
    if loc_lower in COUNTRY_CODE_MAP:
        return COUNTRY_CODE_MAP[loc_lower]
    for key, code in COUNTRY_CODE_MAP.items():
        if key in loc_lower:
            return code
    return "gb"  # default to UK


def search_adzuna(role: str, location: str, num_results: int = 10) -> list:
    """Search Adzuna API. Returns list of job dicts matching job_search.py format."""
    app_id = _get_secret("ADZUNA_APP_ID")
    app_key = _get_secret("ADZUNA_APP_KEY")

    if not app_id or not app_key:
        print("Adzuna credentials not configured (ADZUNA_APP_ID / ADZUNA_APP_KEY missing).")
        return []

    country = infer_country_code(location)
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": num_results,
        "what": role,
        "where": location,
        "content-type": "application/json",
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Adzuna API error: {e}")
        return []

    jobs = []
    for result in data.get("results", []):
        jobs.append({
            "title": result.get("title", ""),
            "company": (result.get("company") or {}).get("display_name", ""),
            "location": (result.get("location") or {}).get("display_name", location),
            "description": result.get("description", ""),
            "url": result.get("redirect_url", ""),
            "source": "Adzuna",
            "date_posted": result.get("created", None),
            "salary_range": _format_salary(result),
        })

    return jobs


def _format_salary(result: dict) -> str | None:
    """Format salary range string from Adzuna result if both bounds present."""
    min_sal = result.get("salary_min")
    max_sal = result.get("salary_max")
    if min_sal and max_sal:
        currency = result.get("salary_currency_code", "")
        symbol = {"GBP": "£", "EUR": "€", "USD": "$", "AUD": "A$", "CAD": "CA$"}.get(currency, currency + " ")
        return f"{symbol}{int(min_sal):,}–{symbol}{int(max_sal):,}"
    if min_sal:
        currency = result.get("salary_currency_code", "")
        symbol = {"GBP": "£", "EUR": "€", "USD": "$", "AUD": "A$", "CAD": "CA$"}.get(currency, currency + " ")
        return f"{symbol}{int(min_sal):,}+"
    return None
