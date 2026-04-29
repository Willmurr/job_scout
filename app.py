import streamlit as st
import os
import tempfile
from cv_parser import parse_cv
from job_search import search_jobs
from matcher import rank_jobs
from cover_letter import generate_cover_letter

st.set_page_config(page_title="Job Scout", page_icon="Target", layout="wide")
st.title("Job Scout")
st.subheader("AI-powered job matching and cover letter generation")

with st.sidebar:
    st.header("Your Search")
    uploaded_file = st.file_uploader("Upload your CV", type=["pdf", "docx"])
    role = st.text_input("Target Role", value="credit analyst")
    location = st.text_input("Location", value="London")
    search_button = st.button("Find Matching Jobs", type="primary")

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

    with st.spinner("Searching for jobs..."):
        jobs = search_jobs(role, location)
        st.session_state["jobs"] = jobs

    with st.spinner("Scoring jobs against your profile..."):
        results = rank_jobs(profile, jobs)
        st.session_state["results"] = results

    os.unlink(tmp_path)

elif search_button and not uploaded_file:
    st.warning("Please upload your CV before searching.")

if "results" in st.session_state:
    results = st.session_state["results"]
    profile = st.session_state["profile"]

    st.success("Scored " + str(len(results)) + " jobs. Showing best matches first.")

    with st.expander("Your Profile Summary"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Skills**")
            st.write(", ".join(profile.get("skills", [])))
        with col2:
            st.write("**Target Roles**")
            st.write(", ".join(profile.get("target_roles", [])))

    st.divider()

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

        if overall >= 70:
            indicator = "GREEN"
        elif overall >= 50:
            indicator = "YELLOW"
        else:
            indicator = "RED"

        col1, col2 = st.columns([4, 1])
        with col1:
            st.subheader(indicator + " | " + title)
            st.write(company + " | " + job_location)
        with col2:
            st.metric("Match Score", str(overall) + "/100")

        col3, col4 = st.columns(2)
        with col3:
            st.write("**Strengths**")
            for s in strengths:
                st.write("+ " + s)
        with col4:
            st.write("**Skill Gaps**")
            for g in gaps:
                st.write("- " + g)

        st.write("**Summary**")
        st.write(summary)

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