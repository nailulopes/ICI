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
# Each facility has: name, asset_uid, country, (optional) language codes
FACILITIES = {
    "brazil_facility": {
        "name": "Brazil Facility",
        "asset_uid": "aT3kXmLeYLtUC6zVAV5abW",
        "country": "Brazil",
        "languages": ["EN", "PT"],
    },
    # Add more facilities here as they become available:
    # "cartagena_hospital": {
    #     "name": "Cartagena Hospital",
    #     "asset_uid": "YOUR_ASSET_UID_HERE",
    #     "country": "Colombia",
    #     "languages": ["EN", "ES"],
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
# TRILINGUAL LABELS (EN, FR, ES, PT)
# ═══════════════════════════════════════════════════════════════════════════════
L = {
    "title": {
        "EN": "Women's Experience Dashboard",
        "FR": "Tableau de bord — Expérience des femmes",
        "ES": "Panel de Experiencia de las Mujeres",
        "PT": "Painel de Experiência das Mulheres"
    },
    "caption": {
        "EN": "International Childbirth Initiative — 12 Steps to Safe and Respectful MotherBaby-Family Maternity Care",
        "FR": "Initiative Internationale pour la Naissance — 12 étapes pour des soins de maternité sûrs et respectueux",
        "ES": "Iniciativa Internacional para el Parto — 12 Pasos para una Atención Materna Segura y Respetuosa",
        "PT": "Iniciativa Internacional pelo Parto — 12 Passos para Cuidados Maternos Seguros e Respeitosos"
    },
    "filters": {"EN": "Filters", "FR": "Filtres", "ES": "Filtros", "PT": "Filtros"},
    "facility": {"EN": "Facility", "FR": "Établissement", "ES": "Centro", "PT": "Unidade"},
    "compare_mode": {"EN": "Compare facilities", "FR": "Comparer établissements", "ES": "Comparar centros", "PT": "Comparar unidades"},
    "date_range": {"EN": "Date range", "FR": "Période", "ES": "Período", "PT": "Período"},
    "birth_method_f": {"EN": "Birth method", "FR": "Mode d'accouchement", "ES": "Modo de parto", "PT": "Tipo de parto"},
    "high_risk_f": {"EN": "High-risk pregnancy", "FR": "Grossesse à risque", "ES": "Embarazo de alto riesgo", "PT": "Gravidez de alto risco"},
    "filtered": {"EN": "Filtered responses", "FR": "Réponses filtrées", "ES": "Respuestas filtradas", "PT": "Respostas filtradas"},
    "refresh": {"EN": "↻ Refresh data", "FR": "↻ Actualiser", "ES": "↻ Actualizar", "PT": "↻ Atualizar"},
    "responses": {"EN": "Responses", "FR": "Réponses", "ES": "Respuestas", "PT": "Respostas"},
    "pct": {"EN": "% of respondents", "FR": "% des répondantes", "ES": "% de encuestadas", "PT": "% das respondentes"},
    "download": {"EN": "⬇ Download CSV", "FR": "⬇ Télécharger CSV", "ES": "⬇ Descargar CSV", "PT": "⬇ Baixar CSV"},
    "raw_data": {"EN": "📋 View raw data", "FR": "📋 Voir les données brutes", "ES": "📋 Ver datos brutos", "PT": "📋 Ver dados brutos"},
    "positive": {"EN": "Positive", "FR": "Positif", "ES": "Positivo", "PT": "Positivo"},
    "negative": {"EN": "Negative", "FR": "Négatif", "ES": "Negativo", "PT": "Negativo"},
    "all": {"EN": "All", "FR": "Tous", "ES": "Todos", "PT": "Todos"},
    
    # Section titles
    "s_overview": {"EN": "Overview", "FR": "Vue d'ensemble", "ES": "Resumen", "PT": "Visão geral"},
    "s_comparison": {"EN": "Facility Comparison", "FR": "Comparaison des établissements", "ES": "Comparación de centros", "PT": "Comparação de unidades"},
    "s_cs_rates": {"EN": "Caesarean Section Rates", "FR": "Taux de césarienne", "ES": "Tasas de cesárea", "PT": "Taxas de cesárea"},
    "s_demographics": {"EN": "Demographics by Facility", "FR": "Démographie par établissement", "ES": "Demografía por centro", "PT": "Demografia por unidade"},
    "s_timeline": {"EN": "Responses Over Time", "FR": "Réponses dans le temps", "ES": "Respuestas en el tiempo", "PT": "Respostas ao longo do tempo"},
    "s_trends": {"EN": "Key Indicators Over Time", "FR": "Indicateurs clés dans le temps", "ES": "Indicadores clave en el tiempo", "PT": "Indicadores-chave ao longo do tempo"},
    "s_profile": {"EN": "Respondent Profile", "FR": "Profil des répondantes", "ES": "Perfil de las encuestadas", "PT": "Perfil das respondentes"},
    "s_likert": {"EN": "Quality of Care — Likert Scales", "FR": "Qualité des soins — Échelles de Likert", "ES": "Calidad de atención — Escalas Likert", "PT": "Qualidade do cuidado — Escalas Likert"},
    "s_likert_cap": {
        "EN": "Response distribution across care dimensions (Always → Never)",
        "FR": "Distribution des réponses par dimension de soins (Toujours → Jamais)",
        "ES": "Distribución de respuestas por dimensión de atención (Siempre → Nunca)",
        "PT": "Distribuição das respostas por dimensão de cuidado (Sempre → Nunca)"
    },
    "s_autonomy": {"EN": "Autonomy & Consent", "FR": "Autonomie et consentement", "ES": "Autonomía y consentimiento", "PT": "Autonomia e consentimento"},
    "s_clinical": {"EN": "Clinical Practices", "FR": "Pratiques cliniques", "ES": "Prácticas clínicas", "PT": "Práticas clínicas"},
    "s_satisfaction": {"EN": "Satisfaction — Expectations vs. Reality", "FR": "Satisfaction — Attentes vs. Réalité", "ES": "Satisfacción — Expectativas vs. Realidad", "PT": "Satisfação — Expectativas vs. Realidade"},
    "s_emotions": {"EN": "How Women Felt at the Time of Delivery", "FR": "Ressenti des femmes au moment de l'accouchement", "ES": "Cómo se sintieron las mujeres durante el parto", "PT": "Como as mulheres se sentiram no momento do parto"},
    "s_emotions_adjusted": {"EN": "Emotions (Adjusted — Exhaustion Filtered)", "FR": "Émotions (Ajusté — Épuisement filtré)", "ES": "Emociones (Ajustado — Agotamiento filtrado)", "PT": "Emoções (Ajustado — Exaustão filtrada)"},
    "emo_note": {
        "EN": "Multiple emotions could be selected — bars show % of respondents who chose each one.",
        "FR": "Plusieurs émotions pouvaient être sélectionnées — les barres montrent le % de répondantes ayant choisi chacune.",
        "ES": "Se podían seleccionar múltiples emociones — las barras muestran el % de encuestadas que eligieron cada una.",
        "PT": "Múltiplas emoções podiam ser selecionadas — as barras mostram % das respondentes que escolheram cada uma."
    },
    "emo_adjusted_note": {
        "EN": "'Exhausted' is included only when it was the sole emotion selected.",
        "FR": "'Épuisée' n'est inclus que si c'était la seule émotion sélectionnée.",
        "ES": "'Agotada' se incluye solo si fue la única emoción seleccionada.",
        "PT": "'Exausta' é incluída apenas quando foi a única emoção selecionada."
    },
    "s_discharge": {"EN": "Information Provided Before Discharge", "FR": "Informations données avant la sortie", "ES": "Información proporcionada antes del alta", "PT": "Informações fornecidas antes da alta"},
    "s_mistreat": {"EN": "Mistreatment & Respect", "FR": "Maltraitance et respect", "ES": "Maltrato y respeto", "PT": "Maus-tratos e respeito"},
    "s_care_journey": {"EN": "Care Journey", "FR": "Parcours de soins", "ES": "Trayectoria de atención", "PT": "Jornada de cuidado"},
    
    # KPIs
    "kpi_total": {"EN": "Total responses", "FR": "Total réponses", "ES": "Total respuestas", "PT": "Total de respostas"},
    "kpi_positive": {"EN": "rated care as Good or Very good", "FR": "ont évalué les soins comme Bons ou Très bons", "ES": "calificaron la atención como Buena o Muy buena", "PT": "avaliaram o cuidado como Bom ou Muito bom"},
    "kpi_skin": {"EN": "had immediate skin-to-skin", "FR": "ont eu le peau à peau immédiat", "ES": "tuvieron contacto piel a piel inmediato", "PT": "tiveram contato pele a pele imediato"},
    "kpi_exam": {"EN": "vaginal exams w/o consent", "FR": "examens vaginaux sans consentement", "ES": "exámenes vaginales sin consentimiento", "PT": "exames vaginais sem consentimento"},
    "kpi_epi": {"EN": "episiotomies w/o consent", "FR": "épisiotomies sans consentement", "ES": "episiotomías sin consentimiento", "PT": "episiotomias sem consentimento"},
    "kpi_staff_equipped": {"EN": "felt staff well equipped", "FR": "ont senti le personnel bien équipé", "ES": "sintieron al personal bien capacitado", "PT": "sentiram a equipe bem preparada"},
    "kpi_no_cost_info": {"EN": "did not know cost in advance", "FR": "ne connaissaient pas le coût à l'avance", "ES": "no conocían el costo por adelantado", "PT": "não sabiam o custo antecipadamente"},
    
    # Profile
    "p_method": {"EN": "Birth method", "FR": "Mode d'accouchement", "ES": "Modo de parto", "PT": "Tipo de parto"},
    "p_age": {"EN": "Age group", "FR": "Groupe d'âge", "ES": "Grupo de edad", "PT": "Faixa etária"},
    "p_education": {"EN": "Education level", "FR": "Niveau d'éducation", "ES": "Nivel educativo", "PT": "Nível de escolaridade"},
    "p_weeks": {"EN": "Gestational weeks at birth", "FR": "Semaines de gestation", "ES": "Semanas de gestación", "PT": "Semanas gestacionais"},
    "p_parity": {"EN": "Number of previous deliveries", "FR": "Nombre d'accouchements précédents", "ES": "Número de partos previos", "PT": "Número de partos anteriores"},
    "mean_weeks": {"EN": "Mean gestational weeks", "FR": "Semaines de gestation (moy.)", "ES": "Semanas de gestación (prom.)", "PT": "Semanas gestacionais (méd.)"},
    "mean_age": {"EN": "Mean age (min–max)", "FR": "Âge moyen (min–max)", "ES": "Edad promedio (min–máx)", "PT": "Idade média (min–máx)"},
    
    # Grouping
    "grp_month": {"EN": "Month", "FR": "Mois", "ES": "Mes", "PT": "Mês"},
    "grp_week": {"EN": "Week", "FR": "Semaine", "ES": "Semana", "PT": "Semana"},
    "grp_day": {"EN": "Day", "FR": "Jour", "ES": "Día", "PT": "Dia"},
    "grp_by": {"EN": "Group by", "FR": "Regrouper par", "ES": "Agrupar por", "PT": "Agrupar por"},
    
    # Trends
    "tr_positive": {"EN": "% Positive rating", "FR": "% Évaluation positive", "ES": "% Calificación positiva", "PT": "% Avaliação positiva"},
    "tr_skin": {"EN": "% Immediate skin-to-skin", "FR": "% Peau à peau immédiat", "ES": "% Piel a piel inmediato", "PT": "% Pele a pele imediato"},
    "tr_exam": {"EN": "% Vaginal exams w/o consent", "FR": "% Examens vaginaux s.c.", "ES": "% Exámenes vaginales s.c.", "PT": "% Exames vaginais s.c."},
    
    # Autonomy
    "a_decisions": {"EN": "Included in care decisions", "FR": "Incluse dans les décisions de soins", "ES": "Incluida en las decisiones de atención", "PT": "Incluída nas decisões de cuidado"},
    "a_exam": {"EN": "Vaginal exam — without consent frequency", "FR": "Examen vaginal — fréquence sans consentement", "ES": "Examen vaginal — frecuencia sin consentimiento", "PT": "Exame vaginal — frequência sem consentimento"},
    "a_epi": {"EN": "Episiotomy", "FR": "Épisiotomie", "ES": "Episiotomía", "PT": "Episiotomia"},
    "a_treat": {"EN": "Unwanted treatments", "FR": "Soins non souhaités", "ES": "Tratamientos no deseados", "PT": "Tratamentos não desejados"},
    
    # Clinical
    "c_skin": {"EN": "Skin-to-skin contact", "FR": "Peau à peau", "ES": "Contacto piel a piel", "PT": "Contato pele a pele"},
    "c_bf": {"EN": "Breastfeeding support", "FR": "Soutien à l'allaitement", "ES": "Apoyo a la lactancia", "PT": "Apoio à amamentação"},
    "c_induce": {"EN": "Labour induction", "FR": "Déclenchement du travail", "ES": "Inducción del parto", "PT": "Indução do parto"},
    "c_pharma": {"EN": "Pain relief received", "FR": "Analgésie reçue", "ES": "Alivio del dolor recibido", "PT": "Alívio da dor recebido"},
    "c_comfort": {"EN": "Non-pharmacological comfort", "FR": "Confort non-pharmacologique", "ES": "Confort no farmacológico", "PT": "Conforto não farmacológico"},
    "c_rooming": {"EN": "Rooming-in (baby with mother)", "FR": "Cohabitation mère-bébé", "ES": "Alojamiento conjunto (bebé con madre)", "PT": "Alojamento conjunto (bebê com mãe)"},
    
    # Satisfaction
    "sat_expect": {"EN": "Before I came here, I expected care to be:", "FR": "Avant de venir ici, je m'attendais à des soins :", "ES": "Antes de venir aquí, esperaba que la atención fuera:", "PT": "Antes de vir aqui, esperava que o cuidado fosse:"},
    "sat_actual": {"EN": "Now, I feel that my care was:", "FR": "Maintenant, j'estime que mes soins étaient :", "ES": "Ahora, siento que mi atención fue:", "PT": "Agora, sinto que meu cuidado foi:"},
    
    # Mistreatment
    "m_verbal": {"EN": "Verbal abuse", "FR": "Violence verbale", "ES": "Abuso verbal", "PT": "Abuso verbal"},
    "m_phys": {"EN": "Physical abuse", "FR": "Violence physique", "ES": "Abuso físico", "PT": "Abuso físico"},
    "m_payment": {"EN": "Informed of costs in advance", "FR": "Informée des coûts à l'avance", "ES": "Informada de los costos por adelantado", "PT": "Informada dos custos antecipadamente"},
    "m_no_cost_info": {"EN": "Did NOT know cost in advance", "FR": "Ne connaissait PAS le coût à l'avance", "ES": "NO conocía el costo por adelantado", "PT": "NÃO sabia o custo antecipadamente"},
    
    # Birth methods
    "vaginal": {"EN": "Vaginal", "FR": "Vaginal", "ES": "Vaginal", "PT": "Vaginal"},
    "assisted": {"EN": "Assisted vaginal", "FR": "Vaginal assisté", "ES": "Vaginal asistido", "PT": "Vaginal assistido"},
    "elective_cs": {"EN": "Elective C/S", "FR": "Césarienne élective", "ES": "Cesárea electiva", "PT": "Cesárea eletiva"},
    "emergency_cs": {"EN": "Emergency C/S", "FR": "Césarienne d'urgence", "ES": "Cesárea de emergencia", "PT": "Cesárea de emergência"},
    "vbac": {"EN": "VBAC", "FR": "AVAC", "ES": "PVDC", "PT": "VBAC"},
}

def t(k, lang):
    """Translate key to language, fallback to EN then key."""
    entry = L.get(k, {})
    return entry.get(lang, entry.get("EN", k))

# ═══════════════════════════════════════════════════════════════════════════════
# VALUE MAPS (Multi-language)
# ═══════════════════════════════════════════════════════════════════════════════
METHOD_MAP = {
    "EN": {1: "Vaginal", 2: "Assisted vaginal (forceps or vacuum)", 3: "Elective/planned caesarean (C/S)", 4: "Emergency caesarean (C/S)", 5: "VBAC", 0: "I don't know"},
    "FR": {1: "Vaginal", 2: "Vaginal assisté (forceps ou ventouse)", 3: "Césarienne élective (planifiée) (C/S)", 4: "Césarienne d'urgence (C/S)", 5: "AVAC", 0: "Je ne sais pas"},
    "ES": {1: "Vaginal", 2: "Vaginal asistido (fórceps o vacío)", 3: "Cesárea electiva/planificada", 4: "Cesárea de emergencia", 5: "PVDC", 0: "No lo sé"},
    "PT": {1: "Vaginal", 2: "Vaginal assistido (fórceps ou vácuo)", 3: "Cesárea eletiva/planejada", 4: "Cesárea de emergência", 5: "VBAC", 0: "Não sei"},
}

EDUCATION_MAP = {
    "EN": {1: "No formal schooling", 2: "Primary", 3: "Secondary", 4: "Higher than secondary"},
    "FR": {1: "Aucune", 2: "Primaire", 3: "Secondaire", 4: "Post-secondaire"},
    "ES": {1: "Sin educación formal", 2: "Primaria", 3: "Secundaria", 4: "Superior"},
    "PT": {1: "Sem escolaridade formal", 2: "Fundamental", 3: "Médio", 4: "Superior"},
}

RISK_MAP = {
    "EN": {1: "Yes", 2: "No", 0: "I don't know"},
    "FR": {1: "Oui", 2: "Non", 0: "Je ne sais pas"},
    "ES": {1: "Sí", 2: "No", 0: "No lo sé"},
    "PT": {1: "Sim", 2: "Não", 0: "Não sei"},
}

LIKERT5_MAP = {
    "EN": {5: "Always", 4: "Most of the time", 3: "Sometimes", 2: "Rarely", 1: "Never", 0: "I don't know/not applicable"},
    "FR": {5: "Toujours", 4: "La plupart du temps", 3: "Quelquefois", 2: "Rarement", 1: "Jamais", 0: "Je ne sais pas/non applicable"},
    "ES": {5: "Siempre", 4: "La mayoría del tiempo", 3: "A veces", 2: "Raramente", 1: "Nunca", 0: "No sé/no aplica"},
    "PT": {5: "Sempre", 4: "Na maioria das vezes", 3: "Às vezes", 2: "Raramente", 1: "Nunca", 0: "Não sei/não se aplica"},
}

QUALITY_MAP = {
    "EN": {5: "Very good", 4: "Good", 3: "Neutral", 2: "Poor", 1: "Very bad", 0: "I don't know"},
    "FR": {5: "Très bonne", 4: "Bon", 3: "Neutre", 2: "Mauvaise", 1: "Très mauvaise", 0: "Je ne sais pas"},
    "ES": {5: "Muy buena", 4: "Buena", 3: "Neutral", 2: "Mala", 1: "Muy mala", 0: "No lo sé"},
    "PT": {5: "Muito bom", 4: "Bom", 3: "Neutro", 2: "Ruim", 1: "Muito ruim", 0: "Não sei"},
}

QUALITY_ORDER = {
    "EN": ["Very bad", "Poor", "Neutral", "Good", "Very good", "I don't know"],
    "FR": ["Très mauvaise", "Mauvaise", "Neutre", "Bon", "Très bonne", "Je ne sais pas"],
    "ES": ["Muy mala", "Mala", "Neutral", "Buena", "Muy buena", "No lo sé"],
    "PT": ["Muito ruim", "Ruim", "Neutro", "Bom", "Muito bom", "Não sei"],
}

DECISIONS_MAP = {
    "EN": {1: "Yes, included with enough information", 2: "Yes, included but not enough information", 3: "Sometimes I was included", 4: "No, I was not included", 0: "I don't know/not applicable"},
    "FR": {1: "Oui, incluse avec suffisamment d'informations", 2: "Oui, incluse mais pas assez d'informations", 3: "J'ai parfois été incluse", 4: "Non, je n'ai pas été incluse", 0: "Je ne sais pas/non applicable"},
    "ES": {1: "Sí, incluida con suficiente información", 2: "Sí, incluida pero sin suficiente información", 3: "A veces fui incluida", 4: "No, no fui incluida", 0: "No sé/no aplica"},
    "PT": {1: "Sim, incluída com informação suficiente", 2: "Sim, incluída mas sem informação suficiente", 3: "Às vezes fui incluída", 4: "Não, não fui incluída", 0: "Não sei/não se aplica"},
}

EPI_MAP = {
    "EN": {1: "Yes, with my consent", 2: "Yes, without full explanation or consent", 3: "No, because I declined", 4: "No, staff did not recommend it"},
    "FR": {1: "Oui, avec mon consentement", 2: "Oui, sans explication complète ou consentement", 3: "Non, parce que j'ai refusé", 4: "Non, le personnel ne l'a pas recommandé"},
    "ES": {1: "Sí, con mi consentimiento", 2: "Sí, sin explicación completa o consentimiento", 3: "No, porque lo rechacé", 4: "No, el personal no lo recomendó"},
    "PT": {1: "Sim, com meu consentimento", 2: "Sim, sem explicação completa ou consentimento", 3: "Não, porque recusei", 4: "Não, a equipe não recomendou"},
}

EXAM_MAP = {
    "EN": {1: "Never without my consent", 2: "Rarely without consent", 3: "Sometimes without consent", 4: "Frequently without consent", 5: "Always without consent"},
    "FR": {1: "Jamais sans mon consentement", 2: "Rarement sans consentement", 3: "Parfois sans consentement", 4: "Fréquemment sans consentement", 5: "Toujours sans consentement"},
    "ES": {1: "Nunca sin mi consentimiento", 2: "Raramente sin consentimiento", 3: "A veces sin consentimiento", 4: "Frecuentemente sin consentimiento", 5: "Siempre sin consentimiento"},
    "PT": {1: "Nunca sem meu consentimento", 2: "Raramente sem consentimento", 3: "Às vezes sem consentimento", 4: "Frequentemente sem consentimento", 5: "Sempre sem consentimento"},
}

TREAT_MAP = {
    "EN": {1: "Yes", 2: "No", 0: "I don't know"},
    "FR": {1: "Oui", 2: "Non", 0: "Je ne sais pas"},
    "ES": {1: "Sí", 2: "No", 0: "No lo sé"},
    "PT": {1: "Sim", 2: "Não", 0: "Não sei"},
}

BF_MAP = {
    "EN": {1: "No, I did not breastfeed", 2: "No, I did not need help", 3: "No, I needed help but did not receive it", 4: "Yes, I was helped but not enough", 5: "Yes, I received the help I needed", 0: "I don't know"},
    "FR": {1: "Non, je n'ai pas allaité", 2: "Non, pas besoin d'aide", 3: "Non, j'avais besoin d'aide mais n'en ai reçu aucune", 4: "Oui, j'ai reçu de l'aide mais insuffisamment", 5: "Oui, j'ai reçu l'aide nécessaire", 0: "Je ne sais pas"},
    "ES": {1: "No, no amamanté", 2: "No, no necesité ayuda", 3: "No, necesitaba ayuda pero no la recibí", 4: "Sí, me ayudaron pero no lo suficiente", 5: "Sí, recibí la ayuda que necesitaba", 0: "No lo sé"},
    "PT": {1: "Não, não amamentei", 2: "Não, não precisei de ajuda", 3: "Não, precisei de ajuda mas não recebi", 4: "Sim, fui ajudada mas não o suficiente", 5: "Sim, recebi a ajuda necessária", 0: "Não sei"},
}

SKIN_MAP = {
    "EN": {1: "Yes", 2: "Yes, but not immediate", 3: "Yes, but less than an hour", 4: "No", 5: "No, chose not to or could not", 6: "I don't know"},
    "FR": {1: "Oui", 2: "Oui, mais pas immédiat", 3: "Oui, moins d'une heure", 4: "Non", 5: "Non, ne souhaitait pas", 6: "Je ne sais pas"},
    "ES": {1: "Sí", 2: "Sí, pero no inmediato", 3: "Sí, pero menos de una hora", 4: "No", 5: "No, elegí no hacerlo o no pude", 6: "No lo sé"},
    "PT": {1: "Sim", 2: "Sim, mas não imediato", 3: "Sim, mas menos de uma hora", 4: "Não", 5: "Não, optei por não ou não pude", 6: "Não sei"},
}

INDUCE_MAP = {
    "EN": {1: "No", 2: "Yes", 0: "I don't know"},
    "FR": {1: "Non", 2: "Oui", 0: "Je ne sais pas"},
    "ES": {1: "No", 2: "Sí", 0: "No lo sé"},
    "PT": {1: "Não", 2: "Sim", 0: "Não sei"},
}

PHARMA_MAP = {
    "EN": {1: "No, I did not want any", 2: "No, even though I wanted it", 3: "Yes, but I received it too late", 4: "Yes, when I wanted it", 5: "No, facility does not offer it", 0: "I don't know"},
    "FR": {1: "Non, je n'en voulais pas", 2: "Non, même si je le voulais", 3: "Oui, mais reçu trop tard", 4: "Oui, quand je le voulais", 5: "Non, non disponible dans l'établissement", 0: "Je ne sais pas"},
    "ES": {1: "No, no lo quería", 2: "No, aunque lo quería", 3: "Sí, pero lo recibí muy tarde", 4: "Sí, cuando lo quise", 5: "No, el centro no lo ofrece", 0: "No lo sé"},
    "PT": {1: "Não, não quis", 2: "Não, embora quisesse", 3: "Sim, mas recebi tarde demais", 4: "Sim, quando quis", 5: "Não, a unidade não oferece", 0: "Não sei"},
}

COMFORT_MAP = {
    "EN": {1: "Yes, and I used them", 2: "Yes, but I did not use them", 3: "No, none were suggested", 0: "I don't know"},
    "FR": {1: "Oui, et je les ai utilisés", 2: "Oui, mais je ne les ai pas utilisés", 3: "Non, aucune mesure proposée", 0: "Je ne sais pas"},
    "ES": {1: "Sí, y los usé", 2: "Sí, pero no los usé", 3: "No, ninguno fue sugerido", 0: "No lo sé"},
    "PT": {1: "Sim, e usei", 2: "Sim, mas não usei", 3: "Não, nenhum foi sugerido", 0: "Não sei"},
}

ROOMING_MAP = {
    "EN": {4: "Yes, with me/us most of the time", 1: "No, baby was sick/sent to unit", 2: "No, baby was not with me/us", 3: "No, I did not want baby with me", 0: "I don't know"},
    "FR": {4: "Oui, avec moi/nous la plupart du temps", 1: "Non, bébé malade/envoyé en néonatalogie", 2: "Non, bébé pas avec moi/nous", 3: "Non, je ne souhaitais pas", 0: "Je ne sais pas"},
    "ES": {4: "Sí, conmigo/nosotros la mayor parte del tiempo", 1: "No, el bebé estaba enfermo/enviado a unidad", 2: "No, el bebé no estaba conmigo/nosotros", 3: "No, no quería al bebé conmigo", 0: "No lo sé"},
    "PT": {4: "Sim, comigo/conosco a maior parte do tempo", 1: "Não, bebê doente/enviado para UTI", 2: "Não, bebê não estava comigo/conosco", 3: "Não, não quis o bebê comigo", 0: "Não sei"},
}

VERBAL_MAP = {
    "EN": {1: "Never", 2: "Rarely", 3: "Sometimes", 4: "Most of the time", 5: "Always", 0: "I don't know/not applicable"},
    "FR": {1: "Jamais", 2: "Rarement", 3: "Quelquefois", 4: "La plupart du temps", 5: "Toujours", 0: "Je ne sais pas/non applicable"},
    "ES": {1: "Nunca", 2: "Raramente", 3: "A veces", 4: "La mayoría del tiempo", 5: "Siempre", 0: "No sé/no aplica"},
    "PT": {1: "Nunca", 2: "Raramente", 3: "Às vezes", 4: "Na maioria das vezes", 5: "Sempre", 0: "Não sei/não se aplica"},
}

PHYS_MAP = {
    "EN": {1: "Never", 2: "Rarely", 3: "Sometimes", 4: "Most of the time", 5: "Always", 0: "I don't know/not applicable"},
    "FR": {1: "Jamais", 2: "De temps en temps", 3: "Quelquefois", 4: "La plupart du temps", 5: "Toujours", 0: "Je ne sais pas/non applicable"},
    "ES": {1: "Nunca", 2: "Raramente", 3: "A veces", 4: "La mayoría del tiempo", 5: "Siempre", 0: "No sé/no aplica"},
    "PT": {1: "Nunca", 2: "Raramente", 3: "Às vezes", 4: "Na maioria das vezes", 5: "Sempre", 0: "Não sei/não se aplica"},
}

PAYMENT_MAP = {
    "EN": {1: "Yes", 2: "No", 3: "No, care was free or covered by insurance", 0: "I don't know"},
    "FR": {1: "Oui", 2: "Non", 3: "Non, soins gratuits ou couverts par l'assurance", 0: "Je ne sais pas"},
    "ES": {1: "Sí", 2: "No", 3: "No, la atención fue gratuita o cubierta por seguro", 0: "No lo sé"},
    "PT": {1: "Sim", 2: "Não", 3: "Não, atendimento gratuito ou coberto por plano", 0: "Não sei"},
}

LIKERT_QS = {
    "EN": {"introduction": "Staff introduced themselves", "spoke": "Staff spoke understandably",
           "communication": "Comfortable asking questions", "privacy": "Privacy protected",
           "respect": "Treated respectfully", "values": "Beliefs & choices respected",
           "positive": "Encouraged to feel empowered", "morale": "Staff happy & supported", "coop": "Coordinated care"},
    "FR": {"introduction": "Le personnel s'est présenté", "spoke": "Le personnel parlait clairement",
           "communication": "À l'aise pour poser des questions", "privacy": "Intimité protégée",
           "respect": "Traitée avec respect", "values": "Croyances et choix respectés",
           "positive": "Encouragée à être autonome", "morale": "Personnel heureux et supporté", "coop": "Soins coordonnés"},
    "ES": {"introduction": "El personal se presentó", "spoke": "El personal habló claramente",
           "communication": "Cómoda haciendo preguntas", "privacy": "Privacidad protegida",
           "respect": "Tratada con respeto", "values": "Creencias y opciones respetadas",
           "positive": "Animada a sentirse empoderada", "morale": "Personal feliz y apoyado", "coop": "Atención coordinada"},
    "PT": {"introduction": "A equipe se apresentou", "spoke": "A equipe falou claramente",
           "communication": "Confortável fazendo perguntas", "privacy": "Privacidade protegida",
           "respect": "Tratada com respeito", "values": "Crenças e escolhas respeitadas",
           "positive": "Encorajada a se sentir empoderada", "morale": "Equipe feliz e apoiada", "coop": "Cuidado coordenado"},
}

EMOTION_LABELS = {
    "EN": {1: "Competence", 2: "Incapable", 3: "Anxious", 4: "Supported", 5: "Exhausted", 6: "Active",
           7: "Relaxed", 8: "Passive", 9: "Responsible", 10: "Dependent", 11: "Secure", 12: "Excluded"},
    "FR": {1: "Compétence", 2: "Incapable", 3: "Anxieuse", 4: "Soutenue", 5: "Épuisée", 6: "Active",
           7: "Détendue", 8: "Passive", 9: "Responsable", 10: "Dépendante", 11: "Sécurisée", 12: "Mise à l'écart"},
    "ES": {1: "Competencia", 2: "Incapaz", 3: "Ansiosa", 4: "Apoyada", 5: "Agotada", 6: "Activa",
           7: "Relajada", 8: "Pasiva", 9: "Responsable", 10: "Dependiente", 11: "Segura", 12: "Excluida"},
    "PT": {1: "Competência", 2: "Incapaz", 3: "Ansiosa", 4: "Apoiada", 5: "Exausta", 6: "Ativa",
           7: "Relaxada", 8: "Passiva", 9: "Responsável", 10: "Dependente", 11: "Segura", 12: "Excluída"},
}

INFO_LABELS = {
    "EN": {1: "Caring for my new baby", 2: "Advice about family planning",
           3: "Warning signs requiring consultation", 4: "Where to go for follow-up care"},
    "FR": {1: "Prendre soin de mon nouveau-né", 2: "Conseils sur la planification familiale",
           3: "Signes à surveiller nécessitant consultation", 4: "Où aller pour les soins de suivi"},
    "ES": {1: "Cuidado de mi nuevo bebé", 2: "Consejos sobre planificación familiar",
           3: "Señales de alerta que requieren consulta", 4: "Dónde ir para atención de seguimiento"},
    "PT": {1: "Cuidados com meu novo bebê", 2: "Orientações sobre planejamento familiar",
           3: "Sinais de alerta que requerem consulta", 4: "Onde buscar acompanhamento"},
}

POSITIVE_EMO = {
    "EN": {"Competence", "Supported", "Active", "Relaxed", "Responsible", "Secure"},
    "FR": {"Compétence", "Soutenue", "Active", "Détendue", "Responsable", "Sécurisée"},
    "ES": {"Competencia", "Apoyada", "Activa", "Relajada", "Responsable", "Segura"},
    "PT": {"Competência", "Apoiada", "Ativa", "Relaxada", "Responsável", "Segura"},
}

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
    
    for col, mp in [("method", METHOD_MAP.get(lang, METHOD_MAP["EN"])),
                    ("education", EDUCATION_MAP.get(lang, EDUCATION_MAP["EN"])),
                    ("risk", RISK_MAP.get(lang, RISK_MAP["EN"])),
                    ("satisfaction", QUALITY_MAP.get(lang, QUALITY_MAP["EN"])),
                    ("expect", QUALITY_MAP.get(lang, QUALITY_MAP["EN"])),
                    ("decisions", DECISIONS_MAP.get(lang, DECISIONS_MAP["EN"])),
                    ("epi", EPI_MAP.get(lang, EPI_MAP["EN"])),
                    ("exam", EXAM_MAP.get(lang, EXAM_MAP["EN"])),
                    ("bf", BF_MAP.get(lang, BF_MAP["EN"])),
                    ("induce", INDUCE_MAP.get(lang, INDUCE_MAP["EN"])),
                    ("treat", TREAT_MAP.get(lang, TREAT_MAP["EN"])),
                    ("pharma", PHARMA_MAP.get(lang, PHARMA_MAP["EN"])),
                    ("comfort", COMFORT_MAP.get(lang, COMFORT_MAP["EN"])),
                    ("rooming", ROOMING_MAP.get(lang, ROOMING_MAP["EN"])),
                    ("verbal", VERBAL_MAP.get(lang, VERBAL_MAP["EN"])),
                    ("phys", PHYS_MAP.get(lang, PHYS_MAP["EN"])),
                    ("payment", PAYMENT_MAP.get(lang, PAYMENT_MAP["EN"]))]:
        if col in df.columns:
            df[col] = to_int(df[col])
            df[col + "_label"] = df[col].map(mp).fillna("?")
    
    lq = LIKERT_QS.get(lang, LIKERT_QS["EN"])
    l5 = LIKERT5_MAP.get(lang, LIKERT5_MAP["EN"])
    for col in lq:
        if col in df.columns:
            df[col] = to_int(df[col])
            df[col + "_label"] = df[col].map(l5).fillna("?")
    
    if "skin" in df.columns:
        df["skin_int"] = first_token_int(df["skin"])
        df["skin_label"] = df["skin_int"].map(SKIN_MAP.get(lang, SKIN_MAP["EN"])).fillna("?")
    
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


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: clean plotly layout
# ═══════════════════════════════════════════════════════════════════════════════
def clean_layout(fig, title="", height=280, legend_below=False):
    """Apply consistent clean layout."""
    b_margin = 80 if legend_below else 20
    layout = dict(
        title=dict(
            text=title,
            font=dict(size=13, family="DM Serif Display, serif", color="#1a1a1a"),
            x=0, xanchor="left", y=0.98, yanchor="top",
            pad=dict(b=6, t=0)
        ),
        margin=dict(t=64, b=b_margin, l=8, r=8),
        height=height,
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="DM Sans, sans-serif", size=11),
    )
    if legend_below:
        layout["legend"] = dict(
            orientation="h", y=-0.18, x=0.5, xanchor="center",
            font=dict(size=10), tracegroupgap=4
        )
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
    border-radius: 20px;
    padding: 32px 44px;
    margin-bottom: 8px;
    position: relative;
    overflow: hidden;
}}
.hero::before {{
    content:'';
    position:absolute;top:0;left:0;right:0;bottom:0;
    background: radial-gradient(ellipse at 80% 50%, rgba(255,255,255,0.08) 0%, transparent 60%);
}}
.hero-title {{
    font-family:'DM Serif Display',serif;
    font-size:2.1rem; font-weight:400; color:white;
    margin:0 0 4px 0; line-height:1.2;
}}
.hero-caption {{
    font-size:0.85rem; color:rgba(255,255,255,0.78); margin:0 0 24px 0;
}}
.hero-stats {{
    display:flex; gap:12px; flex-wrap:nowrap;
}}
.hero-stat {{
    text-align:center;
    background:rgba(255,255,255,0.12);
    border-radius:14px;
    padding:14px 12px;
    backdrop-filter:blur(4px);
    flex:1; min-width:0;
}}
.hero-stat-num {{
    font-size:1.7rem; font-weight:700; color:white; line-height:1;
    font-family:'DM Serif Display',serif;
}}
.hero-stat-label {{
    font-size:0.66rem; color:rgba(255,255,255,0.8);
    margin-top:5px; line-height:1.3;
}}
.hero-stat-bad {{ background:rgba(213,94,0,0.25); }}

