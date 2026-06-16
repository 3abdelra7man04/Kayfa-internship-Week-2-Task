import streamlit as st
import pandas as pd
import plotly.express as px
from utils.components import page_header, page_footer, get_base64_image

logo_base64 = get_base64_image("kayfa logo.svg")

page_header(logo_base64, "Age Demographics")

st.markdown("<h2 class='page-header'>👥 Age Demographics Analysis</h2>", unsafe_allow_html=True)

if "filtered_data" not in st.session_state:
    st.warning("No data found. Please check filters in the sidebar.")
    st.stop()

# Pull precomputed aggregations from the snapshot saved by save_dashboard_state()
snapshot = st.session_state.get("snapshot", {})
agg = snapshot.get("agg", {}) if snapshot else {}

st.markdown("**Performance, Attendance, and Engagement by Age Band**")
st.write("How do different age groups perform across core academic metrics?")

age_analysis_records = agg.get("age_analysis", [])
age_analysis = pd.DataFrame(age_analysis_records) if age_analysis_records else pd.DataFrame()

if age_analysis.empty:
    st.info("No age demographic data available.")
else:
    # We create three columns for three bar charts
    c1, c2, c3 = st.columns(3)
    
    with c1:
        fig_score = px.bar(
            age_analysis, x="age_band", y="avg_score", 
            text="avg_score", title="Average Score",
            labels={"age_band": "Age Band", "avg_score": "Score"},
            color_discrete_sequence=["#3498db"]
        )
        fig_score.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig_score.update_layout(yaxis_range=[0, 100], margin=dict(t=40, b=20, l=10, r=10))
        st.plotly_chart(fig_score, use_container_width=True)
        
    with c2:
        fig_att = px.bar(
            age_analysis, x="age_band", y="attendance_rate", 
            text="attendance_rate", title="Attendance Rate %",
            labels={"age_band": "Age Band", "attendance_rate": "Attendance %"},
            color_discrete_sequence=["#2ecc71"]
        )
        fig_att.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_att.update_layout(yaxis_range=[0, 100], margin=dict(t=40, b=20, l=10, r=10))
        st.plotly_chart(fig_att, use_container_width=True)
        
    with c3:
        fig_eng = px.bar(
            age_analysis, x="age_band", y="engagement_count", 
            text="engagement_count", title="Average Engagement Events",
            labels={"age_band": "Age Band", "engagement_count": "Events"},
            color_discrete_sequence=["#f39c12"]
        )
        fig_eng.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig_eng.update_layout(margin=dict(t=40, b=20, l=10, r=10))
        st.plotly_chart(fig_eng, use_container_width=True)


st.markdown('<div class="section-title" style="font-size: 1.5rem; margin-top: 2rem;">💡 Strategic Insights</div>', unsafe_allow_html=True)
st.markdown("""
<div class="section-sub" style="line-height: 1.6;">
• <b>The Maturity Advantage:</b> Students in the <b>30+ age band</b> consistently outperform their younger peers across all three critical metrics: higher average scores, better attendance rates, and significantly more frequent engagement with platform materials.<br>
• <b>Younger Cohort Friction:</b> The younger demographics (<20 and 20-24) show identical, slightly suppressed academic outcomes and lower asynchronous engagement (event counts). This suggests that younger students might rely more on synchronous instruction but lack the self-driven study habits (like re-watching videos or logging in frequently) that older students possess.
</div>
""", unsafe_allow_html=True)

page_footer(logo_base64)
