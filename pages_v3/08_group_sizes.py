import streamlit as st
import pandas as pd
import plotly.express as px
from utils.components import page_header, page_footer, get_base64_image

logo_base64 = get_base64_image("kayfa logo.svg")

page_header(logo_base64, "Group Sizes & Discrepancies")

st.markdown("<h2 class='page-header'>🔎 Group Size Discrepancies</h2>", unsafe_allow_html=True)

if "filtered_data" not in st.session_state:
    st.warning("No data found. Please check filters in the sidebar.")
    st.stop()

# Pull precomputed aggregations from the snapshot saved by save_dashboard_state()
snapshot = st.session_state.get("snapshot", {})
agg = snapshot.get("agg", {}) if snapshot else {}

discrepancy_records = agg.get("group_discrepancies", [])
df_discrepancy = pd.DataFrame(discrepancy_records) if discrepancy_records else pd.DataFrame()

if df_discrepancy.empty:
    st.info("No group discrepancy data available. Try refreshing filters.")
else:
    st.markdown("**Stated vs. Actual Group Sizes**")
    st.write("Comparing the self-reported (stated) number of students in each group with the true count calculated from the active student database.")
    
    # We melt the dataframe to make a grouped bar chart
    df_melted = df_discrepancy.melt(
        id_vars=["group_id", "group_name"],
        value_vars=["stated_num_students", "student_count"],
        var_name="Metric",
        value_name="Count"
    )
    
    # Rename for the legend
    df_melted["Metric"] = df_melted["Metric"].replace({
        "stated_num_students": "Stated (Self-Reported)",
        "student_count": "Actual (True Count)"
    })
    
    # Grouped Bar Chart
    fig = px.bar(
        df_melted, 
        x="group_id", 
        y="Count", 
        color="Metric",
        barmode="group",
        title="Group Capacities: Stated vs Actual",
        labels={"group_id": "Group ID"},
        color_discrete_sequence=["#95a5a6", "#3498db"],
        text="Count",
    )
    fig.update_traces(texttemplate="%{text}", textposition="outside")
    fig.update_layout(legend_title_text="", uniformtext_minsize=8, uniformtext_mode="hide")
    st.plotly_chart(fig, use_container_width=True)

    

st.markdown('<div class="section-title" style="font-size: 1.5rem; margin-top: 2rem;">💡 Strategic Insights</div>', unsafe_allow_html=True)
st.markdown("""
<div class="section-sub" style="line-height: 1.6;">
• <b>"Ghost Students" Flagged:</b> Several groups (notably G05, G03, and G07) report significantly higher student counts than what exists in the active database (e.g., G05 reports 76 but only has 46 actual students). This negative discrepancy creates "ghost students".<br>
• <b>Administrative Action:</b> These discrepancies artificially inflate reported enrollments and can misalign resource allocation. Instructors for the flagged groups should be investigated to reconcile their rosters, as this could be an indicator of students dropping out without being formally unregistered.
</div>
""", unsafe_allow_html=True)

page_footer(logo_base64)
