"""ICI Dashboard — Women's Experience Page"""

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
    WOMEN_FACILITIES, KOBO_TOKEN, APP_PASSWORD, LOGO_PATH,
    # palette
    TEAL, ORANGE, SKY, VERMILION, BLUISH, PINK, YELLOW,
    LIKERT_COLORS, QUALITY_COLORS, PIE_COLORS, FACILITY_COLORS,
    # utils
    inject_css, password_gate, load_facilities, to_int, first_token_int,
    parse_multiselect, clean_layout, sidebar_logo, sidebar_date_filter,
    # labels
    tw, L_W,
    # value maps
    METHOD_MAP, EDUCATION_MAP, RISK_MAP, LIKERT5_MAP, QUALITY_MAP, QUALITY_ORDER,
    DECISIONS_MAP, EPI_MAP, EXAM_MAP, TREAT_MAP, BF_MAP, SKIN_MAP, INDUCE_MAP,
    PHARMA_MAP, COMFORT_MAP, ROOMING_MAP, VERBAL_MAP, PHYS_MAP, PAYMENT_MAP,
    LIKERT_QS_W, EMOTION_LABELS_W, POSITIVE_EMO_W, INFO_LABELS_W,
)

inject_css()
password_gate()

if not KOBO_TOKEN:
    st.error("⚠ KOBO_TOKEN not found in Streamlit Secrets.")
    st.stop()

# ── Language selector ────────────────────────────────────────────────────────
col_lang = st.columns([6, 1])[1]
lang = col_lang.radio("", ["EN", "FR"], horizontal=True, label_visibility="collapsed", key="lang_w")

# ── Load data ────────────────────────────────────────────────────────────────
with st.spinner("Loading data…" if lang == "EN" else "Chargement…"):
    raw = load_facilities(WOMEN_FACILITIES)
if raw.empty:
    st.warning("No data." if lang == "EN" else "Aucune donnée.")
    st.stop()


