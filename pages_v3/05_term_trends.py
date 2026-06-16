import streamlit as st
import pandas as pd
import plotly.express as px
from utils.components import page_header, page_footer, get_base64_image

logo_base64 = get_base64_image("kayfa logo.svg")

page_header(logo_base64, "Term Trends")

st.markdown("<h2 class='page-header'>📅 Term Trends & Engagement</h2>", unsafe_allow_html=True)

if "filtered_data" not in st.session_state:
    st.warning("No data found. Please check filters in the sidebar.")
    st.stop()

# Pull precomputed aggregations from the snapshot saved by save_dashboard_state()
snapshot = st.session_state.get("snapshot", {})
agg = snapshot.get("agg", {}) if snapshot else {}

c1 = st.columns(1)[0]
with c1:
    st.markdown("**Daily Attendance over the 6-Month Term**")
    
    daily_attendance_records = agg.get("daily_attendance", [])
    daily_attendance = pd.DataFrame(daily_attendance_records) if daily_attendance_records else pd.DataFrame()
    
    if daily_attendance.empty:
        st.info("No attendance trend data available.")
    else:
        fig_att = px.line(
            daily_attendance, 
            x="date", 
            y="attendance_pct",
            labels={
                "date": "Date",
                "attendance_pct": "Attendance %"
            }
        )
        fig_att.update_traces(
            mode="lines+markers",
            line=dict(color="#2ecc71", width=3),
            marker=dict(size=6, color="#2ecc71")
        )
        fig_att.update_layout(yaxis_range=[0, 100], showlegend=False)
        st.plotly_chart(fig_att, use_container_width=True)

c2 = st.columns(1)[0]
with c2:
    st.markdown("**Daily Engagement over the 6-Month Term**")
    
    daily_engagement_records = agg.get("daily_engagement", [])
    daily_engagement = pd.DataFrame(daily_engagement_records) if daily_engagement_records else pd.DataFrame()
    
    if daily_engagement.empty:
        st.info("No engagement trend data available.")
    else:
        fig_eng = px.line(
            daily_engagement, 
            x="date", 
            y="event_count",
            labels={
                "date": "Date",
                "event_count": "Total Engagement Events"
            }
        )
        fig_eng.update_traces(
            mode="lines+markers",
            line=dict(color="#f39c12", width=3),
            marker=dict(size=6, color="#f39c12")
        )
        fig_eng.update_layout(showlegend=False)
        st.plotly_chart(fig_eng, use_container_width=True)


st.markdown('<div class="section-title" style="font-size: 1.5rem; margin-top: 2rem;">💡 Strategic Insights</div>', unsafe_allow_html=True)
st.markdown("""
<div class="section-sub" style="line-height: 1.6;">
• <b>The "March Dip":</b> A distinct, cohort-wide drop in both attendance and asynchronous engagement is visible throughout the first half of March (most significantly around March 4th through March 18th, where attendance plunges to 30%-40%).<br>
• <b>Proposed Cause (Ramadan/Midterms):</b> This sharp, universal decline across all metrics strongly corresponds to either a major academic milestone such as mid-term exams overwhelming students, or the beginning of the holy month of Ramadan altering student sleep and activity schedules. To mitigate this, assignments and synchronous sessions should be adjusted during this known friction period.
</div>
""", unsafe_allow_html=True)

page_footer(logo_base64)
