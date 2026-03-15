"""ICI Women's Experience Dashboard — International Childbirth Initiative
   Multi-Facility Comparison Version
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
from pathlib import Path
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG — Multiple Facilities
# ═══════════════════════════════════════════════════════════════════════════════
# Display names are generic (Facility A, B, C...) to protect facility identity
# Internal names are for your reference only
FACILITIES = {
    "facility_a": {
        "name": "Facility A",  # Canada - displayed as generic name
        "asset_uid": "aT3kXmLeYLtUC6zVAV5abW",
        "country": "Country A",
    },
    # Add more facilities here:
    # "facility_b": {
    #     "name": "Facility B",  # Cartagena
    #     "asset_uid": "YOUR_ASSET_UID_HERE",
    #     "country": "Country B",
    # },
}

BASE_URL = "https://eu.kobotoolbox.org"

try:
    KOBO_TOKEN = st.secrets["KOBO_TOKEN"]
    APP_PASSWORD = st.secrets.get("APP_PASSWORD", "")
except Exception:
    KOBO_TOKEN = ""
    APP_PASSWORD = ""
    st.error("⚠ KOBO_TOKEN not found in Streamlit Secrets.")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# PASSWORD GATE
# ═══════════════════════════════════════════════════════════════════════════════
if APP_PASSWORD:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.markdown("""
        <style>
        .login-box {
            max-width: 380px; margin: 120px auto; padding: 40px 44px;
            background: white; border-radius: 20px;
            box-shadow: 0 4px 32px rgba(0,0,0,0.10);
            text-align: center;
        }
        .login-title {
            font-family: 'DM Serif Display', serif;
            font-size: 1.5rem; color: #005f46; margin-bottom: 6px;
        }
        .login-sub {
            font-size: 0.82rem; color: #888; margin-bottom: 24px;
        }
        </style>
        <div class="login-box">
            <div class="login-title">ICI Dashboard</div>
            <div class="login-sub">International Childbirth Initiative</div>
        </div>
        """, unsafe_allow_html=True)

        pwd = st.text_input("🔒 Password", type="password", label_visibility="collapsed",
                            placeholder="Enter password…")
        col1, col2, col3 = st.columns([1,1,1])
        if col2.button("Enter", use_container_width=True):
            if pwd == APP_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password.")
        st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# COLORBLIND-SAFE PALETTE (Okabe-Ito)
# ═══════════════════════════════════════════════════════════════════════════════
TEAL = "#009E73"
ORANGE = "#E69F00"
SKY = "#56B4E9"
VERMILION = "#D55E00"
BLUISH = "#0072B2"
PINK = "#CC79A7"
YELLOW = "#F0E442"
BLACK = "#000000"

C_GOOD = TEAL
C_WARN = ORANGE
C_BAD = VERMILION
C_NEUTRAL = SKY
C_EXTRA = BLUISH
C_ALT = PINK
C_GREY = "#BBBBBB"

LIKERT_COLORS = [C_GOOD, SKY, ORANGE, PINK, VERMILION, C_GREY]
QUALITY_COLORS = [VERMILION, PINK, ORANGE, SKY, TEAL, C_GREY]
PIE_COLORS = [TEAL, BLUISH, ORANGE, VERMILION, PINK, SKY, C_GREY]
FACILITY_COLORS = [TEAL, BLUISH, ORANGE, VERMILION, PINK, SKY, YELLOW]

# ═══════════════════════════════════════════════════════════════════════════════
# BILINGUAL LABELS
# ═══════════════════════════════════════════════════════════════════════════════
L = {
    "title": {"EN": "Women's Experience Dashboard", "FR": "Tableau de bord — Expérience des femmes"},
    "caption": {"EN": "International Childbirth Initiative — 12 Steps to Safe and Respectful MotherBaby-Family Maternity Care",
                "FR": "Initiative Internationale pour la Naissance — 12 étapes pour des soins de maternité sûrs et respectueux"},
    "filters": {"EN": "Filters", "FR": "Filtres"},
    "facility": {"EN": "Facility", "FR": "Établissement"},
    "compare_mode": {"EN": "Compare facilities", "FR": "Comparer établissements"},
    "date_range": {"EN": "Date range", "FR": "Période"},
    "birth_method_f": {"EN": "Birth method", "FR": "Mode d'accouchement"},
    "high_risk_f": {"EN": "High-risk pregnancy", "FR": "Grossesse à risque"},
    "filtered": {"EN": "Filtered responses", "FR": "Réponses filtrées"},
    "refresh": {"EN": "↻ Refresh data", "FR": "↻ Actualiser"},
    "responses": {"EN": "Responses", "FR": "Réponses"},
    "pct": {"EN": "% of respondents", "FR": "% des répondantes"},
    "download": {"EN": "⬇ Download CSV", "FR": "⬇ Télécharger CSV"},
    "raw_data": {"EN": "📋 View raw data", "FR": "📋 Voir les données brutes"},
    "positive": {"EN": "Positive", "FR": "Positif"},
    "negative": {"EN": "Negative", "FR": "Négatif"},
    "all": {"EN": "All", "FR": "Tous"},
    "s_overview": {"EN": "Overview", "FR": "Vue d'ensemble"},
    "s_comparison": {"EN": "Facility Comparison", "FR": "Comparaison des établissements"},
    "s_timeline": {"EN": "Responses Over Time", "FR": "Réponses dans le temps"},
    "s_trends": {"EN": "Key Indicators Over Time", "FR": "Indicateurs clés dans le temps"},
    "s_profile": {"EN": "Respondent Profile", "FR": "Profil des répondantes"},
    "s_likert": {"EN": "Quality of Care — Likert Scales", "FR": "Qualité des soins — Échelles de Likert"},
    "s_likert_cap": {"EN": "Response distribution across care dimensions (Always → Never)",
                     "FR": "Distribution des réponses par dimension de soins (Toujours → Jamais)"},
    "s_autonomy": {"EN": "Autonomy & Consent", "FR": "Autonomie et consentement"},
    "s_clinical": {"EN": "Clinical Practices", "FR": "Pratiques cliniques"},
    "s_satisfaction": {"EN": "Satisfaction — Expectations vs. Reality", "FR": "Satisfaction — Attentes vs. Réalité"},
    "s_emotions": {"EN": "How Women Felt at the Time of Delivery", "FR": "Ressenti des femmes au moment de l'accouchement"},
    "s_emotions_all": {"EN": "All emotions", "FR": "Toutes les émotions"},
    "s_emotions_no_exhausted": {"EN": "Excluding 'Exhausted'", "FR": "Sans 'Épuisée'"},
    "emo_note": {"EN": "Multiple emotions could be selected — bars show % of respondents who chose each one.",
                 "FR": "Plusieurs émotions pouvaient être sélectionnées — les barres montrent le % de répondantes ayant choisi chacune."},
    "s_discharge": {"EN": "Information Provided Before Discharge", "FR": "Informations données avant la sortie"},
    "s_mistreat": {"EN": "Mistreatment & Respect", "FR": "Maltraitance et respect"},
    "kpi_total": {"EN": "Total responses", "FR": "Total réponses"},
    "kpi_positive": {"EN": "rated care as Good or Very good", "FR": "ont évalué les soins comme Bons ou Très bons"},
    "kpi_skin": {"EN": "had immediate skin-to-skin", "FR": "ont eu le peau à peau immédiat"},
    "kpi_exam": {"EN": "vaginal exams w/o consent", "FR": "examens vaginaux sans consentement"},
    "kpi_epi": {"EN": "episiotomies w/o consent", "FR": "épisiotomies sans consentement"},
    "kpi_no_cost_info": {"EN": "did not know cost in advance", "FR": "ne connaissaient pas le coût à l'avance"},
    "kpi_staff_equipped": {"EN": "Staff well equipped", "FR": "Personnel bien équipé"},
    "p_method": {"EN": "Birth method", "FR": "Mode d'accouchement"},
    "p_age": {"EN": "Age group", "FR": "Groupe d'âge"},
    "p_education": {"EN": "Education level", "FR": "Niveau d'éducation"},
    "p_weeks": {"EN": "Gestational weeks at birth", "FR": "Semaines de gestation"},
    "p_parity": {"EN": "Number of previous deliveries", "FR": "Nombre d'accouchements précédents"},
    "mean_weeks": {"EN": "Mean gest. weeks", "FR": "Sem. gestation (moy.)"},
    "mean_age": {"EN": "Mean age (min–max)", "FR": "Âge moyen (min–max)"},
    "grp_month": {"EN": "Month", "FR": "Mois"},
    "grp_week": {"EN": "Week", "FR": "Semaine"},
    "grp_day": {"EN": "Day", "FR": "Jour"},
    "grp_by": {"EN": "Group by", "FR": "Regrouper par"},
    "tr_positive": {"EN": "% Positive rating", "FR": "% Évaluation positive"},
    "tr_skin": {"EN": "% Immediate skin-to-skin", "FR": "% Peau à peau immédiat"},
    "tr_exam": {"EN": "% Vaginal exams w/o consent", "FR": "% Examens vaginaux s.c."},
    "a_decisions": {"EN": "Included in care decisions", "FR": "Incluse dans les décisions de soins"},
    "a_exam": {"EN": "Vaginal exam — without consent frequency", "FR": "Examen vaginal — fréquence sans consentement"},
    "a_epi": {"EN": "Episiotomy", "FR": "Épisiotomie"},
    "a_treat": {"EN": "Unwanted treatments", "FR": "Soins non souhaités"},
    "c_skin": {"EN": "Skin-to-skin contact", "FR": "Peau à peau"},
    "c_bf": {"EN": "Breastfeeding support", "FR": "Soutien à l'allaitement"},
    "c_induce": {"EN": "Labour induction", "FR": "Déclenchement du travail"},
    "c_pharma": {"EN": "Pain relief received", "FR": "Analgésie reçue"},
    "c_comfort": {"EN": "Non-pharmacological comfort", "FR": "Confort non-pharmacologique"},
    "c_rooming": {"EN": "Rooming-in (baby with mother)", "FR": "Cohabitation mère-bébé"},
    "sat_expect": {"EN": "Before I came here, I expected care to be:", "FR": "Avant de venir ici, je m'attendais à des soins :"},
    "sat_actual": {"EN": "Now, I feel that my care was:", "FR": "Maintenant, j'estime que mes soins étaient :"},
    "m_verbal": {"EN": "Verbal abuse", "FR": "Violence verbale"},
    "m_phys": {"EN": "Physical abuse", "FR": "Violence physique"},
    "m_payment": {"EN": "Informed of costs in advance", "FR": "Informée des coûts à l'avance"},
    "m_no_cost_info": {"EN": "Did NOT know cost in advance", "FR": "Ne connaissait PAS le coût"},
    "vaginal": {"EN": "Vaginal", "FR": "Vaginal"},
    "assisted": {"EN": "Assisted vaginal", "FR": "Vaginal assisté"},
    "elective_cs": {"EN": "Elective C/S", "FR": "Césarienne élective"},
    "emergency_cs": {"EN": "Emergency C/S", "FR": "Césarienne d'urgence"},
    "vbac": {"EN": "VBAC", "FR": "AVAC"},
}

def t(k, lang):
    return L.get(k, {}).get(lang, k)

# ═══════════════════════════════════════════════════════════════════════════════
# VALUE MAPS
# ═══════════════════════════════════════════════════════════════════════════════
METHOD_MAP = {
    "EN": {1: "Vaginal", 2: "Assisted vaginal (forceps or vacuum)", 3: "Elective/planned caesarean (C/S)", 4: "Emergency caesarean (C/S)", 5: "VBAC", 0: "I don't know"},
    "FR": {1: "Vaginal", 2: "Vaginal assisté (forceps ou ventouse)", 3: "Césarienne élective (planifiée) (C/S)", 4: "Césarienne d'urgence (C/S)", 5: "AVAC", 0: "Je ne sais pas"}
}
EDUCATION_MAP = {"EN": {1: "No formal schooling", 2: "Primary", 3: "Secondary", 4: "Higher than secondary"}, "FR": {1: "Aucune", 2: "Primaire", 3: "Secondaire", 4: "Post-secondaire"}}
RISK_MAP = {"EN": {1: "Yes", 2: "No", 0: "I don't know"}, "FR": {1: "Oui", 2: "Non", 0: "Je ne sais pas"}}
LIKERT5_MAP = {"EN": {5: "Always", 4: "Most of the time", 3: "Sometimes", 2: "Rarely", 1: "Never", 0: "I don't know/not applicable"},
               "FR": {5: "Toujours", 4: "La plupart du temps", 3: "Quelquefois", 2: "Rarement", 1: "Jamais", 0: "Je ne sais pas/non applicable"}}
QUALITY_MAP = {"EN": {5: "Very good", 4: "Good", 3: "Neutral", 2: "Poor", 1: "Very bad", 0: "I don't know"},
               "FR": {5: "Très bonne", 4: "Bon", 3: "Neutre", 2: "Mauvaise", 1: "Très mauvaise", 0: "Je ne sais pas"}}
QUALITY_ORDER = {"EN": ["Very bad", "Poor", "Neutral", "Good", "Very good", "I don't know"],
                 "FR": ["Très mauvaise", "Mauvaise", "Neutre", "Bon", "Très bonne", "Je ne sais pas"]}
DECISIONS_MAP = {"EN": {1: "Yes, included with enough information", 2: "Yes, included but not enough information", 3: "Sometimes I was included", 4: "No, I was not included", 0: "I don't know/not applicable"},
                 "FR": {1: "Oui, incluse avec suffisamment d'informations", 2: "Oui, incluse mais pas assez d'informations", 3: "J'ai parfois été incluse", 4: "Non, je n'ai pas été incluse", 0: "Je ne sais pas/non applicable"}}
EPI_MAP = {"EN": {1: "Yes, with my consent", 2: "Yes, without full explanation or consent", 3: "No, because I declined", 4: "No, staff did not recommend it"},
           "FR": {1: "Oui, avec mon consentement", 2: "Oui, sans explication complète ou consentement", 3: "Non, parce que j'ai refusé", 4: "Non, le personnel ne l'a pas recommandé"}}
EXAM_MAP = {"EN": {1: "Never without my consent", 2: "Rarely without consent", 3: "Sometimes without consent", 4: "Frequently without consent", 5: "Always without consent"},
            "FR": {1: "Jamais sans mon consentement", 2: "Rarement sans consentement", 3: "Parfois sans consentement", 4: "Fréquemment sans consentement", 5: "Toujours sans consentement"}}
TREAT_MAP = {"EN": {1: "Yes", 2: "No", 0: "I don't know"}, "FR": {1: "Oui", 2: "Non", 0: "Je ne sais pas"}}
BF_MAP = {"EN": {1: "No, I did not breastfeed", 2: "No, I did not need help", 3: "No, I needed help but did not receive it", 4: "Yes, I was helped but not enough", 5: "Yes, I received the help I needed", 0: "I don't know"},
          "FR": {1: "Non, je n'ai pas allaité", 2: "Non, pas besoin d'aide", 3: "Non, j'avais besoin d'aide mais n'en ai reçu aucune", 4: "Oui, j'ai reçu de l'aide mais insuffisamment", 5: "Oui, j'ai reçu l'aide nécessaire", 0: "Je ne sais pas"}}
SKIN_MAP = {"EN": {1: "Yes", 2: "Yes, but not immediate", 3: "Yes, but less than an hour", 4: "No", 5: "No, chose not to or could not", 6: "I don't know"},
            "FR": {1: "Oui", 2: "Oui, mais pas immédiat", 3: "Oui, moins d'une heure", 4: "Non", 5: "Non, ne souhaitait pas", 6: "Je ne sais pas"}}
INDUCE_MAP = {"EN": {1: "No", 2: "Yes", 0: "I don't know"}, "FR": {1: "Non", 2: "Oui", 0: "Je ne sais pas"}}
PHARMA_MAP = {"EN": {1: "No, I did not want any", 2: "No, even though I wanted it", 3: "Yes, but I received it too late", 4: "Yes, when I wanted it", 5: "No, facility does not offer it", 0: "I don't know"},
              "FR": {1: "Non, je n'en voulais pas", 2: "Non, même si je le voulais", 3: "Oui, mais reçu trop tard", 4: "Oui, quand je le voulais", 5: "Non, non disponible dans l'établissement", 0: "Je ne sais pas"}}
COMFORT_MAP = {"EN": {1: "Yes, and I used them", 2: "Yes, but I did not use them", 3: "No, none were suggested", 0: "I don't know"}, "FR": {1: "Oui, et je les ai utilisés", 2: "Oui, mais je ne les ai pas utilisés", 3: "Non, aucune mesure proposée", 0: "Je ne sais pas"}}
ROOMING_MAP = {"EN": {4: "Yes, with me/us most of the time", 1: "No, baby was sick/sent to unit", 2: "No, baby was not with me/us", 3: "No, I did not want baby with me", 0: "I don't know"},
               "FR": {4: "Oui, avec moi/nous la plupart du temps", 1: "Non, bébé malade/envoyé en néonatalogie", 2: "Non, bébé pas avec moi/nous", 3: "Non, je ne souhaitais pas", 0: "Je ne sais pas"}}
VERBAL_MAP = {"EN": {1: "Never", 2: "Rarely", 3: "Sometimes", 4: "Most of the time", 5: "Always", 0: "I don't know/not applicable"},
              "FR": {1: "Jamais", 2: "Rarement", 3: "Quelquefois", 4: "La plupart du temps", 5: "Toujours", 0: "Je ne sais pas/non applicable"}}
PHYS_MAP = {"EN": {1: "Never", 2: "Rarely", 3: "Sometimes", 4: "Most of the time", 5: "Always", 0: "I don't know/not applicable"},
            "FR": {1: "Jamais", 2: "De temps en temps", 3: "Quelquefois", 4: "La plupart du temps", 5: "Toujours", 0: "Je ne sais pas/non applicable"}}
PAYMENT_MAP = {"EN": {1: "Yes", 2: "No", 3: "No, care was free or covered by insurance", 0: "I don't know"},
               "FR": {1: "Oui", 2: "Non", 3: "Non, soins gratuits ou couverts par l'assurance", 0: "Je ne sais pas"}}
LIKERT_QS = {"EN": {"introduction": "Staff introduced themselves", "spoke": "Staff spoke understandably",
                    "communication": "Comfortable asking questions", "privacy": "Privacy protected",
                    "respect": "Treated respectfully", "values": "Beliefs & choices respected",
                    "positive": "Encouraged to feel empowered", "morale": "Staff happy & supported", "coop": "Coordinated care"},
             "FR": {"introduction": "Le personnel s'est présenté", "spoke": "Le personnel parlait clairement",
                    "communication": "À l'aise pour poser des questions", "privacy": "Intimité protégée",
                    "respect": "Traitée avec respect", "values": "Croyances et choix respectés",
                    "positive": "Encouragée à être autonome", "morale": "Personnel heureux et supporté", "coop": "Soins coordonnés"}}
EMOTION_LABELS = {"EN": {1: "Competence", 2: "Incapable", 3: "Anxious", 4: "Supported", 5: "Exhausted", 6: "Active",
                         7: "Relaxed", 8: "Passive", 9: "Responsible", 10: "Dependent", 11: "Secure", 12: "Excluded"},
                  "FR": {1: "Compétence", 2: "Incapable", 3: "Anxieuse", 4: "Soutenue", 5: "Épuisée", 6: "Active",
                         7: "Détendue", 8: "Passive", 9: "Responsable", 10: "Dépendante", 11: "Sécurisée", 12: "Mise à l'écart"}}
INFO_LABELS = {"EN": {1: "Caring for my new baby", 2: "Advice about family planning",
                      3: "Warning signs requiring consultation", 4: "Where to go for follow-up care"},
               "FR": {1: "Prendre soin de mon nouveau-né", 2: "Conseils sur la planification familiale",
                      3: "Signes à surveiller nécessitant consultation", 4: "Où aller pour les soins de suivi"}}
POSITIVE_EMO = {"EN": {"Competence", "Supported", "Active", "Relaxed", "Responsible", "Secure"},
                "FR": {"Compétence", "Soutenue", "Active", "Détendue", "Responsable", "Sécurisée"}}

LOGO_PATH = Path(__file__).resolve().parent / 'ici_dashboard_assets' / 'ici_logo.png'

# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def load_facility_data(asset_uid: str, facility_name: str):
    """Load data from a single facility."""
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


def load_all_facilities():
    """Load data from all configured facilities."""
    all_dfs = []
    for fac_id, fac_info in FACILITIES.items():
        df = load_facility_data(fac_info["asset_uid"], fac_info["name"])
        if not df.empty:
            df["_country"] = fac_info["country"]
            all_dfs.append(df)
    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    return pd.DataFrame()


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


def parse_multiselect_per_row(series):
    """Return list of selected keys per row for filtering logic."""
    result = []
    for val in series:
        if pd.isna(val):
            result.append([])
        else:
            keys = []
            for tok in str(val).split():
                try:
                    keys.append(int(tok))
                except ValueError:
                    pass
            result.append(keys)
    return result


def prep(df, lang):
    df = df.copy()
    df["_submission_time"] = pd.to_datetime(df["_submission_time"], errors="coerce")
    for col, mp in [("method", METHOD_MAP[lang]), ("education", EDUCATION_MAP[lang]), ("risk", RISK_MAP[lang]),
                    ("satisfaction", QUALITY_MAP[lang]), ("expect", QUALITY_MAP[lang]), ("decisions", DECISIONS_MAP[lang]),
                    ("epi", EPI_MAP[lang]), ("exam", EXAM_MAP[lang]), ("bf", BF_MAP[lang]), ("induce", INDUCE_MAP[lang]),
                    ("treat", TREAT_MAP[lang]), ("pharma", PHARMA_MAP[lang]), ("comfort", COMFORT_MAP[lang]),
                    ("rooming", ROOMING_MAP[lang]), ("verbal", VERBAL_MAP[lang]), ("phys", PHYS_MAP[lang]), ("payment", PAYMENT_MAP[lang])]:
        if col in df.columns:
            df[col] = to_int(df[col])
            df[col + "_label"] = df[col].map(mp).fillna("?")
    for col in LIKERT_QS[lang]:
        if col in df.columns:
            df[col] = to_int(df[col])
            df[col + "_label"] = df[col].map(LIKERT5_MAP[lang]).fillna("?")
    if "skin" in df.columns:
        df["skin_int"] = first_token_int(df["skin"])
        df["skin_label"] = df["skin_int"].map(SKIN_MAP[lang]).fillna("?")
    if "age" in df.columns:
        df["age"] = to_int(df["age"])
        df["age_group"] = pd.cut(df["age"], bins=[0, 19, 24, 29, 34, 39, 99], labels=["<20", "20–24", "25–29", "30–34", "35–39", "40+"])
    if "weeks" in df.columns:
        df["weeks_clean"] = to_int(df["weeks"])
        df.loc[~df["weeks_clean"].between(21, 45), "weeks_clean"] = pd.NA
    if "no_deliveries" in df.columns:
        df["no_deliveries"] = to_int(df["no_deliveries"])
        df.loc[df["no_deliveries"] > 10, "no_deliveries"] = pd.NA
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: clean plotly layout
# ═══════════════════════════════════════════════════════════════════════════════
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
        layout["legend"] = dict(orientation="h", y=-0.18, x=0.5, xanchor="center", font=dict(size=10), tracegroupgap=4)
    else:
        layout["showlegend"] = False
    fig.update_layout(**layout)
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG & GLOBAL CSS
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="ICI Dashboard", page_icon="🤱", layout="wide")
st.markdown(f"""
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

