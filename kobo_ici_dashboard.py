"""ICI Women's Experience Dashboard — International Childbirth Initiative"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import base64
from pathlib import Path
from datetime import datetime

# ── Config ──
ASSET_UID = "aT3kXmLeYLtUC6zVAV5abW"
BASE_URL  = "https://eu.kobotoolbox.org"
try:
    KOBO_TOKEN = st.secrets["KOBO_TOKEN"]
except Exception:
    KOBO_TOKEN = ""
    st.error("⚠️ KOBO_TOKEN not found in Streamlit Secrets.")
    st.stop()

# ════════════════════════════════════════
# BILINGUAL LABELS
# ════════════════════════════════════════
L = {
# UI
"title":        {"EN":"Women's Experience Dashboard","FR":"Tableau de bord — Expérience des femmes"},
"caption":      {"EN":"International Childbirth Initiative · 12 Steps to Safe and Respectful MotherBaby-Family Maternity Care",
                 "FR":"Initiative Internationale pour la Naissance · 12 étapes pour des soins de maternité sûrs et respectueux"},
"filters":      {"EN":"Filters","FR":"Filtres"},
"date_range":   {"EN":"Date range","FR":"Période"},
"birth_method_f":{"EN":"Birth method","FR":"Mode d'accouchement"},
"high_risk_f":  {"EN":"High-risk pregnancy","FR":"Grossesse à risque"},
"filtered":     {"EN":"Filtered responses","FR":"Réponses filtrées"},
"refresh":      {"EN":"🔄 Refresh data","FR":"🔄 Actualiser"},
"responses":    {"EN":"Responses","FR":"Réponses"},
"pct":          {"EN":"% of respondents","FR":"% des répondantes"},
"download":     {"EN":"⬇️ Download CSV","FR":"⬇️ Télécharger CSV"},
"raw_data":     {"EN":"📋 View raw data","FR":"📋 Voir les données brutes"},
"positive":     {"EN":"Positive","FR":"Positif"},
"negative":     {"EN":"Negative","FR":"Négatif"},
"all":          {"EN":"All","FR":"Tous"},
# Sections
"s_overview":   {"EN":"Overview","FR":"Vue d'ensemble"},
"s_timeline":   {"EN":"Responses Over Time","FR":"Réponses dans le temps"},
"s_trends":     {"EN":"Key Indicators Over Time","FR":"Indicateurs clés dans le temps"},
"s_profile":    {"EN":"Respondent Profile","FR":"Profil des répondantes"},
"s_likert":     {"EN":"Quality of Care — Likert Scales","FR":"Qualité des soins — Échelles de Likert"},
"s_autonomy":   {"EN":"Autonomy & Consent","FR":"Autonomie et consentement"},
"s_clinical":   {"EN":"Clinical Practices","FR":"Pratiques cliniques"},
"s_satisfaction":{"EN":"Satisfaction — Expectations vs. Reality","FR":"Satisfaction — Attentes vs. Réalité"},
"s_emotions":   {"EN":"How Women Felt at the Time of Delivery","FR":"Ressenti des femmes au moment de l'accouchement"},
"s_discharge":  {"EN":"Information Provided Before Discharge","FR":"Informations données avant la sortie"},
"s_mistreat":   {"EN":"Mistreatment & Respect","FR":"Maltraitance et respect"},
# KPIs
"kpi_total":    {"EN":"Total responses","FR":"Total réponses"},
"kpi_positive": {"EN":"Positive care rating","FR":"Évaluation positive"},
"kpi_skin":     {"EN":"Immediate skin-to-skin","FR":"Peau à peau immédiat"},
"kpi_exam":     {"EN":"Vaginal exams w/o consent","FR":"Examens vaginaux sans consentement"},
"kpi_epi":      {"EN":"Episiotomies w/o consent","FR":"Épisiotomies sans consentement"},
# Profile
"p_method":     {"EN":"Birth method","FR":"Mode d'accouchement"},
"p_age":        {"EN":"Age group","FR":"Groupe d'âge"},
"p_education":  {"EN":"Education level","FR":"Niveau d'éducation"},
"p_weeks":      {"EN":"Gestational weeks at birth","FR":"Semaines de gestation"},
"p_parity":     {"EN":"Number of previous deliveries","FR":"Nombre d'accouchements précédents"},
# Timeline
"grp_month":    {"EN":"Month","FR":"Mois"},
"grp_week":     {"EN":"Week","FR":"Semaine"},
"grp_day":      {"EN":"Day","FR":"Jour"},
"grp_by":       {"EN":"Group by","FR":"Regrouper par"},
# Trends
"tr_positive":  {"EN":"% Positive care rating","FR":"% Évaluation positive"},
"tr_skin":      {"EN":"% Immediate skin-to-skin","FR":"% Peau à peau immédiat"},
"tr_exam":      {"EN":"% Vaginal exams w/o consent","FR":"% Examens vaginaux s.c."},
# Autonomy
"a_decisions":  {"EN":"Included in care decisions","FR":"Incluse dans les décisions de soins"},
"a_exam":       {"EN":"Vaginal exam without consent","FR":"Examen vaginal sans consentement"},
"a_epi":        {"EN":"Episiotomy","FR":"Épisiotomie"},
"a_treat":      {"EN":"Treatments not wanted / not agreed to","FR":"Soins non souhaités / sans accord"},
# Clinical
"c_skin":       {"EN":"Skin-to-skin contact","FR":"Peau à peau"},
"c_bf":         {"EN":"Breastfeeding support","FR":"Soutien à l'allaitement"},
"c_induce":     {"EN":"Labour induction","FR":"Déclenchement du travail"},
"c_pharma":     {"EN":"Pain relief received","FR":"Analgésie reçue"},
"c_comfort":    {"EN":"Non-pharmacological comfort measures","FR":"Mesures de confort non-pharmacologiques"},
"c_rooming":    {"EN":"Rooming-in (baby with mother)","FR":"Cohabitation mère-bébé"},
# Satisfaction
"sat_expect":   {"EN":"Before I came here, I expected care to be:","FR":"Avant de venir ici, je m'attendais à des soins :"},
"sat_actual":   {"EN":"Now, I feel that my care was:","FR":"Maintenant, j'estime que mes soins étaient :"},
# Emotions note
"emo_note":     {"EN":"Women could select multiple emotions — bars show % of respondents who chose each one.",
                 "FR":"Les femmes pouvaient choisir plusieurs émotions — les barres montrent le % de répondantes ayant choisi chacune."},
# Mistreatment
"m_verbal":     {"EN":"Verbal abuse","FR":"Violence verbale"},
"m_phys":       {"EN":"Physical abuse","FR":"Violence physique"},
"m_payment":    {"EN":"Asked for payment / incentive","FR":"Paiement demandé"},
}
def t(k, lang): return L.get(k,{}).get(lang, k)

# ════════════════════════════════════════
# VALUE MAPS
# ════════════════════════════════════════
METHOD_MAP = {
    "EN":{1:"Vaginal",2:"Assisted vaginal",3:"Elective caesarean",4:"Emergency caesarean",5:"VBAC",0:"Don't know"},
    "FR":{1:"Vaginal",2:"Vaginal assisté",3:"Césarienne élective",4:"Césarienne d'urgence",5:"AVAC",0:"Ne sait pas"}
}
EDUCATION_MAP = {
    "EN":{1:"None",2:"Primary",3:"Secondary",4:"Higher"},
    "FR":{1:"Aucune",2:"Primaire",3:"Secondaire",4:"Supérieur"}
}
RISK_MAP = {
    "EN":{1:"Yes",2:"No",0:"Don't know"},
    "FR":{1:"Oui",2:"Non",0:"Ne sait pas"}
}
LIKERT5_MAP = {
    "EN":{5:"Always",4:"Most of the time",3:"Sometimes",2:"Rarely",1:"Never",0:"Don't know/N.A."},
    "FR":{5:"Toujours",4:"La plupart du temps",3:"Parfois",2:"Rarement",1:"Jamais",0:"Ne sait pas/N.A."}
}
QUALITY_MAP = {
    "EN":{5:"Very good",4:"Good",3:"Neutral",2:"Poor",1:"Very bad",0:"Don't know"},
    "FR":{5:"Très bien",4:"Bien",3:"Neutre",2:"Mauvais",1:"Très mauvais",0:"Ne sait pas"}
}
QUALITY_ORDER = {
    "EN":["Very bad","Poor","Neutral","Good","Very good","Don't know"],
    "FR":["Très mauvais","Mauvais","Neutre","Bien","Très bien","Ne sait pas"]
}
DECISIONS_MAP = {
    "EN":{1:"Yes — included + enough info",2:"Yes — included but not enough info",
          3:"Sometimes included",4:"No — not included",0:"Don't know"},
    "FR":{1:"Oui — incluse + info suffisante",2:"Oui — incluse mais info insuffisante",
          3:"Parfois incluse",4:"Non — pas incluse",0:"Ne sait pas"}
}
EPI_MAP = {
    "EN":{1:"Yes, with consent",2:"Yes, without consent",3:"No — I declined",4:"No — not recommended"},
    "FR":{1:"Oui, avec consentement",2:"Oui, sans consentement",3:"Non — j'ai refusé",4:"Non — non recommandée"}
}
EXAM_MAP = {
    "EN":{1:"Never w/o consent",2:"Rarely w/o consent",3:"Sometimes w/o consent",
          4:"Frequently w/o consent",5:"Always w/o consent"},
    "FR":{1:"Jamais s.c.",2:"Rarement s.c.",3:"Parfois s.c.",4:"Fréquemment s.c.",5:"Toujours s.c."}
}
TREAT_MAP  = {"EN":{2:"Yes",1:"No",0:"Don't know"}, "FR":{2:"Oui",1:"Non",0:"Ne sait pas"}}
BF_MAP = {
    "EN":{1:"Did not breastfeed",2:"Did not need help",3:"Needed help — not received",
          4:"Helped but not enough",5:"Received help needed",0:"Don't know"},
    "FR":{1:"N'a pas allaité",2:"Pas besoin d'aide",3:"Besoin d'aide — non reçue",
          4:"Aidée mais insuffisamment",5:"A reçu l'aide nécessaire",0:"Ne sait pas"}
}
SKIN_MAP = {
    "EN":{1:"Yes — immediate",2:"Yes — not immediate",3:"Yes — <1 hour",4:"No",5:"Don't know",9:"Neonatal unit"},
    "FR":{1:"Oui — immédiat",2:"Oui — pas immédiat",3:"Oui — <1 heure",4:"Non",5:"Ne sait pas",9:"Unité néonatale"}
}
INDUCE_MAP = {"EN":{1:"No",2:"Yes",0:"Don't know"}, "FR":{1:"Non",2:"Oui",0:"Ne sait pas"}}
PHARMA_MAP = {
    "EN":{1:"No analgesia",2:"Non-pharmacological only",3:"Pharmacological offered, declined",
          4:"Pharmacological received",0:"Don't know"},
    "FR":{1:"Pas d'analgésie",2:"Non-pharmacologique seulement",3:"Pharmacologique proposée, refusée",
          4:"Pharmacologique reçue",0:"Ne sait pas"}
}
COMFORT_MAP = {
    "EN":{1:"Yes",2:"No — not offered",3:"No — declined",0:"Don't know"},
    "FR":{1:"Oui",2:"Non — non proposée",3:"Non — refusée",0:"Ne sait pas"}
}
ROOMING_MAP = {
    "EN":{4:"Yes — always",1:"Sometimes",2:"No",0:"Don't know"},
    "FR":{4:"Oui — toujours",1:"Parfois",2:"Non",0:"Ne sait pas"}
}
VERBAL_MAP = {"EN":{1:"No",2:"Yes",5:"Don't know",0:"N/A"}, "FR":{1:"Non",2:"Oui",5:"Ne sait pas",0:"N/A"}}
PHYS_MAP   = {"EN":{1:"No",2:"Yes",3:"Don't know",0:"N/A"}, "FR":{1:"Non",2:"Oui",3:"Ne sait pas",0:"N/A"}}
PAYMENT_MAP = {
    "EN":{1:"Yes — paid",2:"Asked but not paid",3:"Not asked",0:"Don't know"},
    "FR":{1:"Oui — a payé",2:"Demandé mais pas payé",3:"Non demandé",0:"Ne sait pas"}
}
LIKERT_QUESTIONS = {
    "EN":{"introduction":"Staff introduced themselves","spoke":"Staff spoke clearly",
          "communication":"Open to questions","privacy":"Privacy protected","respect":"Treated respectfully",
          "values":"Beliefs & choices respected","positive":"Providers encouraged empowerment",
          "morale":"Staff had what they needed","coop":"Staff worked in a coordinated way"},
    "FR":{"introduction":"Le personnel s'est présenté","spoke":"Le personnel a parlé clairement",
          "communication":"Ouvert aux questions","privacy":"Vie privée protégée","respect":"Traitée avec respect",
          "values":"Croyances et choix respectés","positive":"Prestataires encourageants",
          "morale":"Personnel bien équipé","coop":"Travail coordonné"}
}
EMOTION_LABELS = {
    "EN":{1:"Capable",2:"Incapable",3:"Anxious",4:"Supported",5:"Exhausted",6:"Active",
          7:"Relaxed",8:"Passive",9:"Responsible",10:"Dependent",11:"Secure",12:"Excluded"},
    "FR":{1:"Capable",2:"Incapable",3:"Anxieuse",4:"Soutenue",5:"Épuisée",6:"Active",
          7:"Détendue",8:"Passive",9:"Responsable",10:"Dépendante",11:"En sécurité",12:"Exclue"}
}
INFO_LABELS = {
    "EN":{1:"Caring for my new baby",2:"Family planning advice",
          3:"Warning signs requiring consultation",4:"Where to go for follow-up"},
    "FR":{1:"Soins pour mon nouveau-né",2:"Planification familiale",
          3:"Signes d'alarme nécessitant une consultation",4:"Où aller pour le suivi"}
}
POSITIVE_EMOTIONS = {
    "EN":{"Capable","Supported","Active","Relaxed","Responsible","Secure"},
    "FR":{"Capable","Soutenue","Active","Détendue","Responsable","En sécurité"}
}
LIKERT_COLORS  = ["#1a7f5a","#57bb8a","#f6c344","#f4845f","#d63031","#cccccc"]
QUALITY_COLORS = ["#d63031","#f4845f","#f6c344","#57bb8a","#1a7f5a","#cccccc"]

def get_logo_b64(): return "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8XHoPgCtg4TB4vDQdlj6kcX1n7bvd7yepVm0bTNTpLCn7OL8G/LkZxjIwsS3UOQa2fLOhx8R6itX6vPsc8939Hr7VOtaGtDR3BfqK4UqXs1jLb6v+fY2hERbQEREAREQBERAEREAREQBERAEREBjZShTymNs43IV47NO1E6GeF43bIxw2c0jxBBIXzhsZj8Niq2KxVOGlRqxiOCCFvKyNo7gB4BZaIAiIgCIiA/HNDmlrhuCNio7TeBw2m8UzFYHG1sdRjc5zIK7A1gLiS47eZJJUkiAIiIAiIgCIiAKMx+n8Lj81kM1SxlaDJZLk9NtMZtJPyDZnMfHYHYKTRAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQHxPFFPC+GaNskbxyuY4bhw8iFDfwR01zc3zNV3/kqcRaqlClVeZxT8VkYMClhcRScH1MZUhcPymQtB+3bdZ6IsoU4wWIrACIizAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAf/2Q=="

# ════════════════════════════════════════
# DATA LOADING & PREP
# ════════════════════════════════════════
@st.cache_data(ttl=300)
def load_data():
    headers = {"Authorization": f"Token {KOBO_TOKEN}"}
    url = f"{BASE_URL}/api/v2/assets/{ASSET_UID}/data/?format=json&limit=3000"
    results = []
    while url:
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            st.error(f"Kobo API error: {r.status_code}")
            return pd.DataFrame()
        data = r.json()
        results.extend(data.get("results", []))
        url = data.get("next")
    return pd.DataFrame(results)

def to_int(s): return pd.to_numeric(s, errors="coerce")
def first_token_int(s): return s.astype(str).str.split().str[0].pipe(pd.to_numeric, errors="coerce")

def parse_multiselect_counts(series, valid_keys):
    counts = {k: 0 for k in valid_keys}
    for val in series.dropna():
        for token in str(val).split():
            try:
                k = int(token)
                if k in counts: counts[k] += 1
            except ValueError: pass
    return counts

def prep(df, lang):
    df = df.copy()
    df["_submission_time"] = pd.to_datetime(df["_submission_time"], errors="coerce")

    simple_maps = [
        ("method", METHOD_MAP[lang]), ("education", EDUCATION_MAP[lang]),
        ("risk", RISK_MAP[lang]), ("satisfaction", QUALITY_MAP[lang]),
        ("expect", QUALITY_MAP[lang]), ("decisions", DECISIONS_MAP[lang]),
        ("epi", EPI_MAP[lang]), ("exam", EXAM_MAP[lang]),
        ("bf", BF_MAP[lang]), ("induce", INDUCE_MAP[lang]), ("treat", TREAT_MAP[lang]),
        ("pharma", PHARMA_MAP[lang]), ("comfort", COMFORT_MAP[lang]),
        ("rooming", ROOMING_MAP[lang]), ("verbal", VERBAL_MAP[lang]),
        ("phys", PHYS_MAP[lang]), ("payment", PAYMENT_MAP[lang]),
    ]
    for col, mapping in simple_maps:
        if col in df.columns:
            df[col] = to_int(df[col])
            df[col + "_label"] = df[col].map(mapping).fillna("?")

    for col in LIKERT_QUESTIONS[lang]:
        if col in df.columns:
            df[col] = to_int(df[col])
            df[col + "_label"] = df[col].map(LIKERT5_MAP[lang]).fillna("?")

    if "skin" in df.columns:
        df["skin_int"] = first_token_int(df["skin"])
        df["skin_label"] = df["skin_int"].map(SKIN_MAP[lang]).fillna("?")

    if "age" in df.columns:
        df["age"] = to_int(df["age"])
        df["age_group"] = pd.cut(df["age"], bins=[0,19,24,29,34,39,99],
                                  labels=["<20","20–24","25–29","30–34","35–39","40+"])

    if "weeks" in df.columns:
        df["weeks_clean"] = to_int(df["weeks"])
        df.loc[~df["weeks_clean"].between(24, 45), "weeks_clean"] = pd.NA

    if "no_deliveries" in df.columns:
        df["no_deliveries"] = to_int(df["no_deliveries"])
        df.loc[df["no_deliveries"] > 10, "no_deliveries"] = pd.NA

    return df

# ════════════════════════════════════════
# PAGE SETUP
# ════════════════════════════════════════
st.set_page_config(page_title="ICI Dashboard", page_icon="🤱", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600&family=DM+Serif+Display&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}
h1,h2,h3{font-family:'DM Serif Display',serif;}
.metric-box{background:#f8f4f0;border-radius:12px;padding:20px;text-align:center;}
.metric-num{font-size:2.2rem;font-weight:700;color:#1a7f5a;}
.metric-label{font-size:0.85rem;color:#666;margin-top:4px;}
.section-title{font-family:'DM Serif Display',serif;font-size:1.3rem;color:#2d2d2d;
               border-left:4px solid #1a7f5a;padding-left:12px;margin:28px 0 12px 0;}
</style>""", unsafe_allow_html=True)

