"""ICI — Companion Experience"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ici_shared import (
    FACILITIES, TEAL, ORANGE, SKY, VERMILION, BLUISH, PINK,
    LIKERT_COLORS, QUALITY_COLORS, PIE_COLORS,
    inject_css, sidebar_logo, sidebar_facility_header, logout_button, lang_selector, date_filter,
    load_companion, load_women, prep_companion, prep_women, to_int, parse_multiselect, clean_layout,
    get_facility_ids, get_role,
    LIKERT5_MAP, QUALITY_ORDER, LIKERT_QS_C,
    COMP_EMOTION_MAP, POSITIVE_EMO_C, INFO_LABELS_C,
)

inject_css()
sidebar_logo()

fac_ids = get_facility_ids()
if not fac_ids:
    st.error("Not logged in."); st.stop()

lang = lang_selector("lang_c")
sidebar_facility_header({"EN": "Companion Experience", "FR": "Expérience des acompagnants", "ES": "Experiencia del Acompañante"}[lang])

L = {"EN":{"loading":"Loading…","no_data":"No companion data available."},
     "FR":{"loading":"Chargement…","no_data":"Aucune donnée acompagnant."},
     "ES":{"loading":"Cargando…","no_data":"Sin datos de acompañantes."}}[lang]

with st.spinner(L["loading"]):
    raw = load_companion(fac_ids)
if raw.empty:
    st.info(L["no_data"]); st.stop()
df = prep_companion(raw, lang)


# Admin: facility filter BEFORE date_filter
if get_role() == "admin" and len(fac_ids) > 1:
    fac_opts_labels = {fid: FACILITIES[fid]["display_name"] for fid in fac_ids}
    sel_fac = st.sidebar.selectbox(
        {"EN":"Facility","FR":"Établissement","ES":"Establecimiento"}[lang],
        options=["all"] + fac_ids,
        format_func=lambda x: {"EN":"All","FR":"Tous","ES":"Todos"}[lang] if x=="all" else fac_opts_labels[x],
        key="fac_filter_c"
    )
    if st.session_state.get("_prev_fac_c") != sel_fac:
        st.session_state["_prev_fac_c"] = sel_fac
        for k in ["sy_c", "sm_c", "ey_c", "em_c"]:
            st.session_state.pop(k, None)
        st.rerun()
    if sel_fac != "all":
        df = df[df["_facility_id"] == sel_fac]

df = date_filter(df, key="c")
total_n = len(df)
if total_n == 0:
    st.warning({"EN":"No data for selected period.","FR":"Aucune donnée.","ES":"Sin datos."}[lang]); st.stop()

st.sidebar.metric({"EN":"Responses","FR":"Réponses","ES":"Respuestas"}[lang], total_n)
if st.sidebar.button({"EN":"↻ Refresh","FR":"↻ Actualiser","ES":"↻ Actualizar"}[lang]):
    st.cache_data.clear(); st.rerun()
logout_button()

# ── Hero ──────────────────────────────────────────────────────────────────────
sat_good   = (df["satisfaction"].isin([4,5])).sum()/total_n*100 if "satisfaction" in df.columns else 0
pres_lab   = (df["complab"]==1).sum()/total_n*100 if "complab" in df.columns else 0
pres_del   = (df["comp_deliv"]==1).sum()/total_n*100 if "comp_deliv" in df.columns else 0
confident  = (df["accompany"].isin([4,5])).sum()/total_n*100 if "accompany" in df.columns else 0
if "age" in df.columns and df["age"].notna().sum()>0:
    a = df["age"]; age_disp = f"{a.mean():.0f} ({int(a.min())}–{int(a.max())})"
else:
    age_disp = "–"

titles = {"EN":"Companion Experience Dashboard","FR":"Expérience des Acompagnants","ES":"Experiencia del Acompañante"}
captions = {"EN":"ICI — Companion Questionnaire","FR":"ICI — Questionnaire acompagnant","ES":"ICI — Cuestionario del Acompañante"}
kpi = {"EN":{"total":"Total responses","pos":"rated care Good/Very good","lab":"present during labour",
             "del":"present during birth","conf":"felt confident & prepared","age":"age (mean, range)"},
       "FR":{"total":"Total réponses","pos":"soins Bons/Très bons","lab":"présents lors du travail",
             "del":"présents lors de l'accouchement","conf":"confiants et préparés","age":"âge (moy., étendue)"},
       "ES":{"total":"Total respuestas","pos":"atención Buena/Muy buena","lab":"presente en el parto",
             "del":"presente en el nacimiento","conf":"se sentía seguro","age":"edad (moy., rango)"}}[lang]

st.markdown(f"""
<div class="hero-comp">
  <div class="hero-title">{titles[lang]}</div>
  <div class="hero-caption">{captions[lang]}</div>
  <div class="hero-stats">
    <div class="hero-stat"><div class="hero-stat-num">{total_n:,}</div><div class="hero-stat-label">{kpi['total']}</div></div>
    <div class="hero-stat"><div class="hero-stat-num">{sat_good:.0f}%</div><div class="hero-stat-label">{kpi['pos']}</div></div>
    <div class="hero-stat"><div class="hero-stat-num">{pres_lab:.0f}%</div><div class="hero-stat-label">{kpi['lab']}</div></div>
    <div class="hero-stat"><div class="hero-stat-num">{pres_del:.0f}%</div><div class="hero-stat-label">{kpi['del']}</div></div>
    <div class="hero-stat"><div class="hero-stat-num">{confident:.0f}%</div><div class="hero-stat-label">{kpi['conf']}</div></div>
  </div>