.modebar-container {{top: auto !important; bottom: 4px !important;}}
.modebar {{top: auto !important; bottom: 0 !important;}}
</style>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# LOAD DATA & LANGUAGE SELECTOR
# ═══════════════════════════════════════════════════════════════════════════════
col_lang = st.columns([6, 1])[1]
lang = col_lang.radio("", ["EN", "FR"], horizontal=True, label_visibility="collapsed")

with st.spinner("Loading data..." if lang == "EN" else "Chargement..."):
    raw = load_all_facilities()
if raw.empty:
    st.warning("No data." if lang == "EN" else "Aucune donnée.")
    st.stop()
df = prep(raw, lang)

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
# CSS to center sidebar images
st.markdown("""
<style>
[data-testid="stSidebar"] [data-testid="stImage"] {
    display: flex;
    justify-content: center;
}
[data-testid="stSidebar"] [data-testid="stImage"] img {
    margin: 0 auto;
}
</style>
""", unsafe_allow_html=True)

if LOGO_PATH.exists():
    st.sidebar.image(str(LOGO_PATH), width=110)
st.sidebar.markdown("""
<div style="text-align:center; padding: 0 0 0 0;">
    <div style="font-family:'DM Serif Display',serif; font-size:1.05rem; color:#005f46; font-weight:600; line-height:1.3; margin-bottom:2px;">ICI Dashboard</div>
    <div style="font-size:0.68rem; color:#888; line-height:1.3; margin-bottom:12px;">International Childbirth Initiative</div>
    <hr style="border:none; border-top:1px solid #e0e0e0; margin:0 0 12px 0;">
</div>
""", unsafe_allow_html=True)
st.sidebar.header(t("filters", lang))