logo_b64 = get_logo_b64()
col_logo, col_title, col_lang = st.columns([1, 5, 1])
if logo_b64:
    col_logo.markdown(f'<img src="data:image/png;base64,{logo_b64}" style="width:100%;max-width:160px;margin-top:8px">', unsafe_allow_html=True)
lang = col_lang.radio("🌐", ["EN","FR"], horizontal=True, label_visibility="collapsed")
col_title.title(t("title", lang))
col_title.caption(t("caption", lang))
st.divider()

# ── Load ──
with st.spinner("Loading data..." if lang=="EN" else "Chargement..."):
    raw = load_data()
if raw.empty:
    st.warning("No data." if lang=="EN" else "Aucune donnée.")
    st.stop()
df = prep(raw, lang)

# ── Sidebar ──
if logo_b64:
    st.sidebar.markdown(f'<img src="data:image/png;base64,{logo_b64}" style="width:180px">', unsafe_allow_html=True)
st.sidebar.header(t("filters", lang))

if "_submission_time" in df.columns and df["_submission_time"].notna().any():
    mn, mx = df["_submission_time"].min().date(), df["_submission_time"].max().date()
    dr = st.sidebar.date_input(t("date_range", lang), value=(mn, mx), min_value=mn, max_value=mx)
    if len(dr)==2:
        df = df[(df["_submission_time"].dt.date >= dr[0]) & (df["_submission_time"].dt.date <= dr[1])]

