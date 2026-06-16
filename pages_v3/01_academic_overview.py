import streamlit as st
import pandas as pd
import plotly.express as px
from utils.components import kpi, page_header, page_footer, get_base64_image
from utils.styles import get_plotly_colors


logo_base64 = get_base64_image("kayfa logo.svg")

page_header(logo_base64, "Academic Overview Dashboard")

if "filtered_data" not in st.session_state:
    st.warning("No data found. Please check filters in the sidebar.")
    st.stop()

data = st.session_state.filtered_data
students = data.get("students", pd.DataFrame())
courses = data.get("courses", pd.DataFrame())
grades = data.get("grades", pd.DataFrame())
attendance = data.get("attendance", pd.DataFrame())

# Compute KPIs
total_students = len(students)
total_courses = len(courses)
avg_score = grades["score"].mean() if not grades.empty else 0
attendance_rate = (attendance["status"] == "P").mean() * 100 if not attendance.empty else 0

k1, k2, k3 = st.columns(3)
kpi(k1, "Total Students",    f"{total_students:,}",          '<span class="kpi-delta-pos">↑ Enrolled population</span>',  "blue")
kpi(k2, "Avg Score",         f"{avg_score:.1f}%",            '<span class="kpi-delta-pos">Academic performance</span>', "purple")
kpi(k3, "Attendance Rate",   f"{attendance_rate:.1f}%",      '<span class="kpi-delta-pos">Student engagement</span>', "orange")

st.markdown("<br>", unsafe_allow_html=True)

st.markdown('<div class="section-title">📊 Academic Overview</div>', unsafe_allow_html=True)
st.markdown('<div class="section-sub">Data-driven answers to core academic questions</div>', unsafe_allow_html=True)

c1 = st.columns(1)[0]

colors = get_plotly_colors()

# Pull precomputed aggregations from the snapshot saved by save_dashboard_state()
snapshot = st.session_state.get("snapshot", {})
agg = snapshot.get("agg", {}) if snapshot else {}

with c1:
    st.markdown("**Attendance Rate per Group**")

    att_rate_records = agg.get("attendance_rate_by_group", [])
    att_rate = pd.DataFrame(att_rate_records) if att_rate_records else pd.DataFrame()

    if not att_rate.empty:
        avg_att = att_rate['attendance_rate'].mean()

        # Add custom formatted text string to populate the bars (e.g., "85.4%")
        att_rate['text_label'] = att_rate['attendance_rate'].apply(lambda x: f"{x:.1f}%")

        # Build the Bar Chart with text properties enabled
        fig_q1 = px.bar(att_rate, x="group_id", y="attendance_rate",
                        title="Attendance Rate vs Avg",
                        text="text_label",
                        color_discrete_sequence=[colors[0] if colors else "blue"])

        # Adjust label positions
        fig_q1.update_traces(textposition='auto', textfont_size=18, insidetextanchor='middle')

        # Draw the dynamic average dashed line
        fig_q1.add_hline(
            y=avg_att,
            line_dash="dash",
            line_color="#991B1B",
            annotation_text=f"Avg: {avg_att:.1f}%",
            annotation_position="top left",
            annotation_font_color="#991B1B",
            annotation_font_size=18
        )

        fig_q1.update_layout(margin=dict(t=30, b=20, l=10, r=10), xaxis_title="Group", yaxis_title="Attendance Rate (%)")
        st.plotly_chart(fig_q1, use_container_width=True)

        below_avg = att_rate[att_rate['attendance_rate'] < avg_att]['group_id'].tolist()
        if below_avg:
            st.caption(f"Groups below platform average ({avg_att:.1f}%): **{', '.join(below_avg)}**")
        else:
            st.caption(f"No groups sit below the platform average ({avg_att:.1f}%).")
    else:
        st.info("No attendance data available.")

c2, c3 = st.columns(2)

