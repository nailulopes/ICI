"""ICI Dashboard — Shared config, maps, loaders."""
import streamlit as st
import pandas as pd
import numpy as np
import requests
from pathlib import Path
from datetime import datetime

# ── Facilities ────────────────────────────────────────────────────────────────
FACILITIES = {
    "facility_a": {
        "display_name": "Canada",
        "country":      "Canada",
        "continent":    "North America",
        "women_uid":    "aT3kXmLeYLtUC6zVAV5abW",
        "companion_uid": None,
    },
    "facility_b": {
        "display_name": "Clínica de la Mujer — Cartagena, Colombia",
        "country":      "Colombia",
        "continent":    "South America",
        "women_uid":    "a3KYjwLBStqvGGH4B62e7p",
        "companion_uid": "aFd2ux4ggB3Kcd2Z4JTZbA",
    },
}

BASE_URL  = "https://eu.kobotoolbox.org"
LOGO_PATH = Path(__file__).resolve().parent / "ici_dashboard_assets" / "ici_logo.png"

try:
    KOBO_TOKEN = st.secrets["KOBO_TOKEN"]
except Exception:
    KOBO_TOKEN = ""

# ── Role helpers ──────────────────────────────────────────────────────────────
def get_role():
    return st.session_state.get("role", None)

def get_facility_ids():
    """Return list of facility IDs the current user can see."""
    role = get_role()
    if role == "admin":
        return list(FACILITIES.keys())
    elif role in FACILITIES:
        return [role]
    return []

# ── Palette ───────────────────────────────────────────────────────────────────
TEAL      = "#009E73"
ORANGE    = "#E69F00"
SKY       = "#56B4E9"
VERMILION = "#D55E00"
BLUISH    = "#0072B2"
PINK      = "#CC79A7"
YELLOW    = "#F0E442"
C_GREY    = "#BBBBBB"

LIKERT_COLORS   = [TEAL, SKY, ORANGE, PINK, VERMILION, C_GREY]
QUALITY_COLORS  = [VERMILION, PINK, ORANGE, SKY, TEAL, C_GREY]
PIE_COLORS      = [TEAL, BLUISH, ORANGE, VERMILION, PINK, SKY, C_GREY]
FACILITY_COLORS = [TEAL, BLUISH, ORANGE, VERMILION, PINK, SKY, YELLOW]

