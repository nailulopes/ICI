"""
ICI Women's Experience Dashboard
International Childbirth Initiative — Questionnaire 2026
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import base64
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────
KOBO_TOKEN = "c9a5fc9b8cd8189d3d2059c7c7ee95ba179441df"
ASSET_UID  = "aT3kXmLeYLtUC6zVAV5abW"
BASE_URL   = "https://eu.kobotoolbox.org"
# ─────────────────────────────────────────

METHOD_MAP = {
    1: "Vaginal", 2: "Assisted vaginal (forceps/vacuum)",
    3: "Elective/planned caesarean", 4: "Emergency caesarean",
    5: "VBAC", 0: "I don't know"
}
EDUCATION_MAP = {1: "None", 2: "Primary", 3: "Secondary", 4: "Higher than secondary"}
RISK_MAP      = {1: "Yes", 2: "No", 0: "I don't know"}

LIKERT5_MAP   = {
    5: "Always", 4: "Most of the time", 3: "Sometimes",
    2: "Rarely", 1: "Never", 0: "I don't know/N.A."
}
LIKERT_ORDER  = ["Always", "Most of the time", "Sometimes", "Rarely", "Never", "I don't know/N.A."]
LIKERT_COLORS = ["#1a7f5a", "#57bb8a", "#f6c344", "#f4845f", "#d63031", "#cccccc"]

QUALITY_MAP    = {5: "Very good", 4: "Good", 3: "Neutral", 2: "Poor", 1: "Very bad", 0: "I don't know"}
QUALITY_ORDER  = ["Very bad", "Poor", "Neutral", "Good", "Very good", "I don't know"]
QUALITY_COLORS = ["#d63031", "#f4845f", "#f6c344", "#57bb8a", "#1a7f5a", "#cccccc"]

DECISIONS_MAP = {
    1: "Yes, included + enough information",
    2: "Yes, included but not enough information",
    3: "Sometimes I was included",
    4: "No, not included in most decisions",
    0: "I don't know/N.A."
}
EPI_MAP = {
    1: "Yes, with my consent",
    2: "Yes, but not fully explained / no consent",
    3: "No, because I declined",
    4: "No, because staff did not recommend it"
}
EXAM_MAP = {
    1: "Never without verbal consent",
    2: "Rarely without consent",
    3: "Sometimes without consent",
    4: "Frequently without verbal consent",
    5: "Always without consent/being asked"
}
# treat: 1=No, 2=Yes (confirmed from data)
TREAT_MAP = {2: "Yes", 1: "No", 0: "I don't know"}

BF_MAP = {
    1: "No — did not breastfeed",
    2: "No — did not need help",
    3: "No, even though I needed help",
    4: "Yes, helped but not enough",
    5: "Yes, received the help I needed",
    0: "I don't know"
}
# skin: take first token for multi-select responses like '1 2'
SKIN_MAP = {
    1: "Yes — immediate",
    2: "Yes — not immediate after birth",
    3: "Yes — less than 1 hour",
    4: "No",
    5: "I don't know",
    9: "Baby sent to neonatal unit"
}
INDUCE_MAP = {1: "No", 2: "Yes", 0: "I don't know"}

LIKERT_QUESTIONS = {
    "introduction": "Staff introduced themselves",
    "spoke":        "Staff spoke clearly",
    "communication":"Staff open to questions",
    "privacy":      "Privacy protected",
    "respect":      "Treated respectfully",
    "values":       "Staff respected my beliefs & choices",
    "positive":     "Providers encouraged empowerment",
    "morale":       "Staff had what they needed to do their jobs",
    "coop":         "Staff worked in a coordinated way",
}
EMOTION_MAP = {
    "emotion/1":  "Capable",     "emotion/2":  "Incapable",
    "emotion/3":  "Anxious",     "emotion/4":  "Supported",
    "emotion/5":  "Exhausted",   "emotion/6":  "Active",
    "emotion/7":  "Relaxed",     "emotion/8":  "Passive",
    "emotion/9":  "Responsible", "emotion/10": "Dependent",
    "emotion/11": "Secure",      "emotion/12": "Excluded",
}
INFO_MAP = {
    "info/1": "Caring for my new baby",
    "info/2": "Advice about family planning",
    "info/3": "Warning signs requiring consultation",
    "info/4": "Where to go for follow-up care",
}
POSITIVE_EMOTIONS = {"Capable", "Supported", "Active", "Relaxed", "Responsible", "Secure"}


def get_logo_b64():
    """Load logo as base64 for display — place ici_logo.png in the same folder as this script."""
    logo_path = Path(__file__).parent / "ici_logo.png"
    if logo_path.exists():
        return base64.b64encode(logo_path.read_bytes()).decode()
    return None


@st.cache_data(ttl=300)
def load_data():
    headers = {"Authorization": f"Token {KOBO_TOKEN}"}
    url = f"{BASE_URL}/api/v2/assets/{ASSET_UID}/data/?format=json&limit=3000"
    all_results = []
    while url:
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            st.error(f"Kobo API error: {r.status_code} — check your token and asset UID.")
            return pd.DataFrame()
        data = r.json()
        all_results.extend(data.get("results", []))
        url = data.get("next")
    return pd.DataFrame(all_results)


def to_int(series):
    """Safely convert a series to int, handling strings and NaNs."""
    return pd.to_numeric(series, errors="coerce")


def first_token_int(series):
    """For multi-select columns like '1 2', take the first token as int."""
    return series.astype(str).str.split().str[0].pipe(pd.to_numeric, errors="coerce")


def prep(df):
    df = df.copy()
    df["_submission_time"] = pd.to_datetime(df["_submission_time"], errors="coerce")

    # Standard int mappings
    for col, mapping in [("method", METHOD_MAP), ("education", EDUCATION_MAP),
                         ("risk", RISK_MAP), ("satisfaction", QUALITY_MAP),
                         ("expect", QUALITY_MAP)]:
        if col in df.columns:
            df[col] = to_int(df[col])
            df[col + "_label"] = df[col].map(mapping).fillna("I don't know")

    # Likert questions
    for col in LIKERT_QUESTIONS:
        if col in df.columns:
            df[col] = to_int(df[col])
            df[col + "_label"] = df[col].map(LIKERT5_MAP).fillna("I don't know/N.A.")

    # skin — multi-select, take first token
    if "skin" in df.columns:
        df["skin_int"] = first_token_int(df["skin"])
        df["skin_label"] = df["skin_int"].map(SKIN_MAP).fillna("I don't know")

    # Other cols
    for col, mapping in [("decisions", DECISIONS_MAP), ("epi", EPI_MAP),
                         ("exam", EXAM_MAP), ("bf", BF_MAP),
                         ("induce", INDUCE_MAP), ("treat", TREAT_MAP)]:
        if col in df.columns:
            df[col] = to_int(df[col])
            df[col + "_label"] = df[col].map(mapping).fillna("I don't know")

    # Age groups
    if "age" in df.columns:
        df["age"] = to_int(df["age"])
        df["age_group"] = pd.cut(df["age"], bins=[0, 19, 24, 29, 34, 39, 99],
                                  labels=["<20", "20–24", "25–29", "30–34", "35–39", "40+"])
    return df


# ── Page config ──
st.set_page_config(page_title="ICI Dashboard", page_icon="🤱", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600&family=DM+Serif+Display&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'DM Serif Display', serif; }
.metric-box { background:#f8f4f0; border-radius:12px; padding:20px; text-align:center; }
.metric-num { font-size:2.2rem; font-weight:700; color:#1a7f5a; }
.metric-label { font-size:0.85rem; color:#666; margin-top:4px; }
.section-title { font-family:'DM Serif Display',serif; font-size:1.3rem;
                 color:#2d2d2d; border-left:4px solid #1a7f5a;
                 padding-left:12px; margin:28px 0 12px 0; }
</style>
""", unsafe_allow_html=True)

