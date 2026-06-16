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
    
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    # Compute per-segment average for all 4 features
    radar_summary = segmentation.groupby("segment").agg(
        avg_grade=("avg_grade", "mean"),
        attendance_rate=("attendance_rate", "mean"),
        engagement_count=("engagement_count", "mean"),
        failed_concepts=("failed_concepts", "mean"),
    ).reset_index()

    # Normalize engagement and failed_concepts to 0-100 scale for comparability
    max_eng  = radar_summary["engagement_count"].max() or 1
    max_fail = radar_summary["failed_concepts"].max() or 1
    radar_summary["engagement_norm"] = (radar_summary["engagement_count"] / max_eng)  * 100
    radar_summary["failed_norm"]     = (radar_summary["failed_concepts"]  / max_fail) * 100

    categories = ["Avg Score", "Attendance %", "Engagement", "Failed Concepts"]

    st.markdown("**Individual Segment Radar Charts — All 4 Features**")
    st.write("Each radar shows a single segment's profile across score, attendance, engagement, and concept failure rate (normalized 0–100).")

    # Fixed order so grid is always consistent
    seg_order = ["High Achievers", "Steady Performers", "Struggling Attenders", "Disengaged At-Risk"]

    fig_radar = make_subplots(
        rows=2, cols=2,
        specs=[[{"type": "polar"}, {"type": "polar"}],
               [{"type": "polar"}, {"type": "polar"}]],
        subplot_titles=seg_order,
        vertical_spacing=0.15,
        horizontal_spacing=0.08,
    )

    positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
    polar_refs = ["polar", "polar2", "polar3", "polar4"]

    for idx, seg in enumerate(seg_order):
        row_data = radar_summary[radar_summary["segment"] == seg]
        if row_data.empty:
            continue
        row = row_data.iloc[0]
        values = [
            row["avg_grade"],
            row["attendance_rate"],
            row["engagement_norm"],
            row["failed_norm"],
        ]
        values_closed    = values + [values[0]]
        categories_closed = categories + [categories[0]]
        r, c = positions[idx]
        fig_radar.add_trace(
            go.Scatterpolar(
                r=values_closed,
                theta=categories_closed,
                fill="toself",
                name=seg,
                line_color=segment_colors.get(seg, "#999"),
                fillcolor=segment_colors.get(seg, "#999"),
                opacity=0.55,
                showlegend=False,
            ),
            row=r, col=c,
        )

    # Apply radialaxis settings to all 4 polar subplots
    # rotation=45 shifts the first axis label away from the 12-o'clock
    # position where subplot_titles sit, preventing overlap
    radar_axis = dict(visible=True, range=[0, 100], dtick=20, tickfont=dict(size=9))
    angular_axis = dict(rotation=45)
    fig_radar.update_layout(
        polar=dict(radialaxis=radar_axis,  angularaxis=angular_axis),
        polar2=dict(radialaxis=radar_axis, angularaxis=angular_axis),
        polar3=dict(radialaxis=radar_axis, angularaxis=angular_axis),
        polar4=dict(radialaxis=radar_axis, angularaxis=angular_axis),
        height=750,
        margin=dict(t=80, b=40, l=40, r=40),
    )
    st.plotly_chart(fig_radar, use_container_width=True)



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