</div>""", unsafe_allow_html=True)

# ── Timeline ──────────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{"Responses Over Time" if lang=="EN" else "Réponses dans le temps" if lang=="FR" else "Respuestas en el tiempo"}</div>', unsafe_allow_html=True)
if "_submission_time" in df.columns and df["_submission_time"].notna().any():
    grp_opts = {"EN":["Month","Week","Day"],"FR":["Mois","Semaine","Jour"],"ES":["Mes","Semana","Día"]}[lang]
    freq_map = {grp_opts[0]:"MS", grp_opts[1]:"W", grp_opts[2]:"D"}
    grp = st.radio({"EN":"Group by","FR":"Regrouper par","ES":"Agrupar por"}[lang], grp_opts, horizontal=True, key="grp_c")
    ts = df.groupby(pd.Grouper(key="_submission_time", freq=freq_map[grp])).size().reset_index(name="n")
    ts = ts[ts["n"]>0]
    dtfmt = {grp_opts[0]: "%b %Y", grp_opts[1]: "%d %b %Y", grp_opts[2]: "%d %b %Y"}[grp]
    ts["_label"] = ts["_submission_time"].dt.strftime(dtfmt)
    fig = px.area(ts, x="_label", y="n", color_discrete_sequence=[BLUISH],
                  labels={"_label":"","n":{"EN":"Responses","FR":"Réponses","ES":"Respuestas"}[lang]})
    fig.update_traces(line_width=2, fillcolor="rgba(0,114,178,0.12)")
    fig.update_layout(height=200, margin=dict(t=8,b=8,l=8,r=8), plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

# ── Profile ───────────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{"Companion Profile" if lang=="EN" else "Profil des acompagnants" if lang=="FR" else "Perfil del Acompañante"}</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
for col_lbl, title, color, container in [
    ("comp_detail_label", {"EN":"Relationship","FR":"Relation","ES":"Relación"}[lang],         BLUISH, c1),
    ("education_label",   {"EN":"Education","FR":"Éducation","ES":"Educación"}[lang],          PINK,   c2),
    ("method_label",      {"EN":"Birth method (observed)","FR":"Mode accouchement","ES":"Vía de nacimiento"}[lang], TEAL, c3),
]:
    if col_lbl in df.columns:
        vc = df[col_lbl].dropna().value_counts().reset_index(); vc.columns=["r","n"]
        vc["text"] = vc.apply(lambda x: f"{x['n']} ({x['n']/total_n*100:.1f}%)", axis=1)
        fig = px.bar(vc, x="n", y="r", orientation="h", color_discrete_sequence=[color], text="text", labels={"r":"","n":""})
        fig.update_traces(textposition="outside", textfont=dict(size=9))
        fig = clean_layout(fig, title=title, height=260)
        fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
        container.plotly_chart(fig, use_container_width=True)

# ── Presence ──────────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{"Presence During Labour & Birth" if lang=="EN" else "Présence durant le travail" if lang=="FR" else "Presencia durante el parto"}</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
for col_lbl, title, color, container in [
    ("complab_label",    {"EN":"During labour","FR":"Durant travail","ES":"Durante el parto"}[lang],  TEAL,   c1),
    ("comp_deliv_label", {"EN":"During birth","FR":"Durant naissance","ES":"Durante el nacimiento"}[lang], BLUISH, c2),
    ("accompany_label",  {"EN":"Felt confident before discharge","FR":"Confiant avant sortie","ES":"Seguro antes del alta"}[lang], ORANGE, c3),
]:
    if col_lbl in df.columns:
        vc = df[col_lbl].dropna().value_counts().reset_index(); vc.columns=["r","n"]
        vc["text"] = vc.apply(lambda x: f"{x['n']} ({x['n']/total_n*100:.1f}%)", axis=1)
        fig = px.bar(vc, x="n", y="r", orientation="h", color_discrete_sequence=[color], text="text", labels={"r":"","n":""})
        fig.update_traces(textposition="outside", textfont=dict(size=9))
        fig = clean_layout(fig, title=title, height=260)
        fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
        container.plotly_chart(fig, use_container_width=True)

# ── Likert ────────────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{"Care Quality — Likert" if lang=="EN" else "Qualité des soins — Likert" if lang=="FR" else "Calidad de Atención — Likert"}</div>', unsafe_allow_html=True)
likert_order = list(LIKERT5_MAP[lang].values())
rows = []
for col, label in LIKERT_QS_C[lang].items():
    lbl = col + "_label"
    if lbl in df.columns:
        vc = df[lbl].value_counts(normalize=True).mul(100).round(1)
        for cat in likert_order:
            rows.append({"Dimension":label, "Response":cat, "Pct":vc.get(cat,0)})
if rows:
    ldf = pd.DataFrame(rows)
    fig = px.bar(ldf, x="Pct", y="Dimension", color="Response", orientation="h", barmode="stack",
                 color_discrete_sequence=LIKERT_COLORS, category_orders={"Response":likert_order},
                 labels={"Pct":"%","Dimension":""})
    fig.update_layout(legend=dict(orientation="h",y=-0.22,x=0.5,xanchor="center"),
                      margin=dict(t=8,b=110,l=8,r=8), height=400, plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

# ── Autonomy ──────────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{"Autonomy & Respect" if lang=="EN" else "Autonomie et respect" if lang=="FR" else "Autonomía y respeto"}</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
for col_lbl, title, color, container in [
    ("decisions_label", {"EN":"Included in decisions","FR":"Inclus dans décisions","ES":"Incluido en decisiones"}[lang], TEAL,   c1),
    ("values_label",    {"EN":"Beliefs respected","FR":"Croyances respectées","ES":"Creencias respetadas"}[lang],        BLUISH, c2),
    ("comp_001_label",  {"EN":"Felt respected as companion","FR":"Respecté comme acompagnant","ES":"Respetado como acompañante"}[lang], SKY, c3),
]:
    if col_lbl in df.columns:
        vc = df[col_lbl].dropna().value_counts().reset_index(); vc.columns=["r","n"]
        vc["text"] = vc.apply(lambda x: f"{x['n']} ({x['n']/total_n*100:.1f}%)", axis=1)
        fig = px.bar(vc, x="n", y="r", orientation="h", color_discrete_sequence=[color], text="text", labels={"r":"","n":""})
        fig.update_traces(textposition="outside", textfont=dict(size=10))
        fig = clean_layout(fig, title=title, height=270)
        fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
        container.plotly_chart(fig, use_container_width=True)

# ── Mistreatment ──────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{"Mistreatment Observed" if lang=="EN" else "Maltraitance observée" if lang=="FR" else "Maltrato observado"}</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
for col_lbl, title, color, container in [
    ("verbal_label",  {"EN":"Verbal abuse","FR":"Violence verbale","ES":"Violencia verbal"}[lang],    VERMILION, c1),
    ("phys_label",    {"EN":"Physical abuse","FR":"Violence physique","ES":"Violencia física"}[lang], VERMILION, c2),
    ("payment_label", {"EN":"Cost informed","FR":"Coût informé","ES":"Informado del costo"}[lang],    BLUISH,    c3),
]:
    if col_lbl in df.columns:
        vc = df[col_lbl].dropna().value_counts().reset_index(); vc.columns=["r","n"]
        vc["text"] = vc.apply(lambda x: f"{x['n']} ({x['n']/total_n*100:.1f}%)", axis=1)
        fig = px.bar(vc, x="n", y="r", orientation="h", color_discrete_sequence=[color], text="text", labels={"r":"","n":""})
        fig.update_traces(textposition="outside", textfont=dict(size=9))
        fig = clean_layout(fig, title=title, height=260)
        fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
        container.plotly_chart(fig, use_container_width=True)

# ── Clinical ──────────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{"Clinical & Practical" if lang=="EN" else "Clinique et pratique" if lang=="FR" else "Clínico y práctico"}</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
for col_lbl, title, color, container in [
    ("comfort_label",  {"EN":"Comfort measures encouraged","FR":"Mesures confort","ES":"Medidas de confort"}[lang], TEAL,   c1),
    ("pharma_label",   {"EN":"Pain relief","FR":"Analgésie","ES":"Analgesia"}[lang],                               SKY,    c2),
    ("choices_label",  {"EN":"Treatment options discussed","FR":"Options traitement","ES":"Opciones tratamiento"}[lang], BLUISH, c3),
]:
    if col_lbl in df.columns:
        vc = df[col_lbl].dropna().value_counts().reset_index(); vc.columns=["r","n"]
        vc["text"] = vc.apply(lambda x: f"{x['n']} ({x['n']/total_n*100:.1f}%)", axis=1)
        fig = px.bar(vc, x="n", y="r", orientation="h", color_discrete_sequence=[color], text="text", labels={"r":"","n":""})
        fig.update_traces(textposition="outside", textfont=dict(size=9))
        fig = clean_layout(fig, title=title, height=270)
        fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
        container.plotly_chart(fig, use_container_width=True)

c1, c2, c3 = st.columns(3)
for col_lbl, title, color, container in [
    ("rooming_label", {"EN":"Baby with mother","FR":"Bébé avec mère","ES":"Bebé con madre"}[lang],     TEAL,   c1),
    ("milk_label",    {"EN":"Breastfeeding only","FR":"Allaitement exclusif","ES":"Lactancia exclusiva"}[lang], ORANGE, c2),
    ("emergency_label",{"EN":"Confident in emergency care","FR":"Confiant en urgences","ES":"Confianza en urgencias"}[lang], BLUISH, c3),
]:
    if col_lbl in df.columns:
        vc = df[col_lbl].dropna().value_counts().reset_index(); vc.columns=["r","n"]
        vc["text"] = vc.apply(lambda x: f"{x['n']} ({x['n']/total_n*100:.1f}%)", axis=1)
        fig = px.bar(vc, x="n", y="r", orientation="h", color_discrete_sequence=[color], text="text", labels={"r":"","n":""})
        fig.update_traces(textposition="outside", textfont=dict(size=9))
        fig = clean_layout(fig, title=title, height=270)
        fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
        container.plotly_chart(fig, use_container_width=True)

# ── Satisfaction ──────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{"Satisfaction" if lang=="EN" else "Satisfaction" if lang=="FR" else "Satisfacción"}</div>', unsafe_allow_html=True)
if "expect_label" in df.columns and "satisfaction_label" in df.columns:
    c1, c2 = st.columns(2)
    q_order = QUALITY_ORDER[lang]
    for col_lbl, title, container in [
        ("expect_label",       {"EN":"Expected","FR":"Attendu","ES":"Esperado"}[lang],      c1),
        ("satisfaction_label", {"EN":"Actual","FR":"Reçu","ES":"Recibido"}[lang],           c2),
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
st.markdown(f'<div class="section-title">{"Companion Emotions" if lang=="EN" else "Émotions du acompagnant" if lang=="FR" else "Emociones del Acompañante"}</div>', unsafe_allow_html=True)
if "emotion_label" in df.columns:
    pos_set = POSITIVE_EMO_C.get(lang, POSITIVE_EMO_C["EN"])
    emo_vc = df["emotion_label"].dropna().value_counts().reset_index(); emo_vc.columns=["Emotion","n"]
    emo_vc["Pct"]  = (emo_vc["n"]/total_n*100).round(1)
    emo_vc["text"] = emo_vc.apply(lambda x: f"{x['n']} ({x['Pct']}%)", axis=1)
    pos_lbl = {"EN":"Positive","FR":"Positif","ES":"Positivo"}[lang]
    neg_lbl = {"EN":"Negative","FR":"Négatif","ES":"Negativo"}[lang]
    emo_vc["Type"] = emo_vc["Emotion"].apply(lambda e: pos_lbl if e in pos_set else neg_lbl)
    emo_vc = emo_vc.sort_values("Pct", ascending=True)
    fig = px.bar(emo_vc, x="Pct", y="Emotion", color="Type", orientation="h",
                 color_discrete_map={pos_lbl:TEAL, neg_lbl:VERMILION},
                 labels={"Pct":"%","Emotion":""}, text="text")
    fig.update_traces(textposition="outside", textfont=dict(size=9))
    fig.update_layout(legend=dict(orientation="h",y=-0.12,x=0.5,xanchor="center"),
                      margin=dict(t=8,b=60,l=8,r=8), height=440,
                      plot_bgcolor="white", paper_bgcolor="white")
    fig.update_xaxes(gridcolor="#eeeeee"); fig.update_yaxes(showgrid=False)
    st.caption({"EN":"Single emotion per respondent.","FR":"Une émotion par répondant.","ES":"Una emoción por encuestado."}[lang])
    st.plotly_chart(fig, use_container_width=True)

# ── Paired data (companion ↔ women, linked by 'id') ──────────────────────────
st.markdown(f'<div class="section-title">{"Paired Data — Companion & Mother" if lang=="EN" else "Données croisées — Acompagnant & Mère" if lang=="FR" else "Datos cruzados — Acompañante & Madre"}</div>', unsafe_allow_html=True)

if "id" in df.columns and df["id"].notna().any():
    with st.spinner({"EN":"Loading women's data for matching…","FR":"Chargement données femmes…","ES":"Cargando datos de mujeres…"}[lang]):
        raw_w = load_women(fac_ids)

    if not raw_w.empty:
        import plotly.graph_objects as go
        from ici_shared import to_int as _to_int

        # Apply same facility filter as companion if admin selected one
        raw_w2 = raw_w.copy()
        if get_role() == "admin":
            sel = st.session_state.get("fac_filter_c", "all")
            if sel != "all":
                raw_w2 = raw_w2[raw_w2["_facility_id"] == sel]

        # Work on raw numeric values — convert id to string, coerce numeric fields
        pair_fields = ["satisfaction","expect","coop","decisions","respect","privacy",
                       "spoke","introduction","comfort","pharma",
                       "info/1","info/2","info/3","info/4"]

        def extract_raw(frame, label):
            out = frame.copy()
            out["id"] = out["id"].astype(str).str.strip()
            for f in pair_fields:
                if f in out.columns:
                    out[f] = _to_int(out[f])
            keep = ["id"] + [f for f in pair_fields if f in out.columns]
            return out[keep]

        rc = extract_raw(raw, "c")   # raw companion (already filtered by fac/date above)
        rw = extract_raw(raw_w2, "w")

        paired = rc.merge(rw, on="id", suffixes=("_c","_w"))
        n_paired = len(paired)

        if n_paired == 0:
            st.info({"EN":"No matched pairs found for the selected period/facility.",
                     "FR":"Aucune paire trouvée pour la période/établissement sélectionné.",
                     "ES":"No se encontraron pares para el período/establecimiento seleccionado."}[lang])
        else:
            st.caption({"EN":f"{n_paired} matched pairs (companion + mother, same ID).",
                        "FR":f"{n_paired} paires identifiées (acompagnant + mère, même ID).",
                        "ES":f"{n_paired} pares identificados (acompañante + madre, mismo ID)."}[lang])

            lbl_c = {"EN":"Companion","FR":"Acompagnant","ES":"Acompañante"}[lang]
            lbl_w = {"EN":"Mother","FR":"Mère","ES":"Madre"}[lang]

            def pct(series, vals):
                s = series.dropna()
                return round(s.isin(vals).sum() / len(s) * 100, 1) if len(s) else 0

            def paired_bar(rows_data, title, height=300):
                """rows_data: list of (label, pct_mother, pct_companion)"""
                labels = [r[0] for r in rows_data]
                vals_w = [r[1] for r in rows_data]
                vals_c = [r[2] for r in rows_data]
                fig = go.Figure()
                fig.add_bar(name=lbl_w, x=labels, y=vals_w, marker_color=TEAL,
                            text=[f"{v:.1f}%" for v in vals_w],
                            textposition="outside", textfont=dict(size=9))
                fig.add_bar(name=lbl_c, x=labels, y=vals_c, marker_color=BLUISH,
                            text=[f"{v:.1f}%" for v in vals_c],
                            textposition="outside", textfont=dict(size=9))
                fig.update_layout(
                    barmode="group", height=height,
                    margin=dict(t=44, b=70, l=8, r=8),
                    plot_bgcolor="white", paper_bgcolor="white",
                    yaxis=dict(range=[0,115], gridcolor="#eeeeee", title="%"),
                    xaxis=dict(showgrid=False),
                    legend=dict(orientation="h", y=-0.22, x=0.5, xanchor="center"),
                    title=dict(text=title,
                               font=dict(size=13, family="DM Serif Display, serif"),
                               x=0, xanchor="left"),
                )
                return fig

            # ── 1. Satisfaction — separate from expectations ──────────────────
            c1, c2 = st.columns(2)

            if "satisfaction_c" in paired and "satisfaction_w" in paired:
                c1.plotly_chart(paired_bar(
                    [( {"EN":"Good/Very good","FR":"Bien/Très bien","ES":"Buena/Muy buena"}[lang],
                       pct(paired["satisfaction_w"], [4,5]),
                       pct(paired["satisfaction_c"], [4,5]) )],
                    {"EN":"Overall satisfaction","FR":"Satisfaction globale","ES":"Satisfacción general"}[lang],
                    height=280), use_container_width=True)

            if "expect_c" in paired and "expect_w" in paired:
                c2.plotly_chart(paired_bar(
                    [( {"EN":"Expected good/very good","FR":"Attendait bien/très bien","ES":"Esperaba buena/muy buena"}[lang],
                       pct(paired["expect_w"], [4,5]),
                       pct(paired["expect_c"], [4,5]) )],
                    {"EN":"Expectations before arrival","FR":"Attentes avant l'arrivée","ES":"Expectativas antes de llegar"}[lang],
                    height=280), use_container_width=True)

            # ── 2. Staff quality — respect, privacy, coop ────────────────────
            staff_rows = []
            for col, lbl in [
                ("respect",  {"EN":"Treated respectfully (Always)","FR":"Traité avec respect (Toujours)","ES":"Con respeto (Siempre)"}[lang]),
                ("privacy",  {"EN":"Privacy protected (Always)","FR":"Intimité protégée (Toujours)","ES":"Privacidad protegida (Siempre)"}[lang]),
                ("coop",     {"EN":"Staff coordinated (Always)","FR":"Personnel coordonné (Toujours)","ES":"Personal coordinado (Siempre)"}[lang]),
            ]:
                cc, wc = f"{col}_c", f"{col}_w"
                if cc in paired and wc in paired:
                    staff_rows.append((lbl, pct(paired[wc], [5]), pct(paired[cc], [5])))
            if staff_rows:
                st.plotly_chart(paired_bar(staff_rows,
                    {"EN":"Respect, Privacy & Coordination","FR":"Respect, Intimité & Coordination","ES":"Respeto, Privacidad y Coordinación"}[lang],
                    height=320), use_container_width=True)

            # ── 3. Communication ──────────────────────────────────────────────
            c3, c4 = st.columns(2)
            comm_rows = []
            for col, lbl in [
                ("spoke",        {"EN":"Staff spoke clearly (Always)","FR":"Personnel clair (Toujours)","ES":"Personal habló claro (Siempre)"}[lang]),
                ("introduction", {"EN":"Staff introduced themselves (Always)","FR":"Personnel présenté (Toujours)","ES":"Personal se presentó (Siempre)"}[lang]),
            ]:
                cc, wc = f"{col}_c", f"{col}_w"
                if cc in paired and wc in paired:
                    comm_rows.append((lbl, pct(paired[wc], [5]), pct(paired[cc], [5])))
            if comm_rows:
                c3.plotly_chart(paired_bar(comm_rows,
                    {"EN":"Communication","FR":"Communication","ES":"Comunicación"}[lang],
                    height=300), use_container_width=True)

            # ── 4. Decisions & information ────────────────────────────────────
            dec_rows = []
            if "decisions_c" in paired and "decisions_w" in paired:
                dec_rows.append((
                    {"EN":"Yes, with full information","FR":"Oui, avec toute l'info","ES":"Sí, con toda la información"}[lang],
                    pct(paired["decisions_w"], [1]),
                    pct(paired["decisions_c"], [1]),
                ))
            if dec_rows:
                c4.plotly_chart(paired_bar(dec_rows,
                    {"EN":"Included in decisions","FR":"Inclus dans les décisions","ES":"Incluidos en decisiones"}[lang],
                    height=300), use_container_width=True)

            # ── 5. Discharge information ──────────────────────────────────────
            info_rows = []
            info_labels = {
                "info/1": {"EN":"Baby care","FR":"Soins bébé","ES":"Cuidar bebé"},
                "info/2": {"EN":"Family planning","FR":"Planif. familiar","ES":"Plan. familiar"},
                "info/3": {"EN":"Warning signs","FR":"Signes d'alarme","ES":"Señales de alarma"},
                "info/4": {"EN":"Follow-up","FR":"Suivi","ES":"Seguimiento"},
            }
            for col, lbls in info_labels.items():
                cc, wc = f"{col}_c", f"{col}_w"
                if cc in paired and wc in paired:
                    info_rows.append((lbls[lang], pct(paired[wc], [1]), pct(paired[cc], [1])))
            if info_rows:
                st.plotly_chart(paired_bar(info_rows,
                    {"EN":"Discharge information received","FR":"Informations reçues à la sortie","ES":"Información recibida al alta"}[lang],
                    height=310), use_container_width=True)


# ── Raw data ──────────────────────────────────────────────────────────────────
with st.expander({"EN":"📋 Raw data","FR":"📋 Données brutes","ES":"📋 Datos brutos"}[lang]):
    hide = [c for c in df.columns if c.startswith("_") or c=="meta/rootUuid"]
    show = [c for c in df.columns if c not in hide]
    st.dataframe(df[show], use_container_width=True, height=400)
    st.download_button({"EN":"⬇ Download CSV","FR":"⬇ Télécharger CSV","ES":"⬇ Descargar CSV"}[lang],
                       df[show].to_csv(index=False).encode("utf-8"),
                       f"ici_companion_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
