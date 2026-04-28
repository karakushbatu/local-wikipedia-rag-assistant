import streamlit as st

GOOGLE_FONTS_IMPORT = """
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&family=JetBrains+Mono:wght@400;500&display=swap');
"""

GLOBAL_CSS = """
:root {
  /* Refined dark palette — warm-tinted, not cold blue-black */
  --bg-primary:     #0D0D10;
  --bg-secondary:   #13131A;
  --bg-tertiary:    #1C1C26;
  --bg-elevated:    #22222E;
  --bg-hover:       #262634;

  /* Borders — warm-tinted gray family */
  --border-subtle:  #252530;
  --border-mid:     #32323F;
  --border-accent:  #45455A;

  /* Text — warm off-white, not cold */
  --text-primary:   #EEEEF5;
  --text-secondary: #8A8AA0;
  --text-tertiary:  #52526A;
  --text-muted:     #383848;

  /* Single accent — desaturated steel blue, not screaming */
  --accent:         #6B8FD4;
  --accent-dim:     rgba(107, 143, 212, 0.12);
  --accent-glow:    rgba(107, 143, 212, 0.20);
  --accent-border:  rgba(107, 143, 212, 0.35);

  /* Semantic colors */
  --success:        #4ADE80;
  --success-dim:    rgba(74, 222, 128, 0.12);
  --warning:        #FBBF24;
  --warning-dim:    rgba(251, 191, 36, 0.12);
  --danger:         #F87171;
  --danger-dim:     rgba(248, 113, 113, 0.12);
  --info:           #67E8F9;
  --info-dim:       rgba(103, 232, 249, 0.12);

  /* Shadows — tinted to match background hue */
  --shadow-sm:  0 1px 3px rgba(0, 0, 8, 0.4);
  --shadow-md:  0 4px 16px rgba(0, 0, 8, 0.5);
  --shadow-lg:  0 8px 32px rgba(0, 0, 8, 0.6);
  --shadow-accent: 0 4px 20px rgba(107, 143, 212, 0.18);
}

/* ── Noise overlay for texture ── */
body::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
  pointer-events: none;
  z-index: 9999;
  opacity: 0.6;
}

/* ── Hide Streamlit chrome — do NOT touch header or sidebar toggle ── */
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
.stDeployButton { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

/* Style header bar background only — never hide it */
header[data-testid="stHeader"] {
  background-color: var(--bg-primary) !important;
  border-bottom: 1px solid var(--border-subtle) !important;
}

/* ── Global ── */
html, body {
  background-color: var(--bg-primary) !important;
  color: var(--text-primary) !important;
  font-family: 'DM Sans', sans-serif !important;
  -webkit-font-smoothing: antialiased;
  scroll-behavior: smooth;
}

[data-testid="stAppViewContainer"], .main {
  background-color: var(--bg-primary) !important;
}

.block-container {
  background-color: var(--bg-primary) !important;
  color: var(--text-primary) !important;
  font-family: 'DM Sans', sans-serif !important;
  padding-top: 2rem !important;
  padding-bottom: 3rem !important;
  max-width: 920px !important;
}

/* ── Typography ── */
h1, h2, h3, h4, h5 {
  font-family: 'Outfit', sans-serif !important;
  color: var(--text-primary) !important;
  letter-spacing: -0.02em;
  text-wrap: balance;
}

p {
  line-height: 1.7;
  text-wrap: pretty;
}

code, pre {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 13px !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background-color: var(--bg-secondary) !important;
  border-right: 1px solid var(--border-subtle) !important;
}

[data-testid="stSidebar"] > div {
  background-color: var(--bg-secondary) !important;
}

[data-testid="stSidebar"] .block-container {
  max-width: 100% !important;
  padding: 1.5rem 1rem !important;
  background-color: var(--bg-secondary) !important;
}

[data-testid="stSidebarContent"] {
  background-color: var(--bg-secondary) !important;
}

/* ── Buttons ── */
.stButton > button {
  background-color: var(--bg-tertiary) !important;
  border: 1px solid var(--border-mid) !important;
  color: var(--text-secondary) !important;
  border-radius: 8px !important;
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 500 !important;
  font-size: 13px !important;
  letter-spacing: 0.01em;
  transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1) !important;
  box-shadow: var(--shadow-sm) !important;
}

.stButton > button:hover {
  background-color: var(--bg-elevated) !important;
  border-color: var(--accent-border) !important;
  color: var(--text-primary) !important;
  transform: translateY(-1px) !important;
  box-shadow: var(--shadow-accent) !important;
}

.stButton > button:active {
  transform: translateY(0px) scale(0.98) !important;
}

.stButton > button[kind="primary"] {
  background-color: var(--accent) !important;
  border-color: var(--accent) !important;
  color: #fff !important;
  box-shadow: 0 2px 12px rgba(107, 143, 212, 0.35) !important;
}

.stButton > button[kind="primary"]:hover {
  background-color: #7FA0E0 !important;
  box-shadow: 0 4px 20px rgba(107, 143, 212, 0.45) !important;
}

/* ── Text inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
  background-color: var(--bg-tertiary) !important;
  border: 1px solid var(--border-mid) !important;
  border-radius: 10px !important;
  color: var(--text-primary) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 14px !important;
  box-shadow: var(--shadow-sm) !important;
  transition: border-color 0.18s ease, box-shadow 0.18s ease !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px var(--accent-glow) !important;
  outline: none !important;
}

/* ── Chat input — premium floating bar ── */
[data-testid="stChatInput"] {
  background: transparent !important;
  border: none !important;
  padding: 16px 0 8px !important;
}

[data-testid="stChatInput"] > div {
  background: var(--bg-secondary) !important;
  border: 1px solid var(--border-mid) !important;
  border-radius: 16px !important;
  box-shadow: 0 4px 24px rgba(0,0,8,0.5), 0 0 0 1px var(--border-subtle) !important;
  transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
  overflow: hidden !important;
}

[data-testid="stChatInput"] > div:focus-within {
  border-color: var(--accent-border) !important;
  box-shadow: 0 4px 24px rgba(0,0,8,0.5), 0 0 0 3px var(--accent-glow) !important;
}

[data-testid="stChatInput"] textarea {
  background-color: transparent !important;
  border: none !important;
  border-radius: 0 !important;
  color: var(--text-primary) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 15px !important;
  padding: 14px 16px !important;
  line-height: 1.5 !important;
  box-shadow: none !important;
}

[data-testid="stChatInput"] textarea::placeholder {
  color: var(--text-muted) !important;
  font-style: italic !important;
}

[data-testid="stChatInput"] textarea:focus {
  border: none !important;
  box-shadow: none !important;
  outline: none !important;
}

/* Send button inside chat input */
[data-testid="stChatInput"] button {
  background: var(--accent) !important;
  border: none !important;
  border-radius: 10px !important;
  margin: 8px 8px 8px 0 !important;
  width: 36px !important;
  height: 36px !important;
  transition: background 0.15s ease, transform 0.15s ease !important;
}

[data-testid="stChatInput"] button:hover {
  background: #7FA0E0 !important;
  transform: scale(1.05) !important;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
  animation: message-in 0.25s cubic-bezier(0.4, 0, 0.2, 1) forwards;
  margin-bottom: 4px !important;
}

/* Remove default Streamlit chat bubble backgrounds */
[data-testid="stChatMessage"] {
  background: transparent !important;
  border: none !important;
}

/* User message — right-aligned feel */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
  background-color: var(--bg-tertiary) !important;
  border: 1px solid var(--border-mid) !important;
  border-radius: 18px 18px 4px 18px !important;
  padding: 14px 18px !important;
  margin-left: 60px !important;
  margin-right: 0 !important;
  box-shadow: var(--shadow-sm) !important;
}

/* Assistant message — left accent stripe */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
  background: var(--bg-secondary) !important;
  border: 1px solid var(--border-subtle) !important;
  border-left: 2px solid var(--accent) !important;
  border-radius: 4px 18px 18px 18px !important;
  padding: 14px 18px !important;
  margin-right: 60px !important;
  margin-left: 0 !important;
  box-shadow: var(--shadow-md) !important;
}

/* Message text */
[data-testid="stChatMessage"] p {
  color: var(--text-primary) !important;
  font-size: 14px !important;
  line-height: 1.7 !important;
  margin: 0 !important;
}

/* Avatar */
[data-testid="stChatMessageAvatarUser"],
[data-testid="stChatMessageAvatarAssistant"] {
  width: 28px !important;
  height: 28px !important;
  border-radius: 8px !important;
  font-size: 14px !important;
}

/* ── Expander ── */
details, [data-testid="stExpander"] {
  background-color: var(--bg-secondary) !important;
  border: 1px solid var(--border-subtle) !important;
  border-radius: 10px !important;
  overflow: hidden !important;
}

details summary, .streamlit-expanderHeader {
  background-color: var(--bg-secondary) !important;
  color: var(--text-secondary) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  padding: 12px 16px !important;
  border-radius: 10px !important;
  cursor: pointer !important;
  transition: color 0.15s ease !important;
}

details summary:hover, .streamlit-expanderHeader:hover {
  color: var(--text-primary) !important;
}

.streamlit-expanderContent {
  background-color: var(--bg-secondary) !important;
  border-top: 1px solid var(--border-subtle) !important;
  padding: 12px 16px !important;
}

/* ── Progress bar ── */
.stProgress > div > div > div {
  background: linear-gradient(90deg, var(--accent), #9BB5E8) !important;
  border-radius: 9999px !important;
}

.stProgress > div > div {
  background-color: var(--bg-tertiary) !important;
  border-radius: 9999px !important;
  height: 6px !important;
}

/* ── Radio ── */
.stRadio > div {
  background-color: transparent !important;
  gap: 4px !important;
}

.stRadio label {
  color: var(--text-secondary) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 14px !important;
  transition: color 0.15s ease !important;
}

.stRadio label:hover {
  color: var(--text-primary) !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
  background-color: var(--bg-tertiary) !important;
  border: 1px solid var(--border-mid) !important;
  border-radius: 8px !important;
  color: var(--text-primary) !important;
}

/* ── Slider ── */
.stSlider > div > div > div > div {
  background-color: var(--accent) !important;
}

.stSlider [data-testid="stTickBarMin"],
.stSlider [data-testid="stTickBarMax"] {
  color: var(--text-tertiary) !important;
  font-size: 11px !important;
}

/* ── Metric ── */
[data-testid="stMetric"] {
  background-color: var(--bg-tertiary) !important;
  border: 1px solid var(--border-subtle) !important;
  border-radius: 12px !important;
  padding: 16px !important;
  box-shadow: var(--shadow-sm) !important;
}

[data-testid="stMetricLabel"] {
  color: var(--text-tertiary) !important;
  font-size: 12px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
}

[data-testid="stMetricValue"] {
  color: var(--text-primary) !important;
  font-family: 'Outfit', sans-serif !important;
  font-weight: 700 !important;
}

/* ── Divider ── */
hr {
  border: none !important;
  border-top: 1px solid var(--border-subtle) !important;
  margin: 16px 0 !important;
}

/* ── Checkbox ── */
.stCheckbox label {
  color: var(--text-secondary) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 13px !important;
}

/* ── Alert/info boxes ── */
.stAlert {
  background-color: var(--bg-tertiary) !important;
  border: 1px solid var(--border-mid) !important;
  border-radius: 10px !important;
  color: var(--text-secondary) !important;
}

/* ── Spinner ── */
.stSpinner > div {
  border-color: var(--accent) transparent transparent transparent !important;
}

/* ── Columns gap ── */
[data-testid="column"] {
  padding: 0 8px !important;
}

/* ── Animations ── */
@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.4; transform: scale(0.8); }
}

@keyframes pulse-ring {
  0%   { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.4); }
  70%  { box-shadow: 0 0 0 6px rgba(74, 222, 128, 0); }
  100% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0); }
}

@keyframes message-in {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes thinking {
  0%, 80%, 100% { transform: scale(0.4); opacity: 0.2; }
  40%           { transform: scale(1);   opacity: 1; }
}

@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}

@keyframes flow {
  0%   { opacity: 0.2; transform: translateX(-4px); }
  50%  { opacity: 1;   transform: translateX(0); }
  100% { opacity: 0.2; transform: translateX(4px); }
}

@keyframes glow-pulse {
  0%, 100% { box-shadow: 0 0 8px rgba(107, 143, 212, 0.2); }
  50%       { box-shadow: 0 0 20px rgba(107, 143, 212, 0.4); }
}

/* ── Sidebar quick question buttons — compact style ── */
[data-testid="stSidebar"] .stButton > button {
  background-color: transparent !important;
  border: 1px solid var(--border-subtle) !important;
  color: var(--text-tertiary) !important;
  border-radius: 6px !important;
  font-size: 12px !important;
  padding: 4px 10px !important;
  text-align: left !important;
  justify-content: flex-start !important;
  font-weight: 400 !important;
  height: auto !important;
  min-height: 0 !important;
  line-height: 1.4 !important;
  white-space: normal !important;
}

[data-testid="stSidebar"] .stButton > button:hover {
  background-color: var(--bg-tertiary) !important;
  border-color: var(--accent-border) !important;
  color: var(--text-primary) !important;
  transform: none !important;
  box-shadow: none !important;
}

/* Sidebar expanders */
[data-testid="stSidebar"] details {
  background-color: var(--bg-tertiary) !important;
  border: 1px solid var(--border-subtle) !important;
  border-radius: 8px !important;
  margin-bottom: 6px !important;
}

[data-testid="stSidebar"] details summary {
  font-size: 12px !important;
  font-weight: 600 !important;
  color: var(--text-secondary) !important;
  padding: 8px 12px !important;
  border-radius: 8px !important;
}

[data-testid="stSidebar"] details[open] summary {
  border-bottom: 1px solid var(--border-subtle) !important;
  border-radius: 8px 8px 0 0 !important;
}

/* ── Focus ring ── */
:focus-visible {
  outline: 2px solid var(--accent) !important;
  outline-offset: 2px !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-mid); border-radius: 9999px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

/* ── Selection ── */
::selection {
  background: var(--accent-dim);
  color: var(--text-primary);
}
"""


