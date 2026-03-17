"""ICI — Facility Comparison (admin only)"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ici_shared import (
    FACILITIES, TEAL, ORANGE, SKY, VERMILION, BLUISH, PINK, YELLOW,
    FACILITY_COLORS, PIE_COLORS,
    inject_css, sidebar_logo, logout_button, lang_selector,
    load_women, load_companion, prep_women, prep_companion,
    get_facility_ids, get_role, clean_layout, METHOD_MAP,
)

inject_css()
sidebar_logo()

# Admin only
if get_role() != "admin":
    st.error("Access restricted to administrators."); st.stop()

lang = lang_selector("lang_cmp")

st.sidebar.markdown("""
<div style="text-align:center;">
<div style="font-family:'DM Serif Display',serif;font-size:1.05rem;color:#005f46;font-weight:600;">ICI Dashboard</div>
<div style="font-size:0.68rem;color:#888;margin-bottom:12px;">Facility Comparison</div>
<hr style="border:none;border-top:1px solid #e0e0e0;margin:0 0 12px 0;">
</div>""", unsafe_allow_html=True)

all_fac_ids = list(FACILITIES.keys())
selected = st.sidebar.multiselect(
    {"EN":"Facilities","FR":"Établissements","ES":"Establecimientos"}[lang],
    options=all_fac_ids,
    default=all_fac_ids,
    format_func=lambda x: FACILITIES[x]["display_name"]
)
if not selected:
    st.info({"EN":"Select at least one facility.","FR":"Sélectionnez au moins un établissement.","ES":"Seleccione al menos un establecimiento."}[lang])
    st.stop()

if st.sidebar.button({"EN":"↻ Refresh","FR":"↻ Actualiser","ES":"↻ Actualizar"}[lang]):
    st.cache_data.clear(); st.rerun()
logout_button()

# Load data for selected facilities
with st.spinner({"EN":"Loading…","FR":"Chargement…","ES":"Cargando…"}[lang]):
    raw_w = load_women(selected)

title = {"EN":"Facility Comparison","FR":"Comparaison des établissements","ES":"Comparación de establecimientos"}
st.markdown(f"# {title[lang]}")

if raw_w.empty:
    st.warning({"EN":"No data.","FR":"Aucune donnée.","ES":"Sin datos."}[lang]); st.stop()

df = prep_women(raw_w, lang)

# ── Summary table ─────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{"Summary by Facility" if lang=="EN" else "Résumé par établissement" if lang=="FR" else "Resumen por establecimiento"}</div>', unsafe_allow_html=True)

rows = []
for fid in selected:
    fac_df = df[df["_facility_id"]==fid]
    n = len(fac_df)
    if n == 0:
        continue
    sat = (fac_df["satisfaction"].isin([4,5])).sum()/n*100 if "satisfaction" in fac_df.columns else np.nan
    ecs = (fac_df["method"]==3).sum()/n*100 if "method" in fac_df.columns else np.nan
    emg = (fac_df["method"]==4).sum()/n*100 if "method" in fac_df.columns else np.nan
    vag = (fac_df["method"]==1).sum()/n*100 if "method" in fac_df.columns else np.nan
    skin = (fac_df["skin_int"]==1).sum()/n*100 if "skin_int" in fac_df.columns else np.nan
    verbal = (fac_df["verbal"].isin([3,4,5])).sum()/n*100 if "verbal" in fac_df.columns else np.nan
    exam_nc = (fac_df["exam"].isin([2,3,4,5])).sum()/n*100 if "exam" in fac_df.columns else np.nan
    age_m = fac_df["age"].mean() if "age" in fac_df.columns else np.nan
    weeks_m = fac_df["weeks_clean"].mean() if "weeks_clean" in fac_df.columns else np.nan
    rows.append({
        "Facility": FACILITIES[fid]["display_name"],
        "Country":  FACILITIES[fid]["country"],
        "n": n,
        "% Good/Very good care": f"{sat:.1f}%" if not np.isnan(sat) else "–",
        "% Vaginal": f"{vag:.1f}%" if not np.isnan(vag) else "–",
        "% Elective C/S": f"{ecs:.1f}%" if not np.isnan(ecs) else "–",
        "% Emergency C/S": f"{emg:.1f}%" if not np.isnan(emg) else "–",
        "% Immediate skin-to-skin": f"{skin:.1f}%" if not np.isnan(skin) else "–",
        "% Verbal abuse": f"{verbal:.1f}%" if not np.isnan(verbal) else "–",
        "% Vaginal exam w/o consent": f"{exam_nc:.1f}%" if not np.isnan(exam_nc) else "–",
        "Mean age": f"{age_m:.1f}" if not np.isnan(age_m) else "–",
        "Mean gest. weeks": f"{weeks_m:.1f}" if not np.isnan(weeks_m) else "–",
    })

if rows:
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ── Birth method comparison ───────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{"Birth Method by Facility" if lang=="EN" else "Mode d\'accouchement par établissement" if lang=="FR" else "Vía de nacimiento por establecimiento"}</div>', unsafe_allow_html=True)
if "method" in df.columns:
    method_rows = []
    for fid in selected:
        fac_df = df[df["_facility_id"]==fid]
        n = len(fac_df)
        if n == 0: continue
        for mcode in [1,2,3,4,5]:
            method_rows.append({
                "Facility": FACILITIES[fid]["display_name"],
                "Method": METHOD_MAP[lang].get(mcode, str(mcode)),
                "Pct": (fac_df["method"]==mcode).sum()/n*100,
            })
    if method_rows:
        mdf = pd.DataFrame(method_rows)
        fig = px.bar(mdf, x="Facility", y="Pct", color="Method", barmode="group",
                     color_discrete_sequence=FACILITY_COLORS, labels={"Pct":"%","Facility":""})
        fig.update_layout(height=380, margin=dict(t=8,b=80,l=8,r=8), plot_bgcolor="white", paper_bgcolor="white",
                          legend=dict(orientation="h",y=-0.25,x=0.5,xanchor="center"),
                          yaxis=dict(title="%",gridcolor="#eeeeee"), xaxis=dict(showgrid=False))
        st.plotly_chart(fig, use_container_width=True)

# ── Satisfaction comparison ───────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{"Satisfaction by Facility" if lang=="EN" else "Satisfaction par établissement" if lang=="FR" else "Satisfacción por establecimiento"}</div>', unsafe_allow_html=True)
if "satisfaction" in df.columns:
    sat_rows = []
    for fid in selected:
        fac_df = df[df["_facility_id"]==fid]
        n = len(fac_df)
        if n == 0: continue
        sat_rows.append({
            "Facility": FACILITIES[fid]["display_name"],
            "% Good/Very good": (fac_df["satisfaction"].isin([4,5])).sum()/n*100,
            "% Poor/Very bad":  (fac_df["satisfaction"].isin([1,2])).sum()/n*100,
        })
    if sat_rows:
        sdf = pd.DataFrame(sat_rows)
        fig = px.bar(sdf, x="Facility", y=["% Good/Very good","% Poor/Very bad"],
                     barmode="group", color_discrete_sequence=[TEAL, VERMILION],
                     labels={"value":"%","variable":"","Facility":""})
        fig.update_layout(height=340, margin=dict(t=8,b=80,l=8,r=8), plot_bgcolor="white", paper_bgcolor="white",
                          legend=dict(orientation="h",y=-0.25,x=0.5,xanchor="center"),
                          yaxis=dict(gridcolor="#eeeeee"), xaxis=dict(showgrid=False))
        st.plotly_chart(fig, use_container_width=True)

# ── Companion comparison (if available) ───────────────────────────────────────
comp_fac_ids = [f for f in selected if FACILITIES[f].get("companion_uid")]
if comp_fac_ids:
    st.markdown(f'<div class="section-title">{"Companion Data by Facility" if lang=="EN" else "Données acompagnants par établissement" if lang=="FR" else "Datos acompañantes por establecimiento"}</div>', unsafe_allow_html=True)
    with st.spinner({"EN":"Loading companion data…","FR":"Chargement acompagnants…","ES":"Cargando acompañantes…"}[lang]):
        raw_c = load_companion(comp_fac_ids)
    if not raw_c.empty:
        dfc = prep_companion(raw_c, lang)
        comp_rows = []
        for fid in comp_fac_ids:
            fac_df = dfc[dfc["_facility_id"]==fid]
            n = len(fac_df)
            if n == 0: continue
            sat = (fac_df["satisfaction"].isin([4,5])).sum()/n*100 if "satisfaction" in fac_df.columns else np.nan
            pres_lab = (fac_df["complab"]==1).sum()/n*100 if "complab" in fac_df.columns else np.nan
            pres_del = (fac_df["comp_deliv"]==1).sum()/n*100 if "comp_deliv" in fac_df.columns else np.nan
            comp_rows.append({
                "Facility": FACILITIES[fid]["display_name"],
                "n (companions)": n,
                "% Good/Very good": f"{sat:.1f}%" if not np.isnan(sat) else "–",
                "% Present during labour": f"{pres_lab:.1f}%" if not np.isnan(pres_lab) else "–",
                "% Present during birth": f"{pres_del:.1f}%" if not np.isnan(pres_del) else "–",
            })
        if comp_rows:
            st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)