# ── CSS ───────────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;600;700&family=DM+Serif+Display:ital@0;1&display=swap');
html,body,[class*="css"]{{font-family:'DM Sans',sans-serif;}}
h1,h2,h3{{font-family:'DM Serif Display',serif;}}
.hero{{background:linear-gradient(135deg,#005f46 0%,#009E73 45%,#56B4E9 100%);
    border-radius:20px;padding:32px 44px;margin-bottom:8px;}}
.hero-comp{{background:linear-gradient(135deg,#0072B2 0%,#56B4E9 55%,#009E73 100%);
    border-radius:20px;padding:32px 44px;margin-bottom:8px;}}
.hero-title{{font-family:'DM Serif Display',serif;font-size:2.1rem;font-weight:400;color:white;margin:0 0 4px 0;}}
.hero-caption{{font-size:0.85rem;color:rgba(255,255,255,0.78);margin:0 0 24px 0;}}
.hero-stats{{display:flex;gap:12px;flex-wrap:nowrap;}}
.hero-stat{{text-align:center;background:rgba(255,255,255,0.12);border-radius:14px;
    padding:14px 12px;backdrop-filter:blur(4px);flex:1;min-width:0;}}
.hero-stat-num{{font-size:1.7rem;font-weight:700;color:white;line-height:1;font-family:'DM Serif Display',serif;}}
.hero-stat-label{{font-size:0.66rem;color:rgba(255,255,255,0.8);margin-top:5px;line-height:1.3;}}
.section-title{{font-family:'DM Serif Display',serif;font-size:1.25rem;color:#1a1a1a;
    border-left:4px solid {TEAL};padding-left:14px;margin:32px 0 14px 0;}}
</style>""", unsafe_allow_html=True)

# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def _fetch(asset_uid: str, facility_name: str) -> pd.DataFrame:
    """Fetch all records from a Kobo asset."""
    if not KOBO_TOKEN or not asset_uid:
        return pd.DataFrame()
    headers = {"Authorization": f"Token {KOBO_TOKEN}"}
    url = f"{BASE_URL}/api/v2/assets/{asset_uid}/data/?format=json&limit=3000"
    results = []
    while url:
        try:
            r = requests.get(url, headers=headers, timeout=30)
        except Exception as e:
            st.warning(f"Connection error for {facility_name}: {e}")
            return pd.DataFrame()
        if r.status_code in (502, 503, 504):
            # Transient server error — warn but don't crash
            st.warning(f"Kobo API temporarily unavailable for {facility_name} (HTTP {r.status_code}). Try refreshing.")
            return pd.DataFrame()
        if r.status_code != 200:
            st.error(f"Kobo API {r.status_code} for {facility_name}")
            return pd.DataFrame()
        data = r.json()
        results.extend(data.get("results", []))
        url = data.get("next")
    return pd.DataFrame(results) if results else pd.DataFrame()


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Strip group prefixes like 'interview/' from column names."""
    renames = {}
    existing = set(df.columns)
    for col in df.columns:
        if "/" in col and not col.startswith("_") and not col.startswith("meta") and not col.startswith("formhub"):
            short = col.rsplit("/", 1)[-1]
            if short not in existing:
                renames[col] = short
    return df.rename(columns=renames) if renames else df


def load_women(fac_ids: list) -> pd.DataFrame:
    frames = []
    for fid in fac_ids:
        info = FACILITIES[fid]
        df = _fetch(info["women_uid"], info["display_name"])
        if not df.empty:
            df = _normalize(df)
            df["_facility_id"]   = fid
            df["_facility_name"] = info["display_name"]
            df["_country"]       = info["country"]
            df["_continent"]     = info.get("continent", "")
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def load_companion(fac_ids: list) -> pd.DataFrame:
    frames = []
    for fid in fac_ids:
        info = FACILITIES[fid]
        if not info.get("companion_uid"):
            continue
        df = _fetch(info["companion_uid"], info["display_name"])
        if not df.empty:
            df = _normalize(df)
            df["_facility_id"]   = fid
            df["_facility_name"] = info["display_name"]
            df["_country"]       = info["country"]
            df["_continent"]     = info.get("continent", "")
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

# ── Utilities ─────────────────────────────────────────────────────────────────
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
    b = 80 if legend_below else 20
    layout = dict(
        title=dict(text=title, font=dict(size=13, family="DM Serif Display, serif", color="#1a1a1a"),
                   x=0, xanchor="left", y=0.98, yanchor="top"),
        margin=dict(t=64, b=b, l=8, r=8), height=height,
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="DM Sans, sans-serif", size=11),
    )
    if legend_below:
        layout["legend"] = dict(orientation="h", y=-0.18, x=0.5, xanchor="center", font=dict(size=10))
    else:
        layout["showlegend"] = False
    fig.update_layout(**layout)
    return fig

def sidebar_logo():
    if LOGO_PATH.exists():
        c1, c2, c3 = st.sidebar.columns([1, 2, 1])
        with c2:
            st.image(str(LOGO_PATH), width=110)

def sidebar_facility_header(page_label: str):
    """Show ICI Dashboard title + facility name + page label in sidebar."""
    role = get_role()
    if role == "admin":
        facility_line = ""   # admin sees all facilities — no single name
    else:
        fids = get_facility_ids()
        if fids:
            name = FACILITIES[fids[0]]["display_name"]
            facility_line = f'<div style="font-size:0.78rem;color:#005f46;font-weight:600;margin-bottom:2px;">{name}</div>'
        else:
            facility_line = ""
    st.sidebar.markdown(f"""
<div style="text-align:center;">
<div style="font-family:'DM Serif Display',serif;font-size:1.05rem;color:#005f46;font-weight:600;">ICI Dashboard</div>
{facility_line}<div style="font-size:0.68rem;color:#888;margin-bottom:12px;">{page_label}</div>
<hr style="border:none;border-top:1px solid #e0e0e0;margin:0 0 12px 0;">
</div>""", unsafe_allow_html=True)

def logout_button():
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.role = None
        st.rerun()

def lang_selector(key: str) -> str:
    if key not in st.session_state:
        st.session_state[key] = "EN"
    cols = st.columns([1, 1, 1, 9])
    for i, l in enumerate(["EN", "FR", "ES"]):
        active = st.session_state[key] == l
        if cols[i].button(l, key=f"{key}_btn_{l}", use_container_width=True,
                          type="primary" if active else "secondary"):
            st.session_state[key] = l
            st.rerun()
    return st.session_state[key]

def date_filter(df: pd.DataFrame, key: str = "df") -> pd.DataFrame:
    """Simple date range filter with unique keys per page."""
    if "_submission_time" not in df.columns or df["_submission_time"].isna().all():
        return df
    # Ensure datetime dtype before .dt accessor — handle timezone-aware strings too
    if not pd.api.types.is_datetime64_any_dtype(df["_submission_time"]):
        df = df.copy()
        df["_submission_time"] = pd.to_datetime(df["_submission_time"], errors="coerce", utc=True)
    # Strip timezone info so comparisons with plain date() work
    if hasattr(df["_submission_time"].dtype, "tz") and df["_submission_time"].dtype.tz is not None:
        df = df.copy()
        df["_submission_time"] = df["_submission_time"].dt.tz_localize(None)
    if df["_submission_time"].isna().all():
        return df
    import calendar
    mn, mx = df["_submission_time"].min(), df["_submission_time"].max()
    years  = sorted(df["_submission_time"].dt.year.dropna().unique().astype(int).tolist())
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    st.sidebar.markdown("**Date range**")
    c1, c2 = st.sidebar.columns(2)
    sy = c1.selectbox("", years, key=f"sy_{key}", label_visibility="collapsed")
    sm = c2.selectbox("", months, index=mn.month-1, key=f"sm_{key}", label_visibility="collapsed")
    c3, c4 = st.sidebar.columns(2)
    ey = c3.selectbox("", years, index=len(years)-1, key=f"ey_{key}", label_visibility="collapsed")
    em = c4.selectbox("", months, index=mx.month-1, key=f"em_{key}", label_visibility="collapsed")
    sdt = datetime(sy, months.index(sm)+1, 1).date()
    edt = datetime(ey, months.index(em)+1, calendar.monthrange(ey, months.index(em)+1)[1]).date()
    return df[(df["_submission_time"].dt.date >= sdt) & (df["_submission_time"].dt.date <= edt)]

# ── Value maps ────────────────────────────────────────────────────────────────
METHOD_MAP = {
    "EN": {1:"Vaginal", 2:"Assisted vaginal", 3:"Elective C/S", 4:"Emergency C/S", 5:"VBAC", 0:"Unknown"},
    "FR": {1:"Vaginal", 2:"Vaginal assisté", 3:"Césarienne élective", 4:"Césarienne urgence", 5:"AVAC", 0:"Inconnu"},
    "ES": {1:"Vaginal", 2:"Vaginal asistido", 3:"Cesárea electiva", 4:"Cesárea urgencia", 5:"PVAC", 0:"No sé"},
}
EDUCATION_MAP = {
    "EN": {1:"None", 2:"Primary", 3:"Secondary", 4:"Higher"},
    "FR": {1:"Aucune", 2:"Primaire", 3:"Secondaire", 4:"Supérieur"},
    "ES": {1:"Ninguna", 2:"Básica", 3:"Media", 4:"Superior"},
}
RISK_MAP = {
    "EN": {1:"Yes", 2:"No", 0:"Unknown"},
    "FR": {1:"Oui", 2:"Non", 0:"Inconnu"},
    "ES": {1:"Sí", 2:"No", 0:"No sé"},
}
# Prenatal education — numeric codes (Cartagena form)
# 0=None, 1=At this facility, 2=Public clinic, 3=Private class, 6=Other
# Canada form uses free-text multiselect — handled separately in prep_women
CHILD_ED_MAP = {
    "EN": {0:"None (did not attend)", 1:"At this facility", 2:"Public/government clinic",
           3:"Lamaze class", 4:"Home midwife/doula", 5:"ICCE class", 6:"Other private class/clinic"},
    "FR": {0:"Aucune (n'a pas participé)", 1:"Dans cet établissement", 2:"Clinique publique",
           3:"Cours Lamaze", 4:"Sage-femme à domicile", 5:"Cours ICCE", 6:"Autre cours/clinique privé"},
    "ES": {0:"Ninguna (no asistió)", 1:"En esta institución", 2:"Centro de salud pública",
           3:"Clase Lamaze", 4:"Comadrona/doula a domicilio", 5:"Clase ICCE", 6:"Otra clase/clínica privada"},
}
LIKERT5_MAP = {
    "EN": {5:"Always", 4:"Most of the time", 3:"Sometimes", 2:"Rarely", 1:"Never", 0:"N/A"},
    "FR": {5:"Toujours", 4:"La plupart du temps", 3:"Quelquefois", 2:"Rarement", 1:"Jamais", 0:"N/A"},
    "ES": {5:"Siempre", 4:"La mayoría", 3:"A veces", 2:"Raramente", 1:"Nunca", 0:"N/A"},
}
QUALITY_MAP = {
    "EN": {5:"Very good", 4:"Good", 3:"Neutral", 2:"Poor", 1:"Very bad", 0:"Unknown"},
    "FR": {5:"Très bien", 4:"Bien", 3:"Neutre", 2:"Mauvais", 1:"Très mauvais", 0:"Inconnu"},
    "ES": {5:"Muy bueno", 4:"Bueno", 3:"Neutral", 2:"Malo", 1:"Muy malo", 0:"No sé"},
}
QUALITY_ORDER = {
    "EN": ["Very bad","Poor","Neutral","Good","Very good","Unknown"],
    "FR": ["Très mauvais","Mauvais","Neutre","Bien","Très bien","Inconnu"],
    "ES": ["Muy malo","Malo","Neutral","Bueno","Muy bueno","No sé"],
}
DECISIONS_MAP = {
    "EN": {1:"Yes, with enough info", 2:"Yes, not enough info", 3:"Sometimes", 4:"No", 0:"N/A"},
    "FR": {1:"Oui, avec info", 2:"Oui, sans assez d'info", 3:"Parfois", 4:"Non", 0:"N/A"},
    "ES": {1:"Sí, con info", 2:"Sí, sin suficiente info", 3:"A veces", 4:"No", 0:"N/A"},
}
EPI_MAP = {
    "EN": {1:"Yes, with consent", 2:"Yes, without consent", 3:"No, I declined", 4:"No, not recommended"},
    "FR": {1:"Oui, avec consentement", 2:"Oui, sans consentement", 3:"Non, j'ai refusé", 4:"Non, non recommandé"},
    "ES": {1:"Sí, con consentimiento", 2:"Sí, sin consentimiento", 3:"No, lo rechacé", 4:"No, no recomendado"},
}
EXAM_MAP = {
    "EN": {1:"Never w/o consent", 2:"Rarely w/o consent", 3:"Sometimes w/o consent", 4:"Frequently w/o consent", 5:"Always w/o consent"},
    "FR": {1:"Jamais sans consent.", 2:"Rarement sans consent.", 3:"Parfois sans consent.", 4:"Fréquemment sans consent.", 5:"Toujours sans consent."},
    "ES": {1:"Nunca sin consent.", 2:"Raro sin consent.", 3:"A veces sin consent.", 4:"Frecuente sin consent.", 5:"Siempre sin consent."},
}
TREAT_MAP  = {"EN": {1:"Yes", 2:"No", 0:"Unknown"}, "FR": {1:"Oui", 2:"Non", 0:"Inconnu"}, "ES": {1:"Sí", 2:"No", 0:"No sé"}}
BF_MAP = {
    "EN": {1:"No, didn't breastfeed", 2:"No, didn't need help", 3:"No, needed help — not received", 4:"Yes, but not enough", 5:"Yes, received help", 0:"N/A"},
    "FR": {1:"Non, pas allaitée", 2:"Non, pas besoin", 3:"Non, besoin sans aide", 4:"Oui, insuffisant", 5:"Oui, aide reçue", 0:"N/A"},
    "ES": {1:"No, no amamanté", 2:"No, no necesité ayuda", 3:"No, necesité sin recibir", 4:"Sí, insuficiente", 5:"Sí, recibí ayuda", 0:"N/A"},
}
SKIN_MAP = {
    "EN": {1:"Yes", 2:"Yes, not immediate", 3:"Yes, <1 hour", 4:"No", 5:"No, chose not to", 6:"Unknown"},
    "FR": {1:"Oui", 2:"Oui, pas immédiat", 3:"Oui, <1h", 4:"Non", 5:"Non, choix", 6:"Inconnu"},
    "ES": {1:"Sí", 2:"Sí, no inmediato", 3:"Sí, <1h", 4:"No", 5:"No, no quiso", 6:"No sé"},
}
INDUCE_MAP = {"EN": {1:"No", 2:"Yes", 0:"N/A"}, "FR": {1:"Non", 2:"Oui", 0:"N/A"}, "ES": {1:"No", 2:"Sí", 0:"N/A"}}
PHARMA_MAP = {
    "EN": {1:"No, didn't want", 2:"No, wanted but denied", 3:"Yes, too late", 4:"Yes, on time", 5:"Not offered", 0:"N/A"},
    "FR": {1:"Non, pas voulu", 2:"Non, refusé", 3:"Oui, trop tard", 4:"Oui, à temps", 5:"Non disponible", 0:"N/A"},
    "ES": {1:"No, no quería", 2:"No, quería pero no", 3:"Sí, tarde", 4:"Sí, a tiempo", 5:"No disponible", 0:"N/A"},
}
COMFORT_MAP = {
    "EN": {1:"Yes, used them", 2:"Yes, didn't use", 3:"None suggested", 0:"N/A"},
    "FR": {1:"Oui, utilisé", 2:"Oui, pas utilisé", 3:"Aucune suggestion", 0:"N/A"},
    "ES": {1:"Sí, los usé", 2:"Sí, no los usé", 3:"Ninguno sugerido", 0:"N/A"},
}
ROOMING_MAP = {
    "EN": {4:"Yes, most of the time", 1:"No, baby sick/unit", 2:"No, not with me", 3:"No, didn't want", 0:"N/A"},
    "FR": {4:"Oui, plupart du temps", 1:"Non, bébé malade", 2:"Non, pas avec moi", 3:"Non, pas voulu", 0:"N/A"},
    "ES": {4:"Sí, la mayoría", 1:"No, bebé enfermo", 2:"No, no estuvo", 3:"No, no quería", 0:"N/A"},
}
VERBAL_MAP = {
    "EN": {1:"Never", 2:"Rarely", 3:"Sometimes", 4:"Most of the time", 5:"Always", 0:"N/A"},
    "FR": {1:"Jamais", 2:"Rarement", 3:"Quelquefois", 4:"La plupart", 5:"Toujours", 0:"N/A"},
    "ES": {1:"Nunca", 2:"Raramente", 3:"A veces", 4:"La mayoría", 5:"Siempre", 0:"N/A"},
}
PHYS_MAP = VERBAL_MAP
PAYMENT_MAP = {
    "EN": {1:"Yes", 2:"No", 3:"Free/covered", 0:"Unknown"},
    "FR": {1:"Oui", 2:"Non", 3:"Gratuit/couvert", 0:"Inconnu"},
    "ES": {1:"Sí", 2:"No", 3:"Gratis/cubierto", 0:"No sé"},
}
LIKERT_QS_W = {
    "EN": {"introduction":"Staff introduced themselves","spoke":"Staff spoke clearly",
           "communication":"Comfortable asking questions","privacy":"Privacy protected",
           "respect":"Treated respectfully","values":"Beliefs respected",
           "positive":"Encouraged to feel empowered","morale":"Staff well-supported","coop":"Coordinated care"},
    "FR": {"introduction":"Personnel présenté","spoke":"Personnel clair",
           "communication":"À l'aise pour questions","privacy":"Intimité protégée",
           "respect":"Traitée avec respect","values":"Croyances respectées",
           "positive":"Encouragée","morale":"Personnel soutenu","coop":"Soins coordonnés"},
    "ES": {"introduction":"Personal se presentó","spoke":"Personal habló claro",
           "communication":"Cómoda para preguntas","privacy":"Intimidad protegida",
           "respect":"Tratada con respeto","values":"Creencias respetadas",
           "positive":"Animada a sentirse capaz","morale":"Personal apoyado","coop":"Cuidados coordinados"},
}
EMOTION_LABELS_W = {
    "EN": {1:"Capable",2:"Incapable",3:"Anxious",4:"Supported",5:"Exhausted",
           6:"Active",7:"Relaxed",8:"Passive",9:"Responsible",10:"Dependent",11:"Secure",12:"Excluded"},
    "FR": {1:"Capable",2:"Incapable",3:"Anxieuse",4:"Soutenue",5:"Épuisée",
           6:"Active",7:"Détendue",8:"Passive",9:"Responsable",10:"Dépendante",11:"Sécurisée",12:"Exclue"},
    "ES": {1:"Capaz",2:"Incapaz",3:"Ansiosa",4:"Apoyada",5:"Agotada",
           6:"Activa",7:"Relajada",8:"Pasiva",9:"Responsable",10:"Dependiente",11:"Segura",12:"Excluida"},
}
POSITIVE_EMO_W = {
    "EN": {"Capable","Supported","Active","Relaxed","Responsible","Secure"},
    "FR": {"Capable","Soutenue","Active","Détendue","Responsable","Sécurisée"},
    "ES": {"Capaz","Apoyada","Activa","Relajada","Responsable","Segura"},
}
INFO_LABELS_W = {
    "EN": {1:"Caring for baby",2:"Family planning",3:"Warning signs",4:"Follow-up care"},
    "FR": {1:"Soins bébé",2:"Planification familiale",3:"Signes d'alarme",4:"Suivi"},
    "ES": {1:"Cuidar bebé",2:"Planificación familiar",3:"Señales de alarma",4:"Seguimiento"},
}
COMP_EMOTION_MAP = {
    "EN": {1:"Afraid",3:"Anxious",4:"Confident",5:"Doubtful",6:"Exhausted",7:"Grateful",
           8:"Happy",9:"Loving",10:"Nervous",12:"Reassured",14:"Respected",15:"Satisfied",
           16:"Secure",19:"Supported",20:"Surprised"},
    "FR": {1:"Effrayé",3:"Anxieux",4:"Confiant",5:"Incertain",6:"Épuisé",7:"Reconnaissant",
           8:"Heureux",9:"Aimant",10:"Nerveux",12:"Rassuré",14:"Respecté",15:"Satisfait",
           16:"Sécurisé",19:"Soutenu",20:"Surpris"},
    "ES": {1:"Miedo",3:"Ansiedad",4:"Confianza",5:"Duda",6:"Agotamiento",7:"Gratitud",
           8:"Felicidad",9:"Cariño",10:"Nerviosismo",12:"Tranquilidad",14:"Respeto",
           15:"Satisfacción",16:"Seguridad",19:"Apoyo",20:"Sorpresa"},
}
POSITIVE_EMO_C = {
    "EN": {"Confident","Grateful","Happy","Loving","Reassured","Respected","Satisfied","Secure","Supported"},
    "FR": {"Confiant","Reconnaissant","Heureux","Aimant","Rassuré","Respecté","Satisfait","Sécurisé","Soutenu"},
    "ES": {"Confianza","Gratitud","Felicidad","Cariño","Tranquilidad","Respeto","Satisfacción","Seguridad","Apoyo"},
}
COMPLAB_MAP = {
    "EN": {1:"Yes, all the time",3:"Yes, some of the time",2:"No",9:"Unknown"},
    "FR": {1:"Oui, tout le temps",3:"Oui, parfois",2:"Non",9:"Inconnu"},
    "ES": {1:"Sí, todo el tiempo",3:"Sí, algunas veces",2:"No",9:"No sé"},
}
COMP_DELIV_MAP = {"EN":{1:"Yes",2:"No",0:"Unknown"},"FR":{1:"Oui",2:"Non",0:"Inconnu"},"ES":{1:"Sí",2:"No",0:"No sé"}}
ACCOMPANY_MAP = {
    "EN": {5:"Strongly agree",4:"Agree",3:"Somewhat agree",2:"Disagree",1:"Strongly disagree"},
    "FR": {5:"Tout à fait",4:"D'accord",3:"Plutôt",2:"Pas d'accord",1:"Pas du tout"},
    "ES": {5:"Totalmente",4:"De acuerdo",3:"Algo",2:"En desacuerdo",1:"Totalmente no"},
}
CHOICES_MAP = {
    "EN": {1:"Yes, in depth",2:"Yes, a little",3:"No disadvantages shown",4:"No choices shown",0:"Unknown"},
    "FR": {1:"Oui, en détail",2:"Oui, un peu",3:"Pas de désavantages",4:"Pas de choix",0:"Inconnu"},
    "ES": {1:"Sí, detallado",2:"Sí, poco",3:"Sin desventajas",4:"Sin opciones",0:"No sé"},
}
EMERGENCY_MAP = {
    "EN": {5:"Strongly agree",4:"Agree",3:"Partially agree",2:"Disagree",1:"Strongly disagree",0:"Unknown"},
    "FR": {5:"Tout à fait",4:"D'accord",3:"Partiellement",2:"Pas d'accord",1:"Pas du tout",0:"Inconnu"},
    "ES": {5:"Totalmente",4:"De acuerdo",3:"Parcialmente",2:"En desacuerdo",1:"No en absoluto",0:"No sé"},
}
COMP_ROOMING_MAP = {
    "EN": {4:"Yes, most of the time",1:"No, baby sick",2:"No, not with mother",0:"Unknown"},
    "FR": {4:"Oui, plupart",1:"Non, bébé malade",2:"Non, pas avec mère",0:"Inconnu"},
    "ES": {4:"Sí, la mayoría",1:"No, bebé enfermo",2:"No, no con madre",0:"No sé"},
}
MILK_MAP = {
    "EN": {1:"Yes",2:"No, complications",3:"No, mother chose supplement",4:"No, against mother's wish",0:"Unknown"},
    "FR": {1:"Oui",2:"Non, complications",3:"Non, choix mère",4:"Non, contre souhait",0:"Inconnu"},
    "ES": {1:"Sí",2:"No, complicaciones",3:"No, madre eligió",4:"No, contra deseo",0:"No sé"},
}
COMP_VALUES_MAP = {
    "EN": {5:"Yes, all",4:"Yes, most",3:"Yes, some",2:"Yes, few",1:"No",0:"Unknown"},
    "FR": {5:"Oui, tous",4:"Oui, la plupart",3:"Oui, certains",2:"Oui, quelques",1:"Non",0:"Inconnu"},
    "ES": {5:"Sí, todos",4:"Sí, la mayoría",3:"Sí, algunos",2:"Sí, pocos",1:"No",0:"No sé"},
}
COMP_DECISIONS_MAP = {
    "EN": {1:"Yes, with info",3:"Sometimes",4:"No",0:"N/A"},
    "FR": {1:"Oui, avec info",3:"Parfois",4:"Non",0:"N/A"},
    "ES": {1:"Sí, con info",3:"A veces",4:"No",0:"N/A"},
}
COMP_COOP_MAP = {
    "EN": {5:"Always",4:"Most of the time",3:"Sometimes",2:"Rarely",1:"Never",0:"Unknown"},
    "FR": {5:"Toujours",4:"Plupart",3:"Parfois",2:"Rarement",1:"Jamais",0:"Inconnu"},
    "ES": {5:"Siempre",4:"La mayoría",3:"A veces",2:"Raramente",1:"Nunca",0:"No sé"},
}
COMP_PHARMA_MAP = {
    "EN": {1:"No, didn't want",2:"No, wanted but denied",3:"Yes, too late",4:"Yes, on time",5:"Not offered",0:"Unknown"},
    "FR": {1:"Non, pas voulu",2:"Non, refusé",3:"Oui, trop tard",4:"Oui, à temps",5:"Non dispo",0:"Inconnu"},
    "ES": {1:"No, no quería",2:"No, quería pero no",3:"Sí, tarde",4:"Sí, a tiempo",5:"No dispo",0:"No sé"},
}
COMP_COMFORT_MAP = {
    "EN": {1:"Yes, she used them",2:"Yes, didn't use",3:"None suggested",0:"Unknown"},
    "FR": {1:"Oui, utilisé",2:"Oui, pas utilisé",3:"Aucune suggestion",0:"Inconnu"},
    "ES": {1:"Sí, los usó",2:"Sí, no usó",3:"Ninguno sugerido",0:"No sé"},
}
EXTRA_MAP = {
    "EN": {1:"Yes",2:"No",3:"Free/covered",0:"Unknown"},
    "FR": {1:"Oui",2:"Non",3:"Gratuit/couvert",0:"Inconnu"},
    "ES": {1:"Sí",2:"No",3:"Gratis/cubierto",0:"No sé"},
}
COMP_TREATMENT_MAP = VERBAL_MAP
COMP_RESPECT_MAP   = LIKERT5_MAP
LIKERT_QS_C = {
    "EN": {"introduction":"Staff introduced themselves","spoke":"Staff spoke clearly",
           "privacy":"Privacy protected","respect":"Woman treated respectfully",
           "comp_001":"Felt respected as companion","coop":"Staff coordinated"},
    "FR": {"introduction":"Personnel présenté","spoke":"Personnel clair",
           "privacy":"Intimité protégée","respect":"Femme respectée",
           "comp_001":"Respecté comme accompagnant","coop":"Personnel coordonné"},
    "ES": {"introduction":"Personal se presentó","spoke":"Personal habló claro",
           "privacy":"Intimidad protegida","respect":"Mujer respetada",
           "comp_001":"Respetado como acompañante","coop":"Personal coordinado"},
}
INFO_LABELS_C = {
    "EN": {1:"Baby care",2:"Family planning",3:"Warning signs",4:"Follow-up"},
    "FR": {1:"Soins bébé",2:"Planification",3:"Signes d'alarme",4:"Suivi"},
    "ES": {1:"Cuidar bebé",2:"Planificación",3:"Señales de alarma",4:"Seguimiento"},
}

# ── prep functions ────────────────────────────────────────────────────────────
def prep_women(df: pd.DataFrame, lang: str) -> pd.DataFrame:
    df = df.copy()
    df["_submission_time"] = pd.to_datetime(df["_submission_time"], errors="coerce", utc=True)
    if hasattr(df["_submission_time"].dtype, "tz") and df["_submission_time"].dtype.tz is not None:
        df["_submission_time"] = df["_submission_time"].dt.tz_localize(None)
    for col, mp in [
        ("method",       METHOD_MAP[lang]),
        ("education",    EDUCATION_MAP[lang]),
        ("risk",         RISK_MAP[lang]),
        ("satisfaction", QUALITY_MAP[lang]),
        ("expect",       QUALITY_MAP[lang]),
        ("decisions",    DECISIONS_MAP[lang]),
        ("epi",          EPI_MAP[lang]),
        ("exam",         EXAM_MAP[lang]),
        ("bf",           BF_MAP[lang]),
        ("induce",       INDUCE_MAP[lang]),
        ("treat",        TREAT_MAP[lang]),
        ("pharma",       PHARMA_MAP[lang]),
        ("comfort",      COMFORT_MAP[lang]),
        ("rooming",      ROOMING_MAP[lang]),
        ("verbal",       VERBAL_MAP[lang]),
        ("phys",         PHYS_MAP[lang]),
        ("payment",      PAYMENT_MAP[lang]),
    ]:
        if col in df.columns:
            df[col] = to_int(df[col])
            df[col + "_label"] = df[col].map(mp)
    for col, label in LIKERT_QS_W[lang].items():
        if col in df.columns:
            df[col] = to_int(df[col])
            df[col + "_label"] = df[col].map(LIKERT5_MAP[lang])
    if "skin" in df.columns:
        df["skin_int"]   = first_token_int(df["skin"])
        df["skin_label"] = df["skin_int"].map(SKIN_MAP[lang])
    if "age" in df.columns:
        df["age"] = to_int(df["age"])
        df["age_group"] = pd.cut(df["age"], bins=[0,19,24,29,34,39,99],
                                  labels=["<20","20–24","25–29","30–34","35–39","40+"])
    if "weeks" in df.columns:
        df["weeks_clean"] = to_int(df["weeks"])
        df.loc[~df["weeks_clean"].between(21,45), "weeks_clean"] = pd.NA
    if "no_deliveries" in df.columns:
        df["no_deliveries"] = to_int(df["no_deliveries"])
        df.loc[df["no_deliveries"] > 10, "no_deliveries"] = pd.NA

    # ── Prenatal education ────────────────────────────────────────────────────
    if "child_ed" in df.columns:
        raw_series = df["child_ed"]
        numeric = to_int(raw_series)
        yes_lbl  = {"EN":"Yes",  "FR":"Oui", "ES":"Sí"}[lang]
        no_lbl   = {"EN":"No",   "FR":"Non", "ES":"No"}[lang]
        here_lbl = {"EN":"At this facility","FR":"Dans cet établissement","ES":"En esta institución"}[lang]
        else_lbl = {"EN":"Elsewhere","FR":"Ailleurs","ES":"En otro lugar"}[lang]

        no_strings   = {"none","no","no he recibido educación prenatal.","aucune","non",
                        "did not attend prenatal education"}
        here_strings = {"hospital","birth center","clsc","this facility",
                        "cet établissement","esta institución","delivering"}

        # Process each value independently — handles int, numeric string, or text label
        yes_lbl  = {"EN":"Yes",  "FR":"Oui", "ES":"Sí"}[lang]
        no_lbl   = {"EN":"No",   "FR":"Non", "ES":"No"}[lang]
        here_lbl = {"EN":"At this facility","FR":"Dans cet établissement","ES":"En esta institución"}[lang]
        else_lbl = {"EN":"Elsewhere","FR":"Ailleurs","ES":"En otro lugar"}[lang]

        no_strings   = {"none","no","no he recibido educación prenatal.","aucune","non",
                        "did not attend prenatal education"}
        here_strings = {"hospital","birth center","clsc","this facility",
                        "cet établissement","esta institución","delivering"}

        _num_map = CHILD_ED_MAP[lang]  # int key → label

        def _parse(val):
            """Return (attended, detail, here) for one raw value."""
            if val is None or (isinstance(val, float) and pd.isna(val)):
                return None, None, None
            # Try numeric interpretation first
            try:
                n = int(float(str(val).strip()))
                attended = no_lbl if n == 0 else yes_lbl
                detail   = _num_map.get(n)
                here     = (here_lbl if n == 1 else else_lbl) if n != 0 else None
                return attended, detail, here
            except (ValueError, TypeError):
                pass
            # Text interpretation (Canada-style)
            s = str(val).strip()
            if s in ("nan", "None", ""):
                return None, None, None
            sl = s.lower()
            if sl in no_strings:
                return no_lbl, _num_map[0], None
            attended = yes_lbl
            if any(h in sl for h in here_strings):
                detail, here = _num_map[1], here_lbl
            elif "public" in sl or "government" in sl:
                detail, here = _num_map[2], else_lbl
            elif "lamaze" in sl:
                detail, here = _num_map[3], else_lbl
            elif "midwife" in sl or "doula" in sl:
                detail, here = _num_map[4], else_lbl
            elif "icce" in sl:
                detail, here = _num_map[5], else_lbl
            else:
                detail, here = _num_map[6], else_lbl
            return attended, detail, here

        parsed = df["child_ed"].apply(_parse)
        df["prenatal_attended"] = parsed.apply(lambda x: x[0])
        df["prenatal_detail"]   = parsed.apply(lambda x: x[1])
        df["prenatal_here"]     = parsed.apply(lambda x: x[2])

    return df


def prep_companion(df: pd.DataFrame, lang: str) -> pd.DataFrame:
    df = df.copy()
    df["_submission_time"] = pd.to_datetime(df["_submission_time"], errors="coerce", utc=True)
    if hasattr(df["_submission_time"].dtype, "tz") and df["_submission_time"].dtype.tz is not None:
        df["_submission_time"] = df["_submission_time"].dt.tz_localize(None)
    if "emotion" in df.columns:
        df["emotion"]       = to_int(df["emotion"])
        df["emotion_label"] = df["emotion"].map(COMP_EMOTION_MAP[lang])
    for col, mp in [
        ("education",  EDUCATION_MAP[lang]),
        ("comp",       {"EN":{1:"Father/parent of baby",2:"Family member (specify relationship)",3:"Friend",0:"Other"},
                        "FR":{1:"Père/parent du bébé",2:"Membre de la famille (précisez)",3:"Ami(e)",0:"Autre"},
                        "ES":{1:"Padre del bebé (sean los padres casados o no)",2:"Acompañante - familiar (especifique relación)",3:"Amigo",0:"Otro"}}[lang]),
        ("method",     METHOD_MAP[lang]),
        ("verbal",     VERBAL_MAP[lang]),
        ("phys",       PHYS_MAP[lang]),
        ("payment",    PAYMENT_MAP[lang]),
        ("extra",      EXTRA_MAP[lang]),
        ("satisfaction",QUALITY_MAP[lang]),
        ("expect",     QUALITY_MAP[lang]),
        ("complab",    COMPLAB_MAP[lang]),
        ("comp_deliv", COMP_DELIV_MAP[lang]),
        ("comp_001",   LIKERT5_MAP[lang]),
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
            df[col] = to_int(df[col])
            df[col + "_label"] = df[col].map(mp)
    for col in ["introduction","spoke","privacy","respect","comp_001","coop"]:
        if col in df.columns:
            df[col + "_label"] = df[col].map(LIKERT5_MAP[lang])
    if "age" in df.columns:
        df["age"] = to_int(df["age"])
        df["age_group"] = pd.cut(df["age"], bins=[0,24,29,34,39,99],
                                  labels=["<25","25–29","30–34","35–39","40+"])
    # Build a detailed relationship label:
    # - comp=1 (father) and comp=3 (friend): use comp_label as-is
    # - comp=2 (family member): show only the comp_other value (e.g. "Madre", "Hermana")
    #   falling back to comp_label if comp_other is blank
    if "comp_label" in df.columns:
        def _detail(row):
            other = str(row.get("comp_other", "") or "").strip()
            if other and other.lower() not in ("nan", "none", ""):
                return other.capitalize()
            return row.get("comp_label")
        df["comp_detail_label"] = df.apply(_detail, axis=1)
    return df
