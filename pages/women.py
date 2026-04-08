"""ICI — Women's Experience"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ici_shared import (
    FACILITIES, TEAL, ORANGE, SKY, VERMILION, BLUISH, PINK,
    LIKERT_COLORS, QUALITY_COLORS, PIE_COLORS,
    inject_css, sidebar_logo, sidebar_facility_header, logout_button, lang_selector, date_filter,
    load_women, prep_women, to_int, parse_multiselect, clean_layout,
    get_facility_ids, get_role,
    METHOD_MAP, LIKERT5_MAP, QUALITY_ORDER,
    LIKERT_QS_W, EMOTION_LABELS_W, POSITIVE_EMO_W, INFO_LABELS_W,
)

inject_css()
sidebar_logo()

# ── Auth check ────────────────────────────────────────────────────────────────
fac_ids = get_facility_ids()
if not fac_ids:
    st.error("Not logged in."); st.stop()

# ── Language ──────────────────────────────────────────────────────────────────
lang = lang_selector("lang_w")

# ── Load & prep ───────────────────────────────────────────────────────────────
L = {
    "EN": {"loading":"Loading…","no_data":"No data available."},
    "FR": {"loading":"Chargement…","no_data":"Aucune donnée."},
    "ES": {"loading":"Cargando…","no_data":"Sin datos."},
}[lang]

with st.spinner(L["loading"]):
    raw = load_women(fac_ids)
if raw.empty:
    st.warning(L["no_data"]); st.stop()
df = prep_women(raw, lang)

# ── Sidebar ───────────────────────────────────────────────────────────────────
sidebar_facility_header({"EN": "Women's Experience", "FR": "Expérience des femmes", "ES": "Experiencia de las mujeres"}[lang])

# Admin: facility filter — must come BEFORE date_filter
# so date range reflects the selected facility's actual date span
if get_role() == "admin" and len(fac_ids) > 1:
    fac_opts_labels = {fid: FACILITIES[fid]["display_name"] for fid in fac_ids}
    sel_fac = st.sidebar.selectbox(
        {"EN":"Facility","FR":"Établissement","ES":"Establecimiento"}[lang],
        options=["all"] + fac_ids,
        format_func=lambda x: {"EN":"All","FR":"Tous","ES":"Todos"}[lang] if x=="all" else fac_opts_labels[x],
        key="fac_filter_w"
    )
    # Reset date filter when facility changes to avoid stale year values
    if st.session_state.get("_prev_fac_w") != sel_fac:
        st.session_state["_prev_fac_w"] = sel_fac
        for k in ["sy_w", "sm_w", "ey_w", "em_w"]:
            st.session_state.pop(k, None)
        st.rerun()
    if sel_fac != "all":
        df = df[df["_facility_id"] == sel_fac]

# Date filter (after facility filter so range matches selected facility)
df = date_filter(df, key="w")

total_n = len(df)
if total_n == 0:
    st.warning({"EN":"No data for selected period.","FR":"Aucune donnée.","ES":"Sin datos."}[lang])
    st.stop()

st.sidebar.metric({"EN":"Responses","FR":"Réponses","ES":"Respuestas"}[lang], total_n)
if st.sidebar.button({"EN":"↻ Refresh","FR":"↻ Actualiser","ES":"↻ Actualizar"}[lang]):
    st.cache_data.clear(); st.rerun()
logout_button()

# ── Hero ──────────────────────────────────────────────────────────────────────
sat_good   = (df["satisfaction"].isin([4,5])).sum()/total_n*100 if "satisfaction" in df.columns else 0
elec_cs    = (df["method"]==3).sum()/total_n*100 if "method" in df.columns else 0
gest_disp  = "–"
age_disp   = "–"
if "weeks_clean" in df.columns and df["weeks_clean"].notna().sum()>0:
    w = df["weeks_clean"]; gest_disp = f"{w.mean():.1f} ({int(w.min())}–{int(w.max())})"
if "age" in df.columns and df["age"].notna().sum()>0:
    a = df["age"]; age_disp = f"{a.mean():.0f} ({int(a.min())}–{int(a.max())})"

titles = {"EN":"Women's Experience Dashboard","FR":"Expérience des Femmes","ES":"Experiencia de las Mujeres"}
captions = {"EN":"ICI — 12 Steps to Safe and Respectful MotherBaby-Family Maternity Care",
            "FR":"ICI — 12 étapes pour des soins de maternité sûrs et respectueux",
            "ES":"ICI — 12 Pasos para una Atención Segura y Respetuosa"}
kpi = {"EN":{"total":"Total responses","pos":"rated care Good/Very good","gest":"gest. weeks (mean, range)",
             "age":"age (mean, range)","ecs":"elective caesarean"},
       "FR":{"total":"Total réponses","pos":"soins Bons/Très bons","gest":"sem. gestation","age":"âge","ecs":"césarienne élective"},
       "ES":{"total":"Total respuestas","pos":"atención Buena/Muy buena","gest":"sem. gestación","age":"edad","ecs":"cesárea electiva"}}[lang]

st.markdown(f"""
<div class="hero">
  <div class="hero-title">{titles[lang]}</div>
  <div class="hero-caption">{captions[lang]}</div>
  <div class="hero-stats">
    <div class="hero-stat"><div class="hero-stat-num">{total_n:,}</div><div class="hero-stat-label">{kpi['total']}</div></div>
    <div class="hero-stat"><div class="hero-stat-num">{sat_good:.0f}%</div><div class="hero-stat-label">{kpi['pos']}</div></div>
    <div class="hero-stat"><div class="hero-stat-num">{gest_disp}</div><div class="hero-stat-label">{kpi['gest']}</div></div>
    <div class="hero-stat"><div class="hero-stat-num">{age_disp}</div><div class="hero-stat-label">{kpi['age']}</div></div>
    <div class="hero-stat"><div class="hero-stat-num">{elec_cs:.0f}%</div><div class="hero-stat-label">{kpi['ecs']}</div></div>
  </div>
