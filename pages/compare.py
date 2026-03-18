"""ICI — Facility Comparison (available to all roles)"""
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
    date_filter,
)

inject_css()
sidebar_logo()

role     = get_role()
my_fids  = get_facility_ids()   # facilities this user owns
all_fids = list(FACILITIES.keys())
other_fids = [f for f in all_fids if f not in my_fids]

if not my_fids:
    st.error("Not logged in."); st.stop()

lang = lang_selector("lang_cmp")

st.sidebar.markdown("""
<div style="text-align:center;">
<div style="font-family:'DM Serif Display',serif;font-size:1.05rem;color:#005f46;font-weight:600;">ICI Dashboard</div>
<div style="font-size:0.68rem;color:#888;margin-bottom:12px;">Facility Comparison</div>
<hr style="border:none;border-top:1px solid #e0e0e0;margin:0 0 12px 0;">
</div>""", unsafe_allow_html=True)

# ── Facility selection ────────────────────────────────────────────────────────
lbl     = {"EN": "Compare with", "FR": "Comparer avec",   "ES": "Comparar con"}[lang]

if role == "admin":
    # Admin sees all facilities and can toggle each one; no concept of "own"
    selected_others = st.sidebar.multiselect(
        lbl,
        options=all_fids,
        default=all_fids,
        format_func=lambda x: FACILITIES[x]["display_name"],
    )
    fids_to_load = selected_others if selected_others else all_fids
elif other_fids:
    selected_others = st.sidebar.multiselect(
        lbl,
        options=other_fids,
        default=other_fids,
        # Non-admin sees others as anonymous letters, starting from B
        # (A is reserved for themselves so there's no collision)
        format_func=lambda x: f"{'BCDEFGH'[other_fids.index(x)]}",
    )
    fids_to_load = my_fids + selected_others
else:
    selected_others = []
    st.sidebar.info({"EN": "No other facilities available yet.",
                     "FR": "Aucun autre établissement disponible.",
                     "ES": "No hay otros establecimientos disponibles."}[lang])
    fids_to_load = my_fids

if st.sidebar.button({"EN": "↻ Refresh", "FR": "↻ Actualiser", "ES": "↻ Actualizar"}[lang]):
    st.cache_data.clear(); st.rerun()
logout_button()

# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner({"EN": "Loading…", "FR": "Chargement…", "ES": "Cargando…"}[lang]):
    raw_w = load_women(fids_to_load)

title = {"EN": "Facility Comparison", "FR": "Comparaison des établissements", "ES": "Comparación de establecimientos"}
st.markdown(f"# {title[lang]}")

if raw_w.empty:
    st.warning({"EN": "No data.", "FR": "Aucune donnée.", "ES": "Sin datos."}[lang]); st.stop()

# prep first (parses _submission_time to datetime), then date_filter
df = prep_women(raw_w, lang)
df = date_filter(df, key="cmp_w")

if len(df) == 0:
    st.warning({"EN": "No data for selected period.", "FR": "Aucune donnée.", "ES": "Sin datos."}[lang]); st.stop()

# ── Build display labels ──────────────────────────────────────────────────────
# My facility: shown by real name + "(You)"
# Others: admin sees real names, others see anonymous labels A/B/C...
def display_label(fid: str) -> str:
    real_name = FACILITIES[fid]["display_name"]
    if role == "admin":
        return real_name
    if fid in my_fids:
        you = {"EN": "You", "FR": "Vous", "ES": "Usted"}[lang]
        return f"{real_name} ({you})"
    # Others get anonymous letters starting from B (so "A (You)" vs "B", "C"...)
    anon_idx = other_fids.index(fid) if fid in other_fids else 0
    return f"{'BCDEFGH'[anon_idx]}"

df["_display"] = df["_facility_id"].map(display_label)
my_display = display_label(my_fids[0]) if len(my_fids) == 1 else None

# Color: my facility always TEAL, others cycle through palette
def fac_color(fid: str) -> str:
    if fid in my_fids:
        return TEAL
    others_in_plot = [f for f in fids_to_load if f not in my_fids]
    idx = others_in_plot.index(fid) if fid in others_in_plot else 0
    return [BLUISH, ORANGE, PINK, VERMILION, SKY, YELLOW][idx % 6]

color_map = {display_label(fid): fac_color(fid) for fid in fids_to_load}

# ── Summary table ─────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{"Summary" if lang=="EN" else "Résumé" if lang=="FR" else "Resumen"}</div>',
            unsafe_allow_html=True)

