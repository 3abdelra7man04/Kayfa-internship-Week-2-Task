import streamlit as st
import os
import base64
import plotly.express as px

def get_base64_image(image_path):
    if not os.path.exists(image_path):
        for ext in ['.png', '.jpg', '.jpeg', '.svg']:
            if os.path.exists(image_path + ext):
                image_path = image_path + ext
                break
    try:
        with open(image_path, "rb") as img_file:
            mime_type = "image/svg+xml" if image_path.lower().endswith(".svg") else "image/png"
            return f"data:{mime_type};base64,{base64.b64encode(img_file.read()).decode()}"
    except FileNotFoundError:
        return ""

def kpi(col, label, value, delta_html, accent):
    col.markdown(f"""
    <div class="kpi-card kpi-accent-{accent}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div>{delta_html}</div>
    </div>
    """, unsafe_allow_html=True)

def page_header(logo_b64, subtitle):
    st.markdown(f"""
    <div class="kayfa-header" style="padding: 32px 36px;">
        <div style="display: flex; align-items: center; gap: 24px;">
            <img src="{logo_b64}" style="height: 95px; width: auto; object-fit: contain;" alt="Kayfa Logo">
            <div style="border-left: 1px solid var(--sidebar-border); padding-left: 24px;">
                <div class="kayfa-tagline" style="font-size: 1.25rem; color: var(--text-color); font-weight: 600; margin-bottom: 4px;">Week #2 Task</div>
                <div style="font-size: 0.85rem; color: var(--tagline-color); font-weight: 300; letter-spacing: 0.3px;">{subtitle}</div>
            </div>
        </div>
        <div style="flex:1"></div>
        <div style="text-align:right">
            <div style="font-size:0.72rem;color:var(--tagline-color);">Last Updated</div>
            <div style="font-size:0.88rem;color:var(--text-color);font-weight:500;">June 2026</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def page_footer(logo_b64):
    st.markdown(f"""
    <div style="text-align:center;padding:25px 0 12px;color:var(--tagline-color);font-size:0.75rem; display:flex; align-items:center; justify-content:center; gap:10px;">
        <img src="{logo_b64}" style="height: 24px; width: auto; object-fit: contain;" alt="Kayfa Logo">
        <span>· E-Learning Ed-Tech Platform · Academic Exploratory Analysis · © 2026 Kayfa Inc.</span>
    </div>
    """, unsafe_allow_html=True)

def bar_with_labels(df_plot, x, y, title, x_label, y_label):
    fig = px.bar(df_plot, x=x, y=y, title=title, labels={x: x_label, y: y_label})
    fig.update_traces(
        text=df_plot[y],
        texttemplate='%{text:.1f}%',
        textposition='outside'
    )
    return fig