def apply_styles() -> None:
    """Inject global CSS into every Streamlit page."""
    st.markdown(
        f"<style>{GOOGLE_FONTS_IMPORT}{GLOBAL_CSS}</style>",
        unsafe_allow_html=True,
    )


def card(content: str, variant: str = "default") -> str:
    """Return HTML for a styled card component."""
    borders = {
        "default": "var(--border-subtle)",
        "accent":  "var(--accent)",
        "success": "var(--success)",
        "error":   "var(--danger)",
        "warning": "var(--warning)",
    }
    bgs = {
        "default": "var(--bg-secondary)",
        "accent":  "var(--accent-dim)",
        "success": "var(--success-dim)",
        "error":   "var(--danger-dim)",
        "warning": "var(--warning-dim)",
    }
    border = borders.get(variant, borders["default"])
    bg = bgs.get(variant, bgs["default"])

    return f"""
<div style="
  background: {bg};
  border: 1px solid {border};
  border-radius: 12px;
  padding: 16px 18px;
  margin-bottom: 10px;
  font-family: 'DM Sans', sans-serif;
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
">
  {content}
</div>
"""


def badge(text: str, color: str = "blue") -> str:
    """Return HTML for a colored badge/pill."""
    colors = {
        "blue":   ("var(--accent-dim)",   "var(--accent)"),
        "purple": ("rgba(167,139,250,0.12)", "#A78BFA"),
        "teal":   ("var(--info-dim)",     "var(--info)"),
        "amber":  ("var(--warning-dim)",  "var(--warning)"),
        "red":    ("var(--danger-dim)",   "var(--danger)"),
        "green":  ("var(--success-dim)",  "var(--success)"),
        "gray":   ("rgba(82,82,106,0.15)", "var(--text-tertiary)"),
    }
    bg, fg = colors.get(color, colors["blue"])
    return (
        f'<span style="display:inline-flex;align-items:center;'
        f'background:{bg};color:{fg};border-radius:6px;'
        f'padding:2px 8px;font-size:11px;font-weight:600;letter-spacing:0.03em;'
        f'font-family:\'DM Sans\',sans-serif;">{text}</span>'
    )