rows = []
for fid in fids_to_load:
    fac_df = df[df["_facility_id"] == fid]
    n = len(fac_df)
    if n == 0: continue
    sat   = (fac_df["satisfaction"].isin([4,5])).sum()/n*100 if "satisfaction" in fac_df.columns else np.nan
    ecs   = (fac_df["method"]==3).sum()/n*100 if "method" in fac_df.columns else np.nan
    emg   = (fac_df["method"]==4).sum()/n*100 if "method" in fac_df.columns else np.nan
    vag   = (fac_df["method"]==1).sum()/n*100 if "method" in fac_df.columns else np.nan
    skin  = (fac_df["skin_int"]==1).sum()/n*100 if "skin_int" in fac_df.columns else np.nan
    verb  = (fac_df["verbal"].isin([3,4,5])).sum()/n*100 if "verbal" in fac_df.columns else np.nan
    exam  = (fac_df["exam"].isin([2,3,4,5])).sum()/n*100 if "exam" in fac_df.columns else np.nan
    rows.append({
        {"EN":"Facility","FR":"Établissement","ES":"Establecimiento"}[lang]: display_label(fid),
        "n": n,
        "% Good/Very good": f"{sat:.1f}%" if not np.isnan(sat) else "–",
        "% Vaginal":        f"{vag:.1f}%" if not np.isnan(vag) else "–",
        "% Elective C/S":   f"{ecs:.1f}%" if not np.isnan(ecs) else "–",
        "% Emergency C/S":  f"{emg:.1f}%" if not np.isnan(emg) else "–",
        "% Skin-to-skin":   f"{skin:.1f}%" if not np.isnan(skin) else "–",
        "% Verbal abuse":   f"{verb:.1f}%" if not np.isnan(verb) else "–",
        "% Exam w/o consent": f"{exam:.1f}%" if not np.isnan(exam) else "–",
    })

if rows:
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ── Birth method chart ────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{"Birth Method" if lang=="EN" else "Mode d\'accouchement" if lang=="FR" else "Vía de nacimiento"}</div>',
            unsafe_allow_html=True)
if "method" in df.columns:
    m_rows = []
    for fid in fids_to_load:
        fac_df = df[df["_facility_id"]==fid]; n=len(fac_df)
        if n==0: continue
        for mc in [1,2,3,4,5]:
            m_rows.append({"Facility": display_label(fid),
                           "Method": METHOD_MAP[lang].get(mc, str(mc)),
                           "Pct": (fac_df["method"]==mc).sum()/n*100})
    if m_rows:
        mdf = pd.DataFrame(m_rows)
        fig = px.bar(mdf, x="Facility", y="Pct", color="Method", barmode="group",
                     color_discrete_sequence=FACILITY_COLORS, labels={"Pct":"%","Facility":""})
        fig.update_layout(height=380, margin=dict(t=8,b=80,l=8,r=8),
                          plot_bgcolor="white", paper_bgcolor="white",
                          legend=dict(orientation="h",y=-0.25,x=0.5,xanchor="center"),
                          yaxis=dict(gridcolor="#eeeeee"), xaxis=dict(showgrid=False))
        st.plotly_chart(fig, use_container_width=True)

# ── Satisfaction chart ────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{"Satisfaction" if lang=="EN" else "Satisfaction" if lang=="FR" else "Satisfacción"}</div>',
            unsafe_allow_html=True)
if "satisfaction" in df.columns:
    s_rows = []
    for fid in fids_to_load:
        fac_df = df[df["_facility_id"]==fid]; n=len(fac_df)
        if n==0: continue
        s_rows.append({
            "Facility": display_label(fid),
            "% Good/Very good": (fac_df["satisfaction"].isin([4,5])).sum()/n*100,
            "% Poor/Very bad":  (fac_df["satisfaction"].isin([1,2])).sum()/n*100,
        })
    if s_rows:
        sdf = pd.DataFrame(s_rows)
        fig = px.bar(sdf, x="Facility", y=["% Good/Very good","% Poor/Very bad"],
                     barmode="group", color_discrete_sequence=[TEAL, VERMILION],
                     labels={"value":"%","variable":"","Facility":""})
        fig.update_layout(height=340, margin=dict(t=8,b=80,l=8,r=8),
                          plot_bgcolor="white", paper_bgcolor="white",
                          legend=dict(orientation="h",y=-0.25,x=0.5,xanchor="center"),
                          yaxis=dict(gridcolor="#eeeeee"), xaxis=dict(showgrid=False))
        st.plotly_chart(fig, use_container_width=True)