def prep(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["_submission_time"] = pd.to_datetime(df["_submission_time"], errors="coerce")
    for col, mp in [
        ("method", METHOD_MAP[lang]), ("education", EDUCATION_MAP[lang]),
        ("risk", RISK_MAP[lang]), ("satisfaction", QUALITY_MAP[lang]),
        ("expect", QUALITY_MAP[lang]), ("decisions", DECISIONS_MAP[lang]),
        ("epi", EPI_MAP[lang]), ("exam", EXAM_MAP[lang]), ("bf", BF_MAP[lang]),
        ("induce", INDUCE_MAP[lang]), ("treat", TREAT_MAP[lang]),
        ("pharma", PHARMA_MAP[lang]), ("comfort", COMFORT_MAP[lang]),
        ("rooming", ROOMING_MAP[lang]), ("verbal", VERBAL_MAP[lang]),
        ("phys", PHYS_MAP[lang]), ("payment", PAYMENT_MAP[lang]),
    ]:
        if col in df.columns:
            df[col] = to_int(df[col])
            df[col + "_label"] = df[col].map(mp).fillna("?")
    for col, label in LIKERT_QS_W[lang].items():
        if col in df.columns:
            df[col] = to_int(df[col])
            df[col + "_label"] = df[col].map(LIKERT5_MAP[lang]).fillna("?")
    if "skin" in df.columns:
        df["skin_int"] = first_token_int(df["skin"])
        df["skin_label"] = df["skin_int"].map(SKIN_MAP[lang]).fillna("?")
    if "age" in df.columns:
        df["age"] = to_int(df["age"])
        df["age_group"] = pd.cut(df["age"], bins=[0, 19, 24, 29, 34, 39, 99],
                                  labels=["<20", "20–24", "25–29", "30–34", "35–39", "40+"])
    if "weeks" in df.columns:
        df["weeks_clean"] = to_int(df["weeks"])
        df.loc[~df["weeks_clean"].between(21, 45), "weeks_clean"] = pd.NA
    if "no_deliveries" in df.columns:
        df["no_deliveries"] = to_int(df["no_deliveries"])
        df.loc[df["no_deliveries"] > 10, "no_deliveries"] = pd.NA
    return df


df = prep(raw)

# ── Sidebar ──────────────────────────────────────────────────────────────────
sidebar_logo()
st.sidebar.markdown("""
<div style="text-align:center;padding:0 0 0 0;">
    <div style="font-family:'DM Serif Display',serif;font-size:1.05rem;color:#005f46;font-weight:600;line-height:1.3;margin-bottom:2px;">ICI Dashboard</div>
    <div style="font-size:0.68rem;color:#888;line-height:1.3;margin-bottom:12px;">International Childbirth Initiative</div>
    <hr style="border:none;border-top:1px solid #e0e0e0;margin:0 0 12px 0;">
</div>""", unsafe_allow_html=True)
st.sidebar.header(tw("filters", lang))

facilities_available = df["_facility"].unique().tolist()
countries_available  = df["_country"].unique().tolist() if "_country" in df.columns else []
compare_mode = False

if len(facilities_available) > 1:
    compare_mode = st.sidebar.checkbox(tw("compare_mode", lang), value=False)
    if len(countries_available) > 1:
        sel_country = st.sidebar.selectbox(tw("country", lang),
                                           [tw("all", lang)] + countries_available)
        if sel_country != tw("all", lang):
            df = df[df["_country"] == sel_country]
            facilities_available = df["_facility"].unique().tolist()
    if compare_mode:
        sel_facs = st.sidebar.multiselect(tw("facility", lang),
                                          options=facilities_available,
                                          default=facilities_available)
        if sel_facs:
            df = df[df["_facility"].isin(sel_facs)]
    else:
        sel_fac = st.sidebar.selectbox(tw("facility", lang),
                                       [tw("all", lang)] + facilities_available)
        if sel_fac != tw("all", lang):
            df = df[df["_facility"] == sel_fac]
else:
    st.sidebar.markdown(f"**{tw('facility', lang)}:** {facilities_available[0]}" if facilities_available else "")

df = sidebar_date_filter(df, lang)

if "method_label" in df.columns:
    opts = [tw("all", lang)] + sorted(df["method_label"].dropna().unique().tolist())
    sel = st.sidebar.selectbox(tw("birth_method_f", lang), opts)
    if sel != tw("all", lang):
        df = df[df["method_label"] == sel]
if "risk_label" in df.columns:
    opts = [tw("all", lang)] + sorted(df["risk_label"].dropna().unique().tolist())
    sel = st.sidebar.selectbox(tw("high_risk_f", lang), opts)
    if sel != tw("all", lang):
        df = df[df["risk_label"] == sel]

st.sidebar.metric(tw("filtered", lang), len(df))
if st.sidebar.button(tw("refresh", lang)):
    st.cache_data.clear()
    st.rerun()

sidebar_logo()

# ── Hero banner ──────────────────────────────────────────────────────────────
total_n = len(df)
sat_good = (df["satisfaction"].isin([4, 5])).sum() / total_n * 100 if "satisfaction" in df.columns and total_n > 0 else 0

if "weeks_clean" in df.columns and df["weeks_clean"].notna().sum() > 0:
    gm, gn, gx = df["weeks_clean"].mean(), int(df["weeks_clean"].min()), int(df["weeks_clean"].max())
    gest_display = f"{gm:.1f} ({gn}–{gx})"
else:
    gest_display = "–"

if "age" in df.columns and df["age"].notna().sum() > 0:
    am, an, ax = df["age"].mean(), int(df["age"].min()), int(df["age"].max())
    age_display = f"{am:.0f} ({an}–{ax})"
else:
    age_display = "–"

elective_cs = (df["method"] == 3).sum() / total_n * 100 if "method" in df.columns and total_n > 0 else 0

st.markdown(f"""
<div class="hero">
    <div class="hero-title">{tw("title", lang)}</div>
    <div class="hero-caption">{tw("caption", lang)}</div>
    <div class="hero-stats">
        <div class="hero-stat">
            <div class="hero-stat-num">{total_n:,}</div>
            <div class="hero-stat-label">{tw("kpi_total", lang)}</div>
        </div>
        <div class="hero-stat">
            <div class="hero-stat-num">{sat_good:.0f}%</div>
            <div class="hero-stat-label">{tw("kpi_positive", lang)}</div>
        </div>
        <div class="hero-stat">
            <div class="hero-stat-num">{gest_display}</div>
            <div class="hero-stat-label">{tw("kpi_gest_range", lang)}</div>
        </div>
        <div class="hero-stat">
            <div class="hero-stat-num">{age_display}</div>
            <div class="hero-stat-label">{tw("kpi_age_range", lang)}</div>
        </div>
        <div class="hero-stat">
            <div class="hero-stat-num">{elective_cs:.0f}%</div>
            <div class="hero-stat-label">{tw("kpi_elective_cs", lang)}</div>
        </div>
    </div>
</div>""", unsafe_allow_html=True)

# ── Facility Comparison ──────────────────────────────────────────────────────
if compare_mode and "_facility" in df.columns and df["_facility"].nunique() > 1:
    st.markdown(f'<div class="section-title">{tw("s_comparison", lang)}</div>', unsafe_allow_html=True)
    if "method" in df.columns:
        cs_data = []
        for fac in df["_facility"].unique():
            fac_df = df[df["_facility"] == fac]
            n = len(fac_df)
            if n == 0:
                continue
            cs_data.append({
                "Facility": fac,
                tw("vaginal", lang):      (fac_df["method"] == 1).sum() / n * 100,
                tw("assisted", lang):     (fac_df["method"] == 2).sum() / n * 100,
                tw("elective_cs", lang):  (fac_df["method"] == 3).sum() / n * 100,
                tw("emergency_cs", lang): (fac_df["method"] == 4).sum() / n * 100,
                tw("vbac", lang):         (fac_df["method"] == 5).sum() / n * 100,
            })
        if cs_data:
            cs_df  = pd.DataFrame(cs_data)
            melt_c = [tw("vaginal", lang), tw("assisted", lang), tw("elective_cs", lang),
                      tw("emergency_cs", lang), tw("vbac", lang)]
            cs_melt = cs_df.melt(id_vars=["Facility"], value_vars=melt_c,
                                  var_name="Birth Method", value_name="Percentage")
            fig = px.bar(cs_melt, x="Facility", y="Percentage", color="Birth Method",
                         barmode="group", color_discrete_sequence=FACILITY_COLORS)
            fig.update_layout(height=400, margin=dict(t=32, b=80, l=8, r=8),
                              plot_bgcolor="white", paper_bgcolor="white",
                              font=dict(family="DM Sans, sans-serif"),
                              legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
                              yaxis=dict(title="%", gridcolor="#eeeeee"),
                              xaxis=dict(title="", showgrid=False))
            st.plotly_chart(fig, use_container_width=True)

    demo_data = []
    for fac in df["_facility"].unique():
        fac_df = df[df["_facility"] == fac]
        n = len(fac_df)
        weeks_mean = fac_df["weeks_clean"].mean() if "weeks_clean" in fac_df.columns else np.nan
        age_mean   = fac_df["age"].mean()         if "age" in fac_df.columns else np.nan
        age_min    = fac_df["age"].min()           if "age" in fac_df.columns else np.nan
        age_max    = fac_df["age"].max()           if "age" in fac_df.columns else np.nan
        staff_ok   = (fac_df["morale"].isin([4, 5])).sum() / n * 100 if "morale" in fac_df.columns and n else np.nan
        exam_nc    = (fac_df["exam"].isin([2, 3, 4, 5])).sum() / n * 100 if "exam" in fac_df.columns and n else np.nan
        epi_nc     = (fac_df["epi"] == 2).sum() / n * 100 if "epi" in fac_df.columns and n else np.nan
        verbal_p   = (fac_df["verbal"].isin([2, 3, 4, 5])).sum() / n * 100 if "verbal" in fac_df.columns and n else np.nan
        phys_p     = (fac_df["phys"].isin([2, 3, 4, 5])).sum() / n * 100 if "phys" in fac_df.columns and n else np.nan
        demo_data.append({
            "Facility": fac, "n": n,
            tw("mean_weeks", lang):     f"{weeks_mean:.1f}" if not np.isnan(weeks_mean) else "–",
            tw("mean_age", lang):       f"{age_mean:.1f} ({age_min:.0f}–{age_max:.0f})" if not np.isnan(age_mean) else "–",
            tw("kpi_staff_equipped", lang): f"{staff_ok:.1f}%" if not np.isnan(staff_ok) else "–",
            tw("a_exam", lang):         f"{exam_nc:.1f}%" if not np.isnan(exam_nc) else "–",
            tw("a_epi", lang):          f"{epi_nc:.1f}%" if not np.isnan(epi_nc) else "–",
            tw("m_verbal", lang):       f"{verbal_p:.1f}%" if not np.isnan(verbal_p) else "–",
            tw("m_phys", lang):         f"{phys_p:.1f}%" if not np.isnan(phys_p) else "–",
        })
    st.dataframe(pd.DataFrame(demo_data), use_container_width=True, hide_index=True)

# ── Timeline ─────────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{tw("s_timeline", lang)}</div>', unsafe_allow_html=True)
if "_submission_time" in df.columns and df["_submission_time"].notna().any():
    freq_opts = [tw("grp_month", lang), tw("grp_week", lang), tw("grp_day", lang)]
    freq = st.radio(tw("grp_by", lang), freq_opts, horizontal=True, key="freq_w")
    fmap = {tw("grp_day", lang): "D", tw("grp_week", lang): "W", tw("grp_month", lang): "ME"}
    ts = df.set_index("_submission_time").resample(fmap[freq]).size().reset_index(name="n")
    fig = px.area(ts, x="_submission_time", y="n",
                  labels={"_submission_time": "", "n": tw("responses", lang)},
                  color_discrete_sequence=[TEAL])
    fig.update_traces(line_width=2, fillcolor="rgba(0,158,115,0.12)")
    fig.update_layout(margin=dict(t=8, b=8, l=8, r=8), height=200,
                      plot_bgcolor="white", paper_bgcolor="white",
                      font=dict(family="DM Sans, sans-serif"))
    st.plotly_chart(fig, use_container_width=True)

# ── Trends ───────────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{tw("s_trends", lang)}</div>', unsafe_allow_html=True)
if "_submission_time" in df.columns and df["_submission_time"].notna().any():
    dft = df.copy()
    dft["month"] = dft["_submission_time"].dt.to_period("M").dt.to_timestamp()
    monthly = dft.groupby("month").agg(
        n=("_submission_time", "count"),
        sat_pos=("satisfaction", lambda x: (pd.to_numeric(x, errors="coerce").isin([4, 5])).sum()),
        skin_imm=("skin_int", lambda x: (pd.to_numeric(x, errors="coerce") == 1).sum()),
        exam_nc=("exam",  lambda x: (pd.to_numeric(x, errors="coerce").isin([2, 3, 4, 5])).sum()),
    ).reset_index()
    monthly = monthly[monthly["n"] >= 5]
    monthly["pct_sat"]  = monthly["sat_pos"]  / monthly["n"] * 100
    monthly["pct_skin"] = monthly["skin_imm"] / monthly["n"] * 100
    monthly["pct_exam"] = monthly["exam_nc"]  / monthly["n"] * 100
    tabs = st.tabs([tw("tr_positive", lang), tw("tr_skin", lang), tw("tr_exam", lang)])
    for tab, (ycol, color) in zip(tabs, [("pct_sat", TEAL), ("pct_skin", BLUISH), ("pct_exam", VERMILION)]):
        with tab:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=monthly["month"], y=monthly[ycol], mode="lines+markers",
                                     line=dict(color=color, width=2.5), marker=dict(size=6)))
            fig.update_layout(height=200, margin=dict(t=8, b=8, l=8, r=8),
                              yaxis=dict(title="%", range=[0, 100]),
                              plot_bgcolor="white", paper_bgcolor="white",
                              font=dict(family="DM Sans, sans-serif"))
            st.plotly_chart(fig, use_container_width=True)

