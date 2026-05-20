import streamlit as st
import os
import json
import tempfile
import pandas as pd
import io
import plotly.graph_objects as go
from cv_parser import parse_cv
from job_search import search_jobs
from matcher import rank_jobs, suggest_cv_improvements, suggest_target_roles
from cover_letter import generate_cover_letter

st.set_page_config(page_title="Job Scout", page_icon="Target", layout="wide")
st.title("Job Scout")
st.subheader("AI-powered job matching and cover letter generation")

with st.sidebar:
    st.header("Your Search")
    uploaded_file = st.file_uploader("Upload your CV", type=["pdf", "docx"])
    search_mode = st.radio("Search mode", ["Specific role", "Find best fit"], horizontal=True)
    if search_mode == "Specific role":
        role = st.text_input("Target Role", value="credit analyst")
    else:
        role = None
        st.caption("Job Scout will suggest roles based on your CV.")
    CITIES = [
        "Amsterdam", "Auckland", "Bangalore", "Barcelona", "Berlin",
        "Birmingham", "Boston", "Brisbane", "Cape Town", "Chicago",
        "Delhi", "Dublin", "Edinburgh", "Florence", "Hamburg",
        "Johannesburg", "London", "Los Angeles", "Lyon", "Madrid",
        "Manchester", "Marseille", "Melbourne", "Milan", "Montreal",
        "Moscow", "Mumbai", "Munich", "New York", "Paris",
        "Rome", "Rotterdam", "San Francisco", "São Paulo", "Seattle",
        "Singapore", "Sydney", "Toronto", "Valencia", "Vancouver",
        "Warsaw", "Wellington",
    ]
    COUNTRIES = [
        "Australia", "Brazil", "Canada", "France", "Germany",
        "India", "Ireland", "Italy", "Netherlands", "New Zealand",
        "Poland", "Russia", "South Africa", "Spain",
        "United Kingdom", "United States",
    ]
    loc_type = st.radio("Location type", ["City", "Country"], horizontal=True)
    if loc_type == "City":
        location = st.selectbox("City", CITIES, index=CITIES.index("London"))
    else:
        location = st.selectbox("Country", COUNTRIES, index=COUNTRIES.index("United Kingdom"))
    search_button = st.button("Find Matching Jobs", type="primary")

    st.divider()
    st.subheader("Filter & Sort")
    min_score = st.slider("Minimum match score", 0, 100, 0)
    sort_by = st.selectbox("Sort by", ["Score (High→Low)", "Company A–Z"])

