import streamlit as st
import pandas as pd
import plotly.express as px
from utils.components import page_header, page_footer, get_base64_image

logo_base64 = get_base64_image("kayfa logo.svg")

page_header(logo_base64, "Student Segmentation")

st.markdown("<h2 class='page-header'>🎯 Student Segmentation</h2>", unsafe_allow_html=True)

if "filtered_data" not in st.session_state:
    st.warning("No data found. Please check filters in the sidebar.")
    st.stop()

# Pull precomputed aggregations from the snapshot saved by save_dashboard_state()
snapshot = st.session_state.get("snapshot", {})
agg = snapshot.get("agg", {}) if snapshot else {}

segmentation_records = agg.get("student_segmentation", [])
segmentation = pd.DataFrame(segmentation_records) if segmentation_records else pd.DataFrame()

if segmentation.empty:
    st.info("No student segmentation data available. Try refreshing filters.")
else:
    st.markdown("**Segmenting the Cohort based on Performance, Attendance, and Engagement**")
    st.write("Each student is classified into a segment to enable targeted interventions.")
    
    # Pre-defined colors for segments to keep it consistent
    segment_colors = {
        "High Achievers": "#2ecc71",       # Green
        "Steady Performers": "#3498db",    # Blue
        "Struggling Attenders": "#f39c12", # Orange
        "Disengaged At-Risk": "#e74c3c"    # Red
    }
    
    # 1. Plotly Scatter Plot
    fig = px.scatter(
        segmentation, 
        x="attendance_rate", 
        y="avg_grade", 
        color="segment",
        color_discrete_map=segment_colors,
        size="engagement_count",
        hover_data=["failed_concepts"],
        labels={
            "attendance_rate": "Attendance Rate %",
            "avg_grade": "Average Score",
            "segment": "Student Segment",
            "engagement_count": "Engagement Events",
            "failed_concepts": "Failed Concepts"
        },
        title="Student Distribution by Segment (Bubble size = Engagement)"
    )
    
    fig.update_layout(
        xaxis_range=[0, 105],
        yaxis_range=[0, 105],
        legend_title_text="Segments"
    )
    st.plotly_chart(fig, use_container_width=True)

    # 2. Segment Summary Table
    st.markdown("### 📊 Segment Overview")
    
    # Calculate summary metrics per segment
    summary = segmentation.groupby("segment").agg(
        Students=("student_id", "count"),
        Avg_Score=("avg_grade", "mean"),
        Avg_Attendance=("attendance_rate", "mean"),
        Avg_Engagement=("engagement_count", "mean"),
        Avg_Failed_Concepts=("failed_concepts", "mean")
    ).reset_index()
    
    # Round metrics for display
    summary["Avg_Score"] = summary["Avg_Score"].round(1)
    summary["Avg_Attendance"] = summary["Avg_Attendance"].round(1)
    summary["Avg_Engagement"] = summary["Avg_Engagement"].round(1)
    summary["Avg_Failed_Concepts"] = summary["Avg_Failed_Concepts"].round(1)
    
    # Define an explicit sort order based on performance
    sort_order = {"High Achievers": 1, "Steady Performers": 2, "Struggling Attenders": 3, "Disengaged At-Risk": 4}
    summary["sort"] = summary["segment"].map(sort_order)
    summary = summary.sort_values("sort").drop("sort", axis=1)
    
    st.dataframe(
        summary,
        column_config={
            "segment": "Segment",
            "Students": "Headcount",
            "Avg_Score": "Avg Score",
            "Avg_Attendance": "Avg Attendance %",
            "Avg_Engagement": "Avg Engagement",
            "Avg_Failed_Concepts": "Avg Failed Concepts"
        },
        use_container_width=True,
        hide_index=True
    )


st.markdown('<div class="section-title" style="font-size: 1.5rem; margin-top: 2rem;">💡 Strategic Insights</div>', unsafe_allow_html=True)
st.markdown("""
<div class="section-sub" style="line-height: 1.6;">
• <b>High Achievers:</b> Have both excellent attendance (>75%) and grades (>75%). They exhibit the highest engagement rates and barely fail any concepts. They are prime candidates for advanced/bonus material.<br>
• <b>Steady Performers:</b> Make up the bulk of the cohort. They maintain acceptable attendance and average grades, and their progression is stable but needs occasional encouragement to reach high-achiever status.<br>
• <b>Struggling Attenders:</b> These students attend class consistently (>70%) but are failing multiple concepts and struggling with their grades. <i>This highlights a pedagogical gap</i>—they are putting in the time but not mastering the material. They need immediate tutoring or alternative learning formats, not warnings about attendance.<br>
• <b>Disengaged At-Risk:</b> The most critical segment. They suffer from both low attendance (<70%) and poor grades (<65%). Their extremely low engagement indicates they have largely abandoned the course and require urgent administrative intervention.
</div>
""", unsafe_allow_html=True)

page_footer(logo_base64)