# ── Profile ───────────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{tw("s_profile", lang)}</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)

if "method_label" in df.columns:
    mc = df["method_label"].value_counts().reset_index()
    mc.columns = ["m", "n"]
    fig = px.pie(mc, names="m", values="n", hole=0.45, color_discrete_sequence=PIE_COLORS)
    fig = clean_layout(fig, title=tw("p_method", lang), height=300, legend_below=True)
    c1.plotly_chart(fig, use_container_width=True)

if "age_group" in df.columns:
    ac = df["age_group"].value_counts().sort_index().reset_index()
    ac.columns = ["f", "n"]
    ac["pct"]  = (ac["n"] / total_n * 100).round(1)
    ac["text"] = ac.apply(lambda x: f"{x['n']} ({x['pct']}%)", axis=1)
    fig = px.bar(ac, x="f", y="n", color_discrete_sequence=[BLUISH],
                 labels={"f": "", "n": ""}, text="text")
    fig.update_traces(textposition="outside", textfont=dict(size=9))
    fig = clean_layout(fig, title=tw("p_age", lang), height=300)
    fig.update_xaxes(showgrid=False); fig.update_yaxes(gridcolor="#eeeeee")
    c2.plotly_chart(fig, use_container_width=True)

if "education_label" in df.columns:
    ec = df["education_label"].value_counts().reset_index()
    ec.columns = ["e", "n"]
    ec["pct"]  = (ec["n"] / total_n * 100).round(1)
    ec["text"] = ec.apply(lambda x: f"{x['n']} ({x['pct']}%)", axis=1)
    fig = px.bar(ec, x="n", y="e", orientation="h", color_discrete_sequence=[PINK],
                 labels={"e": "", "n": ""}, text="text")
    fig.update_traces(textposition="outside", textfont=dict(size=9))
    fig = clean_layout(fig, title=tw("p_education", lang), height=300)
    fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
    c3.plotly_chart(fig, use_container_width=True)