# ── Key indicators radar ──────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">{"Key Indicators" if lang=="EN" else "Indicateurs clés" if lang=="FR" else "Indicadores clave"}</div>',
            unsafe_allow_html=True)
indicator_rows = []
indicators = {
    "EN": {"% Good/Very good care": ("satisfaction",[4,5]),
           "% Immediate skin-to-skin": ("skin_int",[1]),
           "% No verbal abuse": ("verbal",[1,2]),
           "% Privacy protected (Always)": ("privacy",[5]),
           "% Treated respectfully (Always)": ("respect",[5])},
    "FR": {"% Bons soins": ("satisfaction",[4,5]),
           "% Peau à peau immédiat": ("skin_int",[1]),
           "% Pas de violence verbale": ("verbal",[1,2]),
           "% Intimité protégée (Toujours)": ("privacy",[5]),
           "% Traitée avec respect (Toujours)": ("respect",[5])},
    "ES": {"% Atención buena/muy buena": ("satisfaction",[4,5]),
           "% Piel con piel inmediato": ("skin_int",[1]),
           "% Sin violencia verbal": ("verbal",[1,2]),
           "% Intimidad protegida (Siempre)": ("privacy",[5]),
           "% Tratada con respeto (Siempre)": ("respect",[5])},
}[lang]

for fid in fids_to_load:
    fac_df = df[df["_facility_id"]==fid]; n=len(fac_df)
    if n==0: continue
    for ind_label, (col, vals) in indicators.items():
        if col in fac_df.columns:
            pct = fac_df[col].isin(vals).sum()/n*100
        else:
            pct = 0
        indicator_rows.append({"Facility": display_label(fid), "Indicator": ind_label, "Pct": round(pct,1)})

if indicator_rows:
    idf = pd.DataFrame(indicator_rows)
    fig = px.bar(idf, x="Indicator", y="Pct", color="Facility",
                 barmode="group", color_discrete_map=color_map,
                 labels={"Pct":"%","Indicator":"","Facility":""},
                 text="Pct")
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside", textfont=dict(size=9))
    fig.update_layout(height=420, margin=dict(t=8,b=120,l=8,r=8),
                      plot_bgcolor="white", paper_bgcolor="white",
                      legend=dict(orientation="h",y=-0.28,x=0.5,xanchor="center"),
                      yaxis=dict(gridcolor="#eeeeee",range=[0,105]),
                      xaxis=dict(showgrid=False))
    st.plotly_chart(fig, use_container_width=True)

# ── Companion comparison ──────────────────────────────────────────────────────
comp_fids = [f for f in fids_to_load if FACILITIES[f].get("companion_uid")]
if comp_fids:
    st.markdown(f'<div class="section-title">{"Companion Data" if lang=="EN" else "Données acompagnants" if lang=="FR" else "Datos acompañantes"}</div>',
                unsafe_allow_html=True)
    with st.spinner("…"):
        raw_c = load_companion(comp_fids)
    if not raw_c.empty:
        dfc = prep_companion(raw_c, lang)
        dfc = date_filter(dfc, key="cmp_c")
        dfc["_display"] = dfc["_facility_id"].map(display_label)
        c_rows = []
        for fid in comp_fids:
            fac_df = dfc[dfc["_facility_id"]==fid]; n=len(fac_df)
            if n==0: continue
            sat  = (fac_df["satisfaction"].isin([4,5])).sum()/n*100 if "satisfaction" in fac_df.columns else np.nan
            plab = (fac_df["complab"]==1).sum()/n*100 if "complab" in fac_df.columns else np.nan
            pdel = (fac_df["comp_deliv"]==1).sum()/n*100 if "comp_deliv" in fac_df.columns else np.nan
            c_rows.append({
                {"EN":"Facility","FR":"Établissement","ES":"Establecimiento"}[lang]: display_label(fid),
                "n": n,
                "% Good/Very good": f"{sat:.1f}%" if not np.isnan(sat) else "–",
                "% Present during labour": f"{plab:.1f}%" if not np.isnan(plab) else "–",
                "% Present during birth":  f"{pdel:.1f}%" if not np.isnan(pdel) else "–",
            })
        if c_rows:
            st.dataframe(pd.DataFrame(c_rows), use_container_width=True, hide_index=True)
