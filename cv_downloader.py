import argparse
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import anthropic
import pandas as pd

from cv_parser import parse_cv_text

DATASET_SLUG = "snehaanbhawal/resume-dataset"
DATASET_CSV_SUBPATH = "Resume/Resume.csv"

# Each entry produces a meaningfully different CV style so the matcher sees varied inputs.
STYLE_VARIATIONS = [
    "metrics-driven: quantify every achievement with numbers, percentages, and monetary values; use tight bullet points; minimal prose",
    "narrative: write experience descriptions as full sentences and short paragraphs rather than bullets; warm and personal summary",
    "technical specialist: lead with a dense skills section grouped by domain; use precise industry terminology throughout; terse summary",
    "senior executive: board-level language; strategic focus; brief high-impact bullets; omit junior-level detail",
    "early-career graduate: education section is prominent; 1-3 years experience; emphasise internships and academic projects; enthusiastic tone",
    "career-changer: transitioning from a different background; explicitly frames transferable skills; acknowledges the pivot in the summary",
    "international candidate: experience spans multiple countries; multilingual; summary highlights cross-cultural adaptability",
    "achievement-oriented: every bullet starts with a strong past-tense action verb and ends with a measurable outcome; no responsibility-only statements",
]


def generate_synthetic_cv(category: str, style_idx: int) -> dict:
    style_hint = STYLE_VARIATIONS[style_idx % len(STYLE_VARIATIONS)]
    prompt = (
        f"Generate a realistic fictional CV for a professional in the {category} industry.\n\n"
        f"Style requirements: {style_hint}\n\n"
        "Return the CV as a JSON object with exactly these fields:\n"
        "- name: Full name (fictional)\n"
        "- email: Email address (fictional)\n"
        "- location: Current city/country\n"
        "- summary: Professional summary\n"
        "- skills: List of technical and soft skills\n"
        "- experience: List of roles, each with company, title, duration, and key_responsibilities (list)\n"
        "- education: List, each with institution, degree, and year\n"
        "- languages: List, each with language and proficiency\n"
        "- target_roles: List of roles this person is targeting\n"
        "- target_industries: List of industries they are suited for\n\n"
        "Make it realistic, internally consistent, and varied in presentation. "
        "Return ONLY valid JSON, no additional text."
    )
    print("Calling Claude API...")
    message = anthropic.Anthropic().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    print("Response received.")
    response_text = message.content[0].text.strip()
    start = response_text.find("{")
    end = response_text.rfind("}") + 1
    return json.loads(response_text[start:end])


def download_dataset(download_dir: str) -> str:
    csv_path = os.path.join(download_dir, DATASET_CSV_SUBPATH)
    if os.path.exists(csv_path):
        print(f"[cv_downloader] Dataset already present: {csv_path}")
        return csv_path

    print(f"[cv_downloader] Downloading dataset from Kaggle...")
    try:
        subprocess.run(
            ["kaggle", "datasets", "download", DATASET_SLUG, "--unzip", "-p", download_dir],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            "Kaggle download failed. Make sure kaggle is installed and credentials are set.\n"
            "Place kaggle.json at C:\\Users\\<you>\\.kaggle\\kaggle.json  OR  set "
            "KAGGLE_USERNAME and KAGGLE_KEY in your .env file.\n"
            f"Original error: {e}"
        ) from e

    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"Download succeeded but expected CSV not found at: {csv_path}"
        )
    print(f"[cv_downloader] Download complete: {csv_path}")
    return csv_path


def load_dataset(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, encoding="utf-8", on_bad_lines="skip")
    df["Category"] = df["Category"].str.strip()
    return df


def get_categories(df: pd.DataFrame, filter_list: list | None) -> list:
    available = sorted(df["Category"].unique().tolist())
    if not filter_list:
        return available
    unknown = [c for c in filter_list if c not in available]
    if unknown:
        raise ValueError(
            f"Unknown categories: {unknown}\nAvailable: {available}"
        )
    return filter_list


def is_already_parsed(output_path: str) -> bool:
    if not os.path.exists(output_path):
        return False
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return bool(data)
    except (json.JSONDecodeError, OSError):
        return False


def load_manifest(manifest_path: str) -> dict:
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"categories": {}, "total_parsed": 0}


