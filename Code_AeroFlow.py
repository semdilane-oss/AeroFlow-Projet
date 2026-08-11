# ==============================================================================
# PROJET : AeroFlow - Gestion Intelligente des Flux de Passagers (AIGE)
# APPLICATION WEB STREAMLIT - INTERFACE PROFESSIONNELLE ADVANCED
# ==============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
from gtts import gTTS
import os
import time

# ------------------------------------------------------------------------------
# 1. CONFIGURATION DE LA PAGE & CHARTE GRAPHIQUE
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="AeroFlow — Control Center AIGE",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injection de CSS personnalisé pour le style professionnel
st.markdown("""
<style>
    /* Arrière-plan global et police */
    .main {
        background-color: #0F172A;
        color: #F8FAFC;
    }
    
    /* Titre Principal */
    .title-text {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        background: linear-gradient(90deg, #38BDF8 0%, #818CF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.3rem;
        margin-bottom: 0.2rem;
    }
    
    .subtitle-text {
        color: #94A3B8;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    
    /* Custom KPI Cards */
    .kpi-card {
        background-color: #1E293B;
        border-radius: 12px;
        padding: 1.2rem;
        border-left: 5px solid #38BDF8;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .kpi-card-danger {
        border-left: 5px solid #EF4444;
    }
    .kpi-title {
        color: #94A3B8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .kpi-value {
        color: #F8FAFC;
        font-size: 1.8rem;
        font-weight: 700;
        margin-top: 0.3rem;
    }

    /* Style de la barre latérale */
    section[data-testid="stSidebar"] {
        background-color: #1E293B !important;
        border-right: 1px solid #334155;
    }

    /* Personnalisation du bouton vocal */
    div.stButton > button {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# Fonction pour générer l'annonce vocale
def generer_annonce_vocale(texte):
    for file in os.listdir("."):
        if file.startswith("alerte_temp_") and file.endswith(".mp3"):
            try:
                os.remove(file)
            except Exception:
                pass

    timestamp = int(time.time() * 1000)
    nom_fichier = f"alerte_temp_{timestamp}.mp3"
    tts = gTTS(text=texte, lang='fr')
    tts.save(nom_fichier)
    return nom_fichier, timestamp

# ------------------------------------------------------------------------------
# 2. EN-TÊTE DU DASHBOARD
# ------------------------------------------------------------------------------
st.markdown('<p class="title-text">✈️ AeroFlow — Operations Control Center</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle-text">Aéroport International Gnassingbé Eyadéma (AIGE) | Plateforme de régulation des flux & correspondances</p>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 3. BARRE LATÉRALE (SIDEBAR)
# ------------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/airport.png", width=60)
    st.title("Paramètres & Données")
    
    st.subheader("📥 Source de Données")
    fichier_importe = st.file_uploader("Charger le programme des vols (CSV)", type=["csv"])

    if fichier_importe is not None:
        df = pd.read_csv(fichier_importe)
        st.success("Données actualisées")
    else:
        try:
            df = pd.read_csv("vols_aige.csv")
            st.info("Données par défaut (AIGE)")
        except Exception:
            st.error("Fichier 'vols_aige.csv' introuvable.")
            st.stop()

    st.markdown("---")
    st.subheader("⚙️ Dimensionnement Guichets")
    capacite_agent_heure = st.slider("Capacité de traitement (pax/agent/h)", 20, 60, 40)
    guichets_ouverts = st.slider("Guichets actifs", 1, 10, 4)

# ------------------------------------------------------------------------------
# 4. CALCULS ET LOGIQUE MÉTIER
# ------------------------------------------------------------------------------
df['Passagers_Transit'] = (df['Passagers'] * df['Taux_Transit']).astype(int)
df['Passagers_Terminus'] = df['Passagers'] - df['Passagers_Transit']

# Identification des vols critiques
vols_critiques = df[df['Temps_Escale_Min'] <= 45]

# ------------------------------------------------------------------------------
# 5. INDICATEURS CLÉS (KPIs) AVEC CARTE PERSONNALISÉE
# ------------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Total Passagers Attendus</div>
        <div class="kpi-value">{df['Passagers'].sum():,} pax</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Flux Passagers en Transit</div>
        <div class="kpi-value">{df['Passagers_Transit'].sum():,} pax</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Capacité de Traitement</div>
        <div class="kpi-value">{guichets_ouverts * capacite_agent_heure} pax/h</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    danger_class = "kpi-card-danger" if len(vols_critiques) > 0 else ""
    st.markdown(f"""
    <div class="kpi-card {danger_class}">
        <div class="kpi-title">Vols à Risque (<=45 min)</div>
        <div class="kpi-value" style="color: {'#EF4444' if len(vols_critiques)>0 else '#10B981'};">{len(vols_critiques)} Vol(s)</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 6. GRAPHIQUES INTERACTIFS (THEME PRO DARK)
# ------------------------------------------------------------------------------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Distribution de l'Affluence par Heure")
    fig_affluence = px.bar(
        df,
        x="Heure_Arrivee",
        y="Passagers",
        color="Vol",
        text_auto=True,
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_affluence.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title="Heure d'Arrivée",
        yaxis_title="Nombre de Passagers"
    )
    st.plotly_chart(fig_affluence, use_container_width=True)

with col_right:
    st.subheader("⏱️ Analyse du Temps d'Escale (Seuil : 45 min)")
    fig_transit = px.bar(
        df,
        x="Vol",
        y="Temps_Escale_Min",
        color="Temps_Escale_Min",
        color_continuous_scale="Reds_r",
        template="plotly_dark",
        text_auto=True
    )
    fig_transit.add_hline(y=45, line_dash="dash", line_color="#EF4444", annotation_text="Seuil critique")
    fig_transit.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title="Code Vol",
        yaxis_title="Escale (minutes)"
    )
    st.plotly_chart(fig_transit, use_container_width=True)