# Facility selection (always show, ready for multiple facilities)
facilities_available = df["_facility"].unique().tolist()
compare_mode = False

if len(facilities_available) > 1:
    compare_mode = st.sidebar.checkbox(t("compare_mode", lang), value=False)
    if compare_mode:
        selected_facilities = st.sidebar.multiselect(t("facility", lang), options=facilities_available, default=facilities_available)
        if selected_facilities:
            df = df[df["_facility"].isin(selected_facilities)]
    else:
        selected_facility = st.sidebar.selectbox(t("facility", lang), options=[t("all", lang)] + facilities_available)
        if selected_facility != t("all", lang):
            df = df[df["_facility"] == selected_facility]
else:
    # Show facility name even with single facility (informational)
    st.sidebar.markdown(f"**{t('facility', lang)}:** {facilities_available[0]}" if facilities_available else "")

# Date range filter
if "_submission_time" in df.columns and df["_submission_time"].notna().any():
    import calendar
    mn = df["_submission_time"].min()
    mx = df["_submission_time"].max()
    years = sorted(df["_submission_time"].dt.year.dropna().unique().astype(int).tolist())
    months_en = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    months_fr = ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun", "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]
    months = months_fr if lang == "FR" else months_en

    st.sidebar.markdown(f"**{t('date_range', lang)}**")
    dc1, dc2 = st.sidebar.columns(2)
    start_year = dc1.selectbox("", years, index=0, key="sy", label_visibility="collapsed")
    start_month = dc2.selectbox("", months, index=mn.month - 1, key="sm", label_visibility="collapsed")
    dc3, dc4 = st.sidebar.columns(2)
    end_year = dc3.selectbox("", years, index=len(years) - 1, key="ey", label_visibility="collapsed")
    end_month = dc4.selectbox("", months, index=mx.month - 1, key="em", label_visibility="collapsed")

    sm_idx = (months_fr if lang == "FR" else months_en).index(start_month) + 1
    em_idx = (months_fr if lang == "FR" else months_en).index(end_month) + 1
    start_dt = datetime(start_year, sm_idx, 1).date()
    end_dt = datetime(end_year, em_idx, calendar.monthrange(end_year, em_idx)[1]).date()
    df = df[(df["_submission_time"].dt.date >= start_dt) & (df["_submission_time"].dt.date <= end_dt)]