c1, c2 = st.columns(2)
if "weeks_clean" in df.columns:
    wk = df["weeks_clean"].dropna()
    fig = px.histogram(wk, nbins=16, color_discrete_sequence=[ORANGE],
                       labels={"value": tw("p_weeks", lang), "count": ""})
    fig = clean_layout(fig, title=tw("p_weeks", lang), height=260)
    fig.update_layout(showlegend=False, xaxis=dict(range=[28, 46], dtick=1))
    fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(gridcolor="#eeeeee")
    c1.plotly_chart(fig, use_container_width=True)

if "no_deliveries" in df.columns:
    nd = df["no_deliveries"].dropna().value_counts().sort_index().reset_index()
    nd.columns = ["nd", "count"]
    nd["pct"]  = (nd["count"] / total_n * 100).round(1)
    nd["text"] = nd.apply(lambda x: f"{x['count']} ({x['pct']}%)", axis=1)
    nd["nd"]   = nd["nd"].astype(int).astype(str)
    fig = px.bar(nd, x="nd", y="count", color_discrete_sequence=[SKY],
                 labels={"nd": tw("p_parity", lang), "count": ""}, text="text")
    fig.update_traces(textposition="outside", textfont=dict(size=9))
    fig = clean_layout(fig, title=tw("p_parity", lang), height=260)
    fig.update_xaxes(showgrid=False); fig.update_yaxes(gridcolor="#eeeeee")
    c2.plotly_chart(fig, use_container_width=True)

