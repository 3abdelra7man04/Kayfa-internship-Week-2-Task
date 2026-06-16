import streamlit as st
import pandas as pd
import plotly.express as px
from utils.components import page_header, page_footer, get_base64_image

logo_base64 = get_base64_image("kayfa logo.svg")

page_header(logo_base64, "Submission Analysis")

st.markdown("<h2 class='page-header'>⏳ Submission Analysis</h2>", unsafe_allow_html=True)

if "filtered_data" not in st.session_state:
    st.warning("No data found. Please check filters in the sidebar.")
    st.stop()

# Pull precomputed aggregations from the snapshot saved by save_dashboard_state()
snapshot = st.session_state.get("snapshot", {})
agg = snapshot.get("agg", {}) if snapshot else {}

c1 = st.columns(1)[0]
with c1:
    st.markdown("**Submission Buffer vs Score**")
    st.write("Does submitting late or close to the deadline affect student scores?")
    
    submission_vs_score_records = agg.get("submission_vs_score", [])
    submission_vs_score = pd.DataFrame(submission_vs_score_records) if submission_vs_score_records else pd.DataFrame()
    
    if submission_vs_score.empty:
        st.info("No submission buffer data available.")
    else:
        if "buffer_hours" in submission_vs_score.columns and "score" in submission_vs_score.columns:
            fig_scatter = px.scatter(
                submission_vs_score, 
                x="buffer_hours", 
                y="score", 
                color="student_id",
                color_discrete_sequence=["#9b59b6"],
                trendline="ols",
                labels={
                    "buffer_hours": "Buffer before Deadline (Hours) (< 0 means Late)",
                    "score": "Average Score"
                }
            )
            fig_scatter.update_layout(showlegend=False)
            
            # Add a vertical line at 0 to denote the deadline
            fig_scatter.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Deadline")
            
            st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown('<div class="section-title" style="font-size: 1.5rem; margin-top: 2rem;">💡 Strategic Insights</div>', unsafe_allow_html=True)
st.markdown("""
<div class="section-sub" style="line-height: 1.6;">
• <b>The Procrastination Penalty:</b> The trendline reveals a positive correlation between the submission buffer and student scores. Students who submit closer to the deadline (or late) tend to have consistently lower average scores.<br>
• <b>Risk of Late Submissions:</b> Submissions landing past the deadline (negative buffer) cluster noticeably lower on the score axis, highlighting the importance of time management and early intervention.
</div>
""", unsafe_allow_html=True)

page_footer(logo_base64)