if "method_label" in df.columns:
    opts = [t("all",lang)] + sorted(df["method_label"].dropna().unique().tolist())
    sel = st.sidebar.selectbox(t("birth_method_f", lang), opts)
    if sel != t("all",lang): df = df[df["method_label"]==sel]

if "risk_label" in df.columns:
    opts = [t("all",lang)] + sorted(df["risk_label"].dropna().unique().tolist())
    sel = st.sidebar.selectbox(t("high_risk_f", lang), opts)
    if sel != t("all",lang): df = df[df["risk_label"]==sel]

st.sidebar.metric(t("filtered",lang), len(df))
if st.sidebar.button(t("refresh",lang)):
    st.cache_data.clear(); st.rerun()

# ════════════════════════════════════════
# PANEL 1 — KPIs
# ════════════════════════════════════════
st.markdown(f'<div class="section-title">{t("s_overview",lang)}</div>', unsafe_allow_html=True)
sat_good  = (df["satisfaction"].isin([4,5])).sum()/len(df)*100 if "satisfaction" in df.columns else 0
skin_imm  = (df["skin_int"]==1).sum()/len(df)*100 if "skin_int" in df.columns else 0
exam_nc   = (df["exam"].isin([2,3,4,5])).sum() if "exam" in df.columns else 0
epi_nc    = (df["epi"]==2).sum() if "epi" in df.columns else 0
for col, num, lbl in [
    (st.columns(5)[0], len(df),            t("kpi_total",lang)),
    (st.columns(5)[1], f"{sat_good:.0f}%", t("kpi_positive",lang)),
    (st.columns(5)[2], f"{skin_imm:.0f}%", t("kpi_skin",lang)),
    (st.columns(5)[3], exam_nc,            t("kpi_exam",lang)),
    (st.columns(5)[4], epi_nc,             t("kpi_epi",lang)),
]:
    pass