</div>""", unsafe_allow_html=True)

# ── Timeline ──────────────────────────────────────────────────────────────────
sec = {"EN":"Responses Over Time","FR":"Réponses dans le temps","ES":"Respuestas en el tiempo"}
st.markdown(f'<div class="section-title">{sec[lang]}</div>', unsafe_allow_html=True)
if "_submission_time" in df.columns and df["_submission_time"].notna().any():
    grp_opts = {"EN":["Month","Week","Day"],"FR":["Mois","Semaine","Jour"],"ES":["Mes","Semana","Día"]}[lang]
    freq_map = {grp_opts[0]:"MS", grp_opts[1]:"W", grp_opts[2]:"D"}
    grp = st.radio({"EN":"Group by","FR":"Regrouper par","ES":"Agrupar por"}[lang], grp_opts, horizontal=True)
    ts = df.groupby(pd.Grouper(key="_submission_time", freq=freq_map[grp])).size().reset_index(name="n")
    ts = ts[ts["n"]>0]
    # Format x-axis label based on grouping to avoid showing time component
    dtfmt = {grp_opts[0]: "%b %Y", grp_opts[1]: "%d %b %Y", grp_opts[2]: "%d %b %Y"}[grp]
    ts["_label"] = ts["_submission_time"].dt.strftime(dtfmt)
    fig = px.area(ts, x="_label", y="n", color_discrete_sequence=[TEAL],
                  labels={"_label":"","n":{"EN":"Responses","FR":"Réponses","ES":"Respuestas"}[lang]})
    fig.update_traces(line_width=2, fillcolor="rgba(0,158,115,0.12)")
    fig.update_layout(height=200, margin=dict(t=8,b=8,l=8,r=8), plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

# ── Profile ───────────────────────────────────────────────────────────────────
sec2 = {"EN":"Respondent Profile","FR":"Profil des répondantes","ES":"Perfil de las encuestadas"}
st.markdown(f'<div class="section-title">{sec2[lang]}</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
if "method_label" in df.columns:
    mc = df["method_label"].dropna().value_counts().reset_index(); mc.columns=["m","n"]
    fig = px.pie(mc, names="m", values="n", hole=0.45, color_discrete_sequence=PIE_COLORS)
    fig = clean_layout(fig, title={"EN":"Birth method","FR":"Mode d'accouchement","ES":"Vía de nacimiento"}[lang], height=300, legend_below=True)
    c1.plotly_chart(fig, use_container_width=True)
if "age_group" in df.columns:
    ac = df["age_group"].value_counts().sort_index().reset_index(); ac.columns=["f","n"]
    ac["text"] = ac.apply(lambda x: f"{x['n']} ({x['n']/total_n*100:.1f}%)", axis=1)
    fig = px.bar(ac, x="f", y="n", color_discrete_sequence=[BLUISH], text="text", labels={"f":"","n":""})
    fig.update_traces(textposition="outside", textfont=dict(size=9))
    fig = clean_layout(fig, title={"EN":"Age group","FR":"Groupe d'âge","ES":"Grupo de edad"}[lang], height=300)
    fig.update_xaxes(showgrid=False); fig.update_yaxes(gridcolor="#eeeeee")
    c2.plotly_chart(fig, use_container_width=True)
if "education_label" in df.columns:
    ec = df["education_label"].dropna().value_counts().reset_index(); ec.columns=["e","n"]
    ec["text"] = ec.apply(lambda x: f"{x['n']} ({x['n']/total_n*100:.1f}%)", axis=1)
    fig = px.bar(ec, x="n", y="e", orientation="h", color_discrete_sequence=[PINK], text="text", labels={"e":"","n":""})
    fig.update_traces(textposition="outside", textfont=dict(size=9))
    fig = clean_layout(fig, title={"EN":"Education","FR":"Éducation","ES":"Educación"}[lang], height=300)
    fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
    c3.plotly_chart(fig, use_container_width=True)

c1, c2 = st.columns(2)
if "weeks_clean" in df.columns and df["weeks_clean"].notna().sum()>0:
    fig = px.histogram(df["weeks_clean"].dropna(), nbins=16, color_discrete_sequence=[ORANGE],
                       labels={"value":{"EN":"Gestational weeks","FR":"Semaines gestation","ES":"Semanas gestación"}[lang],"count":""})
    fig = clean_layout(fig, title={"EN":"Gestational weeks","FR":"Semaines gestation","ES":"Semanas gestación"}[lang], height=260)
    fig.update_layout(showlegend=False, xaxis=dict(range=[28,46], dtick=1))
    fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(gridcolor="#eeeeee")
    c1.plotly_chart(fig, use_container_width=True)
if "no_deliveries" in df.columns:
    nd = df["no_deliveries"].dropna().value_counts().sort_index().reset_index(); nd.columns=["nd","count"]
    nd["text"] = nd.apply(lambda x: f"{x['count']} ({x['count']/total_n*100:.1f}%)", axis=1)
    nd["nd"] = nd["nd"].astype(int).astype(str)
    fig = px.bar(nd, x="nd", y="count", color_discrete_sequence=[SKY], text="text",
                 labels={"nd":{"EN":"Previous deliveries","FR":"Accouchements préc.","ES":"Partos anteriores"}[lang],"count":""})
    fig.update_traces(textposition="outside", textfont=dict(size=9))
    fig = clean_layout(fig, title={"EN":"Previous deliveries","FR":"Parité","ES":"Paridad"}[lang], height=260)
    fig.update_xaxes(showgrid=False); fig.update_yaxes(gridcolor="#eeeeee")
    c2.plotly_chart(fig, use_container_width=True)

# ── Prenatal education ────────────────────────────────────────────────────────
if "prenatal_attended" in df.columns and df["prenatal_attended"].notna().any():
    st.markdown(f'<div class="section-title">{"Prenatal Education" if lang=="EN" else "Éducation prénatale" if lang=="FR" else "Educación prenatal"}</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    # Chart 1: Attended Yes / No
    yes_lbl = {"EN":"Yes","FR":"Oui","ES":"Sí"}[lang]
    att = df["prenatal_attended"].dropna().value_counts().reset_index(); att.columns=["r","n"]
    att["text"] = att.apply(lambda x: f"{x['n']} ({x['n']/total_n*100:.1f}%)", axis=1)
    fig = px.bar(att, x="n", y="r", orientation="h",
                 color_discrete_sequence=[TEAL], text="text", labels={"r":"","n":""})
    fig.update_traces(textposition="outside", textfont=dict(size=9))
    fig = clean_layout(fig, title={"EN":"Attended prenatal education","FR":"A suivi éducation prénatale","ES":"Asistió a educación prenatal"}[lang], height=220)
    fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
    c1.plotly_chart(fig, use_container_width=True)

    # Chart 2: Where — detailed breakdown (all respondents)
    if "prenatal_detail" in df.columns and df["prenatal_detail"].notna().any():
        det = df["prenatal_detail"].dropna().value_counts().reset_index(); det.columns=["r","n"]
        n_answered = det["n"].sum()
        det["text"] = det.apply(lambda x: f"{x['n']} ({x['n']/n_answered*100:.1f}%)", axis=1)
        fig2 = px.bar(det, x="n", y="r", orientation="h",
                      color_discrete_sequence=[ORANGE], text="text", labels={"r":"","n":""})
        fig2.update_traces(textposition="outside", textfont=dict(size=9))
        fig2 = clean_layout(fig2, title={"EN":"Where (all respondents)","FR":"Où (tous les répondants)","ES":"Dónde (todos los encuestados)"}[lang],
                            height=max(240, len(det)*44+80))
        fig2.update_xaxes(gridcolor="#eeeeee"); fig2.update_yaxes(showgrid=False)
        c2.plotly_chart(fig2, use_container_width=True)

    # Chart 3: This facility vs elsewhere (among those who attended)
    if "prenatal_here" in df.columns:
        attended_df = df[df["prenatal_attended"] == yes_lbl]
        if len(attended_df) > 0 and attended_df["prenatal_here"].notna().any():
            loc = attended_df["prenatal_here"].dropna().value_counts().reset_index(); loc.columns=["r","n"]
            n_att = loc["n"].sum()
            loc["text"] = loc.apply(lambda x: f"{x['n']} ({x['n']/n_att*100:.1f}%)", axis=1)
            fig3 = px.bar(loc, x="n", y="r", orientation="h",
                          color_discrete_sequence=[BLUISH], text="text", labels={"r":"","n":""})
            fig3.update_traces(textposition="outside", textfont=dict(size=9))
            fig3 = clean_layout(fig3, title={"EN":"Location (among those who attended)","FR":"Lieu (parmi ceux qui ont participé)","ES":"Lugar (entre quienes asistieron)"}[lang], height=220)
            fig3.update_xaxes(gridcolor="#eeeeee"); fig3.update_yaxes(showgrid=False)
            st.plotly_chart(fig3, use_container_width=True)


st.markdown(f'<div class="section-title">{"Quality of Care — Likert Scales" if lang=="EN" else "Qualité des soins — Échelles de Likert" if lang=="FR" else "Calidad de Atención — Escalas Likert"}</div>', unsafe_allow_html=True)
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
    fig = px.bar(ldf, x="Pct", y="Dimension", color="Response", orientation="h", barmode="stack",
                 color_discrete_sequence=LIKERT_COLORS, category_orders={"Response": likert_order},
                 labels={"Pct":"%","Dimension":""})
    fig.update_layout(legend=dict(orientation="h",y=-0.22,x=0.5,xanchor="center",font=dict(size=10)),
                      margin=dict(t=8,b=110,l=8,r=8), height=480, plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

# ── Autonomy & Consent ────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{"Autonomy & Consent" if lang=="EN" else "Autonomie et consentement" if lang=="FR" else "Autonomía y consentimiento"}</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
for col_lbl, title, container in [
    ("decisions_label", {"EN":"Included in care decisions","FR":"Incluse dans les décisions","ES":"Incluida en decisiones"}[lang], c1),
    ("exam_label",      {"EN":"Vaginal exam w/o consent","FR":"Examen vaginal sans consent.","ES":"Examen vaginal sin consent."}[lang], c2),
]:
    if col_lbl in df.columns:
        vc = df[col_lbl].dropna().value_counts().reset_index(); vc.columns=["r","n"]
        vc["text"] = vc.apply(lambda x: f"{x['n']} ({x['n']/total_n*100:.1f}%)", axis=1)
        fig = px.bar(vc, x="n", y="r", orientation="h", color_discrete_sequence=[TEAL], text="text", labels={"r":"","n":""})
        fig.update_traces(textposition="outside", textfont=dict(size=10))
        fig = clean_layout(fig, title=title, height=270)
        fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
        container.plotly_chart(fig, use_container_width=True)

c1, c2 = st.columns(2)
for col_lbl, title, color, container in [
    ("epi_label",   {"EN":"Episiotomy","FR":"Épisiotomie","ES":"Episiotomía"}[lang],             TEAL,  c1),
    ("treat_label", {"EN":"Unwanted treatments","FR":"Soins non voulus","ES":"Tratos no deseados"}[lang], ORANGE, c2),
]:
    if col_lbl in df.columns:
        vc = df[col_lbl].dropna().value_counts().reset_index(); vc.columns=["r","n"]
        vc["text"] = vc.apply(lambda x: f"{x['n']} ({x['n']/total_n*100:.1f}%)", axis=1)
        fig = px.bar(vc, x="n", y="r", orientation="h", color_discrete_sequence=[color], text="text", labels={"r":"","n":""})
        fig.update_traces(textposition="outside", textfont=dict(size=9))
        fig = clean_layout(fig, title=title, height=250)
        fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
        container.plotly_chart(fig, use_container_width=True)

# ── Clinical Practices ────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{"Clinical Practices" if lang=="EN" else "Pratiques cliniques" if lang=="FR" else "Prácticas clínicas"}</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
for col_lbl, title, color, container in [
    ("skin_label",   {"EN":"Skin-to-skin","FR":"Peau à peau","ES":"Piel con piel"}[lang],                   TEAL,   c1),
    ("bf_label",     {"EN":"Breastfeeding support","FR":"Soutien allaitement","ES":"Apoyo lactancia"}[lang], BLUISH, c2),
    ("rooming_label",{"EN":"Baby with mother","FR":"Cohabitation","ES":"Bebé con madre"}[lang],              TEAL,   c3),
]:
    if col_lbl in df.columns:
        vc = df[col_lbl].dropna().value_counts().reset_index(); vc.columns=["r","n"]
        vc["text"] = vc.apply(lambda x: f"{x['n']} ({x['n']/total_n*100:.1f}%)", axis=1)
        fig = px.bar(vc, x="n", y="r", orientation="h", color_discrete_sequence=[color], text="text", labels={"r":"","n":""})
        fig.update_traces(textposition="outside", textfont=dict(size=9))
        fig = clean_layout(fig, title=title, height=290)
        fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
        container.plotly_chart(fig, use_container_width=True)

c1, c2, c3 = st.columns(3)
for col_lbl, title, color, container in [
    ("pharma_label",  {"EN":"Pain relief","FR":"Analgésie","ES":"Analgesia"}[lang],                            SKY,    c1),
    ("comfort_label", {"EN":"Non-pharma comfort","FR":"Confort non-pharma","ES":"Confort no-farma"}[lang],      ORANGE, c2),
    ("induce_label",  {"EN":"Labour induction","FR":"Déclenchement","ES":"Inducción"}[lang],                    PINK,   c3),
]:
    if col_lbl in df.columns:
        vc = df[col_lbl].dropna().value_counts().reset_index(); vc.columns=["r","n"]
        vc["text"] = vc.apply(lambda x: f"{x['n']} ({x['n']/total_n*100:.1f}%)", axis=1)
        fig = px.bar(vc, x="n", y="r", orientation="h", color_discrete_sequence=[color], text="text", labels={"r":"","n":""})
        fig.update_traces(textposition="outside", textfont=dict(size=9))
        fig = clean_layout(fig, title=title, height=270)
        fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
        container.plotly_chart(fig, use_container_width=True)

# ── Care Journey — Sankey ─────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{"Care Journey: Risk → Birth Method → Skin-to-Skin" if lang=="EN" else "Parcours : Risque → Accouchement → Peau à peau" if lang=="FR" else "Trayecto: Riesgo → Parto → Piel con piel"}</div>', unsafe_allow_html=True)
if "risk" in df.columns and "method" in df.columns and "skin_int" in df.columns:
    risk_lbl  = {1: {"EN":"High-risk","FR":"Grossesse à risque","ES":"Alto riesgo"}[lang],
                 2: {"EN":"Low-risk", "FR":"Grossesse normale", "ES":"Bajo riesgo"}[lang]}
    method_lbl = {k: METHOD_MAP[lang][k] for k in [1,2,3,4]}
    skin_lbl  = {1: {"EN":"✓ Immediate skin-to-skin","FR":"✓ Peau à peau immédiat","ES":"✓ Piel con piel inmediato"}[lang],
                 0: {"EN":"✗ Not immediate / No",    "FR":"✗ Pas immédiat / Non",  "ES":"✗ No inmediato / No"}[lang]}

    fdf = df[df["risk"].isin([1,2]) & df["method"].isin([1,2,3,4])].copy()
    fdf["skin_bin"] = (fdf["skin_int"] == 1).astype(int)
    total_n_sk = len(fdf)

    if total_n_sk > 0:
        all_nodes   = [risk_lbl[1], risk_lbl[2]] + [method_lbl[k] for k in [1,2,3,4]] + [skin_lbl[1], skin_lbl[0]]
        R, M, S     = 0, 2, 6
        sources, targets, values_sk, colors_sk, customdata = [], [], [], [], []

        for r in [1,2]:
            for m in [1,2,3,4]:
                n = len(fdf[(fdf["risk"]==r) & (fdf["method"]==m)])
                if n == 0: continue
                sources.append(R+(r-1)); targets.append(M+[1,2,3,4].index(m))
                values_sk.append(n); customdata.append(f"{n/total_n_sk*100:.1f}%")
                colors_sk.append("rgba(213,94,0,0.20)" if r==1 else "rgba(0,158,115,0.20)")

        for m in [1,2,3,4]:
            for s in [1,0]:
                n = len(fdf[(fdf["method"]==m) & (fdf["skin_bin"]==s)])
                if n == 0: continue
                sources.append(M+[1,2,3,4].index(m)); targets.append(S+(0 if s==1 else 1))
                values_sk.append(n); customdata.append(f"{n/total_n_sk*100:.1f}%")
                colors_sk.append("rgba(0,158,115,0.20)" if s==1 else "rgba(213,94,0,0.20)")

        node_colors = [VERMILION, TEAL, BLUISH, SKY, ORANGE, PINK, TEAL, VERMILION]
        fig = go.Figure(go.Sankey(
            arrangement="snap",
            node=dict(pad=20, thickness=24, line=dict(color="white", width=0.5),
                      label=all_nodes, color=node_colors,
                      hovertemplate="%{label}<br>%{value}<extra></extra>"),
            link=dict(source=sources, target=targets, value=values_sk,
                      color=colors_sk, customdata=customdata,
                      hovertemplate="%{source.label} → %{target.label}<br>%{value} (%{customdata})<extra></extra>")
        ))
        fig.update_traces(textfont=dict(size=12, family="DM Sans, sans-serif", color="#1a1a1a"))
        fig.update_layout(
            title=dict(text={"EN":"Care Journey: Risk Profile → Birth Method → Skin-to-Skin Contact",
                              "FR":"Parcours de soin : Profil de risque → Mode d'accouchement → Peau à peau",
                              "ES":"Trayecto: Perfil de riesgo → Vía de parto → Piel con piel"}[lang],
                       font=dict(size=13, family="DM Serif Display, serif", color="#1a1a1a"), x=0, xanchor="left"),
            margin=dict(t=64,b=16,l=8,r=8), height=440,
            paper_bgcolor="white", font=dict(family="DM Sans, sans-serif", size=11)
        )
        st.plotly_chart(fig, use_container_width=True)


st.markdown(f'<div class="section-title">{"Satisfaction" if lang=="EN" else "Satisfaction" if lang=="FR" else "Satisfacción"}</div>', unsafe_allow_html=True)
if "expect_label" in df.columns and "satisfaction_label" in df.columns:
    c1, c2 = st.columns(2)
    q_order = QUALITY_ORDER[lang]
    for col_lbl, title, container in [
        ("expect_label",       {"EN":"Expected care","FR":"Soins attendus","ES":"Atención esperada"}[lang],  c1),
        ("satisfaction_label", {"EN":"Actual care","FR":"Soins reçus","ES":"Atención recibida"}[lang],       c2),
    ]:
        vc = df[col_lbl].value_counts().reindex(q_order, fill_value=0).reset_index(); vc.columns=["r","n"]
        vc["text"] = vc.apply(lambda x: f"{x['n']} ({x['n']/total_n*100:.1f}%)", axis=1)
        fig = px.bar(vc, x="r", y="n", color="r", color_discrete_sequence=QUALITY_COLORS,
                     category_orders={"r":q_order}, text="text", labels={"r":"","n":""})
        fig.update_traces(textposition="outside", textfont=dict(size=9))
        fig = clean_layout(fig, title=title, height=310)
        fig.update_layout(showlegend=False)
        fig.update_xaxes(showgrid=False); fig.update_yaxes(gridcolor="#eeeeee")
        container.plotly_chart(fig, use_container_width=True)

# ── Emotions ──────────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{"How Women Felt" if lang=="EN" else "Ressenti des femmes" if lang=="FR" else "Cómo se sintieron"}</div>', unsafe_allow_html=True)
if "emotion" in df.columns:
    emo_labels = EMOTION_LABELS_W[lang]
    pos = POSITIVE_EMO_W[lang]
    exhausted = emo_labels[5]
    counts = parse_multiselect(df["emotion"], list(emo_labels.keys()))
    pos_lbl = {"EN":"Positive","FR":"Positif","ES":"Positivo"}[lang]
    neg_lbl = {"EN":"Negative","FR":"Négatif","ES":"Negativo"}[lang]
    rows_all = [{"Emotion":lbl,"Pct":round(counts[k]/total_n*100,1),
                 "Type":pos_lbl if lbl in pos else neg_lbl} for k,lbl in emo_labels.items()]
    rows_nox = [r for r in rows_all if r["Emotion"]!=exhausted]
    c1, c2 = st.columns(2)
    for container, rows, subtitle in [
        (c1, rows_all, {"EN":"All emotions","FR":"Toutes émotions","ES":"Todas las emociones"}[lang]),
        (c2, rows_nox, {"EN":"Excl. 'Exhausted'","FR":"Sans 'Épuisée'","ES":"Sin 'Agotada'"}[lang]),
    ]:
        edf = pd.DataFrame(rows).sort_values("Pct", ascending=True)
        container.markdown(f"**{subtitle}**")
        fig = px.bar(edf, x="Pct", y="Emotion", color="Type", orientation="h",
                     color_discrete_map={pos_lbl:TEAL, neg_lbl:VERMILION},
                     labels={"Pct":"%","Emotion":""})
        fig.update_layout(legend=dict(orientation="h",y=-0.12,x=0.5,xanchor="center"),
                          margin=dict(t=8,b=60,l=8,r=8), height=420,
                          plot_bgcolor="white", paper_bgcolor="white")
        fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
        container.plotly_chart(fig, use_container_width=True)

# ── Emotional experience by birth method — Treemap ───────────────────────────
if "method_label" in df.columns and "method" in df.columns and "emotion" in df.columns:
    pos_keys = [1,4,6,7,9,11]
    neg_keys = [2,3,5,8,10,12]
    pos_lbl  = {"EN":"Positive emotions","FR":"Émotions positives","ES":"Emociones positivas"}[lang]
    neg_lbl  = {"EN":"Negative emotions","FR":"Émotions négatives","ES":"Emociones negativas"}[lang]
    root_lbl = {"EN":"All births","FR":"Tous accouchements","ES":"Todos los partos"}[lang]

    tm_rows = []
    for mcode in [1,2,3,4,5]:
        mlabel = METHOD_MAP[lang].get(mcode)
        if not mlabel: continue
        sub = df[(df["method"]==mcode) & df["emotion"].notna()]
        if len(sub) < 5: continue
        pos_n = sum(parse_multiselect(sub["emotion"], [k])[k] for k in pos_keys)
        neg_n = sum(parse_multiselect(sub["emotion"], [k])[k] for k in neg_keys)
        tm_rows.append({"method":mlabel, "type":pos_lbl, "n":pos_n})
        tm_rows.append({"method":mlabel, "type":neg_lbl, "n":neg_n})

    if tm_rows:
        tmdf = pd.DataFrame(tm_rows)
        method_palette = [BLUISH, TEAL, ORANGE, PINK, SKY]
        ids, labels, parents, values_tm, colors_tm = ["root"], [root_lbl], [""], [0], ["#eef2f0"]

        for i, m in enumerate(tmdf["method"].unique().tolist()):
            mid = f"m_{i}"
            ids.append(mid); labels.append(m); parents.append("root")
            values_tm.append(int(tmdf[tmdf["method"]==m]["n"].sum()))
            colors_tm.append(method_palette[i % len(method_palette)])
            for _, row in tmdf[tmdf["method"]==m].iterrows():
                lid = f"l_{i}_{row['type']}"
                ids.append(lid); labels.append(row["type"]); parents.append(mid)
                values_tm.append(int(row["n"]))
                colors_tm.append("#a8d8c8" if row["type"]==pos_lbl else "#f0c4b0")

        fig = go.Figure(go.Treemap(
            ids=ids, labels=labels, parents=parents, values=values_tm,
            marker=dict(colors=colors_tm, line=dict(width=2, color="white"), cornerradius=5),
            textinfo="label+percent parent",
            textfont=dict(size=12, family="DM Sans, sans-serif", color="#2a2a2a"),
            hovertemplate="<b>%{label}</b><br>%{value}<extra></extra>",
            branchvalues="remainder",
        ))
        fig.update_layout(
            title=dict(text={"EN":"Emotional Experience by Birth Method",
                              "FR":"Vécu émotionnel par mode d'accouchement",
                              "ES":"Experiencia emocional por vía de parto"}[lang],
                       font=dict(size=13, family="DM Serif Display, serif", color="#1a1a1a"),
                       x=0, xanchor="left", y=0.98, yanchor="top"),
            margin=dict(t=44,b=8,l=8,r=8), height=380,
            paper_bgcolor="white", font=dict(family="DM Sans, sans-serif"), showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)


st.markdown(f'<div class="section-title">{"Info Before Discharge" if lang=="EN" else "Info avant sortie" if lang=="FR" else "Info antes del alta"}</div>', unsafe_allow_html=True)
if "info" in df.columns:
    counts = parse_multiselect(df["info"], list(INFO_LABELS_W[lang].keys()))
    rows = [{"Topic":lbl,"n":counts[k],"Pct":round(counts[k]/total_n*100,1)} for k,lbl in INFO_LABELS_W[lang].items()]
    idf = pd.DataFrame(rows).sort_values("Pct")
    idf["text"] = idf.apply(lambda x: f"{x['n']} ({x['Pct']}%)", axis=1)
    fig = px.bar(idf, x="Pct", y="Topic", orientation="h", color_discrete_sequence=[PINK], text="text", labels={"Pct":"%","Topic":""})
    fig.update_traces(textposition="outside", textfont=dict(size=9))
    fig.update_layout(margin=dict(t=16,b=8,l=8,r=8), height=220, plot_bgcolor="white", paper_bgcolor="white")
    fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
    st.plotly_chart(fig, use_container_width=True)

# ── Mistreatment ──────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{"Mistreatment & Respect" if lang=="EN" else "Maltraitance et respect" if lang=="FR" else "Maltrato y respeto"}</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
for col_lbl, title, color, container in [
    ("verbal_label",  {"EN":"Verbal abuse","FR":"Violence verbale","ES":"Violencia verbal"}[lang],     VERMILION, c1),
    ("phys_label",    {"EN":"Physical abuse","FR":"Violence physique","ES":"Violencia física"}[lang],  VERMILION, c2),
    ("payment_label", {"EN":"Cost informed","FR":"Coût informé","ES":"Informada del costo"}[lang],     BLUISH,    c3),
]:
    if col_lbl in df.columns:
        vc = df[col_lbl].dropna().value_counts().reset_index(); vc.columns=["r","n"]
        vc["text"] = vc.apply(lambda x: f"{x['n']} ({x['n']/total_n*100:.1f}%)", axis=1)
        fig = px.bar(vc, x="n", y="r", orientation="h", color_discrete_sequence=[color], text="text", labels={"r":"","n":""})
        fig.update_traces(textposition="outside", textfont=dict(size=9))
        fig = clean_layout(fig, title=title, height=260)
        fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
        container.plotly_chart(fig, use_container_width=True)

# ── Raw data ──────────────────────────────────────────────────────────────────
with st.expander({"EN":"📋 Raw data","FR":"📋 Données brutes","ES":"📋 Datos brutos"}[lang]):
    hide = [c for c in df.columns if c.startswith("_") or c=="meta/rootUuid"]
    show = [c for c in df.columns if c not in hide]
    st.dataframe(df[show], use_container_width=True, height=400)
    st.download_button({"EN":"⬇ Download CSV","FR":"⬇ Télécharger CSV","ES":"⬇ Descargar CSV"}[lang],
                       df[show].to_csv(index=False).encode("utf-8"),
                       f"ici_women_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