if search_button and uploaded_file:
    suffix = "." + uploaded_file.name.split(".")[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    with st.spinner("Parsing your CV..."):
        if os.path.exists("cv_cache.json"):
            os.remove("cv_cache.json")
        profile = parse_cv(tmp_path)
        st.session_state["profile"] = profile

    if search_mode == "Find best fit":
        with st.spinner("Identifying best-fit roles from your CV..."):
            suggested_roles = suggest_target_roles(profile)
            st.session_state["searched_roles"] = suggested_roles

        jobs = []
        seen_urls = set()
        for r in suggested_roles:
            with st.spinner(f"Searching for {r} jobs in {location}..."):
                role_jobs = search_jobs(r, location)
                for j in role_jobs:
                    url = j.get("url") or ""
                    if url not in seen_urls:
                        seen_urls.add(url)
                        jobs.append(j)
        st.session_state["jobs"] = jobs
    else:
        with st.spinner("Searching for jobs..."):
            jobs = search_jobs(role, location)
            st.session_state["jobs"] = jobs
        st.session_state.pop("searched_roles", None)

    if not jobs:
        role_label = ", ".join(st.session_state.get("searched_roles", [role])) if search_mode == "Find best fit" else role
        st.error(
            f"No jobs found for **{role_label}** in **{location}**. "
            "The job search API has limited coverage outside English-speaking markets. "
            "Try London, Madrid, Barcelona, New York, Dublin or Sydney."
        )
        st.stop()

    with st.spinner(f"Scoring {len(jobs)} jobs against your profile..."):
        results = rank_jobs(profile, jobs)
        st.session_state["results"] = results

    try:
        suggestions = suggest_cv_improvements(profile, results)
        st.session_state["cv_suggestions"] = suggestions
    except Exception:
        pass

    os.unlink(tmp_path)

elif search_button and not uploaded_file:
    st.warning("Please upload your CV before searching.")

if "results" not in st.session_state:
    st.markdown("""
    <div style="text-align:center; padding: 2.5rem 1rem 1.5rem;">
        <h1 style="font-size:2.8rem; font-weight:700; margin-bottom:0.4rem;">Find jobs that fit <em>you</em>.</h1>
        <p style="font-size:1.15rem; color:#6c757d; max-width:560px; margin:0 auto 2rem;">
            Upload your CV and Job Scout matches you against real job listings —
            scoring every role against your skills, experience, and location.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="display:flex; gap:1rem; margin-bottom:1rem;">
        <div style="flex:1; background:#495057; border-radius:12px; padding:1.4rem 1.2rem; color:#ffffff;">
            <div style="font-size:1.6rem; margin-bottom:0.5rem;">1</div>
            <h4 style="margin:0 0 0.4rem; color:#ffffff;">Upload your CV</h4>
            <p style="font-size:0.9rem; margin:0;">PDF or Word. Claude reads your experience, skills, and background automatically.</p>
        </div>
        <div style="flex:1; background:#495057; border-radius:12px; padding:1.4rem 1.2rem; color:#ffffff;">
            <div style="font-size:1.6rem; margin-bottom:0.5rem;">2</div>
            <h4 style="margin:0 0 0.4rem; color:#ffffff;">Choose a role</h4>
            <p style="font-size:0.9rem; margin:0;">Search a specific title, or use <strong>Find best fit</strong> for AI-suggested roles.</p>
        </div>
        <div style="flex:1; background:#495057; border-radius:12px; padding:1.4rem 1.2rem; color:#ffffff;">
            <div style="font-size:1.6rem; margin-bottom:0.5rem;">3</div>
            <h4 style="margin:0 0 0.4rem; color:#ffffff;">Get ranked matches</h4>
            <p style="font-size:0.9rem; margin:0;">Every job scored across role, experience, skills, and location — cover letters on demand.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**What you get per match**")

    st.markdown("""
    <div style="display:flex; gap:1rem; margin-bottom:1rem;">
        <div style="flex:1; background:#5a6268; border-radius:8px; padding:0.9rem; text-align:center; color:#ffffff;">
            <strong>Match score</strong><br><span style="font-size:0.85rem;">0–100 across 4 dimensions</span>
        </div>
        <div style="flex:1; background:#5a6268; border-radius:8px; padding:0.9rem; text-align:center; color:#ffffff;">
            <strong>Strengths &amp; gaps</strong><br><span style="font-size:0.85rem;">With actionable tips to close each gap</span>
        </div>
        <div style="flex:1; background:#5a6268; border-radius:8px; padding:0.9rem; text-align:center; color:#ffffff;">
            <strong>Cover letter</strong><br><span style="font-size:0.85rem;">Generated for any job in one click</span>
        </div>
        <div style="flex:1; background:#5a6268; border-radius:8px; padding:0.9rem; text-align:center; color:#ffffff;">
            <strong>CV improvements</strong><br><span style="font-size:0.85rem;">Tailored to your top matches</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<p style="text-align:center; color:#adb5bd; font-size:0.85rem;">'
        'Get started by uploading your CV in the sidebar.</p>',
        unsafe_allow_html=True
    )

if "results" in st.session_state:
    results = st.session_state["results"]
    profile = st.session_state["profile"]

    # Apply filter
    results = [r for r in results if r["score"].get("overall_score", 0) >= min_score]

    # Apply sort
    if sort_by == "Company A–Z":
        results = sorted(results, key=lambda r: str(r["job"].get("company") or "").lower())
    else:
        results = sorted(results, key=lambda r: r["score"].get("overall_score", 0), reverse=True)

    st.success("Scored " + str(len(st.session_state["results"])) + " jobs. Showing best matches first.")

    if "searched_roles" in st.session_state:
        st.info("Searched for: **" + "**, **".join(st.session_state["searched_roles"]) + "**")

    if "cv_suggestions" in st.session_state:
        with st.expander("CV Improvement Suggestions"):
            for tip in st.session_state["cv_suggestions"]:
                st.write("• " + tip)

    with st.expander("Your Profile Summary"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Skills**")
            st.write(", ".join(profile.get("skills", [])))
        with col2:
            st.write("**Target Roles**")
            st.write(", ".join(profile.get("target_roles", [])))

    st.divider()

    applied_urls = set(json.load(open("applications.json")) if os.path.exists("applications.json") else [])

    for i, result in enumerate(results):
        job = result["job"]
        score = result["score"]

        title = str(job.get("title") or "")
        company = str(job.get("company") or "")
        job_location = str(job.get("location") or "")
        url = str(job.get("url") or "#")
        overall = score.get("overall_score", 0)
        summary = score.get("summary", "")
        strengths = score.get("strengths", [])
        gaps = score.get("skill_gaps", [])
        gap_actions = score.get("gap_actions", [])
        salary = score.get("salary_range")
        date_posted = job.get("date_posted")

        if overall >= 70:
            badge_color = "#28a745"
            text_color = "#ffffff"
            indicator = "GREEN"
        elif overall >= 50:
            badge_color = "#ffc107"
            text_color = "#212529"
            indicator = "YELLOW"
        else:
            badge_color = "#dc3545"
            text_color = "#ffffff"
            indicator = "RED"

        applied_label = ' <span style="background:#17a2b8;color:#fff;padding:2px 8px;border-radius:10px;font-size:0.8em;">Applied</span>' if url in applied_urls else ""

        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(
                f'<span style="background:{badge_color};color:{text_color};padding:4px 12px;'
                f'border-radius:12px;font-weight:bold;font-size:1em;">{indicator}</span>'
                f' <span style="font-size:1.3em;font-weight:600;">{title}</span>{applied_label}',
                unsafe_allow_html=True
            )
            st.progress(overall / 100)
            st.write(company + " | " + job_location)
            if date_posted:
                st.caption("Posted: " + date_posted)
        with col2:
            st.metric("Match Score", str(overall) + "/100")
            if salary:
                st.metric("Salary Range", salary)

        was_applied = url in applied_urls
        applied = st.checkbox("Mark as Applied", value=was_applied, key="apply_" + str(i))
        if applied and not was_applied:
            applied_urls.add(url)
            json.dump(list(applied_urls), open("applications.json", "w"))
        elif not applied and was_applied:
            applied_urls.discard(url)
            json.dump(list(applied_urls), open("applications.json", "w"))

        col3, col4 = st.columns(2)
        with col3:
            st.write("**Strengths**")
            for s in strengths:
                st.write("+ " + s)
        with col4:
            st.write("**Skill Gaps**")
            for idx, g in enumerate(gaps):
                st.write("- " + g)
                if idx < len(gap_actions):
                    st.caption("  Tip: " + gap_actions[idx])

        st.write("**Summary**")
        st.write(summary)

        breakdown = score.get("breakdown", {})
        if breakdown:
            with st.expander("Score Breakdown"):
                dimensions = ["role_alignment", "experience_match", "skills_overlap", "location_fit"]
                labels = ["Role Alignment", "Experience Match", "Skills Overlap", "Location Fit"]
                values = [breakdown.get(d, 0) for d in dimensions]
                values_closed = values + [values[0]]
                labels_closed = labels + [labels[0]]

                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(
                    r=values_closed,
                    theta=labels_closed,
                    fill="toself",
                    name="Score"
                ))
                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 25])),
                    showlegend=False,
                    margin=dict(l=20, r=20, t=30, b=20)
                )
                st.plotly_chart(fig, use_container_width=True, key="radar_" + str(i))

        col5, col6 = st.columns([1, 4])
        with col5:
            btn_key = "cover_" + str(i)
            if st.button("Generate Cover Letter", key=btn_key):
                with st.spinner("Writing cover letter..."):
                    letter = generate_cover_letter(profile, job, score)
                    st.session_state["letter_" + str(i)] = letter
        with col6:
            st.link_button("View Job Posting", url)

        letter_key = "letter_" + str(i)
        if letter_key in st.session_state:
            st.text_area("Cover Letter", st.session_state[letter_key], height=400, key="text_" + str(i))

        st.divider()

    rows = [
        {
            "Title": r["job"].get("title", ""),
            "Company": r["job"].get("company", ""),
            "Location": r["job"].get("location", ""),
            "Score": r["score"].get("overall_score", 0),
            "Strengths": "; ".join(r["score"].get("strengths", [])),
            "Skill Gaps": "; ".join(r["score"].get("skill_gaps", []))
        }
        for r in results
    ]
    df_export = pd.DataFrame(rows)
    buf = io.BytesIO()
    df_export.to_csv(buf, index=False)
    st.download_button("Export Results to CSV", buf.getvalue(), "job_matches.csv", "text/csv")
