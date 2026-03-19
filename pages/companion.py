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
        dw = prep_women(raw_w, lang)
        # Apply same facility filter as companion if admin selected one
        if get_role() == "admin":
            sel = st.session_state.get("fac_filter_c", "all")
            if sel != "all":
                dw = dw[dw["_facility_id"] == sel]

        # Merge on id — both forms ask participants to write the same code
        df["id"] = df["id"].astype(str).str.strip()
        dw["id"] = dw["id"].astype(str).str.strip()

        paired = df[["id","satisfaction","comp_detail_label","complab","comp_deliv","emotion_label"]].merge(
            dw[["id","satisfaction","method_label","verbal","phys","skin_int","respect","privacy"]],
            on="id", suffixes=("_c","_w")
        )
        n_paired = len(paired)

        if n_paired == 0:
            st.info({"EN":"No matched pairs found for the selected period/facility.",
                     "FR":"Aucune paire trouvée pour la période/établissement sélectionné.",
                     "ES":"No se encontraron pares para el período/establecimiento seleccionado."}[lang])
        else:
            st.caption({"EN":f"{n_paired} matched pairs (companion + mother with same ID).",
                        "FR":f"{n_paired} paires identifiées (acompagnant + mère, même ID).",
                        "ES":f"{n_paired} pares identificados (acompañante + madre, mismo ID)."}[lang])

            c1, c2 = st.columns(2)

            # Satisfaction comparison: companion vs mother
            if "satisfaction_c" in paired.columns and "satisfaction_w" in paired.columns:
                sat_c = (paired["satisfaction_c"].isin([4,5])).sum() / n_paired * 100
                sat_w = (paired["satisfaction_w"].isin([4,5])).sum() / n_paired * 100
                import plotly.graph_objects as go
                fig = go.Figure()
                fig.add_bar(name={"EN":"Mother","FR":"Mère","ES":"Madre"}[lang],
                            x=[{"EN":"Good/Very good care","FR":"Bons soins","ES":"Atención buena/muy buena"}[lang]],
                            y=[sat_w], marker_color=TEAL,
                            text=[f"{sat_w:.1f}%"], textposition="outside")
                fig.add_bar(name={"EN":"Companion","FR":"Acompagnant","ES":"Acompañante"}[lang],
                            x=[{"EN":"Good/Very good care","FR":"Bons soins","ES":"Atención buena/muy buena"}[lang]],
                            y=[sat_c], marker_color=BLUISH,
                            text=[f"{sat_c:.1f}%"], textposition="outside")
                fig.update_layout(barmode="group", height=280,
                                  margin=dict(t=40,b=8,l=8,r=8),
                                  plot_bgcolor="white", paper_bgcolor="white",
                                  yaxis=dict(range=[0,110], gridcolor="#eeeeee"),
                                  xaxis=dict(showgrid=False),
                                  legend=dict(orientation="h",y=-0.15,x=0.5,xanchor="center"),
                                  title=dict(text={"EN":"Satisfaction","FR":"Satisfaction","ES":"Satisfacción"}[lang],
                                             font=dict(size=13,family="DM Serif Display, serif"),
                                             x=0, xanchor="left"))
                c1.plotly_chart(fig, use_container_width=True)

            # Verbal/physical mistreatment as reported by companion
            if "verbal" in paired.columns and "phys" in paired.columns:
                verb_pct = (paired["verbal"].isin([3,4,5])).sum() / n_paired * 100
                phys_pct = (paired["phys"].isin([3,4,5])).sum() / n_paired * 100
                fig2 = go.Figure()
                cats = [{"EN":"Verbal mistreatment","FR":"Violence verbale","ES":"Violencia verbal"}[lang],
                        {"EN":"Physical mistreatment","FR":"Violence physique","ES":"Violencia física"}[lang]]
                fig2.add_bar(x=cats, y=[verb_pct, phys_pct],
                             marker_color=[VERMILION, ORANGE],
                             text=[f"{verb_pct:.1f}%", f"{phys_pct:.1f}%"],
                             textposition="outside")
                fig2.update_layout(height=280,
                                   margin=dict(t=40,b=8,l=8,r=8),
                                   plot_bgcolor="white", paper_bgcolor="white",
                                   showlegend=False,
                                   yaxis=dict(range=[0,110], gridcolor="#eeeeee"),
                                   xaxis=dict(showgrid=False),
                                   title=dict(text={"EN":"Mistreatment reported by companion","FR":"Maltraitance (acompagnant)","ES":"Maltrato reportado por acompañante"}[lang],
                                              font=dict(size=13,family="DM Serif Display, serif"),
                                              x=0, xanchor="left"))
                c2.plotly_chart(fig2, use_container_width=True)

            # Companion relationship breakdown among paired records
            if "comp_detail_label" in paired.columns:
                rel_vc = paired["comp_detail_label"].dropna().value_counts().reset_index()
                rel_vc.columns = ["r","n"]
                rel_vc["text"] = rel_vc.apply(lambda x: f"{x['n']} ({x['n']/n_paired*100:.1f}%)", axis=1)
                fig3 = px.bar(rel_vc, x="n", y="r", orientation="h",
                              color_discrete_sequence=[BLUISH], text="text",
                              labels={"r":"","n":""})
                fig3.update_traces(textposition="outside", textfont=dict(size=9))
                fig3 = clean_layout(fig3,
                                    title={"EN":"Companion relationship (paired)","FR":"Relation acompagnant (paires)","ES":"Relación acompañante (pares)"}[lang],
                                    height=max(220, len(rel_vc)*32+60))
                fig3.update_xaxes(gridcolor="#eeeeee"); fig3.update_yaxes(showgrid=False)
                st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info({"EN":"Women's data not available for pairing.",
                 "FR":"Données femmes non disponibles.",
                 "ES":"Datos de mujeres no disponibles."}[lang])
else:
    st.info({"EN":"No ID field found in companion data — pairing not available.",
             "FR":"Champ ID absent — croisement non disponible.",
             "ES":"Campo ID no encontrado — cruce no disponible."}[lang])

# ── Raw data ──────────────────────────────────────────────────────────────────
with st.expander({"EN":"📋 Raw data","FR":"📋 Données brutes","ES":"📋 Datos brutos"}[lang]):
    hide = [c for c in df.columns if c.startswith("_") or c=="meta/rootUuid"]
    show = [c for c in df.columns if c not in hide]
    st.dataframe(df[show], use_container_width=True, height=400)
    st.download_button({"EN":"⬇ Download CSV","FR":"⬇ Télécharger CSV","ES":"⬇ Descargar CSV"}[lang],
                       df[show].to_csv(index=False).encode("utf-8"),
                       f"ici_companion_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
