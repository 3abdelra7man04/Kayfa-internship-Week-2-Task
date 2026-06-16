import streamlit as st
import pandas as pd
import plotly.express as px
from utils.components import page_header, page_footer, get_base64_image

logo_base64 = get_base64_image("kayfa logo.svg")

page_header(logo_base64, "Group Grade Trends")

st.markdown("<h2 class='page-header'>📈 Group Grade Trends</h2>", unsafe_allow_html=True)

if "filtered_data" not in st.session_state:
    st.warning("No data found. Please check filters in the sidebar.")
    st.stop()

# Pull precomputed aggregations from the snapshot saved by save_dashboard_state()
snapshot = st.session_state.get("snapshot", {})
agg = snapshot.get("agg", {}) if snapshot else {}

trends_records = agg.get("group_trends", [])
deltas_records = agg.get("group_trend_deltas", [])

df_trends = pd.DataFrame(trends_records) if trends_records else pd.DataFrame()
df_deltas = pd.DataFrame(deltas_records) if deltas_records else pd.DataFrame()

if df_trends.empty or df_deltas.empty:
    st.info("No group trend data available. Try refreshing filters.")
else:
    st.markdown("**Tracking Assessment Performance Over Time**")
    st.write("This dashboard tracks each group's average grade across successive assessments to identify groups that are consistently improving versus those that are sliding down.")
    
    # 1. Timeseries Line Chart
    fig = px.line(
        df_trends, 
        x="date", 
        y="score", 
        color="group_id",
        markers=True,
        title="Average Score per Group over the Term",
        labels={"date": "Assessment Date", "score": "Average Score", "group_id": "Group"},
    )
    
    # Make the lines slightly thicker and add hover details
    fig.update_traces(line=dict(width=3), marker=dict(size=8))
    fig.update_layout(
        xaxis_title="",
        yaxis_title="Average Assessment Score",
        yaxis_range=[df_trends["score"].min() - 5, df_trends["score"].max() + 5],
        legend_title_text="Group ID",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

    # 2. Trend Delta Summary Table
    st.markdown("### 📊 Performance Shift Analysis")
    st.write("Comparing the first assessment's average to the final assessment's average to calculate the overall trend.")
    
    def highlight_delta(val):
        try:
            if float(val) > 0:
                return 'color: #2ecc71; font-weight: bold' # Green for up
            elif float(val) < 0:
                return 'color: #e74c3c; font-weight: bold' # Red for down
            return ''
        except:
            return ''

    st.dataframe(
        df_deltas.style.map(highlight_delta, subset=['delta']),
        column_config={
            "group_id": "Group ID",
            "first_score": "First Assessment Score",
            "last_score": "Latest Assessment Score",
            "delta": "Score Change",
            "trend_status": "Trend Status"
        },
        use_container_width=True,
        hide_index=True
    )

st.markdown('<div class="section-title" style="font-size: 1.5rem; margin-top: 2rem;">💡 Strategic Insights</div>', unsafe_allow_html=True)
st.markdown("""
<div class="section-sub" style="line-height: 1.6;">
• <b>Sliding Down:</b> Groups with a negative Score Change (highlighted in red) are sliding down the curve. The instructor's pedagogy or pacing might be misaligned with the increasing difficulty of the term's later concepts, requiring a curriculum review.<br>
• <b>Trending Up:</b> Groups with a positive Score Change are successfully adapting to the course materials. These instructors should be consulted to share their successful review strategies with the rest of the faculty!
</div>
""", unsafe_allow_html=True)

page_footer(logo_base64)
