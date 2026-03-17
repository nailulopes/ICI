"""ICI Dashboard — Companion Experience Page"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ici_shared import (
    # config
    COMPANION_FACILITIES, KOBO_TOKEN, APP_PASSWORD, LOGO_PATH,
    # palette
    TEAL, ORANGE, SKY, VERMILION, BLUISH, PINK, YELLOW,
    LIKERT_COLORS, QUALITY_COLORS, PIE_COLORS, FACILITY_COLORS,
    # utils
    inject_css, password_gate, load_facilities, to_int, first_token_int,
    parse_multiselect, clean_layout, sidebar_logo, sidebar_date_filter,
    # companion labels & maps
    tc, L_C,
    METHOD_MAP, EDUCATION_MAP, LIKERT5_MAP, QUALITY_MAP, QUALITY_ORDER,
    VERBAL_MAP, PHYS_MAP, PAYMENT_MAP,
    COMP_REL_MAP, COMPLAB_MAP, COMP_DELIV_MAP, COMP_RESPECT_MAP,
    COMP_COMFORT_MAP, CHOICES_MAP, EMERGENCY_MAP, COMP_ROOMING_MAP,
    MILK_MAP, ACCOMPANY_MAP, EXTRA_MAP, COMP_VALUES_MAP, COMP_DECISIONS_MAP,
    COMP_COOP_MAP, COMP_TREATMENT_MAP, COMP_PHARMA_MAP,
    LIKERT_QS_C, POSITIVE_EMO_C, INFO_LABELS_C, COMP_EMOTION_MAP,
)

inject_css()
password_gate()

if not KOBO_TOKEN:
    st.error("⚠ KOBO_TOKEN not found in Streamlit Secrets.")
    st.stop()

# ── Language selector ────────────────────────────────────────────────────────
col_lang = st.columns([6, 1])[1]
lang = col_lang.radio("", ["EN", "FR", "ES"], horizontal=True, label_visibility="collapsed", key="lang_c")

# ── Load data ────────────────────────────────────────────────────────────────
with st.spinner("Loading companion data…" if lang == "EN" else "Chargement acompagnants…"):
    raw = load_facilities(COMPANION_FACILITIES)
if raw.empty:
    st.warning("No companion data found." if lang == "EN" else "Aucune donnée acompagnant.")
    st.stop()


def prep_companion(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["_submission_time"] = pd.to_datetime(df["_submission_time"], errors="coerce")

    # Numeric conversions
    # Map companion emotion codes to labels
    if "emotion" in df.columns:
        df["emotion"] = to_int(df["emotion"])
        df["emotion_label"] = df["emotion"].map(COMP_EMOTION_MAP.get(lang, COMP_EMOTION_MAP["EN"])).fillna("?")

    for col in ["age", "education", "comp", "method", "introduction", "spoke",
                "privacy", "respect", "comp_001", "verbal", "phys", "treatment",
                "payment", "extra", "values", "decisions", "complab", "comp_deliv",
                "comfort", "pharma", "choices", "treat", "emergency", "coop",
                "rooming", "milk", "expect", "satisfaction", "accompany"]:
        if col in df.columns:
            df[col] = to_int(df[col])

    # Labeled columns
    for col, mp in [
        ("education",  EDUCATION_MAP[lang]),
        ("comp",       COMP_REL_MAP[lang]),
        ("method",     METHOD_MAP[lang]),
        ("verbal",     VERBAL_MAP[lang]),
        ("phys",       PHYS_MAP[lang]),
        ("payment",    PAYMENT_MAP[lang]),
        ("extra",      EXTRA_MAP[lang]),
        ("satisfaction", QUALITY_MAP[lang]),
        ("expect",     QUALITY_MAP[lang]),
        ("complab",    COMPLAB_MAP[lang]),
        ("comp_deliv", COMP_DELIV_MAP[lang]),
        ("comp_001",   COMP_RESPECT_MAP[lang]),
        ("comfort",    COMP_COMFORT_MAP[lang]),
        ("pharma",     COMP_PHARMA_MAP[lang]),
        ("choices",    CHOICES_MAP[lang]),
        ("emergency",  EMERGENCY_MAP[lang]),
        ("rooming",    COMP_ROOMING_MAP[lang]),
        ("milk",       MILK_MAP[lang]),
        ("accompany",  ACCOMPANY_MAP[lang]),
        ("values",     COMP_VALUES_MAP[lang]),
        ("decisions",  COMP_DECISIONS_MAP[lang]),
        ("coop",       COMP_COOP_MAP[lang]),
        ("treatment",  COMP_TREATMENT_MAP[lang]),
    ]:
        if col in df.columns:
            df[col + "_label"] = df[col].map(mp).fillna("?")

    # Likert items
    for col in ["introduction", "spoke", "privacy", "respect", "comp_001", "coop"]:
        if col in df.columns:
            df[col + "_label"] = df[col].map(LIKERT5_MAP[lang]).fillna("?")

    # Age
    if "age" in df.columns:
        df["age_group"] = pd.cut(df["age"], bins=[0, 24, 29, 34, 39, 99],
                                  labels=["<25", "25–29", "30–34", "35–39", "40+"])

    return df


df = prep_companion(raw)
total_n = len(df)

# ── Sidebar ──────────────────────────────────────────────────────────────────
sidebar_logo()
st.sidebar.markdown("""
<div style="text-align:center;padding:0 0 0 0;">
    <div style="font-family:'DM Serif Display',serif;font-size:1.05rem;color:#0072B2;font-weight:600;line-height:1.3;margin-bottom:2px;">ICI Dashboard</div>
    <div style="font-size:0.68rem;color:#888;line-height:1.3;margin-bottom:12px;">Companion Experience</div>
    <hr style="border:none;border-top:1px solid #e0e0e0;margin:0 0 12px 0;">