# ── Treemap: birth method × emotions ─────────────────────────────────────────
if "method_label" in df.columns and "emotion" in df.columns:
    treemap_title = {"EN": "Emotional Experience by Birth Method",
                     "FR": "Vécu émotionnel par mode d'accouchement"}[lang]
    pos_keys = [1, 4, 6, 7, 9, 11]
    neg_keys = [2, 3, 5, 8, 10, 12]
    pos_lbl  = {"EN": "Positive emotions", "FR": "Émotions positives"}[lang]
    neg_lbl  = {"EN": "Negative emotions", "FR": "Émotions négatives"}[lang]
    root_lbl = {"EN": "All births",        "FR": "Tous accouchements"}[lang]
    tm_rows  = []
    for mcode in [1, 2, 3, 4, 5]:
        mlabel = METHOD_MAP[lang].get(mcode, str(mcode))
        sub = df[(df["method"] == mcode) & df["emotion"].notna()]
        if len(sub) < 5:
            continue
        pos_n = sum(parse_multiselect(sub["emotion"], [k])[k] for k in pos_keys)
        neg_n = sum(parse_multiselect(sub["emotion"], [k])[k] for k in neg_keys)
        tm_rows.append({"method": mlabel, "type": pos_lbl, "n": pos_n, "root": root_lbl})
        tm_rows.append({"method": mlabel, "type": neg_lbl, "n": neg_n, "root": root_lbl})
    if tm_rows:
        tmdf = pd.DataFrame(tm_rows)
        method_palette = ["#6baed6", "#74c476", "#fd8d3c", "#9e9ac8", "#9e9ac8"]
        ids, labels, parents, values, colors = [], [], [], [], []
        ids.append("root"); labels.append(root_lbl); parents.append(""); values.append(0); colors.append("#eef2f0")
        for i, m in enumerate(tmdf["method"].unique()):
            mid = f"m_{i}"
            ids.append(mid); labels.append(m); parents.append("root")
            values.append(int(tmdf[tmdf["method"] == m]["n"].sum()))
            colors.append(method_palette[i % len(method_palette)])
            for _, row in tmdf[tmdf["method"] == m].iterrows():
                lid = f"l_{i}_{row['type']}"
                ids.append(lid); labels.append(row["type"]); parents.append(mid)
                values.append(int(row["n"]))
                colors.append("#a8d8c8" if row["type"] == pos_lbl else "#f0c4b0")
        fig = go.Figure(go.Treemap(
            ids=ids, labels=labels, parents=parents, values=values,
            marker=dict(colors=colors, line=dict(width=2, color="white"), cornerradius=5),
            textinfo="label+percent parent",
            textfont=dict(size=12, family="DM Sans, sans-serif", color="#2a2a2a"),
            hovertemplate="<b>%{label}</b><br>%{value}<extra></extra>",
            branchvalues="remainder",
        ))
        fig.update_layout(
            title=dict(text=treemap_title, font=dict(size=13, family="DM Serif Display, serif", color="#1a1a1a"),
                       x=0, xanchor="left"),
            margin=dict(t=44, b=8, l=8, r=8), height=360, paper_bgcolor="white",
            font=dict(family="DM Sans, sans-serif"), showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

# ── Likert ────────────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{tw("s_likert", lang)}</div>', unsafe_allow_html=True)
st.caption(tw("s_likert_cap", lang))
likert_order = list(LIKERT5_MAP[lang].values())
rows = []
for col, label in LIKERT_QS_W[lang].items():
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
                      margin=dict(t=8, b=110, l=8, r=8), height=480,
                      plot_bgcolor="white", paper_bgcolor="white",
                      font=dict(family="DM Sans, sans-serif"))
    st.plotly_chart(fig, use_container_width=True)

