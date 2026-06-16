import streamlit as st
import pandas as pd
import plotly.express as px
from utils.components import kpi, page_header, page_footer, get_base64_image

logo_base64 = get_base64_image("kayfa logo.svg")

page_header(logo_base64, "Performance Analysis")

st.markdown("<h2 class='page-header'>Performance Analysis</h2>", unsafe_allow_html=True)

if "filtered_data" not in st.session_state:
    st.warning("No data found. Please check filters in the sidebar.")
    st.stop()

data = st.session_state.filtered_data
grades = data.get("grades", pd.DataFrame())
submissions = data.get("submissions", pd.DataFrame())

# ── Read from snapshot (computed once on filter change, cached in session_state) ──
snapshot = st.session_state.get("snapshot", {})
agg_snap  = snapshot.get("agg",  {})

if grades.empty:
    st.info("No grades data available for the current selection.")
else:
    c1 = st.columns(1)[0]

    avg_grades_att_by_student = pd.DataFrame(agg_snap.get("avg_grades_att_by_student", []))
    
    with c1:
        st.markdown("**Grades vs Attendance Rate**")
        st.write("Displays the correlation between a student's physical attendance and their overall academic performance.")
        fig_scatter = px.scatter(avg_grades_att_by_student, x="attendance_rate", y="score", color="student_id",color_discrete_sequence=["#3498db"],trendline="ols")
        fig_scatter.update_layout(xaxis_title="Attendance Rate %", yaxis_title="Score", showlegend=False)
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    c2, c3 = st.columns(2)
    with c2:
        st.markdown("**Scores vs Login Counts**")
        st.write("Highlights how frequently logging into the platform correlates with higher scores.")
        avg_grades_login_by_student = pd.DataFrame(agg_snap.get("avg_grades_login_by_student", []))
        if not avg_grades_login_by_student.empty:
            fig_scatter = px.scatter(avg_grades_login_by_student, x="login_count", y="score", color_discrete_sequence=["#3498db"], trendline="ols", trendline_color_override="red")
            fig_scatter.update_layout(xaxis_title="Login Count", yaxis_title="Score", showlegend=False)
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("Assessment type data not available.")
    with c3:
        st.markdown("**Scores vs Video Watch Time**")
        st.write("Examines the relationship between asynchronous video engagement and final grades.")
        avg_grades_video_watch_by_student = pd.DataFrame(agg_snap.get("avg_grades_video_watch_by_student", []))
        if not avg_grades_video_watch_by_student.empty:
            fig_scatter = px.scatter(avg_grades_video_watch_by_student, x="total_video_watch_seconds", y="score", color_discrete_sequence=["#3498db"], trendline="ols", trendline_color_override="red")
            fig_scatter.update_layout(xaxis_title="Video Watch Time", yaxis_title="Score", showlegend=False)
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("Video watch data not available.")
    
    st.markdown('<div class="section-title" style="font-size: 1.5rem; margin-top: 2rem;">💡 Strategic Insights</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="section-sub" style="line-height: 1.6;">
    • <b>Attendance Ceiling Effect:</b> While high attendance sets a strong baseline, it doesn't guarantee top scores on its own; however, maintaining attendance above <b>80%</b> effectively eliminates the risk of critically low performance drops below 55.<br>
    • <b>Active Engagement Drives Success:</b> A clear positive correlation exists between score and asynchronous activity—specifically <b>Video Watch Time</b> and <b>Login Counts</b>—suggesting that platform interaction is a stronger predictor of academic excellence than physical presence alone.<br>
    • <b>Targeted Platform Nudges:</b> Students with low login counts (under 15) or minimal watch time (under 5k) show highly volatile, lower-tier grades, highlighting a prime opportunity for automated LMS nudges to boost early digital participation.
    </div>
""", unsafe_allow_html=True)

page_footer(logo_base64)