.section-title {{
    font-family:'DM Serif Display',serif;
    font-size:1.25rem; color:#1a1a1a;
    border-left:4px solid {TEAL};
    padding-left:14px; margin:32px 0 14px 0;
}}

.comparison-card {{
    background: #f8faf9;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
}}

.modebar-container {{top: auto !important; bottom: 4px !important;}}
.modebar {{top: auto !important; bottom: 0 !important;}}
</style>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR & DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════════
col_lang = st.columns([6, 1])[1]
available_langs = ["EN", "FR", "ES", "PT"]
lang = col_lang.radio("", available_langs, horizontal=True, label_visibility="collapsed")

with st.spinner("Loading data..." if lang == "EN" else "Chargement..." if lang == "FR" else "Cargando..." if lang == "ES" else "Carregando..."):
    raw = load_all_facilities()

if raw.empty:
    st.warning("No data." if lang == "EN" else "Aucune donnée." if lang == "FR" else "Sin datos." if lang == "ES" else "Sem dados.")
    st.stop()

df = prep(raw, lang)

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR FILTERS
# ═══════════════════════════════════════════════════════════════════════════════
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

# Facility selection
facilities_available = df["_facility"].unique().tolist()
compare_mode = st.sidebar.checkbox(t("compare_mode", lang), value=len(facilities_available) > 1)

