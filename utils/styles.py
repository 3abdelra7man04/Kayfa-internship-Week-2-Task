import streamlit as st

CUSTOM_CSS_TEMPLATE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

    /* Remove .stApp hardcoded background so Streamlit handles it natively */
    
    [data-testid="stSidebar"] {
        /* Remove hardcoded background so Streamlit handles it natively */
        border-right: 1px solid rgba(128, 128, 128, 0.2);
    }
    
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 { color: var(--text-color); }

    .kayfa-header {
        background: linear-gradient(135deg, var(--secondary-background-color) 0%, var(--background-color) 100%);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 16px;
        margin-bottom: 28px;
        display: flex;
        align-items: center;
        gap: 20px;
    }
    .kayfa-tagline { font-size: 0.9rem; color: var(--text-color); opacity: 0.7; font-weight: 300; letter-spacing: 0.5px; }

    .kpi-card {
        background: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 14px;
        padding: 22px 24px;
        transition: border-color 0.2s;
    }
    .kpi-card:hover { border-color: var(--primary-color); }
    .kpi-label { font-size: 0.75rem; color: var(--text-color); opacity: 0.7; text-transform: uppercase; letter-spacing: 1px; font-weight: 500; margin-bottom: 8px; }
    .kpi-value { font-family: 'Syne', sans-serif; font-size: 2rem; font-weight: 700; color: var(--text-color); line-height: 1; }
    .kpi-delta-pos { font-size: 0.8rem; color: #2da44e; margin-top: 6px; }
    .kpi-delta-neg { font-size: 0.8rem; color: #cf222e; margin-top: 6px; }
    .kpi-accent-blue   { border-top: 3px solid #58a6ff; }
    .kpi-accent-green  { border-top: 3px solid #3fb950; }
    .kpi-accent-red    { border-top: 3px solid #f85149; }
    .kpi-accent-purple { border-top: 3px solid #bc8cff; }

    .section-title {
        font-family: 'Syne', sans-serif;
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-color);
        letter-spacing: -0.3px;
        margin-bottom: 4px;
    }
    .section-sub { font-size: 0.8rem; color: var(--text-color); opacity: 0.7; margin-bottom: 16px; }

    .chart-box { background: var(--secondary-background-color); border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 14px; padding: 20px; }

    .sidebar-section {
        font-family: 'Syne', sans-serif;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: var(--primary-color);
        font-weight: 700;
        margin: 20px 0 8px;
    }

    .js-plotly-plot .plotly .main-svg { background: transparent !important; }

    hr { border-color: rgba(128, 128, 128, 0.2); }
    .stDataFrame { border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 10px; overflow: hidden; }
</style>
"""

def apply_styles():
    st.markdown(CUSTOM_CSS_TEMPLATE, unsafe_allow_html=True)

def get_plotly_colors():
    return ["#f85149", "#3fb950"] # Standard red/green