# ── Bubble: age × parity ──────────────────────────────────────────────────────
if "age" in df.columns and "no_deliveries" in df.columns:
    bubble_title = {"EN": "Respondent Profile — Age × Number of Previous Deliveries",
                    "FR": "Profil des répondantes — Âge × Nombre d'accouchements précédents"}[lang]
    bdf = df.copy()
    bdf["age_grp"] = pd.cut(bdf["age"], bins=[0, 24, 29, 34, 39, 99],
                             labels=["<25", "25–29", "30–34", "35–39", "40+"])
    bdf["nd"] = pd.to_numeric(bdf["no_deliveries"], errors="coerce")
    bdf.loc[bdf["nd"] > 6, "nd"] = pd.NA
    bubble = bdf.dropna(subset=["age_grp", "nd"]).groupby(["age_grp", "nd"]).size().reset_index(name="n")
    bubble["nd_str"] = bubble["nd"].astype(int).astype(str)
    bubble["pct"]    = (bubble["n"] / bubble["n"].sum() * 100).round(1)
    fig = px.scatter(bubble, x="age_grp", y="nd_str", size="n", color="n",
                     color_continuous_scale=[[0, "#e8f4f0"], [0.4, SKY], [1, TEAL]], size_max=55,
                     labels={"age_grp": {"EN": "Age group", "FR": "Groupe d'âge"}[lang],
                             "nd_str": {"EN": "Previous deliveries", "FR": "Accouchements précédents"}[lang],
                             "n": tw("responses", lang)},
                     hover_data={"n": True, "pct": True})
    fig.update_layout(
        title=dict(text=bubble_title, font=dict(size=13, family="DM Serif Display, serif", color="#1a1a1a"),
                   x=0, xanchor="left"),
        margin=dict(t=44, b=16, l=8, r=8), height=360, plot_bgcolor="white", paper_bgcolor="white",
        coloraxis_showscale=False, font=dict(family="DM Sans, sans-serif"),
        xaxis=dict(showgrid=True, gridcolor="#eeeeee"),
        yaxis=dict(showgrid=True, gridcolor="#eeeeee",
                   title={"EN": "Previous deliveries", "FR": "Accouchements précédents"}[lang]),
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Autonomy & Consent ────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{tw("s_autonomy", lang)}</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
for col_lbl, col_raw, key, container in [
    ("decisions_label", "decisions", "a_decisions", c1),
    ("exam_label",      "exam",      "a_exam",      c2),
]:
    if col_lbl in df.columns:
        vc = df[col_lbl].value_counts().reset_index(); vc.columns = ["r", "n"]
        vc["pct"]  = (vc["n"] / total_n * 100).round(1)
        vc["text"] = vc.apply(lambda x: f"{x['n']} ({x['pct']}%)", axis=1)
        fig = px.bar(vc, x="n", y="r", orientation="h", color_discrete_sequence=[TEAL],
                     labels={"r": "", "n": tw("responses", lang)}, text="text")
        fig.update_traces(textposition="outside", textfont=dict(size=10))
        fig = clean_layout(fig, title=tw(key, lang), height=270)
        fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
        container.plotly_chart(fig, use_container_width=True)

c1, c2 = st.columns(2)
if "epi_label" in df.columns:
    ep = df["epi_label"].value_counts().reset_index(); ep.columns = ["r", "n"]
    ep["pct"]  = (ep["n"] / total_n * 100).round(1)
    ep["text"] = ep.apply(lambda x: f"{x['n']} ({x['pct']}%)", axis=1)
    fig = px.bar(ep, x="n", y="r", orientation="h", color_discrete_sequence=[TEAL],
                 labels={"r": "", "n": tw("responses", lang)}, text="text")
    fig.update_traces(textposition="outside", textfont=dict(size=10))
    fig = clean_layout(fig, title=tw("a_epi", lang), height=250)
    fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
    c1.plotly_chart(fig, use_container_width=True)
if "treat_label" in df.columns:
    tc2 = df["treat_label"].value_counts().reset_index(); tc2.columns = ["r", "n"]
    fig = px.pie(tc2, names="r", values="n", hole=0.5, color_discrete_sequence=PIE_COLORS)
    fig = clean_layout(fig, title=tw("a_treat", lang), height=250, legend_below=True)
    c2.plotly_chart(fig, use_container_width=True)

# ── Clinical Practices ────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{tw("s_clinical", lang)}</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
for col_lbl, key, color, container in [
    ("skin_label",  "c_skin",   TEAL,   c1),
    ("bf_label",    "c_bf",     BLUISH, c2),
]:
    if col_lbl in df.columns:
        vc = df[col_lbl].value_counts().reset_index(); vc.columns = ["r", "n"]
        vc["pct"]  = (vc["n"] / total_n * 100).round(1)
        vc["text"] = vc.apply(lambda x: f"{x['n']} ({x['pct']}%)", axis=1)
        fig = px.bar(vc, x="n", y="r", orientation="h", color_discrete_sequence=[color],
                     labels={"r": "", "n": tw("responses", lang)}, text="text")
        fig.update_traces(textposition="outside", textfont=dict(size=9))
        fig = clean_layout(fig, title=tw(key, lang), height=290)
        fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
        container.plotly_chart(fig, use_container_width=True)
if "induce_label" in df.columns:
    ind = df["induce_label"].value_counts().reset_index(); ind.columns = ["r", "n"]
    fig = px.pie(ind, names="r", values="n", hole=0.52, color_discrete_sequence=PIE_COLORS)
    fig = clean_layout(fig, title=tw("c_induce", lang), height=290, legend_below=True)
    c3.plotly_chart(fig, use_container_width=True)

c1, c2, c3 = st.columns(3)
for col_lbl, key, color, container in [
    ("pharma_label",  "c_pharma",  SKY,    c1),
    ("comfort_label", "c_comfort", ORANGE, c2),
    ("rooming_label", "c_rooming", TEAL,   c3),
]:
    if col_lbl in df.columns:
        vc = df[col_lbl].value_counts().reset_index(); vc.columns = ["r", "n"]
        vc["pct"]  = (vc["n"] / total_n * 100).round(1)
        vc["text"] = vc.apply(lambda x: f"{x['n']} ({x['pct']}%)", axis=1)
        fig = px.bar(vc, x="n", y="r", orientation="h", color_discrete_sequence=[color],
                     labels={"r": "", "n": ""}, text="text")
        fig.update_traces(textposition="outside", textfont=dict(size=9))
        fig = clean_layout(fig, title=tw(key, lang), height=270)
        fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
        container.plotly_chart(fig, use_container_width=True)

# ── Sankey: Risk → Birth method → Skin-to-skin ───────────────────────────────
if "risk" in df.columns and "method" in df.columns and "skin_int" in df.columns:
    sk_title = {"EN": "Care Journey: Risk Profile → Birth Method → Skin-to-Skin Contact",
                "FR": "Parcours : Profil de risque → Mode d'accouchement → Peau à peau"}[lang]
    risk_lbl   = {1: {"EN": "High-risk", "FR": "Grossesse à risque"}[lang],
                  2: {"EN": "Low-risk",  "FR": "Grossesse normale"}[lang]}
    method_lbl = {k: METHOD_MAP[lang][k] for k in [1, 2, 3, 4]}
    skin_lbl   = {1: {"EN": "✓ Immediate skin-to-skin", "FR": "✓ Peau à peau immédiat"}[lang],
                  0: {"EN": "✗ Not immediate / No",     "FR": "✗ Pas immédiat / Non"}[lang]}
    fdf = df[df["risk"].isin([1, 2]) & df["method"].isin([1, 2, 3, 4])].copy()
    fdf["skin_bin"] = (fdf["skin_int"] == 1).astype(int)
    sn = len(fdf)
    if sn > 0:
        risk_nodes   = [risk_lbl[1], risk_lbl[2]]
        method_nodes = [method_lbl[k] for k in [1, 2, 3, 4]]
        skin_nodes   = [skin_lbl[1], skin_lbl[0]]
        all_nodes = risk_nodes + method_nodes + skin_nodes
        R, M, S = 0, 2, 6
        sources, targets, values, colors, customdata = [], [], [], [], []
        for r in [1, 2]:
            for m in [1, 2, 3, 4]:
                n = len(fdf[(fdf["risk"] == r) & (fdf["method"] == m)])
                if n == 0:
                    continue
                sources.append(R + (r - 1)); targets.append(M + [1, 2, 3, 4].index(m))
                values.append(n); customdata.append(f"{n/sn*100:.1f}%")
                colors.append("rgba(0,158,115,0.2)" if r == 2 else "rgba(213,94,0,0.2)")
        for m in [1, 2, 3, 4]:
            for s in [1, 0]:
                n = len(fdf[(fdf["method"] == m) & (fdf["skin_bin"] == s)])
                if n == 0:
                    continue
                sources.append(M + [1, 2, 3, 4].index(m)); targets.append(S + (0 if s == 1 else 1))
                values.append(n); customdata.append(f"{n/sn*100:.1f}%")
                colors.append("rgba(0,158,115,0.20)" if s == 1 else "rgba(213,94,0,0.20)")
        node_colors = [VERMILION, TEAL] + [BLUISH, SKY, ORANGE, PINK] + [TEAL, VERMILION]
        fig = go.Figure(go.Sankey(
            arrangement="snap",
            node=dict(pad=20, thickness=24, line=dict(color="white", width=0.5),
                      label=all_nodes, color=node_colors,
                      hovertemplate="%{label}<br>%{value} women<extra></extra>"),
            link=dict(source=sources, target=targets, value=values, color=colors,
                      customdata=customdata,
                      hovertemplate="%{source.label} → %{target.label}<br>%{value} women (%{customdata})<extra></extra>")
        ))
        fig.update_traces(textfont=dict(size=13, family="DM Sans, sans-serif", color="#1a1a1a"))
        fig.update_layout(title=dict(text=sk_title, font=dict(size=13, family="DM Serif Display, serif", color="#1a1a1a"), x=0, xanchor="left"),
                          margin=dict(t=64, b=16, l=8, r=8), height=420,
                          paper_bgcolor="white", font=dict(family="DM Sans, sans-serif", size=11))
        st.plotly_chart(fig, use_container_width=True)

# ── Satisfaction ──────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{tw("s_satisfaction", lang)}</div>', unsafe_allow_html=True)
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
                     labels={"r": "", "n": tw("responses", lang)},
                     category_orders={"r": q_order}, text="text")
        fig.update_traces(textposition="outside", textfont=dict(size=9))
        fig = clean_layout(fig, title=tw(key, lang), height=310)
        fig.update_layout(showlegend=False)
        fig.update_xaxes(showgrid=False); fig.update_yaxes(gridcolor="#eeeeee")
        container.plotly_chart(fig, use_container_width=True)