if compare_mode:
    selected_facilities = st.sidebar.multiselect(
        t("facility", lang),
        options=facilities_available,
        default=facilities_available
    )
    if selected_facilities:
        df = df[df["_facility"].isin(selected_facilities)]
else:
    selected_facility = st.sidebar.selectbox(
        t("facility", lang),
        options=[t("all", lang)] + facilities_available
    )
    if selected_facility != t("all", lang):
        df = df[df["_facility"] == selected_facility]

# Date range filter
if "_submission_time" in df.columns and df["_submission_time"].notna().any():
    import calendar
    mn = df["_submission_time"].min()
    mx = df["_submission_time"].max()
    years = sorted(df["_submission_time"].dt.year.dropna().unique().astype(int).tolist())
    months_map = {
        "EN": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "FR": ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun", "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"],
        "ES": ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
        "PT": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"],
    }
    months = months_map.get(lang, months_map["EN"])
    
    st.sidebar.markdown(f"**{t('date_range', lang)}**")
    dc1, dc2 = st.sidebar.columns(2)
    start_year = dc1.selectbox("", years, index=0, key="sy", label_visibility="collapsed")
    start_month = dc2.selectbox("", months, index=mn.month - 1, key="sm", label_visibility="collapsed")
    dc3, dc4 = st.sidebar.columns(2)
    end_year = dc3.selectbox("", years, index=len(years) - 1, key="ey", label_visibility="collapsed")
    end_month = dc4.selectbox("", months, index=mx.month - 1, key="em", label_visibility="collapsed")
    
    sm_idx = months.index(start_month) + 1
    em_idx = months.index(end_month) + 1
    start_dt = datetime(start_year, sm_idx, 1).date()
    end_dt = datetime(end_year, em_idx, calendar.monthrange(end_year, em_idx)[1]).date()
    df = df[(df["_submission_time"].dt.date >= start_dt) & (df["_submission_time"].dt.date <= end_dt)]