c1,c2,c3,c4,c5 = st.columns(5)
for col, num, lbl in [(c1,len(df),t("kpi_total",lang)),(c2,f"{sat_good:.0f}%",t("kpi_positive",lang)),
                      (c3,f"{skin_imm:.0f}%",t("kpi_skin",lang)),(c4,exam_nc,t("kpi_exam",lang)),(c5,epi_nc,t("kpi_epi",lang))]:
    col.markdown(f'<div class="metric-box"><div class="metric-num">{num}</div><div class="metric-label">{lbl}</div></div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ════════════════════════════════════════
# PANEL 2 — Timeline
# ════════════════════════════════════════
st.markdown(f'<div class="section-title">{t("s_timeline",lang)}</div>', unsafe_allow_html=True)
if "_submission_time" in df.columns and df["_submission_time"].notna().any():
    freq_opts = [t("grp_month",lang), t("grp_week",lang), t("grp_day",lang)]
    freq = st.radio(t("grp_by",lang), freq_opts, horizontal=True)
    fmap = {t("grp_day",lang):"D", t("grp_week",lang):"W", t("grp_month",lang):"ME"}
    ts = df.set_index("_submission_time").resample(fmap[freq]).size().reset_index(name="n")
    fig = px.area(ts, x="_submission_time", y="n",
                  labels={"_submission_time":"","n":t("responses",lang)},
                  color_discrete_sequence=["#1a7f5a"])
    fig.update_traces(line_width=2, fillcolor="rgba(26,127,90,0.15)")
    fig.update_layout(margin=dict(t=10,b=10), height=220, plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════
# PANEL 3 — Key indicators over time
# ════════════════════════════════════════
st.markdown(f'<div class="section-title">{t("s_trends",lang)}</div>', unsafe_allow_html=True)
if "_submission_time" in df.columns and df["_submission_time"].notna().any():
    dft = df.copy()
    dft["month"] = dft["_submission_time"].dt.to_period("M").dt.to_timestamp()
    monthly = dft.groupby("month").agg(
        n=("_submission_time","count"),
        sat_pos=("satisfaction", lambda x: (pd.to_numeric(x,errors="coerce").isin([4,5])).sum()),
        skin_imm=("skin_int", lambda x: (pd.to_numeric(x,errors="coerce")==1).sum()),
        exam_nc=("exam", lambda x: (pd.to_numeric(x,errors="coerce").isin([2,3,4,5])).sum()),
    ).reset_index()
    monthly = monthly[monthly["n"] >= 5]
    monthly["pct_sat"]  = monthly["sat_pos"]/monthly["n"]*100
    monthly["pct_skin"] = monthly["skin_imm"]/monthly["n"]*100
    monthly["pct_exam"] = monthly["exam_nc"]/monthly["n"]*100

    tr_tab1, tr_tab2, tr_tab3 = st.tabs([t("tr_positive",lang), t("tr_skin",lang), t("tr_exam",lang)])
    for tab, ycol, label, color in [
        (tr_tab1, "pct_sat",  t("tr_positive",lang), "#1a7f5a"),
        (tr_tab2, "pct_skin", t("tr_skin",lang),     "#2563eb"),
        (tr_tab3, "pct_exam", t("tr_exam",lang),     "#d63031"),
    ]:
        with tab:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=monthly["month"], y=monthly[ycol],
                                     mode="lines+markers", line=dict(color=color, width=2),
                                     marker=dict(size=5)))
            fig.update_layout(height=220, margin=dict(t=10,b=10),
                              yaxis_title="%", plot_bgcolor="white", paper_bgcolor="white",
                              yaxis=dict(range=[0,100]))
            st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════
