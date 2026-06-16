import streamlit as st
import pandas as pd
import plotly.express as px
from utils.components import page_header, page_footer, get_base64_image

logo_base64 = get_base64_image("kayfa logo.svg")

page_header(logo_base64, "At-Risk Ranking")

st.markdown("<h2 class='page-header'>🚨 At-Risk Student Ranking</h2>", unsafe_allow_html=True)

if "filtered_data" not in st.session_state:
    st.warning("No data found. Please check filters in the sidebar.")
    st.stop()

# Pull precomputed aggregations from the snapshot saved by save_dashboard_state()
snapshot = st.session_state.get("snapshot", {})
agg = snapshot.get("agg", {}) if snapshot else {}

at_risk_records = agg.get("at_risk_ranking", [])
df_risk = pd.DataFrame(at_risk_records) if at_risk_records else pd.DataFrame()

if df_risk.empty:
    st.info("No at-risk ranking data available. Try refreshing filters.")
else:
    st.markdown("**Top 10 Students Requiring Immediate Intervention**")
    st.write("This composite ranking identifies students exhibiting the most critical combination of poor attendance, declining asynchronous engagement, and repeated concept failure.")
    
    # Render the interactive dataframe
    st.markdown("### 📋 Top 10 Priority List")
    
    # Highlight highest risk scores in red
    def highlight_risk(val):
        if val > 60:
            return 'color: #c0392b; font-weight: bold'
        elif val > 40:
            return 'color: #e67e22; font-weight: bold'
        return ''

    st.dataframe(
        df_risk.style.map(highlight_risk, subset=['risk_score']),
        column_config={
            "student_id": "Student ID",
            "student_name": "Name",
            "attendance_rate": "Attendance Rate %",
            "engagement_decline": "Engagement Drop (Events)",
            "failed_concepts": "Failed Concepts Count",
            "risk_score": st.column_config.ProgressColumn(
                "Risk Severity Score",
                help="Composite metric combining low attendance, declining engagement, and high concept failure rates.",
                format="%.1f",
                min_value=0,
                max_value=100,
            ),
        },
        use_container_width=True,
        hide_index=True
    )

    


st.markdown('<div class="section-title" style="font-size: 1.5rem; margin-top: 2rem;">💡 Strategic Insights</div>', unsafe_allow_html=True)
st.markdown("""
<div class="section-sub" style="line-height: 1.6;">
• <b>Intervention Prioritization:</b> The ranking effectively funnels instructors' attention to the 10 students who most urgently need a check-in. By relying on a composite score rather than a single metric, it prevents "false alarms" (e.g., someone with low attendance but perfect grades).<br>
• <b>Risk Factors:</b> If a student appears high on this list, it means they are simultaneously skipping live sessions, drastically cutting down on asynchronous study time, and failing critical concept checks. <b>Instructors should contact these students immediately.</b>
</div>
""", unsafe_allow_html=True)

page_footer(logo_base64)