def status_dot(is_active: bool) -> str:
    """Return HTML for an animated status indicator dot."""
    if is_active:
        return (
            '<span style="display:inline-block;width:7px;height:7px;'
            'background:var(--success);border-radius:50%;'
            'animation:pulse-dot 2s ease-in-out infinite;'
            'margin-right:7px;vertical-align:middle;'
            'box-shadow:0 0 6px rgba(74,222,128,0.5);"></span>'
        )
    return (
        '<span style="display:inline-block;width:7px;height:7px;'
        'background:var(--danger);border-radius:50%;'
        'margin-right:7px;vertical-align:middle;"></span>'
    )


def metric_card(value: str, label: str, icon: str) -> str:
    """Return HTML for a metric display card."""
    return f"""
<div style="
  background: var(--bg-tertiary);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 20px 16px;
  text-align: center;
  font-family: 'DM Sans', sans-serif;
  box-shadow: var(--shadow-sm);
  transition: border-color 0.2s ease;
">
  <div style="font-size:24px;margin-bottom:8px;opacity:0.8;">{icon}</div>
  <div style="font-family:'Outfit',sans-serif;font-size:30px;font-weight:700;
              color:var(--text-primary);line-height:1;letter-spacing:-0.03em;">{value}</div>
  <div style="color:var(--text-tertiary);font-size:11px;margin-top:6px;
              text-transform:uppercase;letter-spacing:0.08em;font-weight:500;">{label}</div>
</div>
"""