</div>""", unsafe_allow_html=True)
st.sidebar.header(tc("filters", lang))

facilities_available = df["_facility"].unique().tolist()
if len(facilities_available) > 1:
    sel_fac = st.sidebar.selectbox(tc("facility", lang),
                                   [tc("all", lang)] + facilities_available)
    if sel_fac != tc("all", lang):
        df = df[df["_facility"] == sel_fac]
        total_n = len(df)
else:
    st.sidebar.markdown(f"**{tc('facility', lang)}:** {facilities_available[0]}" if facilities_available else "")

df = sidebar_date_filter(df, lang, key_prefix="c")
total_n = len(df)

# Birth method filter
if "method_label" in df.columns:
    opts = [tc("all", lang)] + sorted(df["method_label"].dropna().unique().tolist())
    sel = st.sidebar.selectbox(tc("birth_method_f", lang), opts)
    if sel != tc("all", lang):
        df = df[df["method_label"] == sel]
        total_n = len(df)

st.sidebar.metric(tc("filtered", lang), total_n)
if st.sidebar.button(tc("refresh", lang)):
    st.cache_data.clear()
    st.rerun()
sidebar_logo()

# ── Hero banner ───────────────────────────────────────────────────────────────
sat_good = (df["satisfaction"].isin([4, 5])).sum() / total_n * 100 if "satisfaction" in df.columns and total_n > 0 else 0

# Present during labour
pres_lab = (df["complab"] == 1).sum() / total_n * 100 if "complab" in df.columns and total_n > 0 else 0

# Present during birth
pres_del = (df["comp_deliv"] == 1).sum() / total_n * 100 if "comp_deliv" in df.columns and total_n > 0 else 0

# Felt confident & prepared (strongly agree + agree)
confident = (df["accompany"].isin([5, 4])).sum() / total_n * 100 if "accompany" in df.columns and total_n > 0 else 0

# Age
if "age" in df.columns and df["age"].notna().sum() > 0:
    am, an, ax = df["age"].mean(), int(df["age"].min()), int(df["age"].max())
    age_display = f"{am:.0f} ({an}–{ax})"
else:
    age_display = "–"

st.markdown(f"""
<div class="hero-comp">
    <div class="hero-title">{tc("title", lang)}</div>
    <div class="hero-caption">{tc("caption", lang)}</div>
    <div class="hero-stats">
        <div class="hero-stat">
            <div class="hero-stat-num">{total_n:,}</div>
            <div class="hero-stat-label">{tc("kpi_total", lang)}</div>
        </div>
        <div class="hero-stat">
            <div class="hero-stat-num">{sat_good:.0f}%</div>
            <div class="hero-stat-label">{tc("kpi_positive", lang)}</div>
        </div>
        <div class="hero-stat">
            <div class="hero-stat-num">{pres_lab:.0f}%</div>
            <div class="hero-stat-label">{tc("kpi_present_labour", lang)}</div>
        </div>
        <div class="hero-stat">
            <div class="hero-stat-num">{pres_del:.0f}%</div>
            <div class="hero-stat-label">{tc("kpi_present_birth", lang)}</div>
        </div>
        <div class="hero-stat">
            <div class="hero-stat-num">{confident:.0f}%</div>
            <div class="hero-stat-label">{tc("kpi_confident", lang)}</div>
        </div>
    </div>