with c2:
    st.markdown("**Score Distribution & Volatility**")
    if not grades.empty and "type" in grades.columns and "score" in grades.columns:
        fig_q2 = px.box(grades, x="type", y="score", color="type",
                        title="Scores by Assessment Type",
                        color_discrete_sequence=colors)
        fig_q2.update_layout(margin=dict(t=30, b=20, l=10, r=10), xaxis_title="Assessment Type", yaxis_title="Score", showlegend=False)
        st.plotly_chart(fig_q2, use_container_width=True)

        # Use precomputed volatility from the snapshot
        vol_records = agg.get("score_volatility", [])
        volatility_df = pd.DataFrame(vol_records) if vol_records else pd.DataFrame()
        if not volatility_df.empty:
            most_volatile = volatility_df.iloc[0]["type"]
            st.caption(f"Performance is most volatile in **{most_volatile}** assessments.")
    else:
        st.info("No grade data available.")

with c3:
    st.markdown("**Grade Spread by Course**")
    if not grades.empty and "course_id" in grades.columns and "score" in grades.columns:
        if not courses.empty and "course_id" in courses.columns and "course_name" in courses.columns:
            df_q3 = pd.merge(grades, courses[['course_id', 'course_name']], on='course_id', how='left')
            x_col = "course_name"
        else:
            df_q3 = grades
            x_col = "course_id"

        # Use precomputed average grades from the snapshot
        avg_grade_records = agg.get("course_avg_grade", [])
        avg_grades_df = pd.DataFrame(avg_grade_records) if avg_grade_records else pd.DataFrame()

        if not avg_grades_df.empty and x_col in avg_grades_df.columns:
            avg_grades_df = avg_grades_df.sort_values(by="avg_score")
            highest_course = avg_grades_df.iloc[-1][x_col]
            lowest_course = avg_grades_df.iloc[0][x_col]

            fig_q3 = px.box(df_q3, x=x_col, y="score", color=x_col,
                            title="Grade Spread by Course",
                            category_orders={x_col: avg_grades_df[x_col].tolist()},
                            color_discrete_sequence=colors)
            fig_q3.update_traces(boxmean=True)
            fig_q3.update_layout(margin=dict(t=30, b=20, l=10, r=10), xaxis_title="Course", yaxis_title="Score", showlegend=False)
            st.plotly_chart(fig_q3, use_container_width=True)

            st.caption(f"Highest Avg: **{highest_course}** | Lowest Avg: **{lowest_course}**")
        else:
            # Fallback: render without ordering if snapshot data is missing
            fig_q3 = px.box(df_q3, x=x_col, y="score", color=x_col,
                            title="Grade Spread by Course",
                            color_discrete_sequence=colors)
            fig_q3.update_traces(boxmean=True)
            fig_q3.update_layout(margin=dict(t=30, b=20, l=10, r=10), xaxis_title="Course", yaxis_title="Score", showlegend=False)
            st.plotly_chart(fig_q3, use_container_width=True)
    else:
        st.info("No course grade data available.")

st.markdown('<div class="section-title" style="font-size: 1.5rem; margin-top: 2rem;">💡 Strategic Insights</div>', unsafe_allow_html=True)
st.markdown("""
<div class="section-sub" style="line-height: 1.6;">
• <b>Targeted Attendance Intervention:</b> Group <b>G07</b> is a significant outlier with a <b>60.4%</b> attendance rate (well below the 77.0% average), requiring urgent outreach to address localized engagement issues.<br>
• <b>Assessment Volatility and Support:</b> Student performance is most volatile in <b>assignments</b>, indicating a need for clearer evaluation rubric standards or stepped milestones to prevent trailing outliers and zeroes.<br>
• <b>Curriculum Alignment Strategy:</b> Academic performance peaks in <b>Machine Learning Basics</b> but drops lowest in <b>Digital Marketing</b>, signaling an opportunity to redesign foundational modules or adjust instruction in lower-performing courses.
</div>
""", unsafe_allow_html=True)

page_footer(logo_base64)