# ── Emotions ──────────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{tw("s_emotions", lang)}</div>', unsafe_allow_html=True)
st.caption(tw("emo_note", lang))
if "emotion" in df.columns:
    emo_labels = EMOTION_LABELS_W[lang]
    pos        = POSITIVE_EMO_W[lang]
    exhausted_key   = 5
    exhausted_label = emo_labels[exhausted_key]
    counts = parse_multiselect(df["emotion"], list(emo_labels.keys()))
    rows_all = [{"Emotion": lbl, "Pct": round(counts[k] / total_n * 100, 1),
                 "Type": tw("positive", lang) if lbl in pos else tw("negative", lang)}
                for k, lbl in emo_labels.items()]
    rows_nox = [r for r in rows_all if r["Emotion"] != exhausted_label]
    c1, c2 = st.columns(2)
    for container, rows, subtitle in [
        (c1, rows_all, tw("s_emotions_all", lang)),
        (c2, rows_nox, tw("s_emotions_no_exhausted", lang)),
    ]:
        edf = pd.DataFrame(rows).sort_values("Pct", ascending=True)
        container.markdown(f"**{subtitle}**")
        fig = px.bar(edf, x="Pct", y="Emotion", color="Type", orientation="h",
                     color_discrete_map={tw("positive", lang): TEAL, tw("negative", lang): VERMILION},
                     labels={"Pct": tw("pct", lang), "Emotion": ""})
        fig.update_layout(legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center", font=dict(size=10)),
                          margin=dict(t=8, b=60, l=8, r=8), height=420,
                          plot_bgcolor="white", paper_bgcolor="white",
                          font=dict(family="DM Sans, sans-serif"))
        fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
        container.plotly_chart(fig, use_container_width=True)