# PANEL 4 — Respondent Profile
# ════════════════════════════════════════
st.markdown(f'<div class="section-title">{t("s_profile",lang)}</div>', unsafe_allow_html=True)
c1,c2,c3 = st.columns(3)

if "method_label" in df.columns:
    mc = df["method_label"].value_counts().reset_index(); mc.columns=["m","n"]
    fig = px.pie(mc, names="m", values="n", hole=0.45, color_discrete_sequence=px.colors.qualitative.Safe)
    fig.update_layout(title=t("p_method",lang), margin=dict(t=40,b=10), height=280)
    c1.plotly_chart(fig, use_container_width=True)

if "age_group" in df.columns:
    ac = df["age_group"].value_counts().sort_index().reset_index(); ac.columns=["f","n"]
    fig = px.bar(ac, x="f", y="n", color_discrete_sequence=["#2563eb"],
                 labels={"f":t("p_age",lang),"n":""})
    fig.update_layout(title=t("p_age",lang), margin=dict(t=40,b=10), height=280, plot_bgcolor="white")
    c2.plotly_chart(fig, use_container_width=True)

if "education_label" in df.columns:
    ec = df["education_label"].value_counts().reset_index(); ec.columns=["e","n"]
    fig = px.bar(ec, x="n", y="e", orientation="h", color_discrete_sequence=["#7c3aed"],
                 labels={"e":"","n":""})
    fig.update_layout(title=t("p_education",lang), margin=dict(t=40,b=10), height=280, plot_bgcolor="white")
    c3.plotly_chart(fig, use_container_width=True)

