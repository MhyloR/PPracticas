# core/styles.py
import streamlit as st

def inject_css():
    ACCENT      = "#571D92"
    SIDEBAR_BG  = "#6D59D1FF"
    APP_BG      = "#E6E6E6"
    PANEL_BG    = "#00966C"
    TEXT        = "#E7E9EE"
    TEXT_DARK   = "#000000"
    MUTED       = "#9AA0AA"
    RADIUS      = "12px"

    INPUT_BG    = "#FFFFFF"
    INPUT_TEXT  = "#111827"
    INPUT_BORDER= "#D1D5DB"
    INPUT_FOCUS = "#6366F1"

    SPACE_XS="6px"; SPACE_S="10px"; SPACE_M="16px"; SPACE_L="20px"; SPACE_XL="28px"

    st.markdown(f"""
    <style>
    :root {{
      --accent:{ACCENT}; --sidebar-bg:{SIDEBAR_BG}; --app-bg:{APP_BG}; --panel-bg:{PANEL_BG};
      --text:{TEXT}; --text-dark:{TEXT_DARK}; --muted:{MUTED}; --radius:{RADIUS};
      --xs:{SPACE_XS}; --s:{SPACE_S}; --m:{SPACE_M}; --l:{SPACE_L}; --xl:{SPACE_XL};
      --input-bg:{INPUT_BG}; --input-text:{INPUT_TEXT}; --input-border:{INPUT_BORDER}; --input-focus:{INPUT_FOCUS};
    }}

    [data-testid="stAppViewContainer"]{{ background-color: var(--app-bg); }}
    .main .block-container{{ padding: var(--l) !important; }}

    [data-testid="stSidebar"]{{ background-color: var(--sidebar-bg) !important; padding: var(--l) var(--m) !important; }}
    [data-testid="stSidebar"] *{{ color:#FFFFFF !important; }}
    [data-testid="stSidebar"] .stTextInput>div>div>input,
    [data-testid="stSidebar"] .stSelectbox>div>div>div,
    [data-testid="stSidebar"] .stDateInput>div>div>input{{ background-color:#FFFFFF !important; color:#000 !important; border-radius:6px; }}
    [data-testid="stSidebar"] button[kind="secondary"]{{ color:var(--sidebar-bg) !important; background-color:#FFFFFF !important; border:1px solid #FFFFFF33 !important; border-radius:8px; }}
    [data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3{{ color:#FFFFFF !important; margin:var(--m) 0; }}

    .app-header{{ background-color:#5b1fa6; padding:var(--m); border-radius:8px; color:#FFFFFF; text-align:center; font-size:20px; font-weight:800; margin:0 0 var(--l) 0; }}
    .section-title{{ font-weight:700; font-size:28px; color:var(--accent); margin:0 0 var(--s) 0; }}
    .card{{ border:3px solid var(--accent); background-color:#F4F3FA; border-radius:var(--radius); padding:var(--l); min-height:300px; margin:0; }}
    .card h3{{ color:var(--accent); margin:0 0 var(--s) 0; }}
    .card p{{ color:var(--text-dark); margin:0; }}

    .st-key-filtro{{ border-radius:var(--radius); background:var(--panel-bg); padding:var(--m) var(--l); box-sizing:border-box; margin:0; }}
    .st-key-filtro h3{{ margin:0 0 var(--s) 0; font-weight:800; color:var(--text); letter-spacing:.2px; }}
    .st-key-filtro .stRadio div[role="radiogroup"]>label{{ display:grid; grid-template-columns:18px 1fr; align-items:center; column-gap:10px; padding:6px 4px; border-radius:8px; line-height:1.25; color:var(--text); }}
    .st-key-filtro .stRadio div[role="radiogroup"]>label:hover{{ background:rgba(255,255,255,0.06); }}
    .st-key-filtro .muted{{ color:var(--muted); font-size:.9rem; margin-top:var(--s); }}

    .css-ocqkz7, .css-1kyxreq{{ gap:var(--l) !important; }}

    /* DateInput: campo */
    [data-testid="stDateInput"] [data-baseweb="input"]{{
      background: var(--input-bg) !important; border: none !important; box-shadow: none !important; border-radius: 10px !important;
    }}
    [data-testid="stDateInput"] input{{
      background: var(--input-bg) !important; color: var(--input-text) !important; border: 1px solid var(--input-border) !important;
      border-radius: 10px !important; padding: 10px 14px !important; box-shadow: none !important;
    }}
    [data-testid="stDateInput"] [data-baseweb="input"]:focus-within,
    [data-testid="stDateInput"] input:focus{{
      border-color: var(--input-focus) !important; box-shadow: 0 0 0 3px rgba(99,102,241,.25) !important; outline: none !important;
    }}
    [data-testid="stDateInput"] svg{{ color: var(--input-focus) !important; }}

    /* TextInput en contenido principal */
    div[data-testid="stAppViewContainer"] .stTextInput > div > div > input {{
      background: var(--input-bg) !important; color: var(--input-text) !important; border: 1px solid var(--input-border) !important;
      border-radius: 10px !important; padding: 10px 14px !important; box-shadow: none !important;
    }}
    div[data-testid="stAppViewContainer"] .stTextInput [data-baseweb="input"] {{
      background: var(--input-bg) !important; border: none !important; box-shadow: none !important; border-radius: 10px !important;
    }}

    /* Selectbox (cerrado) */
    div[data-testid="stAppViewContainer"] .stSelectbox > div > div {{
      background: var(--input-bg) !important; color: var(--input-text) !important; border: 1px solid var(--input-border) !important;
      border-radius: 10px !important; box-shadow: none !important;
    }}
    div[data-testid="stAppViewContainer"] .stSelectbox [data-baseweb="select"] {{
      background: var(--input-bg) !important; border: none !important; box-shadow: none !important; border-radius: 10px !important;
    }}
    div[data-testid="stAppViewContainer"] .stSelectbox [data-baseweb="select"]:focus-within {{
      border-color: var(--input-focus) !important; box-shadow: 0 0 0 3px rgba(99,102,241,.25) !important;
    }}
    div[data-testid="stAppViewContainer"] .stSelectbox svg {{ color: var(--input-focus) !important; }}

    /* Placeholders legibles */
    div[data-testid="stAppViewContainer"] .stTextInput input::placeholder {{ color: var(--text-dark) !important; opacity: 0.75 !important; }}

    /* Botones */
    div[data-testid="stAppViewContainer"] .stButton > button {{
      background: var(--accent) !important; color: #FFFFFF !important; border: 1px solid rgba(0,0,0,0.08) !important;
      border-radius: 10px !important; padding: 10px 16px !important; box-shadow: none !important;
      transition: background .15s ease, box-shadow .15s ease, transform .02s ease;
    }}
    div[data-testid="stAppViewContainer"] .stButton > button:hover:enabled {{ background: #4d1a84 !important; box-shadow: 0 2px 6px rgba(0,0,0,.12) !important; }}
    div[data-testid="stAppViewContainer"] .stButton > button:active:enabled {{ background: #431671 !important; transform: translateY(.5px); }}
    div[data-testid="stAppViewContainer"] .stButton > button:disabled {{ background: #E5E7EB !important; color: #9AA0AA !important; border-color: #E5E7EB !important; }}
    div[data-testid="stAppViewContainer"] .stButton > button:focus-visible {{
      outline: none !important; box-shadow: 0 0 0 3px rgba(99,102,241,.25) !important;
    }}
    </style>
    """, unsafe_allow_html=True)