# ── Discharge info ────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{tw("s_discharge", lang)}</div>', unsafe_allow_html=True)
if "info" in df.columns:
    info_labels = INFO_LABELS_W[lang]
    counts = parse_multiselect(df["info"], list(info_labels.keys()))
    rows = [{"Topic": lbl, "n": counts[k], "Pct": round(counts[k] / total_n * 100, 1)}
            for k, lbl in info_labels.items()]
    idf = pd.DataFrame(rows).sort_values("Pct")
    idf["text"] = idf.apply(lambda x: f"{x['n']} ({x['Pct']}%)", axis=1)
    fig = px.bar(idf, x="Pct", y="Topic", orientation="h", color_discrete_sequence=[PINK],
                 labels={"Pct": tw("pct", lang), "Topic": ""}, text="text")
    fig.update_traces(textposition="outside", textfont=dict(size=9))
    fig.update_layout(margin=dict(t=16, b=8, l=8, r=8), height=220,
                      plot_bgcolor="white", paper_bgcolor="white",
                      font=dict(family="DM Sans, sans-serif"))
    fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
    st.plotly_chart(fig, use_container_width=True)

# ── Mistreatment ──────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{tw("s_mistreat", lang)}</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
for col_lbl, key, color, container in [
    ("verbal_label",  "m_verbal",  VERMILION, c1),
    ("phys_label",    "m_phys",    VERMILION, c2),
    ("payment_label", "m_payment", BLUISH,    c3),
]:
    if col_lbl in df.columns:
        vc = df[col_lbl].value_counts().reset_index(); vc.columns = ["r", "n"]
        vc["pct"]  = (vc["n"] / total_n * 100).round(1)
        vc["text"] = vc.apply(lambda x: f"{x['n']} ({x['pct']}%)", axis=1)
        fig = px.bar(vc, x="n", y="r", orientation="h", color_discrete_sequence=[color],
                     labels={"r": "", "n": tw("responses", lang)}, text="text")
        fig.update_traces(textposition="outside", textfont=dict(size=9))
        fig = clean_layout(fig, title=tw(key, lang), height=260)
        fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
        container.plotly_chart(fig, use_container_width=True)

# ── Raw data ──────────────────────────────────────────────────────────────────
with st.expander(tw("raw_data", lang)):
    hide = [c for c in df.columns if c.startswith("_") or c == "meta/rootUuid"]
    show = [c for c in df.columns if c not in hide]
    st.dataframe(df[show], use_container_width=True, height=400)
    csv = df[show].to_csv(index=False).encode("utf-8")
    st.download_button(tw("download", lang), csv,
                       f"ici_women_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