# ── Header with logo ──
logo_b64 = get_logo_b64()
col_logo, col_title = st.columns([1, 5])
if logo_b64:
    col_logo.markdown(
        f'<img src="data:image/png;base64,{logo_b64}" style="width:100%;max-width:160px;margin-top:8px">',
        unsafe_allow_html=True
    )
col_title.title("Women's Experience Dashboard")
col_title.caption("International Childbirth Initiative · 12 Steps to Safe and Respectful MotherBaby-Family Maternity Care · Questionnaire 2026")

st.divider()

# ── Load data ──
with st.spinner("Loading data from KoboToolbox..."):
    raw = load_data()

if raw.empty:
    st.warning("No data available.")
    st.stop()

df = prep(raw)

# ── Sidebar ──
if Path("ici_logo.png").exists():
    st.sidebar.image("ici_logo.png", width=180)
st.sidebar.header("Filters")

if "_submission_time" in df.columns and df["_submission_time"].notna().any():
    min_d = df["_submission_time"].min().date()
    max_d = df["_submission_time"].max().date()
    dr = st.sidebar.date_input("Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
    if len(dr) == 2:
        df = df[(df["_submission_time"].dt.date >= dr[0]) &
                (df["_submission_time"].dt.date <= dr[1])]

if "method_label" in df.columns:
    opts = ["All"] + sorted(df["method_label"].dropna().unique().tolist())
    sel = st.sidebar.selectbox("Birth method", opts)
    if sel != "All":
        df = df[df["method_label"] == sel]

if "risk_label" in df.columns:
    opts = ["All"] + sorted(df["risk_label"].dropna().unique().tolist())
    sel = st.sidebar.selectbox("High-risk pregnancy", opts)
    if sel != "All":
        df = df[df["risk_label"] == sel]

st.sidebar.metric("Filtered responses", len(df))
if st.sidebar.button("🔄 Refresh data"):
    st.cache_data.clear()
    st.rerun()


# ═══ PANEL 1 — KPIs ═══
st.markdown('<div class="section-title">Overview</div>', unsafe_allow_html=True)

sat_good   = (df["satisfaction"].isin([4, 5])).sum() / len(df) * 100 if "satisfaction" in df.columns else 0
exam_nc    = (df["exam"].isin([2, 3, 4, 5])).sum() if "exam" in df.columns else 0
epi_nc     = (df["epi"] == 2).sum() if "epi" in df.columns else 0
skin_immed = (df["skin_int"] == 1).sum() / len(df) * 100 if "skin_int" in df.columns else 0

c1, c2, c3, c4, c5 = st.columns(5)
for col, num, label in [
    (c1, len(df),              "Total responses"),
    (c2, f"{sat_good:.0f}%",   "Positive care rating"),
    (c3, f"{skin_immed:.0f}%", "Immediate skin-to-skin"),
    (c4, exam_nc,              "Vaginal exams w/o consent"),
    (c5, epi_nc,               "Episiotomies w/o consent"),
]:
    col.markdown(f'<div class="metric-box"><div class="metric-num">{num}</div>'
                 f'<div class="metric-label">{label}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ═══ PANEL 2 — Timeline ═══
st.markdown('<div class="section-title">Responses Over Time</div>', unsafe_allow_html=True)

if "_submission_time" in df.columns and df["_submission_time"].notna().any():
    freq = st.radio("Group by", ["Month", "Week", "Day"], horizontal=True)
    fmap = {"Day": "D", "Week": "W", "Month": "ME"}
    ts = df.set_index("_submission_time").resample(fmap[freq]).size().reset_index(name="n")
    fig = px.area(ts, x="_submission_time", y="n",
                  labels={"_submission_time": "", "n": "Responses"},
                  color_discrete_sequence=["#1a7f5a"])
    fig.update_traces(line_width=2, fillcolor="rgba(26,127,90,0.15)")
    fig.update_layout(margin=dict(t=10, b=10), height=220,
                      plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)


# ═══ PANEL 3 — Respondent Profile ═══
st.markdown('<div class="section-title">Respondent Profile</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)

if "method_label" in df.columns:
    mc = df["method_label"].value_counts().reset_index(); mc.columns = ["m", "n"]
    fig = px.pie(mc, names="m", values="n", hole=0.45,
                 color_discrete_sequence=px.colors.qualitative.Safe)
    fig.update_layout(title="Birth method", margin=dict(t=40, b=10), height=280)
    c1.plotly_chart(fig, use_container_width=True)

if "age_group" in df.columns:
    ac = df["age_group"].value_counts().sort_index().reset_index(); ac.columns = ["f", "n"]
    fig = px.bar(ac, x="f", y="n", color_discrete_sequence=["#2563eb"],
                 labels={"f": "Age group", "n": ""})
    fig.update_layout(title="Age group", margin=dict(t=40, b=10), height=280, plot_bgcolor="white")
    c2.plotly_chart(fig, use_container_width=True)

if "education_label" in df.columns:
    ec = df["education_label"].value_counts().reset_index(); ec.columns = ["e", "n"]
    fig = px.bar(ec, x="n", y="e", orientation="h",
                 color_discrete_sequence=["#7c3aed"], labels={"e": "", "n": ""})
    fig.update_layout(title="Education level", margin=dict(t=40, b=10), height=280, plot_bgcolor="white")
    c3.plotly_chart(fig, use_container_width=True)

if "weeks" in df.columns:
    wk = to_int(df["weeks"]).dropna()
    fig = px.histogram(wk, nbins=20, color_discrete_sequence=["#f59e0b"],
                       labels={"value": "Gestational weeks at birth", "count": ""})
    fig.update_layout(title="Gestational weeks at birth", showlegend=False,
                      margin=dict(t=40, b=10), height=220, plot_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)


# ═══ PANEL 4 — Quality of Care Likert ═══
st.markdown('<div class="section-title">Quality of Care — Likert Scales</div>', unsafe_allow_html=True)
st.caption("Response distribution across care dimensions (Always → Never)")

rows = []
for col, label in LIKERT_QUESTIONS.items():
    lbl = col + "_label"
    if lbl in df.columns:
        vc = df[lbl].value_counts(normalize=True).mul(100).round(1)
        for cat in LIKERT_ORDER:
            rows.append({"Dimension": label, "Response": cat, "Pct": vc.get(cat, 0)})

if rows:
    ldf = pd.DataFrame(rows)
    fig = px.bar(ldf, x="Pct", y="Dimension", color="Response", orientation="h",
                 barmode="stack", color_discrete_sequence=LIKERT_COLORS,
                 category_orders={"Response": LIKERT_ORDER},
                 labels={"Pct": "%", "Dimension": ""})
    fig.update_layout(legend=dict(orientation="h", y=-0.18, x=0),
                      margin=dict(t=10, b=90), height=440,
                      plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)


# ═══ PANEL 5 — Autonomy & Consent ═══
st.markdown('<div class="section-title">Autonomy & Consent</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)

if "decisions_label" in df.columns:
    dc = df["decisions_label"].value_counts().reset_index(); dc.columns = ["r", "n"]
    fig = px.bar(dc, x="n", y="r", orientation="h",
                 color_discrete_sequence=["#1a7f5a"], labels={"r": "", "n": "Responses"})
    fig.update_layout(title="Included in care decisions",
                      plot_bgcolor="white", margin=dict(t=40, b=10), height=250)
    c1.plotly_chart(fig, use_container_width=True)

if "exam_label" in df.columns:
    ec = df["exam_label"].value_counts().reset_index(); ec.columns = ["r", "n"]
    fig = px.bar(ec, x="n", y="r", orientation="h",
                 color="r", color_discrete_sequence=LIKERT_COLORS,
                 labels={"r": "", "n": ""})
    fig.update_layout(title="Vaginal exam without consent",
                      showlegend=False, plot_bgcolor="white",
                      margin=dict(t=40, b=10), height=250)
    c2.plotly_chart(fig, use_container_width=True)

c1, c2 = st.columns(2)

if "epi_label" in df.columns:
    ep = df["epi_label"].value_counts().reset_index(); ep.columns = ["r", "n"]
    fig = px.pie(ep, names="r", values="n", hole=0.4,
                 color_discrete_sequence=["#1a7f5a", "#d63031", "#f6c344", "#57bb8a"])
    fig.update_layout(title="Episiotomy", margin=dict(t=40, b=10), height=280)
    c1.plotly_chart(fig, use_container_width=True)

if "treat_label" in df.columns:
    tc = df["treat_label"].value_counts().reset_index(); tc.columns = ["r", "n"]
    fig = px.pie(tc, names="r", values="n", hole=0.4,
                 color_discrete_sequence=["#1a7f5a", "#d63031", "#cccccc"])
    fig.update_layout(title="Treatments or procedures not wanted / not agreed to",
                      margin=dict(t=40, b=10), height=280)
    c2.plotly_chart(fig, use_container_width=True)


# ═══ PANEL 6 — Clinical Practices ═══
st.markdown('<div class="section-title">Clinical Practices</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)

if "skin_label" in df.columns:
    sk = df["skin_label"].value_counts().reset_index(); sk.columns = ["r", "n"]
    fig = px.pie(sk, names="r", values="n", hole=0.4,
                 color_discrete_sequence=["#1a7f5a", "#57bb8a", "#f6c344", "#d63031", "#cccccc"])
    fig.update_layout(title="Skin-to-skin contact after birth", margin=dict(t=40, b=10), height=280)
    c1.plotly_chart(fig, use_container_width=True)

if "bf_label" in df.columns:
    bf = df["bf_label"].value_counts().reset_index(); bf.columns = ["r", "n"]
    fig = px.bar(bf, x="n", y="r", orientation="h",
                 color_discrete_sequence=["#2563eb"], labels={"r": "", "n": ""})
    fig.update_layout(title="Breastfeeding support", plot_bgcolor="white",
                      margin=dict(t=40, b=10), height=280)
    c2.plotly_chart(fig, use_container_width=True)

if "induce_label" in df.columns:
    ind = df["induce_label"].value_counts().reset_index(); ind.columns = ["r", "n"]
    fig = px.pie(ind, names="r", values="n", hole=0.4,
                 color_discrete_sequence=["#1a7f5a", "#f59e0b", "#cccccc"])
    fig.update_layout(title="Labour induction", margin=dict(t=40, b=10), height=280)
    c3.plotly_chart(fig, use_container_width=True)


# ═══ PANEL 7 — Satisfaction ═══
st.markdown('<div class="section-title">Satisfaction — Expectations vs. Reality</div>', unsafe_allow_html=True)

if "expect_label" in df.columns and "satisfaction_label" in df.columns:
    c1, c2 = st.columns(2)
    for col, field, title in [
        (c1, "expect_label",      "Before I came here, I expected care to be:"),
        (c2, "satisfaction_label","Now, I feel that my care was:")
    ]:
        vc = df[field].value_counts().reindex(QUALITY_ORDER, fill_value=0).reset_index()
        vc.columns = ["r", "n"]
        fig = px.bar(vc, x="r", y="n", color="r",
                     color_discrete_sequence=QUALITY_COLORS,
                     labels={"r": "", "n": "Responses"},
                     category_orders={"r": QUALITY_ORDER})
        fig.update_layout(title=title, showlegend=False, plot_bgcolor="white",
                          margin=dict(t=60, b=10), height=300)
        col.plotly_chart(fig, use_container_width=True)


# ═══ PANEL 8 — Emotions ═══
st.markdown('<div class="section-title">How Women Felt at the Time of Delivery</div>', unsafe_allow_html=True)

rows = []
for col, label in EMOTION_MAP.items():
    if col in df.columns:
        pct = to_int(df[col]).sum() / len(df) * 100
        rows.append({"Emotion": label, "Pct": round(pct, 1),
                     "Type": "Positive" if label in POSITIVE_EMOTIONS else "Negative"})
if rows:
    edf = pd.DataFrame(rows).sort_values("Pct", ascending=True)
    fig = px.bar(edf, x="Pct", y="Emotion", color="Type", orientation="h",
                 color_discrete_map={"Positive": "#1a7f5a", "Negative": "#d63031"},
                 labels={"Pct": "% of respondents", "Emotion": ""})
    fig.update_layout(margin=dict(t=10, b=10), height=380,
                      plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)


# ═══ PANEL 9 — Discharge information ═══
st.markdown('<div class="section-title">Information Provided Before Discharge</div>', unsafe_allow_html=True)

rows = []
for col, label in INFO_MAP.items():
    if col in df.columns:
        pct = to_int(df[col]).sum() / len(df) * 100
        rows.append({"Topic": label, "Pct": round(pct, 1)})
if rows:
    idf = pd.DataFrame(rows).sort_values("Pct")
    fig = px.bar(idf, x="Pct", y="Topic", orientation="h",
                 color_discrete_sequence=["#7c3aed"],
                 labels={"Pct": "% who received this information", "Topic": ""})
    fig.update_layout(margin=dict(t=10, b=10), height=220, plot_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)


# ═══ PANEL 10 — Raw data ═══
with st.expander("📋 View raw data"):
    hide = [c for c in df.columns if c.startswith("_") or c == "meta/rootUuid"]
    show = [c for c in df.columns if c not in hide]
    st.dataframe(df[show], use_container_width=True, height=400)
    csv = df[show].to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", csv,
                       f"ici_data_{datetime.today().strftime('%Y%m%d')}.csv", "text/csv")