# ------------------------------------------------------------------------------
# 7. SECTION ALERTES ET ANNONCES
# ------------------------------------------------------------------------------
st.markdown("---")
st.subheader("⚠️ Centre de Traitement des Alertes")

if len(vols_critiques) > 0:
    for _, vol in vols_critiques.iterrows():
        st.error(
            f"🚨 **ALERTE FLUX CORRESPONDANCE [Vol {vol['Vol']} — {vol['Compagnie']}]** : "
            f"Arrivée estimée à **{vol['Heure_Arrivee']}**. "
            f"**{vol['Passagers_Transit']} passagers** en transit ne disposent que de **{vol['Temps_Escale_Min']} min**."
        )
    
    col_act1, col_act2 = st.columns([1, 2])
    with col_act1:
        if st.button("🔊 Diffuser l'Annonce Vocale Globale"):
            phrases_vols = []
            for _, vol in vols_critiques.iterrows():
                phrases_vols.append(
                    f"vol {vol['Vol']}, {vol['Passagers_Transit']} passagers en transit, escale de {vol['Temps_Escale_Min']} minutes."
                )
            
            message_audio = f"Attention PC Sécurité. Alerte correspondance sur {len(vols_critiques)} vol{'s' if len(vols_critiques) > 1 else ''}. " + " ".join(phrases_vols)
            fichier_mp3, key_unique = generer_annonce_vocale(message_audio)
            
            st.audio(fichier_mp3, format="audio/mp3", autoplay=True, key=f"audio_{key_unique}")
            st.success("Annonce diffusée en zone d'embarquement.")
else:
    st.success("✅ Aucun risque de correspondance détecté. Trafic sous contrôle.")

# ------------------------------------------------------------------------------
# 8. TABLEAU DE DONNÉES DETAILLÉ
# ------------------------------------------------------------------------------
with st.expander("📄 Programme complet des vols du jour (AIGE)"):
    st.dataframe(
        df.style.highlight_between(left=0, right=45, subset=['Temps_Escale_Min'], color='#7F1D1D'),
        use_container_width=True
    )