# Other filters
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
# Payment: value 2 means "No" (did not know cost in advance)
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
# FACILITY COMPARISON SECTION (when compare_mode is ON)
# ═══════════════════════════════════════════════════════════════════════════════
if compare_mode and "_facility" in df.columns and df["_facility"].nunique() > 1:
    st.markdown(f'<div class="section-title">{t("s_comparison", lang)}</div>', unsafe_allow_html=True)
    
    # ─────────────────────────────────────────────────────────────────────────
    # CS Rates by Facility and Country
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown(f'<div class="section-title">{t("s_cs_rates", lang)}</div>', unsafe_allow_html=True)
    
    if "method" in df.columns:
        # Calculate CS rates
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
                "Facility": fac,
                "Country": country,
                "n": n,
                t("vaginal", lang): vaginal,
                t("assisted", lang): assisted,
                t("elective_cs", lang): elective_cs,
                t("emergency_cs", lang): emergency_cs,
                t("vbac", lang): vbac,
            })
        
        if cs_data:
            cs_df = pd.DataFrame(cs_data)
            
            # Grouped bar chart
            melt_cols = [t("vaginal", lang), t("assisted", lang), t("elective_cs", lang), 
                         t("emergency_cs", lang), t("vbac", lang)]
            cs_melt = cs_df.melt(id_vars=["Facility", "Country", "n"], value_vars=melt_cols,
                                  var_name="Birth Method", value_name="Percentage")
            
            fig = px.bar(cs_melt, x="Facility", y="Percentage", color="Birth Method",
                         barmode="group", color_discrete_sequence=FACILITY_COLORS,
                         hover_data={"Country": True, "n": True})
            fig.update_layout(
                height=400,
                margin=dict(t=32, b=80, l=8, r=8),
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="DM Sans, sans-serif"),
                legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
                yaxis=dict(title="%", gridcolor="#eeeeee"),
                xaxis=dict(title="", showgrid=False),
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Demographics Comparison Table
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown(f'<div class="section-title">{t("s_demographics", lang)}</div>', unsafe_allow_html=True)
    
    demo_data = []
    for fac in df["_facility"].unique():
        fac_df = df[df["_facility"] == fac]
        country = fac_df["_country"].iloc[0] if "_country" in fac_df.columns else "Unknown"
        n = len(fac_df)
        
        # Gestational weeks
        weeks_mean = fac_df["weeks_clean"].mean() if "weeks_clean" in fac_df.columns else np.nan
        
        # Age stats
        age_mean = fac_df["age"].mean() if "age" in fac_df.columns else np.nan
        age_min = fac_df["age"].min() if "age" in fac_df.columns else np.nan
        age_max = fac_df["age"].max() if "age" in fac_df.columns else np.nan
        
        # Staff equipped (morale question as proxy)
        staff_ok = (fac_df["morale"].isin([4, 5])).sum() / n * 100 if "morale" in fac_df.columns and n > 0 else np.nan
        
        # Vaginal exam without consent
        exam_nc_pct = (fac_df["exam"].isin([2, 3, 4, 5])).sum() / n * 100 if "exam" in fac_df.columns and n > 0 else np.nan
        
        # Episiotomy without consent
        epi_nc_pct = (fac_df["epi"] == 2).sum() / n * 100 if "epi" in fac_df.columns and n > 0 else np.nan
        
        # Unwanted treatments
        treat_pct = (fac_df["treat"] == 1).sum() / n * 100 if "treat" in fac_df.columns and n > 0 else np.nan
        
        # Verbal abuse (any: 2-5)
        verbal_pct = (fac_df["verbal"].isin([2, 3, 4, 5])).sum() / n * 100 if "verbal" in fac_df.columns and n > 0 else np.nan
        
        # Physical abuse (any: 2-5)
        phys_pct = (fac_df["phys"].isin([2, 3, 4, 5])).sum() / n * 100 if "phys" in fac_df.columns and n > 0 else np.nan
        
        # Did not know cost (payment == 2)
        no_cost_pct = (fac_df["payment"] == 2).sum() / n * 100 if "payment" in fac_df.columns and n > 0 else np.nan
        
        demo_data.append({
            "Facility": fac,
            "Country": country,
            "n": n,
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
# CARE JOURNEY (Sankey) — Now with PERCENTAGES
# ═══════════════════════════════════════════════════════════════════════════════
if "risk" in df.columns and "method" in df.columns and "skin_int" in df.columns:
    st.markdown(f'<div class="section-title">{t("s_care_journey", lang)}</div>', unsafe_allow_html=True)
    
    sk_title = {"EN": "Care Journey: Risk Profile → Birth Method → Skin-to-Skin Contact (% of women)",
                "FR": "Parcours : Profil de risque → Mode d'accouchement → Peau à peau (% des femmes)",
                "ES": "Trayectoria: Perfil de riesgo → Modo de parto → Piel a piel (% de mujeres)",
                "PT": "Jornada: Perfil de risco → Tipo de parto → Pele a pele (% das mulheres)"}[lang]
    
    risk_lbl = {1: {"EN": "High-risk", "FR": "Grossesse à risque", "ES": "Alto riesgo", "PT": "Alto risco"}[lang],
                2: {"EN": "Low-risk", "FR": "Grossesse normale", "ES": "Bajo riesgo", "PT": "Baixo risco"}[lang]}
    method_lbl = {1: METHOD_MAP[lang][1], 2: METHOD_MAP[lang][2],
                  3: METHOD_MAP[lang][3], 4: METHOD_MAP[lang][4]}
    skin_lbl = {1: {"EN": "✓ Immediate skin-to-skin", "FR": "✓ Peau à peau immédiat", "ES": "✓ Piel a piel inmediato", "PT": "✓ Pele a pele imediato"}[lang],
                0: {"EN": "✗ Not immediate / No", "FR": "✗ Pas immédiat / Non", "ES": "✗ No inmediato / No", "PT": "✗ Não imediato / Não"}[lang]}
    
    fdf = df[df["risk"].isin([1, 2]) & df["method"].isin([1, 2, 3, 4])].copy()
    fdf["skin_bin"] = (fdf["skin_int"] == 1).astype(int)
    total_n = len(fdf)
    
    if total_n > 0:
        risk_nodes = [risk_lbl[1], risk_lbl[2]]
        method_nodes = [method_lbl[k] for k in [1, 2, 3, 4]]
        skin_nodes = [skin_lbl[1], skin_lbl[0]]
        all_nodes = risk_nodes + method_nodes + skin_nodes
        R, M, S = 0, 2, 6  # offsets
        
        sources, targets, values, colors, customdata = [], [], [], [], []
        
        # risk → method
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
        
        # method → skin
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
            node=dict(pad=20, thickness=24,
                      line=dict(color="white", width=0.5),
                      label=all_nodes, color=node_colors,
                      hovertemplate="%{label}<br>%{value} women<extra></extra>"),
            link=dict(source=sources, target=targets, value=values, color=colors,
                      customdata=customdata,
                      hovertemplate="%{source.label} → %{target.label}<br>%{value} women (%{customdata})<extra></extra>")
        ))
        fig.update_traces(textfont=dict(size=13, family="DM Sans, sans-serif", color="#1a1a1a"))
        fig.update_layout(
            title=dict(text=sk_title,
                       font=dict(size=13, family="DM Serif Display, serif", color="#1a1a1a"),
                       x=0, xanchor="left"),
            margin=dict(t=64, b=16, l=8, r=8), height=420,
            paper_bgcolor="white",
            font=dict(family="DM Sans, sans-serif", size=11),
        )
        st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# EMOTIONS — Two views: Original and Adjusted (Exhausted filtered)
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(f'<div class="section-title">{t("s_emotions", lang)}</div>', unsafe_allow_html=True)
st.caption(t("emo_note", lang))