</div>""", unsafe_allow_html=True)

# ── Timeline ──────────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{tc("s_timeline", lang)}</div>', unsafe_allow_html=True)
if "_submission_time" in df.columns and df["_submission_time"].notna().any():
    freq_opts = [tc("grp_month", lang), tc("grp_week", lang), tc("grp_day", lang)]
    freq = st.radio(tc("grp_by", lang), freq_opts, horizontal=True, key="freq_c")
    fmap = {tc("grp_day", lang): "D", tc("grp_week", lang): "W", tc("grp_month", lang): "MS"}
    ts = df.groupby(pd.Grouper(key="_submission_time", freq=fmap[freq])).size().reset_index(name="n")
    ts = ts[ts["n"] > 0]
    fig = px.area(ts, x="_submission_time", y="n",
                  labels={"_submission_time": "", "n": tc("responses", lang)},
                  color_discrete_sequence=[BLUISH])
    fig.update_traces(line_width=2, fillcolor="rgba(0,114,178,0.12)")
    fig.update_layout(margin=dict(t=8, b=8, l=8, r=8), height=200,
                      plot_bgcolor="white", paper_bgcolor="white",
                      font=dict(family="DM Sans, sans-serif"))
    st.plotly_chart(fig, use_container_width=True)

# ── Companion Profile ─────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{tc("s_profile", lang)}</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)

# Relationship
if "comp_label" in df.columns:
    rc = df["comp_label"].value_counts().reset_index(); rc.columns = ["r", "n"]
    rc["pct"]  = (rc["n"] / total_n * 100).round(1)
    rc["text"] = rc.apply(lambda x: f"{x['n']} ({x['pct']}%)", axis=1)
    fig = px.bar(rc, x="n", y="r", orientation="h", color_discrete_sequence=[BLUISH],
                 labels={"r": "", "n": ""}, text="text")
    fig.update_traces(textposition="outside", textfont=dict(size=9))
    fig = clean_layout(fig, title=tc("p_relation", lang), height=260)
    fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
    c1.plotly_chart(fig, use_container_width=True)

# Age group
if "age_group" in df.columns:
    ac = df["age_group"].value_counts().sort_index().reset_index(); ac.columns = ["f", "n"]
    ac["pct"]  = (ac["n"] / total_n * 100).round(1)
    ac["text"] = ac.apply(lambda x: f"{x['n']} ({x['pct']}%)", axis=1)
    fig = px.bar(ac, x="f", y="n", color_discrete_sequence=[SKY],
                 labels={"f": "", "n": ""}, text="text")
    fig.update_traces(textposition="outside", textfont=dict(size=9))
    fig = clean_layout(fig, title=tc("p_age", lang), height=260)
    fig.update_xaxes(showgrid=False); fig.update_yaxes(gridcolor="#eeeeee")
    c2.plotly_chart(fig, use_container_width=True)

# Education
if "education_label" in df.columns:
    ec = df["education_label"].value_counts().reset_index(); ec.columns = ["e", "n"]
    ec["pct"]  = (ec["n"] / total_n * 100).round(1)
    ec["text"] = ec.apply(lambda x: f"{x['n']} ({x['pct']}%)", axis=1)
    fig = px.bar(ec, x="n", y="e", orientation="h", color_discrete_sequence=[PINK],
                 labels={"e": "", "n": ""}, text="text")
    fig.update_traces(textposition="outside", textfont=dict(size=9))
    fig = clean_layout(fig, title=tc("p_education", lang), height=260)
    fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
    c3.plotly_chart(fig, use_container_width=True)

# Birth method (observed by companion)
if "method_label" in df.columns:
    mc = df["method_label"].value_counts().reset_index(); mc.columns = ["m", "n"]
    fig = px.pie(mc, names="m", values="n", hole=0.45, color_discrete_sequence=PIE_COLORS)
    fig = clean_layout(fig, title=tc("p_method", lang), height=300, legend_below=True)
    st.plotly_chart(fig, use_container_width=True)

# ── Presence During Labour & Birth ────────────────────────────────────────────
st.markdown(f'<div class="section-title">{tc("s_presence", lang)}</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)

for col_lbl, key, color, container in [
    ("complab_label",    "c_complab",    TEAL,   c1),
    ("comp_deliv_label", "c_comp_deliv", BLUISH, c2),
    ("accompany_label",  "c_accompany",  ORANGE, c3),
]:
    if col_lbl in df.columns:
        vc = df[col_lbl].value_counts().reset_index(); vc.columns = ["r", "n"]
        vc["pct"]  = (vc["n"] / total_n * 100).round(1)
        vc["text"] = vc.apply(lambda x: f"{x['n']} ({x['pct']}%)", axis=1)
        fig = px.bar(vc, x="n", y="r", orientation="h", color_discrete_sequence=[color],
                     labels={"r": "", "n": tc("responses", lang)}, text="text")
        fig.update_traces(textposition="outside", textfont=dict(size=9))
        fig = clean_layout(fig, title=tc(key, lang), height=260)
        fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
        container.plotly_chart(fig, use_container_width=True)

# ── Likert — Care Quality (companion perception) ───────────────────────────────
st.markdown(f'<div class="section-title">{tc("s_likert", lang)}</div>', unsafe_allow_html=True)
st.caption(tc("s_likert_cap", lang))
likert_order = list(LIKERT5_MAP[lang].values())
rows = []
for col, label in LIKERT_QS_C[lang].items():
    lbl = col + "_label"
    if lbl in df.columns:
        vc = df[lbl].value_counts(normalize=True).mul(100).round(1)
        for cat in likert_order:
            rows.append({"Dimension": label, "Response": cat, "Pct": vc.get(cat, 0)})
if rows:
    ldf = pd.DataFrame(rows)
    fig = px.bar(ldf, x="Pct", y="Dimension", color="Response", orientation="h",
                 barmode="stack", color_discrete_sequence=LIKERT_COLORS,
                 category_orders={"Response": likert_order}, labels={"Pct": "%", "Dimension": ""})
    fig.update_layout(legend=dict(orientation="h", y=-0.22, x=0.5, xanchor="center", font=dict(size=10)),
                      margin=dict(t=8, b=110, l=8, r=8), height=420,
                      plot_bgcolor="white", paper_bgcolor="white",
                      font=dict(family="DM Sans, sans-serif"))
    st.plotly_chart(fig, use_container_width=True)

# ── Autonomy, Consent & Respect ───────────────────────────────────────────────
st.markdown(f'<div class="section-title">{tc("s_autonomy", lang)}</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)

for col_lbl, key, color, container in [
    ("decisions_label",  "a_decisions", TEAL,   c1),
    ("values_label",     "a_values",    BLUISH, c2),
    ("comp_001_label",   "a_comp001",   SKY,    c3),
]:
    if col_lbl in df.columns:
        vc = df[col_lbl].value_counts().reset_index(); vc.columns = ["r", "n"]
        vc["pct"]  = (vc["n"] / total_n * 100).round(1)
        vc["text"] = vc.apply(lambda x: f"{x['n']} ({x['pct']}%)", axis=1)
        fig = px.bar(vc, x="n", y="r", orientation="h", color_discrete_sequence=[color],
                     labels={"r": "", "n": tc("responses", lang)}, text="text")
        fig.update_traces(textposition="outside", textfont=dict(size=10))
        fig = clean_layout(fig, title=tc(key, lang), height=270)
        fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
        container.plotly_chart(fig, use_container_width=True)

# Mistreatment observed
st.markdown(f'<div class="section-title">{tc("s_mistreat", lang)}</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
for col_lbl, key, color, container in [
    ("verbal_label",    "m_verbal",  VERMILION, c1),
    ("phys_label",      "m_phys",    VERMILION, c2),
    ("payment_label",   "m_payment", BLUISH,    c3),
]:
    if col_lbl in df.columns:
        vc = df[col_lbl].value_counts().reset_index(); vc.columns = ["r", "n"]
        vc["pct"]  = (vc["n"] / total_n * 100).round(1)
        vc["text"] = vc.apply(lambda x: f"{x['n']} ({x['pct']}%)", axis=1)
        fig = px.bar(vc, x="n", y="r", orientation="h", color_discrete_sequence=[color],
                     labels={"r": "", "n": tc("responses", lang)}, text="text")
        fig.update_traces(textposition="outside", textfont=dict(size=9))
        fig = clean_layout(fig, title=tc(key, lang), height=260)
        fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
        container.plotly_chart(fig, use_container_width=True)

# ── Clinical & Practical ──────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{tc("s_clinical", lang)}</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
for col_lbl, key, color, container in [
    ("comfort_label",   "c_comfort",   TEAL,   c1),
    ("pharma_label",    "c_pharma",    SKY,    c2),
    ("choices_label",   "c_choices",   BLUISH, c3),
]:
    if col_lbl in df.columns:
        vc = df[col_lbl].value_counts().reset_index(); vc.columns = ["r", "n"]
        vc["pct"]  = (vc["n"] / total_n * 100).round(1)
        vc["text"] = vc.apply(lambda x: f"{x['n']} ({x['pct']}%)", axis=1)
        fig = px.bar(vc, x="n", y="r", orientation="h", color_discrete_sequence=[color],
                     labels={"r": "", "n": ""}, text="text")
        fig.update_traces(textposition="outside", textfont=dict(size=9))
        fig = clean_layout(fig, title=tc(key, lang), height=270)
        fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
        container.plotly_chart(fig, use_container_width=True)

c1, c2, c3 = st.columns(3)
for col_lbl, key, color, container in [
    ("rooming_label",   "c_rooming",  TEAL,   c1),
    ("milk_label",      "c_milk",     ORANGE, c2),
    ("emergency_label", "c_emergency",BLUISH, c3),
]:
    if col_lbl in df.columns:
        vc = df[col_lbl].value_counts().reset_index(); vc.columns = ["r", "n"]
        vc["pct"]  = (vc["n"] / total_n * 100).round(1)
        vc["text"] = vc.apply(lambda x: f"{x['n']} ({x['pct']}%)", axis=1)
        fig = px.bar(vc, x="n", y="r", orientation="h", color_discrete_sequence=[color],
                     labels={"r": "", "n": ""}, text="text")
        fig.update_traces(textposition="outside", textfont=dict(size=9))
        fig = clean_layout(fig, title=tc(key, lang), height=270)
        fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
        container.plotly_chart(fig, use_container_width=True)

# ── Satisfaction ──────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{tc("s_satisfaction", lang)}</div>', unsafe_allow_html=True)
if "expect_label" in df.columns and "satisfaction_label" in df.columns:
    c1, c2 = st.columns(2)
    q_order = QUALITY_ORDER[lang]
    for col_lbl, key, container in [
        ("expect_label",       "sat_expect", c1),
        ("satisfaction_label", "sat_actual", c2),
    ]:
        vc = df[col_lbl].value_counts().reindex(q_order, fill_value=0).reset_index()
        vc.columns = ["r", "n"]
        vc["pct"]  = (vc["n"] / total_n * 100).round(1)
        vc["text"] = vc.apply(lambda x: f"{x['n']} ({x['pct']}%)", axis=1)
        fig = px.bar(vc, x="r", y="n", color="r", color_discrete_sequence=QUALITY_COLORS,
                     labels={"r": "", "n": tc("responses", lang)},
                     category_orders={"r": q_order}, text="text")
        fig.update_traces(textposition="outside", textfont=dict(size=9))
        fig = clean_layout(fig, title=tc(key, lang), height=310)
        fig.update_layout(showlegend=False)
        fig.update_xaxes(showgrid=False); fig.update_yaxes(gridcolor="#eeeeee")
        container.plotly_chart(fig, use_container_width=True)

# ── Companion Emotions ────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{tc("s_emotions", lang)}</div>', unsafe_allow_html=True)
if "emotion_label" in df.columns:
    pos_set = POSITIVE_EMO_C.get(lang, POSITIVE_EMO_C["EN"])
    emo_vc = df["emotion_label"].dropna().value_counts().reset_index()
    emo_vc.columns = ["Emotion", "n"]
    emo_vc = emo_vc[emo_vc["Emotion"] != "?"]
    emo_vc["Pct"]  = (emo_vc["n"] / total_n * 100).round(1)
    emo_vc["text"] = emo_vc.apply(lambda x: f"{x['n']} ({x['Pct']}%)", axis=1)
    emo_vc["Type"] = emo_vc["Emotion"].apply(
        lambda e: tc("positive", lang) if e in pos_set else tc("negative", lang)
    )
    emo_vc = emo_vc.sort_values("Pct", ascending=True)
    fig = px.bar(emo_vc, x="Pct", y="Emotion", color="Type", orientation="h",
                 color_discrete_map={tc("positive", lang): TEAL, tc("negative", lang): VERMILION},
                 labels={"Pct": tc("pct", lang), "Emotion": ""}, text="text")
    fig.update_traces(textposition="outside", textfont=dict(size=9))
    fig.update_layout(legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center", font=dict(size=10)),
                      margin=dict(t=8, b=60, l=8, r=8), height=440,
                      plot_bgcolor="white", paper_bgcolor="white",
                      font=dict(family="DM Sans, sans-serif"))
    fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
    st.caption({"EN": "Single emotion selected per respondent.",
                "FR": "Une seule émotion sélectionnée par répondant.",
                "ES": "Una sola emoción seleccionada por encuestado."}[lang])
    st.plotly_chart(fig, use_container_width=True)

# ── Information Before Discharge ──────────────────────────────────────────────
st.markdown(f'<div class="section-title">{tc("s_discharge", lang)}</div>', unsafe_allow_html=True)
if "info" in df.columns:
    info_keys = [1, 2, 3, 4]
    info_labels = INFO_LABELS_C[lang]
    counts = parse_multiselect(df["info"], info_keys)
    rows = [{"Topic": info_labels[k], "n": counts[k], "Pct": round(counts[k] / total_n * 100, 1)}
            for k in info_keys]
    idf = pd.DataFrame(rows).sort_values("Pct")
    idf["text"] = idf.apply(lambda x: f"{x['n']} ({x['Pct']}%)", axis=1)
    fig = px.bar(idf, x="Pct", y="Topic", orientation="h", color_discrete_sequence=[PINK],
                 labels={"Pct": tc("pct", lang), "Topic": ""}, text="text")
    fig.update_traces(textposition="outside", textfont=dict(size=9))
    fig.update_layout(margin=dict(t=16, b=8, l=8, r=8), height=220,
                      plot_bgcolor="white", paper_bgcolor="white",
                      font=dict(family="DM Sans, sans-serif"))
    fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
    st.plotly_chart(fig, use_container_width=True)

# ── Raw data ──────────────────────────────────────────────────────────────────
with st.expander(tc("raw_data", lang)):
    hide = [c for c in df.columns if c.startswith("_") or c == "meta/rootUuid"]
    show = [c for c in df.columns if c not in hide]
    st.dataframe(df[show], use_container_width=True, height=400)
    csv = df[show].to_csv(index=False).encode("utf-8")
    st.download_button(tc("download", lang), csv,
                       f"ici_companion_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