c1,c2 = st.columns(2)
if "weeks_clean" in df.columns:
    wk = df["weeks_clean"].dropna()
    fig = px.histogram(wk, nbins=16, color_discrete_sequence=["#f59e0b"],
                       labels={"value":t("p_weeks",lang),"count":""})
    fig.update_layout(title=t("p_weeks",lang), showlegend=False,
                      margin=dict(t=40,b=10), height=240, plot_bgcolor="white",
                      xaxis=dict(range=[28,46], dtick=1))
    c1.plotly_chart(fig, use_container_width=True)

if "no_deliveries" in df.columns:
    nd = df["no_deliveries"].dropna().value_counts().sort_index().reset_index()
    nd.columns=["n","count"]
    nd["n"] = nd["n"].astype(int).astype(str)
    fig = px.bar(nd, x="n", y="count", color_discrete_sequence=["#0891b2"],
                 labels={"n":t("p_parity",lang),"count":""})
    fig.update_layout(title=t("p_parity",lang), margin=dict(t=40,b=10), height=240, plot_bgcolor="white")
    c2.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════
# PANEL 5 — Likert
# ════════════════════════════════════════
st.markdown(f'<div class="section-title">{t("s_likert",lang)}</div>', unsafe_allow_html=True)
likert_order = list(LIKERT5_MAP[lang].values())
rows = []
for col, label in LIKERT_QUESTIONS[lang].items():
    lbl = col+"_label"
    if lbl in df.columns:
        vc = df[lbl].value_counts(normalize=True).mul(100).round(1)
        for cat in likert_order:
            rows.append({"Dimension":label,"Response":cat,"Pct":vc.get(cat,0)})