if "emotion" in df.columns:
    emo_labels = EMOTION_LABELS.get(lang, EMOTION_LABELS["EN"])
    pos = POSITIVE_EMO.get(lang, POSITIVE_EMO["EN"])
    
    # Original view
    counts = parse_multiselect(df["emotion"], list(emo_labels.keys()))
    rows = [{"Emotion": lbl, "Pct": round(counts[k] / len(df) * 100, 1),
             "Type": t("positive", lang) if lbl in pos else t("negative", lang)}
            for k, lbl in emo_labels.items()]
    edf = pd.DataFrame(rows).sort_values("Pct", ascending=True)
    
    tab1, tab2 = st.tabs([t("s_emotions", lang), t("s_emotions_adjusted", lang)])
    
    with tab1:
        fig = px.bar(edf, x="Pct", y="Emotion", color="Type", orientation="h",
                     color_discrete_map={t("positive", lang): TEAL, t("negative", lang): VERMILION},
                     labels={"Pct": t("pct", lang), "Emotion": ""})
        fig.update_layout(
            legend=dict(orientation="h", y=-0.16, x=0.5, xanchor="center", font=dict(size=11)),
            margin=dict(t=16, b=80, l=8, r=8), height=440,
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="DM Sans, sans-serif"))
        fig.update_xaxes(gridcolor="#eeeeee")
        fig.update_yaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.caption(t("emo_adjusted_note", lang))
        
        # Adjusted: exclude "Exhausted" unless it was the ONLY emotion selected
        exhausted_key = 5  # Exhausted is key 5
        parsed_per_row = parse_multiselect_per_row(df["emotion"])
        
        adjusted_counts = {k: 0 for k in emo_labels.keys()}
        valid_responses = 0
        
        for keys in parsed_per_row:
            if not keys:
                continue
            # If exhausted is selected AND there are other emotions, skip exhausted
            if exhausted_key in keys:
                if len(keys) == 1:
                    # Exhausted was the only emotion — include it
                    adjusted_counts[exhausted_key] += 1
                    valid_responses += 1
                else:
                    # Include all others except exhausted
                    for k in keys:
                        if k != exhausted_key:
                            adjusted_counts[k] += 1
                    valid_responses += 1
            else:
                for k in keys:
                    adjusted_counts[k] += 1
                valid_responses += 1
        
        if valid_responses > 0:
            adj_rows = [{"Emotion": lbl, "Pct": round(adjusted_counts[k] / valid_responses * 100, 1),
                         "Type": t("positive", lang) if lbl in pos else t("negative", lang)}
                        for k, lbl in emo_labels.items()]
            adj_edf = pd.DataFrame(adj_rows).sort_values("Pct", ascending=True)
            
            fig2 = px.bar(adj_edf, x="Pct", y="Emotion", color="Type", orientation="h",
                          color_discrete_map={t("positive", lang): TEAL, t("negative", lang): VERMILION},
                          labels={"Pct": t("pct", lang), "Emotion": ""})
            fig2.update_layout(
                legend=dict(orientation="h", y=-0.16, x=0.5, xanchor="center", font=dict(size=11)),
                margin=dict(t=16, b=80, l=8, r=8), height=440,
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="DM Sans, sans-serif"))
            fig2.update_xaxes(gridcolor="#eeeeee")
            fig2.update_yaxes(showgrid=False)
            st.plotly_chart(fig2, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# MISTREATMENT & RESPECT — Including "Did not know cost"
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(f'<div class="section-title">{t("s_mistreat", lang)}</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

# Verbal abuse
if "verbal_label" in df.columns:
    vc = df["verbal_label"].value_counts().reset_index()
    vc.columns = ["r", "n"]
    fig = px.bar(vc, x="n", y="r", orientation="h", color_discrete_sequence=[VERMILION],
                 labels={"r": "", "n": t("responses", lang)})
    fig = clean_layout(fig, title=t("m_verbal", lang), height=260)
    fig.update_xaxes(gridcolor="#eeeeee")
    fig.update_yaxes(showgrid=False)
    c1.plotly_chart(fig, use_container_width=True)

# Physical abuse
if "phys_label" in df.columns:
    vc = df["phys_label"].value_counts().reset_index()
    vc.columns = ["r", "n"]
    fig = px.bar(vc, x="n", y="r", orientation="h", color_discrete_sequence=[VERMILION],
                 labels={"r": "", "n": t("responses", lang)})
    fig = clean_layout(fig, title=t("m_phys", lang), height=260)
    fig.update_xaxes(gridcolor="#eeeeee")
    fig.update_yaxes(showgrid=False)
    c2.plotly_chart(fig, use_container_width=True)

# Payment/cost info
if "payment_label" in df.columns:
    vc = df["payment_label"].value_counts().reset_index()
    vc.columns = ["r", "n"]
    fig = px.bar(vc, x="n", y="r", orientation="h", color_discrete_sequence=[BLUISH],
                 labels={"r": "", "n": t("responses", lang)})
    fig = clean_layout(fig, title=t("m_payment", lang), height=260)
    fig.update_xaxes(gridcolor="#eeeeee")
    fig.update_yaxes(showgrid=False)
    c3.plotly_chart(fig, use_container_width=True)

# % who did NOT know cost (highlight metric)
if "payment" in df.columns and len(df) > 0:
    no_cost_n = (df["payment"] == 2).sum()
    no_cost_pct = no_cost_n / len(df) * 100
    c4.markdown(f"""
    <div style="background: rgba(213,94,0,0.1); border-radius: 12px; padding: 24px; text-align: center; height: 200px; display: flex; flex-direction: column; justify-content: center;">
        <div style="font-size: 2.5rem; font-weight: 700; color: {VERMILION}; font-family: 'DM Serif Display', serif;">{no_cost_pct:.1f}%</div>
        <div style="font-size: 0.85rem; color: #666; margin-top: 8px;">{t("m_no_cost_info", lang)}</div>
        <div style="font-size: 0.75rem; color: #999; margin-top: 4px;">(n={no_cost_n})</div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# Continue with remaining panels from original code...
# (Timeline, Trends, Profile, Likert, Autonomy, Clinical, Satisfaction, Discharge)
# ═══════════════════════════════════════════════════════════════════════════════

# PANEL: Timeline
st.markdown(f'<div class="section-title">{t("s_timeline", lang)}</div>', unsafe_allow_html=True)
if "_submission_time" in df.columns and df["_submission_time"].notna().any():
    freq_opts = [t("grp_month", lang), t("grp_week", lang), t("grp_day", lang)]
    freq = st.radio(t("grp_by", lang), freq_opts, horizontal=True)
    fmap = {t("grp_day", lang): "D", t("grp_week", lang): "W", t("grp_month", lang): "ME"}
    
    if compare_mode and "_facility" in df.columns:
        # Show by facility
        ts_all = []
        for fac in df["_facility"].unique():
            ts = df[df["_facility"] == fac].set_index("_submission_time").resample(fmap[freq]).size().reset_index(name="n")
            ts["Facility"] = fac
            ts_all.append(ts)
        ts_df = pd.concat(ts_all)
        fig = px.line(ts_df, x="_submission_time", y="n", color="Facility",
                      labels={"_submission_time": "", "n": t("responses", lang)},
                      color_discrete_sequence=FACILITY_COLORS)
    else:
        ts = df.set_index("_submission_time").resample(fmap[freq]).size().reset_index(name="n")
        fig = px.area(ts, x="_submission_time", y="n",
                      labels={"_submission_time": "", "n": t("responses", lang)},
                      color_discrete_sequence=[TEAL])
        fig.update_traces(line_width=2, fillcolor="rgba(0,158,115,0.12)")
    
    fig.update_layout(margin=dict(t=8, b=8, l=8, r=8), height=200,
                      plot_bgcolor="white", paper_bgcolor="white",
                      font=dict(family="DM Sans, sans-serif"))
    st.plotly_chart(fig, use_container_width=True)

# PANEL: Profile
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

# PANEL: Likert scales
st.markdown(f'<div class="section-title">{t("s_likert", lang)}</div>', unsafe_allow_html=True)
st.caption(t("s_likert_cap", lang))
likert_order = list(LIKERT5_MAP.get(lang, LIKERT5_MAP["EN"]).values())
rows = []
lq = LIKERT_QS.get(lang, LIKERT_QS["EN"])
for col, label in lq.items():
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
    fig.update_layout(
        legend=dict(orientation="h", y=-0.22, x=0.5, xanchor="center", font=dict(size=10)),
        margin=dict(t=8, b=110, l=8, r=8), height=480,
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="DM Sans, sans-serif"))
    st.plotly_chart(fig, use_container_width=True)

# PANEL: Autonomy & Consent
st.markdown(f'<div class="section-title">{t("s_autonomy", lang)}</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
if "decisions_label" in df.columns:
    dc = df["decisions_label"].value_counts().reset_index()
    dc.columns = ["r", "n"]
    fig = px.bar(dc, x="n", y="r", orientation="h", color_discrete_sequence=[TEAL],
                 labels={"r": "", "n": t("responses", lang)})
    fig = clean_layout(fig, title=t("a_decisions", lang), height=270)
    fig.update_xaxes(gridcolor="#eeeeee")
    fig.update_yaxes(showgrid=False)
    c1.plotly_chart(fig, use_container_width=True)

if "exam_label" in df.columns:
    ec = df["exam_label"].value_counts().reset_index()
    ec.columns = ["r", "n"]
    color_map = {v: c for v, c in zip(ec["r"].tolist(), [TEAL, SKY, ORANGE, PINK, VERMILION])}
    fig = px.bar(ec, x="n", y="r", orientation="h", color="r", color_discrete_map=color_map,
                 labels={"r": "", "n": ""})
    fig = clean_layout(fig, title=t("a_exam", lang), height=270)
    fig.update_layout(showlegend=False)
    fig.update_xaxes(gridcolor="#eeeeee")
    fig.update_yaxes(showgrid=False)
    c2.plotly_chart(fig, use_container_width=True)

c1, c2 = st.columns(2)
if "epi_label" in df.columns:
    ep = df["epi_label"].value_counts().reset_index()
    ep.columns = ["r", "n"]
    fig = px.bar(ep, x="n", y="r", orientation="h", color_discrete_sequence=[TEAL],
                 labels={"r": "", "n": t("responses", lang)})
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

# PANEL: Clinical Practices
st.markdown(f'<div class="section-title">{t("s_clinical", lang)}</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)

if "skin_label" in df.columns:
    sk = df["skin_label"].value_counts().reset_index()
    sk.columns = ["r", "n"]
    fig = px.bar(sk, x="n", y="r", orientation="h", color_discrete_sequence=[TEAL],
                 labels={"r": "", "n": t("responses", lang)})
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

# PANEL: Satisfaction
st.markdown(f'<div class="section-title">{t("s_satisfaction", lang)}</div>', unsafe_allow_html=True)
if "expect_label" in df.columns and "satisfaction_label" in df.columns:
    c1, c2 = st.columns(2)
    q_order = QUALITY_ORDER.get(lang, QUALITY_ORDER["EN"])
    for col, field, title in [(c1, "expect_label", t("sat_expect", lang)), (c2, "satisfaction_label", t("sat_actual", lang))]:
        vc = df[field].value_counts().reindex(q_order, fill_value=0).reset_index()
        vc.columns = ["r", "n"]
        fig = px.bar(vc, x="r", y="n", color="r", color_discrete_sequence=QUALITY_COLORS,
                     labels={"r": "", "n": t("responses", lang)}, category_orders={"r": q_order})
        fig = clean_layout(fig, title=title, height=310)
        fig.update_layout(showlegend=False)
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(gridcolor="#eeeeee")
        col.plotly_chart(fig, use_container_width=True)

# PANEL: Discharge Info
st.markdown(f'<div class="section-title">{t("s_discharge", lang)}</div>', unsafe_allow_html=True)
if "info" in df.columns:
    info_labels = INFO_LABELS.get(lang, INFO_LABELS["EN"])
    counts = parse_multiselect(df["info"], list(info_labels.keys()))
    rows = [{"Topic": lbl, "Pct": round(counts[k] / len(df) * 100, 1)} for k, lbl in info_labels.items()]
    idf = pd.DataFrame(rows).sort_values("Pct")
    fig = px.bar(idf, x="Pct", y="Topic", orientation="h", color_discrete_sequence=[PINK],
                 labels={"Pct": t("pct", lang), "Topic": ""})
    fig.update_layout(margin=dict(t=16, b=8, l=8, r=8), height=220,
                      plot_bgcolor="white", paper_bgcolor="white",
                      font=dict(family="DM Sans, sans-serif"))
    fig.update_xaxes(gridcolor="#eeeeee")
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(fig, use_container_width=True)

# PANEL: Raw data
with st.expander(t("raw_data", lang)):
    hide = [c for c in df.columns if c.startswith("_") or c == "meta/rootUuid"]
    show = [c for c in df.columns if c not in hide]
    st.dataframe(df[show], use_container_width=True, height=400)
    csv = df[show].to_csv(index=False).encode("utf-8")
    st.download_button(t("download", lang), csv,
                       f"ici_data_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