if "method_label" in df.columns:
    opts = [t("all", lang)] + sorted(df["method_label"].dropna().unique().tolist())
    sel = st.sidebar.selectbox(t("birth_method_f", lang), opts)
    if sel != t("all", lang):
        df = df[df["method_label"] == sel]
if "risk_label" in df.columns:
    opts = [t("all", lang)] + sorted(df["risk_label"].dropna().unique().tolist())
    sel = st.sidebar.selectbox(t("high_risk_f", lang), opts)
    if sel != t("all", lang):
        df = df[df["risk_label"] == sel]
st.sidebar.metric(t("filtered", lang), len(df))
if st.sidebar.button(t("refresh", lang)):
    st.cache_data.clear()
    st.rerun()

if LOGO_PATH.exists():
    st.sidebar.image(str(LOGO_PATH), width=85)

# ═══════════════════════════════════════════════════════════════════════════════
# HERO BANNER
# ═══════════════════════════════════════════════════════════════════════════════
sat_good = (df["satisfaction"].isin([4, 5])).sum() / len(df) * 100 if "satisfaction" in df.columns and len(df) > 0 else 0
skin_imm = (df["skin_int"] == 1).sum() / len(df) * 100 if "skin_int" in df.columns and len(df) > 0 else 0
exam_nc = (df["exam"].isin([2, 3, 4, 5])).sum() if "exam" in df.columns else 0
epi_nc = (df["epi"] == 2).sum() if "epi" in df.columns else 0
no_cost_info = (df["payment"] == 2).sum() / len(df) * 100 if "payment" in df.columns and len(df) > 0 else 0

