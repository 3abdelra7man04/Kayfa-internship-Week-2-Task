import streamlit as st
import pandas as pd
from utils.mongo import load_all_data, get_latest_state, save_dashboard_state, apply_filters
from utils.styles import apply_styles
from utils.components import get_base64_image

# ── Page Config (must be first) ───────────────────────────────────────────────
st.set_page_config(
    page_title="Kayfa | E-Learning Dashboard v3",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply light/dark mode CSS
apply_styles()

logo_base64 = get_base64_image("kayfa logo.svg")

# ══════════════════════════════════════════════════════════════════════════════
# NAVIGATION ROUTING (Must be initialized before st.page_link is called)
# ══════════════════════════════════════════════════════════════════════════════

pages = {
    "Dashboard": [
        st.Page("pages_v3/01_academic_overview.py", title="📊 Academic Overview"),
        st.Page("pages_v3/02_performance_analysis.py", title="📈 Performance Analysis"),
        st.Page("pages_v3/03_concept_mastery.py", title="🧠 Concept Mastery"),
        st.Page("pages_v3/04_submission_analysis.py", title="⏳ Submission Analysis"),
        st.Page("pages_v3/05_term_trends.py", title="📅 Term Trends"),
        st.Page("pages_v3/06_age_analysis.py", title="👥 Age Demographics"),
        st.Page("pages_v3/07_student_segmentation.py", title="🎯 Student Segmentation"),
        st.Page("pages_v3/08_group_sizes.py", title="🔎 Group Sizes"),
        st.Page("pages_v3/09_at_risk_ranking.py", title="🚨 At-Risk Ranking"),
        st.Page("pages_v3/10_group_trends.py", title="📈 Group Grade Trends"),
    ]
}

pg = st.navigation(pages, position="hidden")

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR – Global Filters Shared Across st.navigation
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div style='padding: 12px 0 24px; display: flex; flex-direction: column; align-items: flex-start; gap: 10px;'>
        <img src="{logo_base64}" style="height: 65px; width: auto; object-fit: contain;" alt="Kayfa Logo">
        <div style='font-size:0.72rem;color:var(--tagline-color);letter-spacing:0.5px;'>Educational Analytics Platform</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">Filters</div>', unsafe_allow_html=True)

    # Load all data to populate the filters
    data_dict = load_all_data()
    students = data_dict.get("students", pd.DataFrame())
    courses = data_dict.get("courses", pd.DataFrame())
    groups = data_dict.get("groups", pd.DataFrame())

    course_options = ["All"] + sorted(courses["course_id"].dropna().unique().tolist()) if not courses.empty else ["All"]
    group_options = ["All"] + sorted(groups["group_id"].dropna().unique().tolist()) if not groups.empty else ["All"]
    gender_options = ["All"] + sorted(students["gender"].dropna().unique().tolist()) if not students.empty and "gender" in students.columns else ["All"]

    if "filters" not in st.session_state:
        latest_filters, latest_snapshot = get_latest_state()
        if latest_filters:
            st.session_state.filters = latest_filters
        else:
            st.session_state.filters = {
                "course": "All",
                "group": "All",
                "gender": "All"
            }
        if latest_snapshot:
            st.session_state.snapshot = latest_snapshot
    
    f = st.session_state.filters

    try: course_idx = course_options.index(f.get("course", "All"))
    except ValueError: course_idx = 0

    try: group_idx = group_options.index(f.get("group", "All"))
    except ValueError: group_idx = 0

    try: gender_idx = gender_options.index(f.get("gender", "All"))
    except ValueError: gender_idx = 0

    selected_course = st.selectbox("Course ID", course_options, index=course_idx)
    selected_group  = st.selectbox("Group ID",  group_options, index=group_idx)
    selected_gender = st.selectbox("Gender",    gender_options, index=gender_idx)

    current_filters = {
        "course": selected_course,
        "group": selected_group,
        "gender": selected_gender
    }

    if current_filters != st.session_state.filters or "filtered_data" not in st.session_state:
        st.session_state.filters = current_filters
        # Apply filters
        df_filtered = apply_filters(data_dict, selected_course, selected_group, selected_gender)
        st.session_state.filtered_data = df_filtered
        st.session_state.snapshot = save_dashboard_state(current_filters, df_filtered)

    st.markdown("---")
    st.markdown('<div class="sidebar-section">Navigation</div>', unsafe_allow_html=True)
    
    st.page_link("pages_v3/01_academic_overview.py", label="Academic Overview", icon="📊")
    st.page_link("pages_v3/02_performance_analysis.py", label="Performance Analysis", icon="📈")
    st.page_link("pages_v3/03_concept_mastery.py", label="Concept Mastery", icon="🧠")
    st.page_link("pages_v3/04_submission_analysis.py", label="Submission Analysis", icon="⏳")
    st.page_link("pages_v3/05_term_trends.py", label="Term Trends", icon="📅")
    st.page_link("pages_v3/06_age_analysis.py", label="Age Demographics", icon="👥")
    st.page_link("pages_v3/07_student_segmentation.py", label="Student Segmentation", icon="🎯")
    st.page_link("pages_v3/08_group_sizes.py", label="Group Sizes", icon="🔎")
    st.page_link("pages_v3/09_at_risk_ranking.py", label="At-Risk Ranking", icon="🚨")
    st.page_link("pages_v3/10_group_trends.py", label="Group Grade Trends", icon="📈")



# Render the selected page
pg.run()

with st.sidebar:
    st.markdown("---")
    st.markdown('<div style="font-size:0.72rem;color:var(--tagline-color);">📊 Based on MongoDB Atlas data<br>generated for Kayfa exploratory analysis.</div>',
                unsafe_allow_html=True)