def thinking_dots() -> str:
    """Return HTML for an animated thinking indicator."""
    return """
<div style="display:inline-flex;align-items:center;gap:5px;padding:8px 14px;
            background:var(--bg-tertiary);border:1px solid var(--border-subtle);
            border-radius:20px;">
  <span style="font-size:12px;color:var(--text-tertiary);margin-right:4px;
               font-family:'DM Sans',sans-serif;letter-spacing:0.02em;">thinking</span>
  <span style="display:inline-block;width:6px;height:6px;background:var(--accent);
               border-radius:50%;animation:thinking 1.4s ease-in-out infinite;
               animation-delay:0s;"></span>
  <span style="display:inline-block;width:6px;height:6px;background:var(--accent);
               border-radius:50%;animation:thinking 1.4s ease-in-out infinite;
               animation-delay:0.16s;"></span>
  <span style="display:inline-block;width:6px;height:6px;background:var(--accent);
               border-radius:50%;animation:thinking 1.4s ease-in-out infinite;
               animation-delay:0.32s;"></span>
</div>
"""


def page_header(title: str, subtitle: str = "") -> None:
    """Render a styled page header."""
    subtitle_html = (
        f'<p style="color:var(--text-tertiary);font-size:13px;margin:4px 0 0 0;'
        f'font-weight:400;letter-spacing:0.01em;">{subtitle}</p>'
        if subtitle else ""
    )
    st.markdown(f"""
<div style="margin-bottom:32px;">
  <h1 style="font-family:'Outfit',sans-serif;font-size:28px;font-weight:700;
             color:var(--text-primary);margin:0;letter-spacing:-0.03em;
             line-height:1.2;">{title}</h1>
  {subtitle_html}
  <div style="margin-top:16px;height:1px;
              background:linear-gradient(90deg,var(--accent-border),transparent);"></div>
</div>
""", unsafe_allow_html=True)


def label(text: str) -> str:
    """Small uppercase section label."""
    return (
        f'<p style="font-size:10px;color:var(--text-tertiary);'
        f'text-transform:uppercase;letter-spacing:0.12em;font-weight:600;'
        f'font-family:\'DM Sans\',sans-serif;margin:0 0 8px 0;">{text}</p>'
    )
