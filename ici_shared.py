"""ICI Dashboard — Shared configuration, palettes, labels, and loaders."""

import streamlit as st
import pandas as pd
import numpy as np
import requests
from pathlib import Path
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# FACILITIES
# ═══════════════════════════════════════════════════════════════════════════════
WOMEN_FACILITIES = {
    "facility_a": {
        "name": "Facility A",
        "asset_uid": "aT3kXmLeYLtUC6zVAV5abW",
        "country": "Country A",
    },
    "facility_b": {
        "name": "Facility B",
        "asset_uid": "a3KYjwLBStqvGGH4B62e7p",
        "country": "Country B",
    },
}

COMPANION_FACILITIES = {
    "facility_b": {
        "name": "Facility B",
        "asset_uid": "aFd2ux4ggB3Kcd2Z4JTZbA",
        "country": "Country B",
    },
    # Add companion forms for other facilities here:
    # "facility_a": { "name": "Facility A", "asset_uid": "...", "country": "Country A" },
}

BASE_URL = "https://eu.kobotoolbox.org"

try:
    KOBO_TOKEN = st.secrets["KOBO_TOKEN"]
    APP_PASSWORD = st.secrets.get("APP_PASSWORD", "")
except Exception:
    KOBO_TOKEN = ""
    APP_PASSWORD = ""

LOGO_PATH = Path(__file__).resolve().parent / "ici_dashboard_assets" / "ici_logo.png"

# ═══════════════════════════════════════════════════════════════════════════════
# COLORBLIND-SAFE PALETTE (Okabe-Ito)
# ═══════════════════════════════════════════════════════════════════════════════
TEAL      = "#009E73"
ORANGE    = "#E69F00"
SKY       = "#56B4E9"
VERMILION = "#D55E00"
BLUISH    = "#0072B2"
PINK      = "#CC79A7"
YELLOW    = "#F0E442"

C_GOOD    = TEAL
C_WARN    = ORANGE
C_BAD     = VERMILION
C_NEUTRAL = SKY
C_EXTRA   = BLUISH
C_ALT     = PINK
C_GREY    = "#BBBBBB"

LIKERT_COLORS   = [C_GOOD, SKY, ORANGE, PINK, VERMILION, C_GREY]
QUALITY_COLORS  = [VERMILION, PINK, ORANGE, SKY, TEAL, C_GREY]
PIE_COLORS      = [TEAL, BLUISH, ORANGE, VERMILION, PINK, SKY, C_GREY]
FACILITY_COLORS = [TEAL, BLUISH, ORANGE, VERMILION, PINK, SKY, YELLOW]

# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS (injected once per page)
# ═══════════════════════════════════════════════════════════════════════════════
GLOBAL_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;600;700&family=DM+Serif+Display:ital@0;1&display=swap');
html,body,[class*="css"]{{font-family:'DM Sans',sans-serif;}}
h1,h2,h3{{font-family:'DM Serif Display',serif;}}
.hero {{
    background: linear-gradient(135deg, #005f46 0%, #009E73 45%, #56B4E9 100%);
    border-radius: 20px; padding: 32px 44px; margin-bottom: 8px;
    position: relative; overflow: hidden;
}}
.hero::before {{
    content:''; position:absolute;top:0;left:0;right:0;bottom:0;
    background: radial-gradient(ellipse at 80% 50%, rgba(255,255,255,0.08) 0%, transparent 60%);
}}
.hero-comp {{
    background: linear-gradient(135deg, #0072B2 0%, #56B4E9 55%, #009E73 100%);
    border-radius: 20px; padding: 32px 44px; margin-bottom: 8px;
    position: relative; overflow: hidden;
}}
.hero-title {{
    font-family:'DM Serif Display',serif; font-size:2.1rem; font-weight:400; color:white;
    margin:0 0 4px 0; line-height:1.2;
}}
.hero-caption {{ font-size:0.85rem; color:rgba(255,255,255,0.78); margin:0 0 24px 0; }}
.hero-stats {{ display:flex; gap:12px; flex-wrap:nowrap; }}
.hero-stat {{
    text-align:center; background:rgba(255,255,255,0.12); border-radius:14px;
    padding:14px 12px; backdrop-filter:blur(4px); flex:1; min-width:0;
}}
.hero-stat-num {{ font-size:1.7rem; font-weight:700; color:white; line-height:1; font-family:'DM Serif Display',serif; }}
.hero-stat-label {{ font-size:0.66rem; color:rgba(255,255,255,0.8); margin-top:5px; line-height:1.3; }}
.hero-stat-bad {{ background:rgba(213,94,0,0.25); }}
.section-title {{
    font-family:'DM Serif Display',serif; font-size:1.25rem; color:#1a1a1a;
    border-left:4px solid {TEAL}; padding-left:14px; margin:32px 0 14px 0;
}}
</style>"""


def inject_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PASSWORD GATE
# ═══════════════════════════════════════════════════════════════════════════════
def password_gate():
    if not APP_PASSWORD:
        return
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.markdown("""
        <div style="max-width:380px;margin:120px auto;padding:40px 44px;background:white;
             border-radius:20px;box-shadow:0 4px 32px rgba(0,0,0,0.10);text-align:center;">
            <div style="font-family:'DM Serif Display',serif;font-size:1.5rem;color:#005f46;margin-bottom:6px;">ICI Dashboard</div>
            <div style="font-size:0.82rem;color:#888;margin-bottom:24px;">International Childbirth Initiative</div>
        </div>""", unsafe_allow_html=True)
        pwd = st.text_input("🔒 Password", type="password", label_visibility="collapsed", placeholder="Enter password…")
        c1, c2, c3 = st.columns([1, 1, 1])
        if c2.button("Enter", use_container_width=True):
            if pwd == APP_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password.")
        st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def load_facility_data(asset_uid: str, facility_name: str):
    headers = {"Authorization": f"Token {KOBO_TOKEN}"}
    url = f"{BASE_URL}/api/v2/assets/{asset_uid}/data/?format=json&limit=3000"
    results = []
    while url:
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            st.error(f"Kobo API error {r.status_code} for {facility_name}")
            return pd.DataFrame()
        data = r.json()
        results.extend(data.get("results", []))
        url = data.get("next")
    df = pd.DataFrame(results)
    if not df.empty:
        df["_facility"] = facility_name
    return df


def load_facilities(facility_dict: dict) -> pd.DataFrame:
    all_dfs = []
    for fac_id, fac_info in facility_dict.items():
        df = load_facility_data(fac_info["asset_uid"], fac_info["name"])
        if not df.empty:
            df = normalize_columns(df)
            df["_country"] = fac_info["country"]
            all_dfs.append(df)
    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    return pd.DataFrame()


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Strip Kobo group prefixes from column names.
    
    The Kobo API sometimes returns columns as 'group_xyz/question_name'
    instead of just 'question_name'. This strips everything before the
    last '/' for columns that contain a slash, but only if the resulting
    short name is not already taken by another column.
    """
    new_cols = {}
    existing = set(df.columns)
    for col in df.columns:
        if '/' in col:
            short = col.rsplit('/', 1)[-1]
            # Only rename if the short name doesn't already exist as a standalone column
            if short not in existing:
                new_cols[col] = short
    if new_cols:
        df = df.rename(columns=new_cols)
    return df


def to_int(s):
    return pd.to_numeric(s, errors="coerce")


def first_token_int(s):
    return s.astype(str).str.split().str[0].pipe(pd.to_numeric, errors="coerce")


def parse_multiselect(series, keys):
    counts = {k: 0 for k in keys}
    for val in series.dropna():
        for tok in str(val).split():
            try:
                k = int(tok)
                if k in counts:
                    counts[k] += 1
            except ValueError:
                pass
    return counts


def clean_layout(fig, title="", height=280, legend_below=False):
    b_margin = 80 if legend_below else 20
    layout = dict(
        title=dict(text=title, font=dict(size=13, family="DM Serif Display, serif", color="#1a1a1a"),
                   x=0, xanchor="left", y=0.98, yanchor="top", pad=dict(b=6, t=0)),
        margin=dict(t=64, b=b_margin, l=8, r=8),
        height=height, plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="DM Sans, sans-serif", size=11),
    )
    if legend_below:
        layout["legend"] = dict(orientation="h", y=-0.18, x=0.5, xanchor="center",
                                font=dict(size=10), tracegroupgap=4)
    else:
        layout["showlegend"] = False
    fig.update_layout(**layout)
    return fig


def sidebar_logo():
    if LOGO_PATH.exists():
        c1, c2, c3 = st.sidebar.columns([1, 2, 1])
        with c2:
            st.image(str(LOGO_PATH), width=110)


def sidebar_date_filter(df, lang):
    """Render date-range filter in sidebar, return filtered df."""
    if "_submission_time" not in df.columns or df["_submission_time"].isna().all():
        return df
    import calendar
    mn = df["_submission_time"].min()
    mx = df["_submission_time"].max()
    years = sorted(df["_submission_time"].dt.year.dropna().unique().astype(int).tolist())
    months_en = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    months_fr = ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun",
                 "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]
    months = months_fr if lang == "FR" else months_en
    lbl = {"EN": "Date range", "FR": "Période"}[lang]
    st.sidebar.markdown(f"**{lbl}**")
    dc1, dc2 = st.sidebar.columns(2)
    start_year  = dc1.selectbox("", years, index=0, key="sy_w", label_visibility="collapsed")
    start_month = dc2.selectbox("", months, index=mn.month - 1, key="sm_w", label_visibility="collapsed")
    dc3, dc4 = st.sidebar.columns(2)
    end_year  = dc3.selectbox("", years, index=len(years) - 1, key="ey_w", label_visibility="collapsed")
    end_month = dc4.selectbox("", months, index=mx.month - 1, key="em_w", label_visibility="collapsed")
    sm_idx = months.index(start_month) + 1
    em_idx = months.index(end_month) + 1
    start_dt = datetime(start_year, sm_idx, 1).date()
    end_dt   = datetime(end_year, em_idx, calendar.monthrange(end_year, em_idx)[1]).date()
    return df[(df["_submission_time"].dt.date >= start_dt) &
              (df["_submission_time"].dt.date <= end_dt)]


# ═══════════════════════════════════════════════════════════════════════════════
# BILINGUAL LABELS — WOMEN
# ═══════════════════════════════════════════════════════════════════════════════
L_W = {
    "title":          {"EN": "Women's Experience Dashboard",     "FR": "Tableau de bord — Expérience des femmes"},
    "caption":        {"EN": "International Childbirth Initiative — 12 Steps to Safe and Respectful MotherBaby-Family Maternity Care",
                       "FR": "Initiative Internationale pour la Naissance — 12 étapes pour des soins de maternité sûrs et respectueux"},
    "filters":        {"EN": "Filters",              "FR": "Filtres"},
    "facility":       {"EN": "Facility",             "FR": "Établissement"},
    "country":        {"EN": "Country",              "FR": "Pays"},
    "compare_mode":   {"EN": "Compare facilities",   "FR": "Comparer établissements"},
    "birth_method_f": {"EN": "Birth method",         "FR": "Mode d'accouchement"},
    "high_risk_f":    {"EN": "High-risk pregnancy",  "FR": "Grossesse à risque"},
    "filtered":       {"EN": "Filtered responses",   "FR": "Réponses filtrées"},
    "refresh":        {"EN": "↻ Refresh data",        "FR": "↻ Actualiser"},
    "responses":      {"EN": "Responses",            "FR": "Réponses"},
    "pct":            {"EN": "% of respondents",     "FR": "% des répondantes"},
    "download":       {"EN": "⬇ Download CSV",        "FR": "⬇ Télécharger CSV"},
    "raw_data":       {"EN": "📋 View raw data",      "FR": "📋 Voir les données brutes"},
    "positive":       {"EN": "Positive",             "FR": "Positif"},
    "negative":       {"EN": "Negative",             "FR": "Négatif"},
    "all":            {"EN": "All",                  "FR": "Tous"},
    "s_comparison":   {"EN": "Facility Comparison",  "FR": "Comparaison des établissements"},
    "s_timeline":     {"EN": "Responses Over Time",  "FR": "Réponses dans le temps"},
    "s_trends":       {"EN": "Key Indicators Over Time", "FR": "Indicateurs clés dans le temps"},
    "s_profile":      {"EN": "Respondent Profile",   "FR": "Profil des répondantes"},
    "s_likert":       {"EN": "Quality of Care — Likert Scales", "FR": "Qualité des soins — Échelles de Likert"},
    "s_likert_cap":   {"EN": "Response distribution across care dimensions (Always → Never)",
                       "FR": "Distribution des réponses par dimension de soins (Toujours → Jamais)"},
    "s_autonomy":     {"EN": "Autonomy & Consent",   "FR": "Autonomie et consentement"},
    "s_clinical":     {"EN": "Clinical Practices",   "FR": "Pratiques cliniques"},
    "s_satisfaction": {"EN": "Satisfaction — Expectations vs. Reality", "FR": "Satisfaction — Attentes vs. Réalité"},
    "s_emotions":     {"EN": "How Women Felt at the Time of Delivery", "FR": "Ressenti des femmes au moment de l'accouchement"},
    "s_emotions_all": {"EN": "All emotions",         "FR": "Toutes les émotions"},
    "s_emotions_no_exhausted": {"EN": "Excluding 'Exhausted'", "FR": "Sans 'Épuisée'"},
    "emo_note":       {"EN": "Multiple emotions could be selected — bars show % of respondents who chose each one.",
                       "FR": "Plusieurs émotions pouvaient être sélectionnées — les barres montrent le % de répondantes ayant choisi chacune."},
    "s_discharge":    {"EN": "Information Provided Before Discharge", "FR": "Informations données avant la sortie"},
    "s_mistreat":     {"EN": "Mistreatment & Respect", "FR": "Maltraitance et respect"},
    "kpi_total":      {"EN": "Total responses",      "FR": "Total réponses"},
    "kpi_positive":   {"EN": "rated care as Good or Very good", "FR": "ont évalué les soins comme Bons ou Très bons"},
    "kpi_skin":       {"EN": "had immediate skin-to-skin", "FR": "ont eu le peau à peau immédiat"},
    "kpi_gest_range": {"EN": "gestational weeks (mean, range)", "FR": "semaines de gestation (moy., étendue)"},
    "kpi_age_range":  {"EN": "age in years (mean, range)", "FR": "âge en années (moy., étendue)"},
    "kpi_elective_cs":{"EN": "elective caesarean",   "FR": "césarienne élective"},
    "p_method":       {"EN": "Birth method",         "FR": "Mode d'accouchement"},
    "p_age":          {"EN": "Age group",            "FR": "Groupe d'âge"},
    "p_education":    {"EN": "Education level",      "FR": "Niveau d'éducation"},
    "p_weeks":        {"EN": "Gestational weeks at birth", "FR": "Semaines de gestation"},
    "p_parity":       {"EN": "Number of previous deliveries", "FR": "Nombre d'accouchements précédents"},
    "mean_weeks":     {"EN": "Mean gest. weeks",     "FR": "Sem. gestation (moy.)"},
    "mean_age":       {"EN": "Mean age (min–max)",   "FR": "Âge moyen (min–max)"},
    "grp_month":      {"EN": "Month",    "FR": "Mois"},
    "grp_week":       {"EN": "Week",     "FR": "Semaine"},
    "grp_day":        {"EN": "Day",      "FR": "Jour"},
    "grp_by":         {"EN": "Group by", "FR": "Regrouper par"},
    "tr_positive":    {"EN": "% Positive rating",            "FR": "% Évaluation positive"},
    "tr_skin":        {"EN": "% Immediate skin-to-skin",     "FR": "% Peau à peau immédiat"},
    "tr_exam":        {"EN": "% Vaginal exams w/o consent",  "FR": "% Examens vaginaux s.c."},
    "a_decisions":    {"EN": "Included in care decisions",   "FR": "Incluse dans les décisions de soins"},
    "a_exam":         {"EN": "Vaginal exam — without consent frequency", "FR": "Examen vaginal — fréquence sans consentement"},
    "a_epi":          {"EN": "Episiotomy",           "FR": "Épisiotomie"},
    "a_treat":        {"EN": "Unwanted treatments",  "FR": "Soins non souhaités"},
    "c_skin":         {"EN": "Skin-to-skin contact", "FR": "Peau à peau"},
    "c_bf":           {"EN": "Breastfeeding support","FR": "Soutien à l'allaitement"},
    "c_induce":       {"EN": "Labour induction",     "FR": "Déclenchement du travail"},
    "c_pharma":       {"EN": "Pain relief received", "FR": "Analgésie reçue"},
    "c_comfort":      {"EN": "Non-pharmacological comfort", "FR": "Confort non-pharmacologique"},
    "c_rooming":      {"EN": "Rooming-in (baby with mother)", "FR": "Cohabitation mère-bébé"},
    "sat_expect":     {"EN": "Before I came here, I expected care to be:", "FR": "Avant de venir ici, je m'attendais à des soins :"},
    "sat_actual":     {"EN": "Now, I feel that my care was:", "FR": "Maintenant, j'estime que mes soins étaient :"},
    "m_verbal":       {"EN": "Verbal abuse",         "FR": "Violence verbale"},
    "m_phys":         {"EN": "Physical abuse",       "FR": "Violence physique"},
    "m_payment":      {"EN": "Informed of costs in advance", "FR": "Informée des coûts à l'avance"},
    "m_no_cost_info": {"EN": "Did NOT know cost in advance", "FR": "Ne connaissait PAS le coût"},
    "kpi_staff_equipped": {"EN": "Staff well equipped", "FR": "Personnel bien équipé"},
    "vaginal":        {"EN": "Vaginal",              "FR": "Vaginal"},
    "assisted":       {"EN": "Assisted vaginal",     "FR": "Vaginal assisté"},
    "elective_cs":    {"EN": "Elective C/S",         "FR": "Césarienne élective"},
    "emergency_cs":   {"EN": "Emergency C/S",        "FR": "Césarienne d'urgence"},
    "vbac":           {"EN": "VBAC",                 "FR": "AVAC"},
}

def tw(k, lang):
    return L_W.get(k, {}).get(lang, k)


# ═══════════════════════════════════════════════════════════════════════════════
# BILINGUAL LABELS — COMPANION
# ═══════════════════════════════════════════════════════════════════════════════
L_C = {
    "title":        {"EN": "Companion Experience Dashboard",  "FR": "Tableau de bord — Expérience des acompagnants"},
    "caption":      {"EN": "International Childbirth Initiative — Companion Questionnaire",
                     "FR": "Initiative Internationale pour la Naissance — Questionnaire acompagnant"},
    "filters":      {"EN": "Filters",             "FR": "Filtres"},
    "facility":     {"EN": "Facility",            "FR": "Établissement"},
    "filtered":     {"EN": "Filtered responses",  "FR": "Réponses filtrées"},
    "refresh":      {"EN": "↻ Refresh data",       "FR": "↻ Actualiser"},
    "all":          {"EN": "All",                 "FR": "Tous"},
    "responses":    {"EN": "Responses",           "FR": "Réponses"},
    "pct":          {"EN": "% of respondents",    "FR": "% des répondants"},
    "download":     {"EN": "⬇ Download CSV",       "FR": "⬇ Télécharger CSV"},
    "raw_data":     {"EN": "📋 View raw data",     "FR": "📋 Voir les données brutes"},
    "positive":     {"EN": "Positive",            "FR": "Positif"},
    "negative":     {"EN": "Negative",            "FR": "Négatif"},
    "kpi_total":    {"EN": "Total responses",     "FR": "Total réponses"},
    "kpi_positive": {"EN": "rated care as Good or Very good", "FR": "ont évalué les soins comme Bons ou Très bons"},
    "kpi_present_labour":  {"EN": "present during labour",   "FR": "présents lors du travail"},
    "kpi_present_birth":   {"EN": "present during birth",    "FR": "présents lors de l'accouchement"},
    "kpi_confident":       {"EN": "felt confident & prepared","FR": "se sentaient confiants et préparés"},
    "kpi_age_range":       {"EN": "age (mean, range)",        "FR": "âge (moy., étendue)"},
    "s_profile":    {"EN": "Companion Profile",           "FR": "Profil des acompagnants"},
    "s_presence":   {"EN": "Presence During Labour & Birth","FR": "Présence durant le travail et l'accouchement"},
    "s_likert":     {"EN": "Care Quality — Likert Scales", "FR": "Qualité des soins — Échelles de Likert"},
    "s_likert_cap": {"EN": "Companion perception of care provided to the woman (Always → Never)",
                     "FR": "Perception de l'acompagnant sur les soins dispensés à la femme (Toujours → Jamais)"},
    "s_autonomy":   {"EN": "Autonomy, Consent & Respect",  "FR": "Autonomie, consentement et respect"},
    "s_clinical":   {"EN": "Clinical & Practical",         "FR": "Pratiques cliniques et pratiques"},
    "s_satisfaction":{"EN": "Satisfaction — Expectations vs. Reality","FR": "Satisfaction — Attentes vs. Réalité"},
    "s_emotions":   {"EN": "Companion Emotions",           "FR": "Émotions de l'acompagnant"},
    "s_discharge":  {"EN": "Information Before Discharge", "FR": "Informations avant la sortie"},
    "s_mistreat":   {"EN": "Mistreatment Observed",        "FR": "Maltraitance observée"},
    "s_timeline":   {"EN": "Responses Over Time",          "FR": "Réponses dans le temps"},
    "grp_month":    {"EN": "Month", "FR": "Mois"},
    "grp_week":     {"EN": "Week",  "FR": "Semaine"},
    "grp_day":      {"EN": "Day",   "FR": "Jour"},
    "grp_by":       {"EN": "Group by", "FR": "Regrouper par"},
    "p_relation":   {"EN": "Relationship to woman",        "FR": "Relation avec la femme"},
    "p_age":        {"EN": "Age group",                    "FR": "Groupe d'âge"},
    "p_education":  {"EN": "Education level",              "FR": "Niveau d'éducation"},
    "p_method":     {"EN": "Birth method (as observed)",   "FR": "Mode d'accouchement (observé)"},
    "a_comp001":    {"EN": "Felt respected as companion",  "FR": "Se sentait respecté comme acompagnant"},
    "a_decisions":  {"EN": "Included in decisions",        "FR": "Inclus dans les décisions"},
    "a_values":     {"EN": "Staff respected beliefs & choices", "FR": "Personnel a respecté les croyances et choix"},
    "a_verbal":     {"EN": "Verbal abuse observed",        "FR": "Violence verbale observée"},
    "a_phys":       {"EN": "Physical abuse observed",      "FR": "Violence physique observée"},
    "a_treatment":  {"EN": "Equal treatment",              "FR": "Traitement égal"},
    "c_complab":    {"EN": "Present during labour",        "FR": "Présent lors du travail"},
    "c_comp_deliv": {"EN": "Present during birth",         "FR": "Présent lors de l'accouchement"},
    "c_comfort":    {"EN": "Encouraged to use comfort measures", "FR": "Encouragé à utiliser mesures de confort"},
    "c_pharma":     {"EN": "Pain relief received",         "FR": "Analgésie reçue"},
    "c_choices":    {"EN": "Informed of treatment options","FR": "Informé des options de traitement"},
    "c_rooming":    {"EN": "Baby with mother",             "FR": "Bébé avec la mère"},
    "c_milk":       {"EN": "Breastfeeding only",           "FR": "Allaitement exclusif"},
    "c_emergency":  {"EN": "Confident emergency care available","FR": "Confiant en soins d'urgence"},
    "c_coop":       {"EN": "Staff coordination",           "FR": "Coordination du personnel"},
    "c_accompany":  {"EN": "Felt confident & prepared before discharge","FR": "Se sentait confiant avant la sortie"},
    "sat_expect":   {"EN": "Expected care to be:",         "FR": "Soins attendus :"},
    "sat_actual":   {"EN": "Actual care was:",             "FR": "Soins reçus :"},
    "m_verbal":     {"EN": "Verbal abuse",                 "FR": "Violence verbale"},
    "m_phys":       {"EN": "Physical abuse",               "FR": "Violence physique"},
    "m_payment":    {"EN": "Knew cost in advance",         "FR": "Connaissait les coûts à l'avance"},
    "m_extra":      {"EN": "Extra fees requested",         "FR": "Frais supplémentaires demandés"},
    "birth_method_f":{"EN": "Birth method",               "FR": "Mode d'accouchement"},
}

def tc(k, lang):
    return L_C.get(k, {}).get(lang, k)


# ═══════════════════════════════════════════════════════════════════════════════
# VALUE MAPS — WOMEN (unchanged from original)
# ═══════════════════════════════════════════════════════════════════════════════
METHOD_MAP = {
    "EN": {1: "Vaginal", 2: "Assisted vaginal (forceps or vacuum)",
           3: "Elective/planned caesarean (C/S)", 4: "Emergency caesarean (C/S)", 5: "VBAC", 0: "I don't know"},
    "FR": {1: "Vaginal", 2: "Vaginal assisté (forceps ou ventouse)",
           3: "Césarienne élective (planifiée) (C/S)", 4: "Césarienne d'urgence (C/S)", 5: "AVAC", 0: "Je ne sais pas"},
}
EDUCATION_MAP = {
    "EN": {1: "No formal schooling", 2: "Primary", 3: "Secondary", 4: "Higher than secondary"},
    "FR": {1: "Aucune", 2: "Primaire", 3: "Secondaire", 4: "Post-secondaire"},
}
RISK_MAP      = {"EN": {1: "Yes", 2: "No", 0: "I don't know"}, "FR": {1: "Oui", 2: "Non", 0: "Je ne sais pas"}}
LIKERT5_MAP   = {
    "EN": {5: "Always", 4: "Most of the time", 3: "Sometimes", 2: "Rarely", 1: "Never", 0: "I don't know/not applicable"},
    "FR": {5: "Toujours", 4: "La plupart du temps", 3: "Quelquefois", 2: "Rarement", 1: "Jamais", 0: "Je ne sais pas/non applicable"},
}
QUALITY_MAP   = {
    "EN": {5: "Very good", 4: "Good", 3: "Neutral", 2: "Poor", 1: "Very bad", 0: "I don't know"},
    "FR": {5: "Très bonne", 4: "Bon", 3: "Neutre", 2: "Mauvaise", 1: "Très mauvaise", 0: "Je ne sais pas"},
}
QUALITY_ORDER = {
    "EN": ["Very bad", "Poor", "Neutral", "Good", "Very good", "I don't know"],
    "FR": ["Très mauvaise", "Mauvaise", "Neutre", "Bon", "Très bonne", "Je ne sais pas"],
}
DECISIONS_MAP = {
    "EN": {1: "Yes, included with enough information", 2: "Yes, included but not enough information",
           3: "Sometimes I was included", 4: "No, I was not included", 0: "I don't know/not applicable"},
    "FR": {1: "Oui, incluse avec suffisamment d'informations", 2: "Oui, incluse mais pas assez d'informations",
           3: "J'ai parfois été incluse", 4: "Non, je n'ai pas été incluse", 0: "Je ne sais pas/non applicable"},
}
EPI_MAP = {
    "EN": {1: "Yes, with my consent", 2: "Yes, without full explanation or consent",
           3: "No, because I declined", 4: "No, staff did not recommend it"},
    "FR": {1: "Oui, avec mon consentement", 2: "Oui, sans explication complète ou consentement",
           3: "Non, parce que j'ai refusé", 4: "Non, le personnel ne l'a pas recommandé"},
}
EXAM_MAP = {
    "EN": {1: "Never without my consent", 2: "Rarely without consent", 3: "Sometimes without consent",
           4: "Frequently without consent", 5: "Always without consent"},
    "FR": {1: "Jamais sans mon consentement", 2: "Rarement sans consentement", 3: "Parfois sans consentement",
           4: "Fréquemment sans consentement", 5: "Toujours sans consentement"},
}
TREAT_MAP   = {"EN": {1: "Yes", 2: "No", 0: "I don't know"}, "FR": {1: "Oui", 2: "Non", 0: "Je ne sais pas"}}
BF_MAP      = {
    "EN": {1: "No, I did not breastfeed", 2: "No, I did not need help",
           3: "No, I needed help but did not receive it", 4: "Yes, I was helped but not enough",
           5: "Yes, I received the help I needed", 0: "I don't know"},
    "FR": {1: "Non, je n'ai pas allaité", 2: "Non, pas besoin d'aide",
           3: "Non, j'avais besoin d'aide mais n'en ai reçu aucune", 4: "Oui, j'ai reçu de l'aide mais insuffisamment",
           5: "Oui, j'ai reçu l'aide nécessaire", 0: "Je ne sais pas"},
}
SKIN_MAP    = {
    "EN": {1: "Yes", 2: "Yes, but not immediate", 3: "Yes, but less than an hour",
           4: "No", 5: "No, chose not to or could not", 6: "I don't know"},
    "FR": {1: "Oui", 2: "Oui, mais pas immédiat", 3: "Oui, moins d'une heure",
           4: "Non", 5: "Non, ne souhaitait pas", 6: "Je ne sais pas"},
}
INDUCE_MAP  = {"EN": {1: "No", 2: "Yes", 0: "I don't know"}, "FR": {1: "Non", 2: "Oui", 0: "Je ne sais pas"}}
PHARMA_MAP  = {
    "EN": {1: "No, I did not want any", 2: "No, even though I wanted it",
           3: "Yes, but I received it too late", 4: "Yes, when I wanted it",
           5: "No, facility does not offer it", 0: "I don't know"},
    "FR": {1: "Non, je n'en voulais pas", 2: "Non, même si je le voulais",
           3: "Oui, mais reçu trop tard", 4: "Oui, quand je le voulais",
           5: "Non, non disponible dans l'établissement", 0: "Je ne sais pas"},
}
COMFORT_MAP = {
    "EN": {1: "Yes, and I used them", 2: "Yes, but I did not use them", 3: "No, none were suggested", 0: "I don't know"},
    "FR": {1: "Oui, et je les ai utilisés", 2: "Oui, mais je ne les ai pas utilisés",
           3: "Non, aucune mesure proposée", 0: "Je ne sais pas"},
}
ROOMING_MAP = {
    "EN": {4: "Yes, with me/us most of the time", 1: "No, baby was sick/sent to unit",
           2: "No, baby was not with me/us", 3: "No, I did not want baby with me", 0: "I don't know"},
    "FR": {4: "Oui, avec moi/nous la plupart du temps", 1: "Non, bébé malade/envoyé en néonatalogie",
           2: "Non, bébé pas avec moi/nous", 3: "Non, je ne souhaitais pas", 0: "Je ne sais pas"},
}
VERBAL_MAP  = {
    "EN": {1: "Never", 2: "Rarely", 3: "Sometimes", 4: "Most of the time", 5: "Always", 0: "I don't know/not applicable"},
    "FR": {1: "Jamais", 2: "Rarement", 3: "Quelquefois", 4: "La plupart du temps", 5: "Toujours", 0: "Je ne sais pas/non applicable"},
}
PHYS_MAP    = {
    "EN": {1: "Never", 2: "Rarely", 3: "Sometimes", 4: "Most of the time", 5: "Always", 0: "I don't know/not applicable"},
    "FR": {1: "Jamais", 2: "De temps en temps", 3: "Quelquefois", 4: "La plupart du temps", 5: "Toujours", 0: "Je ne sais pas/non applicable"},
}
PAYMENT_MAP = {
    "EN": {1: "Yes", 2: "No", 3: "No, care was free or covered by insurance", 0: "I don't know"},
    "FR": {1: "Oui", 2: "Non", 3: "Non, soins gratuits ou couverts par l'assurance", 0: "Je ne sais pas"},
}
LIKERT_QS_W = {
    "EN": {"introduction": "Staff introduced themselves", "spoke": "Staff spoke understandably",
           "communication": "Comfortable asking questions", "privacy": "Privacy protected",
           "respect": "Treated respectfully", "values": "Beliefs & choices respected",
           "positive": "Encouraged to feel empowered", "morale": "Staff happy & supported", "coop": "Coordinated care"},
    "FR": {"introduction": "Le personnel s'est présenté", "spoke": "Le personnel parlait clairement",
           "communication": "À l'aise pour poser des questions", "privacy": "Intimité protégée",
           "respect": "Traitée avec respect", "values": "Croyances et choix respectés",
           "positive": "Encouragée à être autonome", "morale": "Personnel heureux et supporté", "coop": "Soins coordonnés"},
}
EMOTION_LABELS_W = {
    "EN": {1: "Competence", 2: "Incapable", 3: "Anxious", 4: "Supported", 5: "Exhausted",
           6: "Active", 7: "Relaxed", 8: "Passive", 9: "Responsible", 10: "Dependent", 11: "Secure", 12: "Excluded"},
    "FR": {1: "Compétence", 2: "Incapable", 3: "Anxieuse", 4: "Soutenue", 5: "Épuisée",
           6: "Active", 7: "Détendue", 8: "Passive", 9: "Responsable", 10: "Dépendante", 11: "Sécurisée", 12: "Mise à l'écart"},
}
POSITIVE_EMO_W = {
    "EN": {"Competence", "Supported", "Active", "Relaxed", "Responsible", "Secure"},
    "FR": {"Compétence", "Soutenue", "Active", "Détendue", "Responsable", "Sécurisée"},
}
INFO_LABELS_W = {
    "EN": {1: "Caring for my new baby", 2: "Advice about family planning",
           3: "Warning signs requiring consultation", 4: "Where to go for follow-up care"},
    "FR": {1: "Prendre soin de mon nouveau-né", 2: "Conseils sur la planification familiale",
           3: "Signes à surveiller nécessitant consultation", 4: "Où aller pour les soins de suivi"},
}

# ═══════════════════════════════════════════════════════════════════════════════
# VALUE MAPS — COMPANION
# ═══════════════════════════════════════════════════════════════════════════════
# Companion uses same METHOD_MAP, EDUCATION_MAP, QUALITY_MAP, QUALITY_ORDER,
# LIKERT5_MAP, PAYMENT_MAP, VERBAL_MAP, PHYS_MAP as Women (imported above).

# Companion relationship (comp)
COMP_REL_MAP = {
    "EN": {1: "Partner/Father of baby", 2: "Family member", 3: "Friend", 0: "Other"},
    "FR": {1: "Partenaire/Père du bébé", 2: "Membre de la famille", 3: "Ami(e)", 0: "Autre"},
}
# Presence during labour (complab)
COMPLAB_MAP = {
    "EN": {1: "Yes, all the time", 2: "No", 3: "Yes, some of the time", 9: "I don't know"},
    "FR": {1: "Oui, tout le temps", 2: "Non", 3: "Oui, parfois", 9: "Je ne sais pas"},
}
# Presence during birth (comp_deliv)
COMP_DELIV_MAP = {
    "EN": {1: "Yes", 2: "No", 0: "I don't know"},
    "FR": {1: "Oui", 2: "Non", 0: "Je ne sais pas"},
}
# Respect as companion (comp_001)
COMP_RESPECT_MAP = {
    "EN": {5: "Always", 4: "Most of the time", 3: "Sometimes", 2: "Rarely", 1: "Never", 0: "I don't know/not applicable"},
    "FR": {5: "Toujours", 4: "La plupart du temps", 3: "Quelquefois", 2: "Rarement", 1: "Jamais", 0: "Je ne sais pas/non applicable"},
}
# Comfort measures (comfort — same as women but different context)
COMP_COMFORT_MAP = {
    "EN": {1: "Yes, and she used them", 2: "Yes, but she did not use them", 3: "No, none were suggested", 0: "I don't know"},
    "FR": {1: "Oui, et elle les a utilisés", 2: "Oui, mais elle ne les a pas utilisés",
           3: "Non, aucune mesure proposée", 0: "Je ne sais pas"},
}
# Treatment/choices discussed (choices)
CHOICES_MAP = {
    "EN": {1: "Yes, in depth", 2: "Yes, a little", 3: "Did not present disadvantages/alternatives",
           4: "No choices presented — some actions not understood", 0: "I don't know"},
    "FR": {1: "Oui, en détail", 2: "Oui, un peu", 3: "N'a pas présenté désavantages/alternatives",
           4: "Aucun choix présenté — certains actes non compris", 0: "Je ne sais pas"},
}
# Emergency confidence (emergency)
EMERGENCY_MAP = {
    "EN": {5: "Strongly agree", 4: "Agree", 3: "Partially agree", 2: "Disagree", 1: "Strongly disagree", 0: "I don't know"},
    "FR": {5: "Tout à fait d'accord", 4: "D'accord", 3: "Partiellement d'accord", 2: "Pas d'accord", 1: "Pas du tout d'accord", 0: "Je ne sais pas"},
}
# Rooming (companion perspective)
COMP_ROOMING_MAP = {
    "EN": {4: "Yes, most of the time", 1: "No, baby was sick/sent to unit",
           2: "No, baby was not with mother most of the time", 0: "I don't know"},
    "FR": {4: "Oui, la plupart du temps", 1: "Non, bébé malade/envoyé en unité",
           2: "Non, bébé pas avec la mère la plupart du temps", 0: "Je ne sais pas"},
}
# Breastfeeding only (milk)
MILK_MAP = {
    "EN": {1: "Yes", 2: "No, baby had complications", 3: "No, mother chose supplementary feeding",
           4: "No, even though she did not want supplementary feeding", 0: "I don't know"},
    "FR": {1: "Oui", 2: "Non, bébé avec complications", 3: "Non, mère a choisi alimentation complémentaire",
           4: "Non, même si elle ne voulait pas", 0: "Je ne sais pas"},
}
# Accompany (confident & prepared)
ACCOMPANY_MAP = {
    "EN": {5: "Strongly agree", 4: "Agree", 3: "Somewhat agree", 2: "Disagree", 1: "Strongly disagree"},
    "FR": {5: "Tout à fait d'accord", 4: "D'accord", 3: "Plutôt d'accord", 2: "Pas d'accord", 1: "Pas du tout d'accord"},
}
# Extra fees
EXTRA_MAP = {
    "EN": {2: "No", 3: "No, care was free or covered", 1: "Yes", 0: "I don't know"},
    "FR": {2: "Non", 3: "Non, soins gratuits ou couverts", 1: "Oui", 0: "Je ne sais pas"},
}
# Values/beliefs respected (companion)
COMP_VALUES_MAP = {
    "EN": {5: "Yes, all of them", 4: "Yes, most of them", 3: "Yes, some of them",
           2: "Yes, a few of them", 1: "No", 0: "I don't know"},
    "FR": {5: "Oui, tout le personnel", 4: "Oui, la plupart", 3: "Oui, certains",
           2: "Oui, quelques-uns", 1: "Non", 0: "Je ne sais pas"},
}
# Decisions (companion version — 3 levels)
COMP_DECISIONS_MAP = {
    "EN": {1: "Yes, included with enough information", 3: "Sometimes included",
           4: "No, not included", 0: "I don't know/not applicable"},
    "FR": {1: "Oui, inclus avec suffisamment d'informations", 3: "Parfois inclus",
           4: "Non, pas inclus", 0: "Je ne sais pas/non applicable"},
}
# Coop (companion)
COMP_COOP_MAP = {
    "EN": {5: "Always", 4: "Most of the time", 3: "Sometimes", 2: "Rarely", 1: "Never", 0: "I don't know"},
    "FR": {5: "Toujours", 4: "La plupart du temps", 3: "Quelquefois", 2: "Rarement", 1: "Jamais", 0: "Je ne sais pas"},
}
# Treatment/equal (treatment)
COMP_TREATMENT_MAP = {
    "EN": {5: "Always", 4: "Most of the time", 3: "Sometimes", 2: "Rarely", 1: "Never", 0: "I don't know/not applicable"},
    "FR": {5: "Toujours", 4: "La plupart du temps", 3: "Quelquefois", 2: "Rarement", 1: "Jamais", 0: "Je ne sais pas/non applicable"},
}
# Pharma (companion perspective — same structure as women)
COMP_PHARMA_MAP = {
    "EN": {1: "No, she did not want any", 2: "No, even though she wanted it",
           3: "Yes, but received too late", 4: "Yes, when she wanted it",
           5: "No, facility does not offer it", 0: "I don't know"},
    "FR": {1: "Non, elle n'en voulait pas", 2: "Non, même si elle le voulait",
           3: "Oui, mais reçu trop tard", 4: "Oui, quand elle le voulait",
           5: "Non, non disponible dans l'établissement", 0: "Je ne sais pas"},
}

# Likert questions for companion
LIKERT_QS_C = {
    "EN": {
        "introduction": "Staff introduced themselves",
        "spoke":        "Staff spoke understandably",
        "privacy":      "Privacy protected during labour/birth/after",
        "respect":      "Woman treated respectfully",
        "comp_001":     "Felt respected as companion",
        "coop":         "Staff coordinated care",
    },
    "FR": {
        "introduction": "Le personnel s'est présenté",
        "spoke":        "Le personnel parlait clairement",
        "privacy":      "Intimité protégée",
        "respect":      "Femme traitée avec respect",
        "comp_001":     "Se sentait respecté comme acompagnant",
        "coop":         "Personnel coordonné",
    },
}

# Companion emotions — single select, text labels from data
POSITIVE_EMO_C = {
    "EN": {"Happy", "Confident", "Grateful", "Reassured", "Respected", "Loving", "Secure", "Satisfied", "Supported"},
    "FR": {"Felicidad", "Confianza", "Gratitud", "Tranquilidad", "Respetado", "Amor", "Seguro", "Satisfecho", "Apoyo"},
}

# Info labels (companion — same keys but companion phrasing)
INFO_LABELS_C = {
    "EN": {1: "Caring for the new baby", 2: "Advice about family planning",
           3: "Warning signs requiring consultation", 4: "Where to go for follow-up care",
           5: "None — we/she declined information", 9: "None of this was offered", 99: "I don't know"},
    "FR": {1: "Prendre soin du nouveau-né", 2: "Conseils planification familiale",
           3: "Signes d'alarme nécessitant consultation", 4: "Où aller pour le suivi",
           5: "Aucune — nous/elle avons refusé", 9: "Rien n'a été proposé", 99: "Je ne sais pas"},
}
