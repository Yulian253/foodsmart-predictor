# -*- coding: utf-8 -*-
"""
Tema Dark Profesional — FoodSmart Predictor
Basado en el diseño original de PredictaVentas La 22
"""

DARK_THEME_CSS = """
<style>
    /* ── BASE ────────────────────────────────────────────────────── */
    .stApp {
        background-color: #0f1117 !important;
        color: #e0e0e0 !important;
    }
    
    .main .block-container {
        padding-top: 1rem;
        max-width: 1200px;
    }
    
    /* ── SIDEBAR ─────────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 1px solid #21262d !important;
    }
    [data-testid="stSidebar"] * {
        color: #c9d1d9 !important;
    }
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #2a9d8f !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: #21262d !important;
    }
    
    /* ── TYPOGRAPHY ──────────────────────────────────────────────── */
    h1, h2, h3, h4, h5, h6 {
        color: #e6edf3 !important;
    }
    p, span, label, .stMarkdown {
        color: #c9d1d9 !important;
    }
    
    /* ── HEADER BANNER ───────────────────────────────────────────── */
    .page-header {
        background: linear-gradient(135deg, #161b22 0%, #1c2333 100%);
        border: 1px solid #21262d;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .page-header h2 {
        margin: 0 !important;
        font-size: 1.4rem !important;
        color: #e6edf3 !important;
        font-weight: 700;
    }
    .page-header p {
        margin: 0.2rem 0 0 !important;
        color: #8b949e !important;
        font-size: 0.9rem;
    }
    
    /* ── STATUS BAR (green top bar) ──────────────────────────────── */
    .status-bar {
        background: linear-gradient(90deg, #1a3a2a 0%, #0d2818 100%);
        border: 1px solid #238636;
        border-radius: 8px;
        padding: 0.7rem 1.2rem;
        margin-bottom: 1.2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 0.9rem;
    }
    .status-bar .status-dot {
        width: 8px; height: 8px;
        background: #3fb950;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
    }
    .status-bar .status-badge {
        background: #238636;
        color: #ffffff;
        padding: 0.2rem 0.7rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .status-bar .status-info {
        color: #8b949e;
        font-size: 0.85rem;
    }
    
    /* ── KPI CARDS ───────────────────────────────────────────────── */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .kpi-card {
        background: #161b22;
        border: 1px solid #21262d;
        border-radius: 10px;
        padding: 1.2rem;
        position: relative;
        overflow: hidden;
    }
    .kpi-card .kpi-icon {
        position: absolute;
        top: 1rem;
        right: 1rem;
        font-size: 1.5rem;
        opacity: 0.5;
    }
    .kpi-card .kpi-label {
        font-size: 0.85rem;
        color: #8b949e;
        margin-bottom: 0.3rem;
        font-weight: 500;
    }
    .kpi-card .kpi-value {
        font-size: 2rem;
        font-weight: 800;
        margin: 0.2rem 0;
        line-height: 1;
    }
    .kpi-card .kpi-sub {
        font-size: 0.8rem;
        color: #8b949e;
        margin-top: 0.3rem;
    }
    .kpi-value.green { color: #3fb950; }
    .kpi-value.teal { color: #2a9d8f; }
    .kpi-value.orange { color: #e76f51; }
    .kpi-value.gold { color: #e9c46a; }
    .kpi-value.blue { color: #58a6ff; }
    .kpi-value.red { color: #e63946; }
    .kpi-value.white { color: #e6edf3; }
    
    /* ── SECTION CARDS ───────────────────────────────────────────── */
    .section-card {
        background: #161b22;
        border: 1px solid #21262d;
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
    }
    .section-card h3, .section-card h4 {
        color: #e6edf3 !important;
        margin-top: 0 !important;
    }
    .section-card p {
        color: #8b949e !important;
    }
    
    /* ── CATEGORY HEADERS ────────────────────────────────────────── */
    .cat-header {
        background: linear-gradient(90deg, #21262d 0%, transparent 100%);
        border-left: 4px solid #2a9d8f;
        padding: 0.6rem 1rem;
        border-radius: 0 8px 8px 0;
        font-weight: 700;
        color: #e6edf3 !important;
        font-size: 1rem;
        margin: 1rem 0 0.5rem;
    }
    
    /* ── PLATO CARDS (prediction results) ────────────────────────── */
    .plato-row {
        background: #161b22;
        border: 1px solid #21262d;
        border-radius: 8px;
        padding: 0.7rem 1rem;
        margin-bottom: 0.4rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: border-color 0.2s;
    }
    .plato-row:hover {
        border-color: #2a9d8f;
    }
    .plato-row .plato-name {
        font-weight: 600;
        color: #e6edf3;
        font-size: 0.95rem;
    }
    .plato-row .plato-price {
        color: #8b949e;
        font-size: 0.8rem;
        margin-left: 8px;
    }
    .plato-row .plato-qty {
        background: #1a3a2a;
        border: 1px solid #238636;
        color: #3fb950;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 1rem;
    }
    .plato-row .plato-income {
        color: #8b949e;
        font-size: 0.85rem;
        margin-right: 12px;
    }

    /* ── TOTAL CARDS ─────────────────────────────────────────────── */
    .total-card {
        background: linear-gradient(135deg, #1a3a2a 0%, #0d2818 100%);
        border: 1px solid #238636;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
    }
    .total-card .total-label {
        color: #8b949e;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .total-card .total-value {
        color: #3fb950;
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0.3rem 0;
    }
    .total-card .total-sub {
        color: #8b949e;
        font-size: 0.85rem;
    }
    .total-card.alt {
        background: linear-gradient(135deg, #1c2333 0%, #161b22 100%);
        border-color: #2a9d8f;
    }
    .total-card.alt .total-value { color: #2a9d8f; }
    .total-card.warn {
        background: linear-gradient(135deg, #3d2e1a 0%, #2d1f0f 100%);
        border-color: #e9c46a;
    }
    .total-card.warn .total-value { color: #e9c46a; }
    
    /* ── METRIC CARDS (ML metrics) ───────────────────────────────── */
    .metric-card {
        background: #161b22;
        border: 1px solid #21262d;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
        position: relative;
    }
    .metric-card .metric-topbar {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        border-radius: 10px 10px 0 0;
    }
    .metric-card .metric-label {
        color: #8b949e;
        font-size: 0.85rem;
        margin-bottom: 0.3rem;
    }
    .metric-card .metric-value {
        font-size: 2rem;
        font-weight: 800;
        margin: 0.2rem 0;
    }
    .metric-card .metric-desc {
        color: #8b949e;
        font-size: 0.8rem;
    }
    
    /* ── ALERTS ──────────────────────────────────────────────────── */
    .alert-item {
        background: #161b22;
        border: 1px solid #21262d;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
    }
    .alert-item.unread { border-left: 4px solid #e63946; }
    .alert-item.success-a { border-left: 4px solid #3fb950; }
    .alert-item.warning-a { border-left: 4px solid #e9c46a; }
    .alert-item.info-a { border-left: 4px solid #58a6ff; }
    .alert-badge {
        display: inline-block;
        padding: 0.15rem 0.5rem;
        border-radius: 10px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    .badge-success { background: #1a3a2a; color: #3fb950; }
    .badge-warning { background: #3d2e1a; color: #e9c46a; }
    .badge-danger { background: #3a1a1a; color: #e63946; }
    .badge-info { background: #1a2a3a; color: #58a6ff; }
    
    /* ── FORM INPUTS ─────────────────────────────────────────────── */
    .stNumberInput > div > div > input,
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stDateInput > div > div > input {
        background-color: #0d1117 !important;
        border-color: #21262d !important;
        color: #e6edf3 !important;
    }
    .stNumberInput label, .stTextInput label, 
    .stSelectbox label, .stDateInput label {
        color: #c9d1d9 !important;
    }
    
    /* ── BUTTONS ──────────────────────────────────────────────────── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #238636 0%, #2a9d8f 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.5rem !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #2ea043 0%, #33b8a8 100%) !important;
    }
    
    /* ── TABLES ───────────────────────────────────────────────────── */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* ── TABS ─────────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        background: #161b22;
        border-radius: 8px;
        padding: 0.3rem;
        gap: 0.3rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        color: #8b949e;
    }
    .stTabs [aria-selected="true"] {
        background: #21262d !important;
        color: #e6edf3 !important;
    }
    
    /* ── DIVIDERS ─────────────────────────────────────────────────── */
    hr {
        border-color: #21262d !important;
    }
    
    /* ── PLOTLY OVERRIDES ─────────────────────────────────────────── */
    .js-plotly-plot .plotly .modebar {
        background: transparent !important;
    }

    /* ── SIDEBAR LOGO ────────────────────────────────────────────── */
    .sidebar-brand {
        padding: 0.5rem 0 1rem;
        border-bottom: 1px solid #21262d;
        margin-bottom: 1rem;
    }
    .sidebar-brand h2 {
        color: #e6edf3 !important;
        font-size: 1.15rem !important;
        margin: 0 !important;
        font-weight: 700;
    }
    .sidebar-brand p {
        color: #2a9d8f !important;
        font-size: 0.85rem !important;
        margin: 0.2rem 0 0 !important;
    }
    
    /* ── MODEL BADGE ─────────────────────────────────────────────── */
    .model-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .model-active {
        background: #1a3a2a;
        color: #3fb950;
        border: 1px solid #238636;
    }
    .model-inactive {
        background: #3a1a1a;
        color: #e63946;
        border: 1px solid #e63946;
    }

    /* ── REGISTRATION FORM ───────────────────────────────────────── */
    .reg-plate-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 0.8rem;
        margin-bottom: 1rem;
    }
    .reg-plate-item {
        background: #0d1117;
        border: 1px solid #21262d;
        border-radius: 8px;
        padding: 0.8rem;
        transition: border-color 0.2s;
    }
    .reg-plate-item:hover {
        border-color: #2a9d8f;
    }
    .reg-plate-name {
        color: #e6edf3;
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 0.2rem;
    }
    .reg-plate-price {
        color: #8b949e;
        font-size: 0.75rem;
    }
    .reg-plate-pred {
        color: #2a9d8f;
        font-size: 0.75rem;
        font-style: italic;
    }

    /* ── INFO BOXES ──────────────────────────────────────────────── */
    .stAlert, [data-testid="stAlert"] {
        background-color: #161b22 !important;
        border: 1px solid #21262d !important;
        color: #c9d1d9 !important;
    }
    
    /* ── PROGRESS BAR ────────────────────────────────────────────── */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #238636, #2a9d8f) !important;
    }

    /* ── DOWNLOAD BUTTON ─────────────────────────────────────────── */
    .stDownloadButton > button {
        background: #21262d !important;
        color: #c9d1d9 !important;
        border: 1px solid #30363d !important;
    }

    /* ── RADIO / CHECKBOX ────────────────────────────────────────── */
    .stRadio > div {
        background: #161b22;
        border-radius: 8px;
        padding: 0.5rem;
    }
</style>
"""

# Plotly dark theme settings
PLOTLY_LAYOUT = dict(
    plot_bgcolor="#161b22",
    paper_bgcolor="#161b22",
    font=dict(color="#c9d1d9", family="Calibri"),
    margin=dict(l=20, r=20, t=30, b=20),
    xaxis=dict(gridcolor="#21262d", linecolor="#21262d"),
    yaxis=dict(gridcolor="#21262d", linecolor="#21262d"),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(color="#c9d1d9"),
    ),
)

CHART_COLORS = ["#2a9d8f", "#e9c46a", "#e76f51", "#264653", "#3fb950", "#58a6ff", "#e63946"]

def apply_plotly_dark(fig):
    """Aplica tema dark a una figura Plotly."""
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_xaxes(gridcolor="#21262d", linecolor="#21262d")
    fig.update_yaxes(gridcolor="#21262d", linecolor="#21262d")
    return fig