def save_manifest(manifest_path: str, manifest: dict) -> None:
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    manifest["total_parsed"] = sum(
        c.get("count", 0) for c in manifest["categories"].values()
    )
    manifest["dataset"] = DATASET_SLUG
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def process_category(
    df: pd.DataFrame,
    category: str,
    n: int,
    output_dir: str,
    manifest: dict,
    rate_limit_seconds: float = 1.0,
) -> tuple:
    category_dir = os.path.join(output_dir, category.replace(" ", "_"))
    os.makedirs(category_dir, exist_ok=True)

    rows = df[df["Category"] == category].head(n)
    parsed_count = 0
    skipped_count = 0
    error_count = 0
    files = []

    for idx, (_, row) in enumerate(rows.iterrows()):
        rel_path = f"{category.replace(' ', '_')}/{idx}.json"
        output_path = os.path.join(output_dir, rel_path)

        if is_already_parsed(output_path):
            print(f"  [SKIP]  {rel_path}")
            skipped_count += 1
            files.append(rel_path)
            continue

        raw_text = str(row.get("Resume_str", "")).strip()
        if len(raw_text) < 100:
            print(f"  [SKIP]  {rel_path} (resume text too short)")
            skipped_count += 1
            continue

        try:
            profile = parse_cv_text(raw_text)
            record = {
                "meta": {
                    "category": category,
                    "dataset_id": int(row.get("ID", idx)),
                    "source": DATASET_SLUG,
                },
                "profile": profile,
            }
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2, ensure_ascii=False)
            print(f"  [PARSE] {rel_path} ... OK")
            parsed_count += 1
            files.append(rel_path)
            time.sleep(rate_limit_seconds)

        except json.JSONDecodeError as e:
            print(f"  [ERROR] {rel_path}: Claude returned invalid JSON — {e}")
            error_count += 1
        except anthropic.RateLimitError:
            print(f"  [ERROR] {rel_path}: Rate limited. Sleeping 60s...")
            time.sleep(60)
            error_count += 1
        except anthropic.APIStatusError as e:
            print(f"  [ERROR] {rel_path}: API error {e.status_code} — {e.message}")
            error_count += 1
        except Exception as e:
            print(f"  [ERROR] {rel_path}: Unexpected — {e}")
            error_count += 1

    manifest["categories"][category] = {"count": len(files), "files": files}
    return parsed_count, skipped_count, error_count


def generate_synthetic_category(
    category: str,
    n: int,
    output_dir: str,
    manifest: dict,
    rate_limit: float = 1.0,
    style_offset: int = 0,
) -> tuple:
    category_dir = os.path.join(output_dir, category.replace(" ", "_"))
    os.makedirs(category_dir, exist_ok=True)

    parsed_count = skipped_count = error_count = 0
    files = list(manifest.get("categories", {}).get(category, {}).get("files", []))
    existing = len(files)

    for idx in range(n):
        rel_path = f"{category.replace(' ', '_')}/{idx}.json"
        output_path = os.path.join(output_dir, rel_path)

        if is_already_parsed(output_path):
            print(f"  [SKIP]  {rel_path}")
            skipped_count += 1
            if rel_path not in files:
                files.append(rel_path)
            continue

        style_idx = (style_offset + idx) % len(STYLE_VARIATIONS)
        style_label = STYLE_VARIATIONS[style_idx].split(":")[0]
        print(f"  [GEN]   {rel_path} (style: {style_label}) ...")

        try:
            profile = generate_synthetic_cv(category, style_idx)
            record = {
                "meta": {
                    "category": category,
                    "source": "synthetic",
                    "style": STYLE_VARIATIONS[style_idx],
                },
                "profile": profile,
            }
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2, ensure_ascii=False)
            print(f"         ... OK")
            parsed_count += 1
            files.append(rel_path)
            if idx < n - 1:
                time.sleep(rate_limit)

        except json.JSONDecodeError as e:
            print(f"  [ERROR] {rel_path}: Claude returned invalid JSON — {e}")
            error_count += 1
        except anthropic.RateLimitError:
            print(f"  [ERROR] {rel_path}: Rate limited. Sleeping 60s...")
            time.sleep(60)
            error_count += 1
        except anthropic.APIStatusError as e:
            print(f"  [ERROR] {rel_path}: API error {e.status_code} — {e.message}")
            error_count += 1
        except Exception as e:
            print(f"  [ERROR] {rel_path}: Unexpected — {e}")
            error_count += 1

    manifest.setdefault("categories", {})[category] = {"count": len(files), "files": files}
    return parsed_count, skipped_count, error_count


