import argparse
import json
import os
import time

import pandas as pd

from job_search import search_jobs
from matcher import score_job

CATEGORY_QUERIES = {
    "Finance": "Financial Analyst",
    "Banking": "Investment Banking Analyst",
    "Information Technology": "Head of Engineering",
    "Healthcare": "Healthcare Manager",
    "Engineering": "Mechanical Engineer",
    "HR": "HR Manager",
    "Sales": "Sales Manager",
    "Marketing": "Marketing Manager",
    "Consulting": "Management Consultant",
    "Education": "Teacher",
}

RESULTS_DIR = "test_results"
CACHE_PATH = os.path.join(RESULTS_DIR, "scores_cache.json")
MATRIX_PATH = os.path.join(RESULTS_DIR, "score_matrix.csv")


def load_profiles(sample_cvs_dir: str, cv_categories: list | None = None) -> list:
    profiles = []
    for category in sorted(os.listdir(sample_cvs_dir)):
        cat_dir = os.path.join(sample_cvs_dir, category)
        if not os.path.isdir(cat_dir):
            continue
        if cv_categories and category.replace("_", " ") not in cv_categories and category not in cv_categories:
            continue
        for fname in sorted(os.listdir(cat_dir)):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(cat_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            profile = data.get("profile", data)
            idx = fname.replace(".json", "")
            name = profile.get("name", "Unknown")
            label = f"{category}_{idx}_{name}"
            profiles.append((label, category, profile))
    return profiles


def fetch_jobs(category_map: dict, location: str, n: int) -> dict:
    jobs_by_category = {}
    for category, query in category_map.items():
        print(f"  Fetching jobs: {query} in {location} ...")
        jobs = search_jobs(query, location, num_results=n)
        jobs_by_category[category] = jobs
        print(f"  Got {len(jobs)} jobs for {category}")
    return jobs_by_category


def score_key(label: str, job: dict) -> str:
    return f"{label}__{job['title']}__{job['company']}"


def load_score_cache(path: str) -> dict:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_score_cache(cache: dict, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


def run_matrix(
    profiles: list,
    jobs_by_category: dict,
    cache: dict,
    use_cache: bool = True,
) -> dict:
    all_jobs = []
    for jobs in jobs_by_category.values():
        all_jobs.extend(jobs)

    total_pairs = len(profiles) * len(all_jobs)
    scored = 0
    skipped = 0
    errors = 0

    results = {}

    for label, cv_category, profile in profiles:
        results[label] = {}
        for job in all_jobs:
            key = score_key(label, job)
            col = f"{job['title']} @ {job['company']}"

            if use_cache and key in cache:
                results[label][col] = cache[key]["overall_score"]
                skipped += 1
                continue

            try:
                score = score_job(profile, job)
                cache[key] = score
                results[label][col] = score["overall_score"]
                scored += 1
                # Save cache every 10 new scores to protect against interruptions
                if scored % 10 == 0:
                    save_score_cache(cache, CACHE_PATH)
                    print(f"  Progress: {scored + skipped}/{total_pairs} pairs scored ({skipped} from cache)")
                time.sleep(0.3)
            except Exception as e:
                print(f"  [ERROR] {label} × {col}: {e}")
                results[label][col] = None
                errors += 1

    save_score_cache(cache, CACHE_PATH)
    print(f"\n  Scoring complete: {scored} new, {skipped} from cache, {errors} errors")
    return results


def build_dataframe(results: dict) -> pd.DataFrame:
    df = pd.DataFrame.from_dict(results, orient="index")
    df.index.name = "cv_label"
    return df


def save_csv(df: pd.DataFrame, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path)
    print(f"\n  CSV saved: {path}")


def print_summary(df: pd.DataFrame, profiles: list, jobs_by_category: dict) -> None:
    job_to_category = {}
    for category, jobs in jobs_by_category.items():
        for job in jobs:
            col = f"{job['title']} @ {job['company']}"
            job_to_category[col] = category

    print("\n" + "=" * 70)
    print("TOP MATCH PER CV")
    print("=" * 70)

    correct = 0
    total = 0

    for label, cv_category, _ in profiles:
        if label not in df.index:
            continue
        row = df.loc[label].dropna()
        if row.empty:
            continue
        top_job = row.idxmax()
        top_score = int(row.max())
        matched_category = job_to_category.get(top_job, "?")
        is_correct = matched_category == cv_category
        tag = "[CORRECT]" if is_correct else f"[WRONG — expected {cv_category}]"
        if is_correct:
            correct += 1
        total += 1
        print(f"  {label:<45} -> {top_job:<45} score={top_score:>3}  {tag}")

    print("=" * 70)
    if total > 0:
        pct = round(correct / total * 100)
        print(f"  Validation: {correct}/{total} CVs matched their own category ({pct}%)")
    print("=" * 70 + "\n")


def main(
    location: str = "London",
    jobs_per_category: int = 5,
    use_cache: bool = True,
    sample_cvs_dir: str = "sample_cvs",
    cv_categories: list | None = None,
) -> None:
    print("[test_matcher] Loading CV profiles...")
    profiles = load_profiles(sample_cvs_dir, cv_categories)
    print(f"[test_matcher] Loaded {len(profiles)} profiles\n")

    print("[test_matcher] Fetching jobs...")
    jobs_by_category = fetch_jobs(CATEGORY_QUERIES, location, jobs_per_category)
    total_jobs = sum(len(j) for j in jobs_by_category.values())
    print(f"\n[test_matcher] {total_jobs} jobs fetched across {len(jobs_by_category)} categories")
    print(f"[test_matcher] Scoring {len(profiles)} CVs × {total_jobs} jobs = {len(profiles) * total_jobs} pairs\n")

    cache = load_score_cache(CACHE_PATH)  # always load to preserve existing entries
    print("[test_matcher] Running scoring matrix...")
    results = run_matrix(profiles, jobs_by_category, cache, use_cache)

    df = build_dataframe(results)
    save_csv(df, MATRIX_PATH)
    print_summary(df, profiles, jobs_by_category)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Score all sample CVs against real job listings and produce a matrix."
    )
    parser.add_argument("--location", type=str, default="London",
                        help="Job search location (default: London)")
    parser.add_argument("--jobs-per-category", type=int, default=5,
                        help="Number of jobs to fetch per category (default: 5)")
    parser.add_argument("--no-cache", action="store_true",
                        help="Ignore cached scores and re-score everything")
    parser.add_argument("--sample-cvs-dir", type=str, default="sample_cvs",
                        help="Directory containing synthetic CV JSON files")
    parser.add_argument("--cv-categories", nargs="*", default=None,
                        help="Only test CVs from these categories (e.g. Finance Banking)")

    args = parser.parse_args()
    main(
        location=args.location,
        jobs_per_category=args.jobs_per_category,
        use_cache=not args.no_cache,
        sample_cvs_dir=args.sample_cvs_dir,
        cv_categories=args.cv_categories,
    )