st.markdown(f"""
<div class="hero">
    <div class="hero-title">{t("title", lang)}</div>
    <div class="hero-caption">{t("caption", lang)}</div>
    <div class="hero-stats">
        <div class="hero-stat">
            <div class="hero-stat-num">{len(df):,}</div>
            <div class="hero-stat-label">{t("kpi_total", lang)}</div>
        </div>
        <div class="hero-stat">
            <div class="hero-stat-num">{sat_good:.0f}%</div>
            <div class="hero-stat-label">{t("kpi_positive", lang)}</div>
        </div>
        <div class="hero-stat">
            <div class="hero-stat-num">{skin_imm:.0f}%</div>
            <div class="hero-stat-label">{t("kpi_skin", lang)}</div>
        </div>
        <div class="hero-stat hero-stat-bad">
            <div class="hero-stat-num">{exam_nc}</div>
            <div class="hero-stat-label">{t("kpi_exam", lang)}</div>
        </div>
        <div class="hero-stat hero-stat-bad">
            <div class="hero-stat-num">{no_cost_info:.0f}%</div>
            <div class="hero-stat-label">{t("kpi_no_cost_info", lang)}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# FACILITY COMPARISON (when multiple facilities and compare_mode)
# ═══════════════════════════════════════════════════════════════════════════════
if compare_mode and "_facility" in df.columns and df["_facility"].nunique() > 1:
    st.markdown(f'<div class="section-title">{t("s_comparison", lang)}</div>', unsafe_allow_html=True)
    
    # CS Rates comparison
    if "method" in df.columns:
        cs_data = []
        for fac in df["_facility"].unique():
            fac_df = df[df["_facility"] == fac]
            country = fac_df["_country"].iloc[0] if "_country" in fac_df.columns else "Unknown"
            n = len(fac_df)
            if n == 0:
                continue
            vaginal = (fac_df["method"] == 1).sum() / n * 100
            assisted = (fac_df["method"] == 2).sum() / n * 100
            elective_cs = (fac_df["method"] == 3).sum() / n * 100
            emergency_cs = (fac_df["method"] == 4).sum() / n * 100
            vbac = (fac_df["method"] == 5).sum() / n * 100
            cs_data.append({
                "Facility": fac, "Country": country, "n": n,
                t("vaginal", lang): vaginal, t("assisted", lang): assisted,
                t("elective_cs", lang): elective_cs, t("emergency_cs", lang): emergency_cs,
                t("vbac", lang): vbac,
            })
        
        if cs_data:
            cs_df = pd.DataFrame(cs_data)
            melt_cols = [t("vaginal", lang), t("assisted", lang), t("elective_cs", lang), t("emergency_cs", lang), t("vbac", lang)]
            cs_melt = cs_df.melt(id_vars=["Facility", "Country", "n"], value_vars=melt_cols, var_name="Birth Method", value_name="Percentage")
            fig = px.bar(cs_melt, x="Facility", y="Percentage", color="Birth Method", barmode="group",
                         color_discrete_sequence=FACILITY_COLORS, hover_data={"Country": True, "n": True})
            fig.update_layout(height=400, margin=dict(t=32, b=80, l=8, r=8), plot_bgcolor="white", paper_bgcolor="white",
                              font=dict(family="DM Sans, sans-serif"),
                              legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
                              yaxis=dict(title="%", gridcolor="#eeeeee"), xaxis=dict(title="", showgrid=False))
            st.plotly_chart(fig, use_container_width=True)
    
    # Demographics comparison table
    demo_data = []
    for fac in df["_facility"].unique():
        fac_df = df[df["_facility"] == fac]
        country = fac_df["_country"].iloc[0] if "_country" in fac_df.columns else "Unknown"
        n = len(fac_df)
        weeks_mean = fac_df["weeks_clean"].mean() if "weeks_clean" in fac_df.columns else np.nan
        age_mean = fac_df["age"].mean() if "age" in fac_df.columns else np.nan
        age_min = fac_df["age"].min() if "age" in fac_df.columns else np.nan
        age_max = fac_df["age"].max() if "age" in fac_df.columns else np.nan
        staff_ok = (fac_df["morale"].isin([4, 5])).sum() / n * 100 if "morale" in fac_df.columns and n > 0 else np.nan
        exam_nc_pct = (fac_df["exam"].isin([2, 3, 4, 5])).sum() / n * 100 if "exam" in fac_df.columns and n > 0 else np.nan
        epi_nc_pct = (fac_df["epi"] == 2).sum() / n * 100 if "epi" in fac_df.columns and n > 0 else np.nan
        treat_pct = (fac_df["treat"] == 1).sum() / n * 100 if "treat" in fac_df.columns and n > 0 else np.nan
        verbal_pct = (fac_df["verbal"].isin([2, 3, 4, 5])).sum() / n * 100 if "verbal" in fac_df.columns and n > 0 else np.nan
        phys_pct = (fac_df["phys"].isin([2, 3, 4, 5])).sum() / n * 100 if "phys" in fac_df.columns and n > 0 else np.nan
        no_cost_pct = (fac_df["payment"] == 2).sum() / n * 100 if "payment" in fac_df.columns and n > 0 else np.nan
        
        demo_data.append({
            "Facility": fac, "Country": country, "n": n,
            t("mean_weeks", lang): f"{weeks_mean:.1f}" if not np.isnan(weeks_mean) else "–",
            t("mean_age", lang): f"{age_mean:.1f} ({age_min:.0f}–{age_max:.0f})" if not np.isnan(age_mean) else "–",
            t("kpi_staff_equipped", lang): f"{staff_ok:.1f}%" if not np.isnan(staff_ok) else "–",
            t("a_exam", lang): f"{exam_nc_pct:.1f}%" if not np.isnan(exam_nc_pct) else "–",
            t("a_epi", lang): f"{epi_nc_pct:.1f}%" if not np.isnan(epi_nc_pct) else "–",
            t("a_treat", lang): f"{treat_pct:.1f}%" if not np.isnan(treat_pct) else "–",
            t("m_verbal", lang): f"{verbal_pct:.1f}%" if not np.isnan(verbal_pct) else "–",
            t("m_phys", lang): f"{phys_pct:.1f}%" if not np.isnan(phys_pct) else "–",
            t("m_no_cost_info", lang): f"{no_cost_pct:.1f}%" if not np.isnan(no_cost_pct) else "–",
        })
    
    if demo_data:
        demo_df = pd.DataFrame(demo_data)
        st.dataframe(demo_df, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL 1 — Timeline
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(f'<div class="section-title">{t("s_timeline", lang)}</div>', unsafe_allow_html=True)
if "_submission_time" in df.columns and df["_submission_time"].notna().any():
    freq_opts = [t("grp_month", lang), t("grp_week", lang), t("grp_day", lang)]
    freq = st.radio(t("grp_by", lang), freq_opts, horizontal=True)
    fmap = {t("grp_day", lang): "D", t("grp_week", lang): "W", t("grp_month", lang): "ME"}
    ts = df.set_index("_submission_time").resample(fmap[freq]).size().reset_index(name="n")
    fig = px.area(ts, x="_submission_time", y="n", labels={"_submission_time": "", "n": t("responses", lang)}, color_discrete_sequence=[TEAL])
    fig.update_traces(line_width=2, fillcolor="rgba(0,158,115,0.12)")
    fig.update_layout(margin=dict(t=8, b=8, l=8, r=8), height=200, plot_bgcolor="white", paper_bgcolor="white", font=dict(family="DM Sans, sans-serif"))
    st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL 2 — Trends over time
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(f'<div class="section-title">{t("s_trends", lang)}</div>', unsafe_allow_html=True)
if "_submission_time" in df.columns and df["_submission_time"].notna().any():
    dft = df.copy()
    dft["month"] = dft["_submission_time"].dt.to_period("M").dt.to_timestamp()
    monthly = dft.groupby("month").agg(
        n=("_submission_time", "count"),
        sat_pos=("satisfaction", lambda x: (pd.to_numeric(x, errors="coerce").isin([4, 5])).sum()),
        skin_imm=("skin_int", lambda x: (pd.to_numeric(x, errors="coerce") == 1).sum()),
        exam_nc=("exam", lambda x: (pd.to_numeric(x, errors="coerce").isin([2, 3, 4, 5])).sum()),
    ).reset_index()
    monthly = monthly[monthly["n"] >= 5]
    monthly["pct_sat"] = monthly["sat_pos"] / monthly["n"] * 100
    monthly["pct_skin"] = monthly["skin_imm"] / monthly["n"] * 100
    monthly["pct_exam"] = monthly["exam_nc"] / monthly["n"] * 100

    tabs = st.tabs([t("tr_positive", lang), t("tr_skin", lang), t("tr_exam", lang)])
    for tab, (ycol, color) in zip(tabs, [("pct_sat", TEAL), ("pct_skin", BLUISH), ("pct_exam", VERMILION)]):
        with tab:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=monthly["month"], y=monthly[ycol], mode="lines+markers", line=dict(color=color, width=2.5), marker=dict(size=6)))
            fig.update_layout(height=200, margin=dict(t=8, b=8, l=8, r=8), yaxis=dict(title="%", range=[0, 100]), plot_bgcolor="white", paper_bgcolor="white", font=dict(family="DM Sans, sans-serif"))
            st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL 3 — Profile
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(f'<div class="section-title">{t("s_profile", lang)}</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)

if "method_label" in df.columns:
    mc = df["method_label"].value_counts().reset_index()
    mc.columns = ["m", "n"]
    fig = px.pie(mc, names="m", values="n", hole=0.45, color_discrete_sequence=PIE_COLORS)
    fig = clean_layout(fig, title=t("p_method", lang), height=300, legend_below=True)
    c1.plotly_chart(fig, use_container_width=True)

if "age_group" in df.columns:
    ac = df["age_group"].value_counts().sort_index().reset_index()
    ac.columns = ["f", "n"]
    fig = px.bar(ac, x="f", y="n", color_discrete_sequence=[BLUISH], labels={"f": "", "n": ""})
    fig = clean_layout(fig, title=t("p_age", lang), height=300)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#eeeeee")
    c2.plotly_chart(fig, use_container_width=True)

if "education_label" in df.columns:
    ec = df["education_label"].value_counts().reset_index()
    ec.columns = ["e", "n"]
    fig = px.bar(ec, x="n", y="e", orientation="h", color_discrete_sequence=[PINK], labels={"e": "", "n": ""})
    fig = clean_layout(fig, title=t("p_education", lang), height=300)
    fig.update_xaxes(gridcolor="#eeeeee")
    fig.update_yaxes(showgrid=False)
    c3.plotly_chart(fig, use_container_width=True)

c1, c2 = st.columns(2)
if "weeks_clean" in df.columns:
    wk = df["weeks_clean"].dropna()
    fig = px.histogram(wk, nbins=16, color_discrete_sequence=[ORANGE], labels={"value": t("p_weeks", lang), "count": ""})
    fig = clean_layout(fig, title=t("p_weeks", lang), height=260)
    fig.update_layout(showlegend=False, xaxis=dict(range=[28, 46], dtick=1))
    fig.update_xaxes(gridcolor="#eeeeee")
    fig.update_yaxes(gridcolor="#eeeeee")
    c1.plotly_chart(fig, use_container_width=True)

if "no_deliveries" in df.columns:
    nd = df["no_deliveries"].dropna().value_counts().sort_index().reset_index()
    nd.columns = ["n", "count"]
    nd["n"] = nd["n"].astype(int).astype(str)
    fig = px.bar(nd, x="n", y="count", color_discrete_sequence=[SKY], labels={"n": t("p_parity", lang), "count": ""})
    fig = clean_layout(fig, title=t("p_parity", lang), height=260)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#eeeeee")
    c2.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# Treemap: birth method → emotional experience
# ═══════════════════════════════════════════════════════════════════════════════
if "method_label" in df.columns and "emotion" in df.columns:
    treemap_title = {"EN": "Emotional Experience by Birth Method", "FR": "Vécu émotionnel par mode d'accouchement"}[lang]
    pos_keys = [1, 4, 6, 7, 9, 11]
    neg_keys = [2, 3, 5, 8, 10, 12]
    pos_lbl = {"EN": "Positive emotions", "FR": "Émotions positives"}[lang]
    neg_lbl = {"EN": "Negative emotions", "FR": "Émotions négatives"}[lang]
    root_lbl = {"EN": "All births", "FR": "Tous accouchements"}[lang]

    tm_rows = []
    for mcode, mlabel in [(1, METHOD_MAP[lang][1]), (2, METHOD_MAP[lang][2]), (3, METHOD_MAP[lang][3]), (4, METHOD_MAP[lang][4]), (5, METHOD_MAP[lang][5])]:
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
        ids.append("root")
        labels.append(root_lbl)
        parents.append("")
        values.append(0)
        colors.append("#eef2f0")

        methods_seen = tmdf["method"].unique().tolist()
        for i, m in enumerate(methods_seen):
            mid = f"m_{i}"
            ids.append(mid)
            labels.append(m)
            parents.append("root")
            values.append(int(tmdf[tmdf["method"] == m]["n"].sum()))
            colors.append(method_palette[i % len(method_palette)])
            for _, row in tmdf[tmdf["method"] == m].iterrows():
                lid = f"l_{i}_{row['type']}"
                ids.append(lid)
                labels.append(row["type"])
                parents.append(mid)
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
            title=dict(text=treemap_title, font=dict(size=13, family="DM Serif Display, serif", color="#1a1a1a"), x=0, xanchor="left", y=0.98, yanchor="top"),
            margin=dict(t=44, b=8, l=8, r=8), height=360, paper_bgcolor="white", font=dict(family="DM Sans, sans-serif"), showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL 4 — Likert
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(f'<div class="section-title">{t("s_likert", lang)}</div>', unsafe_allow_html=True)
st.caption(t("s_likert_cap", lang))
likert_order = list(LIKERT5_MAP[lang].values())
rows = []
for col, label in LIKERT_QS[lang].items():
    lbl = col + "_label"
    if lbl in df.columns:
        vc = df[lbl].value_counts(normalize=True).mul(100).round(1)
        for cat in likert_order:
            rows.append({"Dimension": label, "Response": cat, "Pct": vc.get(cat, 0)})
if rows:
    ldf = pd.DataFrame(rows)
    fig = px.bar(ldf, x="Pct", y="Dimension", color="Response", orientation="h", barmode="stack", color_discrete_sequence=LIKERT_COLORS,
                 category_orders={"Response": likert_order}, labels={"Pct": "%", "Dimension": ""})
    fig.update_layout(legend=dict(orientation="h", y=-0.22, x=0.5, xanchor="center", font=dict(size=10)),
                      margin=dict(t=8, b=110, l=8, r=8), height=480, plot_bgcolor="white", paper_bgcolor="white", font=dict(family="DM Sans, sans-serif"))
    st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL 4b — Bubble: age group × parity × count
# ═══════════════════════════════════════════════════════════════════════════════
if "age" in df.columns and "no_deliveries" in df.columns:
    bubble_title = {"EN": "Respondent Profile — Age × Number of Previous Deliveries", "FR": "Profil des répondantes — Âge × Nombre d'accouchements précédents"}[lang]
    bdf = df.copy()
    bdf["age_grp"] = pd.cut(bdf["age"], bins=[0, 24, 29, 34, 39, 99], labels=["<25", "25–29", "30–34", "35–39", "40+"])
    bdf["nd"] = pd.to_numeric(bdf["no_deliveries"], errors="coerce")
    bdf.loc[bdf["nd"] > 6, "nd"] = pd.NA
    bubble = bdf.dropna(subset=["age_grp", "nd"]).groupby(["age_grp", "nd"]).size().reset_index(name="n")
    bubble["nd_str"] = bubble["nd"].astype(int).astype(str)
    bubble["pct"] = (bubble["n"] / bubble["n"].sum() * 100).round(1)

    fig = px.scatter(bubble, x="age_grp", y="nd_str", size="n", color="n",
                     color_continuous_scale=[[0, "#e8f4f0"], [0.4, SKY], [1, TEAL]], size_max=55,
                     labels={"age_grp": {"EN": "Age group", "FR": "Groupe d'âge"}[lang],
                             "nd_str": {"EN": "Previous deliveries", "FR": "Accouchements précédents"}[lang], "n": t("responses", lang)},
                     hover_data={"n": True, "pct": True, "age_grp": True, "nd_str": True})
    fig.update_layout(
        title=dict(text=bubble_title, font=dict(size=13, family="DM Serif Display, serif", color="#1a1a1a"), x=0, xanchor="left", y=0.98, yanchor="top"),
        margin=dict(t=44, b=16, l=8, r=8), height=360, plot_bgcolor="white", paper_bgcolor="white", coloraxis_showscale=False, font=dict(family="DM Sans, sans-serif"),
        xaxis=dict(showgrid=True, gridcolor="#eeeeee"), yaxis=dict(showgrid=True, gridcolor="#eeeeee", title={"EN": "Previous deliveries", "FR": "Accouchements précédents"}[lang]),
    )
    st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL 5 — Autonomy & Consent
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(f'<div class="section-title">{t("s_autonomy", lang)}</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
if "decisions_label" in df.columns:
    dc = df["decisions_label"].value_counts().reset_index()
    dc.columns = ["r", "n"]
    fig = px.bar(dc, x="n", y="r", orientation="h", color_discrete_sequence=[TEAL], labels={"r": "", "n": t("responses", lang)})
    fig = clean_layout(fig, title=t("a_decisions", lang), height=270)
    fig.update_xaxes(gridcolor="#eeeeee")
    fig.update_yaxes(showgrid=False)
    c1.plotly_chart(fig, use_container_width=True)
if "exam_label" in df.columns:
    ec = df["exam_label"].value_counts().reset_index()
    ec.columns = ["r", "n"]
    color_map = {v: c for v, c in zip(ec["r"].tolist(), [TEAL, SKY, ORANGE, PINK, VERMILION])}
    fig = px.bar(ec, x="n", y="r", orientation="h", color="r", color_discrete_map=color_map, labels={"r": "", "n": ""})
    fig = clean_layout(fig, title=t("a_exam", lang), height=270)
    fig.update_layout(showlegend=False)
    fig.update_xaxes(gridcolor="#eeeeee")
    fig.update_yaxes(showgrid=False)
    c2.plotly_chart(fig, use_container_width=True)

c1, c2 = st.columns(2)
if "epi_label" in df.columns:
    ep = df["epi_label"].value_counts().reset_index()
    ep.columns = ["r", "n"]
    fig = px.bar(ep, x="n", y="r", orientation="h", color_discrete_sequence=[TEAL], labels={"r": "", "n": t("responses", lang)})
    fig = clean_layout(fig, title=t("a_epi", lang), height=250)
    fig.update_xaxes(gridcolor="#eeeeee")
    fig.update_yaxes(showgrid=False)
    c1.plotly_chart(fig, use_container_width=True)
if "treat_label" in df.columns:
    tc = df["treat_label"].value_counts().reset_index()
    tc.columns = ["r", "n"]
    fig = px.pie(tc, names="r", values="n", hole=0.5, color_discrete_sequence=PIE_COLORS)
    fig = clean_layout(fig, title=t("a_treat", lang), height=250, legend_below=True)
    c2.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL 6 — Clinical Practices
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(f'<div class="section-title">{t("s_clinical", lang)}</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
if "skin_label" in df.columns:
    sk = df["skin_label"].value_counts().reset_index()
    sk.columns = ["r", "n"]
    fig = px.bar(sk, x="n", y="r", orientation="h", color_discrete_sequence=[TEAL], labels={"r": "", "n": t("responses", lang)})
    fig = clean_layout(fig, title=t("c_skin", lang), height=290)
    fig.update_xaxes(gridcolor="#eeeeee")
    fig.update_yaxes(showgrid=False)
    c1.plotly_chart(fig, use_container_width=True)
if "bf_label" in df.columns:
    bf = df["bf_label"].value_counts().reset_index()
    bf.columns = ["r", "n"]
    fig = px.bar(bf, x="n", y="r", orientation="h", color_discrete_sequence=[BLUISH], labels={"r": "", "n": ""})
    fig = clean_layout(fig, title=t("c_bf", lang), height=290)
    fig.update_xaxes(gridcolor="#eeeeee")
    fig.update_yaxes(showgrid=False)
    c2.plotly_chart(fig, use_container_width=True)
if "induce_label" in df.columns:
    ind = df["induce_label"].value_counts().reset_index()
    ind.columns = ["r", "n"]
    fig = px.pie(ind, names="r", values="n", hole=0.52, color_discrete_sequence=PIE_COLORS)
    fig = clean_layout(fig, title=t("c_induce", lang), height=290, legend_below=True)
    c3.plotly_chart(fig, use_container_width=True)

c1, c2, c3 = st.columns(3)
if "pharma_label" in df.columns:
    ph = df["pharma_label"].value_counts().reset_index()
    ph.columns = ["r", "n"]
    fig = px.bar(ph, x="n", y="r", orientation="h", color_discrete_sequence=[SKY], labels={"r": "", "n": ""})
    fig = clean_layout(fig, title=t("c_pharma", lang), height=270)
    fig.update_xaxes(gridcolor="#eeeeee")
    fig.update_yaxes(showgrid=False)
    c1.plotly_chart(fig, use_container_width=True)
if "comfort_label" in df.columns:
    co = df["comfort_label"].value_counts().reset_index()
    co.columns = ["r", "n"]
    fig = px.bar(co, x="n", y="r", orientation="h", color_discrete_sequence=[ORANGE], labels={"r": "", "n": ""})
    fig = clean_layout(fig, title=t("c_comfort", lang), height=270)
    fig.update_xaxes(gridcolor="#eeeeee")
    fig.update_yaxes(showgrid=False)
    c2.plotly_chart(fig, use_container_width=True)
if "rooming_label" in df.columns:
    ro = df["rooming_label"].value_counts().reset_index()
    ro.columns = ["r", "n"]
    fig = px.bar(ro, x="n", y="r", orientation="h", color_discrete_sequence=[TEAL], labels={"r": "", "n": t("responses", lang)})
    fig = clean_layout(fig, title=t("c_rooming", lang), height=270)
    fig.update_xaxes(gridcolor="#eeeeee")
    fig.update_yaxes(showgrid=False)
    c3.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL 6b — Sankey: Risk → Birth method → Skin-to-skin (with percentages)
# ═══════════════════════════════════════════════════════════════════════════════
if "risk" in df.columns and "method" in df.columns and "skin_int" in df.columns:
    sk_title = {"EN": "Care Journey: Risk Profile → Birth Method → Skin-to-Skin Contact",
                "FR": "Parcours : Profil de risque → Mode d'accouchement → Peau à peau"}[lang]

    risk_lbl = {1: {"EN": "High-risk", "FR": "Grossesse à risque"}[lang], 2: {"EN": "Low-risk", "FR": "Grossesse normale"}[lang]}
    method_lbl = {1: METHOD_MAP[lang][1], 2: METHOD_MAP[lang][2], 3: METHOD_MAP[lang][3], 4: METHOD_MAP[lang][4]}
    skin_lbl = {1: {"EN": "✓ Immediate skin-to-skin", "FR": "✓ Peau à peau immédiat"}[lang],
                0: {"EN": "✗ Not immediate / No", "FR": "✗ Pas immédiat / Non"}[lang]}

    fdf = df[df["risk"].isin([1, 2]) & df["method"].isin([1, 2, 3, 4])].copy()
    fdf["skin_bin"] = (fdf["skin_int"] == 1).astype(int)
    total_n = len(fdf)

    if total_n > 0:
        risk_nodes = [risk_lbl[1], risk_lbl[2]]
        method_nodes = [method_lbl[k] for k in [1, 2, 3, 4]]
        skin_nodes = [skin_lbl[1], skin_lbl[0]]
        all_nodes = risk_nodes + method_nodes + skin_nodes
        R, M, S = 0, 2, 6

        sources, targets, values, colors, customdata = [], [], [], [], []

        for r in [1, 2]:
            for m in [1, 2, 3, 4]:
                n = len(fdf[(fdf["risk"] == r) & (fdf["method"] == m)])
                if n == 0:
                    continue
                pct = n / total_n * 100
                sources.append(R + (r - 1))
                targets.append(M + [1, 2, 3, 4].index(m))
                values.append(n)
                customdata.append(f"{pct:.1f}%")
                colors.append("rgba(0,158,115,0.2)" if r == 2 else "rgba(213,94,0,0.2)")

        for m in [1, 2, 3, 4]:
            for s in [1, 0]:
                n = len(fdf[(fdf["method"] == m) & (fdf["skin_bin"] == s)])
                if n == 0:
                    continue
                pct = n / total_n * 100
                sources.append(M + [1, 2, 3, 4].index(m))
                targets.append(S + (0 if s == 1 else 1))
                values.append(n)
                customdata.append(f"{pct:.1f}%")
                colors.append("rgba(0,158,115,0.20)" if s == 1 else "rgba(213,94,0,0.20)")

        node_colors = [VERMILION, TEAL] + [BLUISH, SKY, ORANGE, PINK] + [TEAL, VERMILION]

        fig = go.Figure(go.Sankey(
            arrangement="snap",
            node=dict(pad=20, thickness=24, line=dict(color="white", width=0.5), label=all_nodes, color=node_colors,
                      hovertemplate="%{label}<br>%{value} women<extra></extra>"),
            link=dict(source=sources, target=targets, value=values, color=colors, customdata=customdata,
                      hovertemplate="%{source.label} → %{target.label}<br>%{value} women (%{customdata})<extra></extra>")
        ))
        fig.update_traces(textfont=dict(size=13, family="DM Sans, sans-serif", color="#1a1a1a"))
        fig.update_layout(title=dict(text=sk_title, font=dict(size=13, family="DM Serif Display, serif", color="#1a1a1a"), x=0, xanchor="left"),
                          margin=dict(t=64, b=16, l=8, r=8), height=420, paper_bgcolor="white", font=dict(family="DM Sans, sans-serif", size=11))
        st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL 7 — Satisfaction
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(f'<div class="section-title">{t("s_satisfaction", lang)}</div>', unsafe_allow_html=True)
if "expect_label" in df.columns and "satisfaction_label" in df.columns:
    c1, c2 = st.columns(2)
    q_order = QUALITY_ORDER[lang]
    for col, field, title in [(c1, "expect_label", t("sat_expect", lang)), (c2, "satisfaction_label", t("sat_actual", lang))]:
        vc = df[field].value_counts().reindex(q_order, fill_value=0).reset_index()
        vc.columns = ["r", "n"]
        fig = px.bar(vc, x="r", y="n", color="r", color_discrete_sequence=QUALITY_COLORS, labels={"r": "", "n": t("responses", lang)}, category_orders={"r": q_order})
        fig = clean_layout(fig, title=title, height=310)
        fig.update_layout(showlegend=False)
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(gridcolor="#eeeeee")
        col.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL 8 — Emotions (two views: all emotions, and excluding exhaustion)
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(f'<div class="section-title">{t("s_emotions", lang)}</div>', unsafe_allow_html=True)
st.caption(t("emo_note", lang))

if "emotion" in df.columns:
    emo_labels = EMOTION_LABELS[lang]
    pos = POSITIVE_EMO[lang]
    exhausted_key = 5
    exhausted_label = emo_labels[exhausted_key]
    
    # Count all emotions
    counts = parse_multiselect(df["emotion"], list(emo_labels.keys()))
    
    # All emotions
    rows_all = [{"Emotion": lbl, "Pct": round(counts[k] / len(df) * 100, 1), 
                 "Type": t("positive", lang) if lbl in pos else t("negative", lang)} 
                for k, lbl in emo_labels.items()]
    edf_all = pd.DataFrame(rows_all).sort_values("Pct", ascending=True)
    
    # Excluding exhausted
    rows_no_exhaust = [{"Emotion": lbl, "Pct": round(counts[k] / len(df) * 100, 1), 
                        "Type": t("positive", lang) if lbl in pos else t("negative", lang)} 
                       for k, lbl in emo_labels.items() if k != exhausted_key]
    edf_no_exhaust = pd.DataFrame(rows_no_exhaust).sort_values("Pct", ascending=True)
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown(f"**{t('s_emotions_all', lang)}**")
        fig = px.bar(edf_all, x="Pct", y="Emotion", color="Type", orientation="h",
                     color_discrete_map={t("positive", lang): TEAL, t("negative", lang): VERMILION}, 
                     labels={"Pct": t("pct", lang), "Emotion": ""})
        fig.update_layout(legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center", font=dict(size=10)),
                          margin=dict(t=8, b=60, l=8, r=8), height=420, plot_bgcolor="white", paper_bgcolor="white", 
                          font=dict(family="DM Sans, sans-serif"))
        fig.update_xaxes(gridcolor="#eeeeee")
        fig.update_yaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with c2:
        st.markdown(f"**{t('s_emotions_no_exhausted', lang)}**")
        fig2 = px.bar(edf_no_exhaust, x="Pct", y="Emotion", color="Type", orientation="h",
                      color_discrete_map={t("positive", lang): TEAL, t("negative", lang): VERMILION}, 
                      labels={"Pct": t("pct", lang), "Emotion": ""})
        fig2.update_layout(legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center", font=dict(size=10)),
                           margin=dict(t=8, b=60, l=8, r=8), height=420, plot_bgcolor="white", paper_bgcolor="white", 
                           font=dict(family="DM Sans, sans-serif"))
        fig2.update_xaxes(gridcolor="#eeeeee")
        fig2.update_yaxes(showgrid=False)
        st.plotly_chart(fig2, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL 9 — Discharge Info
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(f'<div class="section-title">{t("s_discharge", lang)}</div>', unsafe_allow_html=True)
if "info" in df.columns:
    info_labels = INFO_LABELS[lang]
    counts = parse_multiselect(df["info"], list(info_labels.keys()))
    rows = [{"Topic": lbl, "Pct": round(counts[k] / len(df) * 100, 1)} for k, lbl in info_labels.items()]
    idf = pd.DataFrame(rows).sort_values("Pct")
    fig = px.bar(idf, x="Pct", y="Topic", orientation="h", color_discrete_sequence=[PINK], labels={"Pct": t("pct", lang), "Topic": ""})
    fig.update_layout(margin=dict(t=16, b=8, l=8, r=8), height=220, plot_bgcolor="white", paper_bgcolor="white", font=dict(family="DM Sans, sans-serif"))
    fig.update_xaxes(gridcolor="#eeeeee")
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL 10 — Mistreatment (with "did not know cost" highlight)
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(f'<div class="section-title">{t("s_mistreat", lang)}</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
for col, field, title in [(c1, "verbal_label", t("m_verbal", lang)), (c2, "phys_label", t("m_phys", lang)), (c3, "payment_label", t("m_payment", lang))]:
    if field in df.columns:
        vc = df[field].value_counts().reset_index()
        vc.columns = ["r", "n"]
        color = VERMILION if field in ["verbal_label", "phys_label"] else BLUISH
        fig = px.bar(vc, x="n", y="r", orientation="h", color_discrete_sequence=[color], labels={"r": "", "n": t("responses", lang)})
        fig = clean_layout(fig, title=title, height=260)
        fig.update_xaxes(gridcolor="#eeeeee")
        fig.update_yaxes(showgrid=False)
        col.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL 11 — Raw data
# ═══════════════════════════════════════════════════════════════════════════════
with st.expander(t("raw_data", lang)):
    hide = [c for c in df.columns if c.startswith("_") or c == "meta/rootUuid"]
    show = [c for c in df.columns if c not in hide]
    st.dataframe(df[show], use_container_width=True, height=400)
    csv = df[show].to_csv(index=False).encode("utf-8")
    st.download_button(t("download", lang), csv, f"ici_data_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
