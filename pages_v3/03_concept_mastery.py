import streamlit as st
import pandas as pd
import plotly.express as px
from utils.components import page_header, page_footer, get_base64_image



logo_base64 = get_base64_image("kayfa logo.svg")

page_header(logo_base64, "Concepts Mastery")

st.markdown("<h2 class='page-header'>🧠 Concepts Mastery</h2>", unsafe_allow_html=True)

if "filtered_data" not in st.session_state:
    st.warning("No data found. Please check filters in the sidebar.")
    st.stop()

data = st.session_state.filtered_data

c1 = st.columns(1)[0]

# Pull precomputed aggregations from the snapshot saved by save_dashboard_state()
snapshot = st.session_state.get("snapshot", {})
agg = snapshot.get("agg", {}) if snapshot else {}

with c1:

    st.markdown("**Concepts with the Highest Failure Rate (Top 10)**")
    concepts_top_10_failure_rate_records = agg.get("concepts_top_10_failure_rate", [])
    concepts_top_10_failure_rate = pd.DataFrame(concepts_top_10_failure_rate_records) if concepts_top_10_failure_rate_records else pd.DataFrame()
    
    if concepts_top_10_failure_rate.empty:
        st.info("No concepts failure rate data available.")
    else:
        if "failure_rate" in concepts_top_10_failure_rate.columns:
            fig_failure = px.bar(
        concepts_top_10_failure_rate,
        x="course_concept_name",
        y="failure_rate",
        text="failure_rate",
        labels={
            "course_concept_name": "Course - Concept",
            "failure_rate": "Failure Rate %"
        })

            fig_failure.update_traces(
                texttemplate="%{text:.2f}%",
                textposition="outside",
                textfont_size=18
            )
            fig_failure.update_layout(
                margin=dict(t=30, b=20, l=10, r=10),
                xaxis_tickangle=-45
            )

            st.plotly_chart(fig_failure, use_container_width=True)
    
c2 = st.columns(1)[0]
with c2:
    st.markdown("**Recursion Overtime**")
    Recursion_Overtime = agg.get("recursion_overtime", [])
    Recursion_Overtime = pd.DataFrame(Recursion_Overtime) if Recursion_Overtime else pd.DataFrame()
    
    if Recursion_Overtime.empty:
        st.info("No Recursion Overtime data available.")
    else:
        if "score_pct" in Recursion_Overtime.columns:
            if "date" not in Recursion_Overtime.columns and "timestamp" in Recursion_Overtime.columns:
                Recursion_Overtime["date"] = Recursion_Overtime["timestamp"].astype(str).str.split('T').str[0]

            x_col = "date" if "date" in Recursion_Overtime.columns else "timestamp"
            fig_mastery = px.line(
                                Recursion_Overtime,
                                x=x_col,
                                y="score_pct",
                                labels={
                                    x_col: "Date",
                                    "score_pct": "Mastery Score %"
                                })

            fig_mastery.update_traces(
                mode="lines",
                line=dict(color="#3498db", width=3),
                hovertemplate="<b>Date</b>: %{x}<br><b>Score</b>: %{y:.2f}%<extra></extra>",
                marker=dict(size=10, color="#3498db", symbol="circle", line=dict(width=2, color="White"))
            )
            fig_mastery.update_layout(
                margin=dict(t=30, b=20, l=10, r=10),
                xaxis_tickangle=-45,
                yaxis_range=[0, 100]
            )

            st.plotly_chart(fig_mastery, use_container_width=True)

st.markdown('<div class="section-title" style="font-size: 1.5rem; margin-top: 2rem;">💡 Strategic Insights</div>', unsafe_allow_html=True)
st.markdown("""
<div class="section-sub" style="line-height: 1.6;">
• <b>Critical Concept Bottleneck:</b> <b>Python Programming - Recursion</b> represents an extreme academic bottleneck with a staggering <b>85.11%</b> failure rate, towering over all other conceptual gaps and requiring immediate structural intervention.<br>
• <b>Persistent Mastery Plateau:</b> Historical timeline data shows that mastery scores for Recursion have remained stubbornly suppressed—constantly plateauing or dropping below <b>50%</b> without seasonal recovery—proving that current pedagogical approaches are not translating into conceptual comprehension.<br>
• <b>Broad-Spectrum Technical Friction:</b> Beyond coding, abstract analytical topics like data joins/merges, model overfitting, and funnel analytics cluster tightly together with near-identical failure rates (~<b>46%</b>), highlighting a systemic student deficit in relational logic and technical abstractions.
</div>
""", unsafe_allow_html=True)


page_footer(logo_base64)