if rows:
    ldf = pd.DataFrame(rows)
    fig = px.bar(ldf, x="Pct", y="Dimension", color="Response", orientation="h",
                 barmode="stack", color_discrete_sequence=LIKERT_COLORS,
                 category_orders={"Response":likert_order}, labels={"Pct":"%","Dimension":""})
    fig.update_layout(legend=dict(orientation="h",y=-0.18,x=0),
                      margin=dict(t=10,b=90), height=440, plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════
# PANEL 6 — Autonomy & Consent
# ════════════════════════════════════════
st.markdown(f'<div class="section-title">{t("s_autonomy",lang)}</div>', unsafe_allow_html=True)
c1,c2 = st.columns(2)
if "decisions_label" in df.columns:
    dc = df["decisions_label"].value_counts().reset_index(); dc.columns=["r","n"]
    fig = px.bar(dc, x="n", y="r", orientation="h", color_discrete_sequence=["#1a7f5a"],
                 labels={"r":"","n":t("responses",lang)})
    fig.update_layout(title=t("a_decisions",lang), plot_bgcolor="white", margin=dict(t=40,b=10), height=250)
    c1.plotly_chart(fig, use_container_width=True)
if "exam_label" in df.columns:
    ec = df["exam_label"].value_counts().reset_index(); ec.columns=["r","n"]
    fig = px.bar(ec, x="n", y="r", orientation="h", color_discrete_sequence=LIKERT_COLORS,
                 labels={"r":"","n":""})
    fig.update_layout(title=t("a_exam",lang), showlegend=False, plot_bgcolor="white",
                      margin=dict(t=40,b=10), height=250)
    c2.plotly_chart(fig, use_container_width=True)

c1,c2 = st.columns(2)
if "epi_label" in df.columns:
    ep = df["epi_label"].value_counts().reset_index(); ep.columns=["r","n"]
    fig = px.pie(ep, names="r", values="n", hole=0.4,
                 color_discrete_sequence=["#1a7f5a","#d63031","#f6c344","#57bb8a"])
    fig.update_layout(title=t("a_epi",lang), margin=dict(t=40,b=10), height=280)
    c1.plotly_chart(fig, use_container_width=True)
if "treat_label" in df.columns:
    tc = df["treat_label"].value_counts().reset_index(); tc.columns=["r","n"]
    fig = px.pie(tc, names="r", values="n", hole=0.4,
                 color_discrete_sequence=["#1a7f5a","#d63031","#cccccc"])
    fig.update_layout(title=t("a_treat",lang), margin=dict(t=40,b=10), height=280)
    c2.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════
# PANEL 7 — Clinical Practices
# ════════════════════════════════════════
st.markdown(f'<div class="section-title">{t("s_clinical",lang)}</div>', unsafe_allow_html=True)
c1,c2,c3 = st.columns(3)
if "skin_label" in df.columns:
    sk = df["skin_label"].value_counts().reset_index(); sk.columns=["r","n"]
    fig = px.pie(sk, names="r", values="n", hole=0.4,
                 color_discrete_sequence=["#1a7f5a","#57bb8a","#f6c344","#d63031","#cccccc"])
    fig.update_layout(title=t("c_skin",lang), margin=dict(t=40,b=10), height=280)
    c1.plotly_chart(fig, use_container_width=True)
if "bf_label" in df.columns:
    bf = df["bf_label"].value_counts().reset_index(); bf.columns=["r","n"]
    fig = px.bar(bf, x="n", y="r", orientation="h", color_discrete_sequence=["#2563eb"],
                 labels={"r":"","n":""})
    fig.update_layout(title=t("c_bf",lang), plot_bgcolor="white", margin=dict(t=40,b=10), height=280)
    c2.plotly_chart(fig, use_container_width=True)
if "induce_label" in df.columns:
    ind = df["induce_label"].value_counts().reset_index(); ind.columns=["r","n"]
    fig = px.pie(ind, names="r", values="n", hole=0.4,
                 color_discrete_sequence=["#1a7f5a","#f59e0b","#cccccc"])
    fig.update_layout(title=t("c_induce",lang), margin=dict(t=40,b=10), height=280)
    c3.plotly_chart(fig, use_container_width=True)

c1,c2,c3 = st.columns(3)
if "pharma_label" in df.columns:
    ph = df["pharma_label"].value_counts().reset_index(); ph.columns=["r","n"]
    fig = px.bar(ph, x="n", y="r", orientation="h", color_discrete_sequence=["#0891b2"],
                 labels={"r":"","n":""})
    fig.update_layout(title=t("c_pharma",lang), plot_bgcolor="white", margin=dict(t=40,b=10), height=250)
    c1.plotly_chart(fig, use_container_width=True)
if "comfort_label" in df.columns:
    co = df["comfort_label"].value_counts().reset_index(); co.columns=["r","n"]
    fig = px.pie(co, names="r", values="n", hole=0.4,
                 color_discrete_sequence=["#1a7f5a","#f59e0b","#d63031","#cccccc"])
    fig.update_layout(title=t("c_comfort",lang), margin=dict(t=40,b=10), height=250)
    c2.plotly_chart(fig, use_container_width=True)
if "rooming_label" in df.columns:
    ro = df["rooming_label"].value_counts().reset_index(); ro.columns=["r","n"]
    fig = px.pie(ro, names="r", values="n", hole=0.4,
                 color_discrete_sequence=["#1a7f5a","#f59e0b","#d63031","#cccccc"])
    fig.update_layout(title=t("c_rooming",lang), margin=dict(t=40,b=10), height=250)
    c3.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════
# PANEL 8 — Satisfaction
# ════════════════════════════════════════
st.markdown(f'<div class="section-title">{t("s_satisfaction",lang)}</div>', unsafe_allow_html=True)
if "expect_label" in df.columns and "satisfaction_label" in df.columns:
    c1,c2 = st.columns(2)
    q_order = QUALITY_ORDER[lang]
    for col, field, title in [(c1,"expect_label",t("sat_expect",lang)),(c2,"satisfaction_label",t("sat_actual",lang))]:
        vc = df[field].value_counts().reindex(q_order, fill_value=0).reset_index()
        vc.columns=["r","n"]
        fig = px.bar(vc, x="r", y="n", color="r", color_discrete_sequence=QUALITY_COLORS,
                     labels={"r":"","n":t("responses",lang)}, category_orders={"r":q_order})
        fig.update_layout(title=title, showlegend=False, plot_bgcolor="white",
                          margin=dict(t=60,b=10), height=300)
        col.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════
# PANEL 9 — Emotions
# ════════════════════════════════════════
st.markdown(f'<div class="section-title">{t("s_emotions",lang)}</div>', unsafe_allow_html=True)
st.caption(t("emo_note", lang))
if "emotion" in df.columns:
    emo_labels = EMOTION_LABELS[lang]
    pos = POSITIVE_EMOTIONS[lang]
    counts = parse_multiselect_counts(df["emotion"], list(emo_labels.keys()))
    rows = [{"Emotion":lbl, "n":counts[k], "Pct":round(counts[k]/len(df)*100,1),
             "Type": t("positive",lang) if lbl in pos else t("negative",lang)}
            for k,lbl in emo_labels.items()]
    edf = pd.DataFrame(rows).sort_values("Pct", ascending=True)
    fig = px.bar(edf, x="Pct", y="Emotion", color="Type", orientation="h",
                 color_discrete_map={t("positive",lang):"#1a7f5a", t("negative",lang):"#d63031"},
                 labels={"Pct":t("pct",lang),"Emotion":""})
    fig.update_layout(margin=dict(t=10,b=10), height=380, plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════
# PANEL 10 — Discharge Info
# ════════════════════════════════════════
st.markdown(f'<div class="section-title">{t("s_discharge",lang)}</div>', unsafe_allow_html=True)
if "info" in df.columns:
    info_labels = INFO_LABELS[lang]
    counts = parse_multiselect_counts(df["info"], list(info_labels.keys()))
    rows = [{"Topic":lbl,"Pct":round(counts[k]/len(df)*100,1)} for k,lbl in info_labels.items()]
    idf = pd.DataFrame(rows).sort_values("Pct")
    fig = px.bar(idf, x="Pct", y="Topic", orientation="h", color_discrete_sequence=["#7c3aed"],
                 labels={"Pct":t("pct",lang),"Topic":""})
    fig.update_layout(margin=dict(t=10,b=10), height=220, plot_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════
# PANEL 11 — Mistreatment
# ════════════════════════════════════════
st.markdown(f'<div class="section-title">{t("s_mistreat",lang)}</div>', unsafe_allow_html=True)
c1,c2,c3 = st.columns(3)
for col, field, title in [(c1,"verbal_label",t("m_verbal",lang)),
                           (c2,"phys_label",t("m_phys",lang)),
                           (c3,"payment_label",t("m_payment",lang))]:
    if field in df.columns:
        vc = df[field].value_counts().reset_index(); vc.columns=["r","n"]
        fig = px.pie(vc, names="r", values="n", hole=0.4,
                     color_discrete_sequence=["#1a7f5a","#d63031","#f6c344","#cccccc"])
        fig.update_layout(title=title, margin=dict(t=40,b=10), height=260)
        col.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════
# PANEL 12 — Raw data
# ════════════════════════════════════════
with st.expander(t("raw_data",lang)):
    hide = [c for c in df.columns if c.startswith("_") or c in ("meta/rootUuid",)]
    show = [c for c in df.columns if c not in hide]
    st.dataframe(df[show], use_container_width=True, height=400)
    csv = df[show].to_csv(index=False).encode("utf-8")
    st.download_button(t("download",lang), csv,
                       f"ici_data_{datetime.today().strftime('%Y%m%d')}.csv", "text/csv")