def main(
    n_per_category: int = 5,
    categories: list | None = None,
    output_dir: str = "sample_cvs",
    download_dir: str = "kaggle_data",
    rate_limit: float = 1.0,
    synthetic: bool = False,
) -> None:
    os.makedirs(output_dir, exist_ok=True)
    manifest_path = os.path.join(output_dir, "manifest.json")
    manifest = load_manifest(manifest_path)
    manifest["n_per_category"] = n_per_category

    total_parsed = total_skipped = total_errors = 0

    if synthetic:
        default_categories = [
            "Finance", "Banking", "Information Technology", "Healthcare",
            "Engineering", "HR", "Sales", "Marketing", "Consulting", "Education",
        ]
        selected_categories = categories if categories else default_categories
        print(f"[cv_downloader] Synthetic mode — generating {n_per_category} CV(s) × {len(selected_categories)} categories\n")

        for i, category in enumerate(selected_categories, 1):
            print(f"--- Generating: {category} ({i}/{len(selected_categories)}) ---")
            # Offset styles so different categories don't repeat the same style at idx 0
            style_offset = (i - 1) * 3
            parsed, skipped, errors = generate_synthetic_category(
                category, n_per_category, output_dir, manifest, rate_limit, style_offset
            )
            total_parsed += parsed
            total_skipped += skipped
            total_errors += errors
            print(f"  Category done: {parsed} generated, {skipped} skipped, {errors} errors")
            save_manifest(manifest_path, manifest)
            print()
    else:
        print("[cv_downloader] Checking Kaggle credentials...")
        csv_path = download_dataset(download_dir)
        print("[cv_downloader] Loading dataset...")
        df = load_dataset(csv_path)
        print(f"[cv_downloader] Loaded {len(df)} CVs")
        selected_categories = get_categories(df, categories)
        print(f"[cv_downloader] Categories to process: {len(selected_categories)}")
        print(f"[cv_downloader] n_per_category: {n_per_category}, rate_limit: {rate_limit}s\n")

        for i, category in enumerate(selected_categories, 1):
            print(f"--- Processing: {category} ({i}/{len(selected_categories)}) ---")
            parsed, skipped, errors = process_category(
                df, category, n_per_category, output_dir, manifest, rate_limit
            )
            total_parsed += parsed
            total_skipped += skipped
            total_errors += errors
            print(f"  Category done: {parsed} parsed, {skipped} skipped, {errors} errors")
            save_manifest(manifest_path, manifest)
            print()

    print(f"[cv_downloader] Complete: {total_parsed} generated, {total_skipped} skipped, {total_errors} errors")
    print(f"[cv_downloader] Manifest: {manifest_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download and parse sample CVs from the Kaggle Resume Dataset."
    )
    parser.add_argument(
        "--n-per-category", type=int, default=5,
        help="Number of CVs to parse per industry category (default: 5)"
    )
    parser.add_argument(
        "--categories", nargs="*", default=None,
        help="Limit to specific categories (e.g. Finance Banking HR). Omit for all."
    )
    parser.add_argument(
        "--output-dir", type=str, default="sample_cvs",
        help="Directory to write parsed JSON files (default: sample_cvs)"
    )
    parser.add_argument(
        "--download-dir", type=str, default="kaggle_data",
        help="Directory to store the raw Kaggle download (default: kaggle_data)"
    )
    parser.add_argument(
        "--rate-limit", type=float, default=1.0,
        help="Seconds to sleep between Claude API calls (default: 1.0)"
    )
    parser.add_argument(
        "--synthetic", action="store_true",
        help="Generate fictional CVs with Claude instead of downloading from Kaggle"
    )

    args = parser.parse_args()
    main(
        n_per_category=args.n_per_category,
        categories=args.categories,
        output_dir=args.output_dir,
        download_dir=args.download_dir,
        rate_limit=args.rate_limit,
        synthetic=args.synthetic,
    )
