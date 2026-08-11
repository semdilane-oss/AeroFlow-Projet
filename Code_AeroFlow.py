# ==============================================================================
# PROJET : AeroFlow - Control Center (AIGE)
# APPLICATION WEB STREAMLIT - DESIGN EXECUTIVE & CORRECTION AUDIO
# ==============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
from gtts import gTTS
import os
import time

# ------------------------------------------------------------------------------
# 1. CONFIGURATION DE LA PAGE & DESIGN PREMIUM LIGHT / AÉRO
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="AeroFlow — Control Center AIGE",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS Avancé (Design Aéro Pro - Bleu Aviation, Blanc Épuré & Cartes Relief)
st.markdown("""
<style>
    /* Fond principal et typographie */
    .stApp {
        background-color: #F8FAFC;
        color: #1E293B;
    }

    /* Titres et en-tête */
    .header-title {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 800;
        font-size: 2.2rem;
        color: #0F172A;
        margin-bottom: 0px;
    }
    .header-subtitle {
        color: #0284C7;
        font-weight: 600;
        font-size: 1rem;
        margin-bottom: 20px;
    }

    /* Cartes KPI Style Modern Dashboard */
    .kpi-container {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border-top: 4px solid #0284C7;
    }
    .kpi-container-alert {
        border-top: 4px solid #EF4444 !important;
        background-color: #FEF2F2;
    }
    .kpi-label {
        font-size: 0.8rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .kpi-val {
        font-size: 1.8rem;
        font-weight: 800;
        color: #0F172A;
        margin-top: 4px;
    }

    /* Bouton principal customisé */
    div.stButton > button {
        background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 10px 20px !important;
        box-shadow: 0 4px 10px rgba(2, 132, 199, 0.3) !important;
        width: 100%;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #0369A1 0%, #075985 100%) !important;
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

# Fonction de génération d'annonce vocale sécurisée
def generer_annonce_vocale(texte):
    # Nettoyage
    for file in os.listdir("."):
        if file.startswith("annonce_") and file.endswith(".mp3"):
            try:
                os.remove(file)
            except Exception:
                pass

    timestamp = int(time.time())
    nom_fichier = f"annonce_{timestamp}.mp3"
    tts = gTTS(text=texte, lang='fr')
    tts.save(nom_fichier)
    return nom_fichier

# ------------------------------------------------------------------------------
# 2. EN-TÊTE DU DASHBOARD
# ------------------------------------------------------------------------------
st.markdown('<div class="header-title">✈️ AeroFlow — Operations Control Center</div>', unsafe_allow_html=True)
st.markdown('<div class="header-subtitle">Aéroport International Gnassingbé Eyadéma (AIGE) | Plateforme de suivi & régulation des flux</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 3. BARRE LATÉRALE (SIDEBAR)
# ------------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Configuration")
    
    fichier_importe = st.file_uploader("Charger programme vols (CSV)", type=["csv"])

    if fichier_importe is not None:
        df = pd.read_csv(fichier_importe)
        st.success("Fichier chargé avec succès")
    else:
        try:
            df = pd.read_csv("vols_aige.csv")
            st.info("Source : vols_aige.csv")
        except Exception:
            st.error("Fichier 'vols_aige.csv' introuvable.")
            st.stop()

    st.markdown("---")
    capacite_agent_heure = st.slider("Capacité traitement (pax/agent/h)", 20, 60, 40)
    guichets_ouverts = st.slider("Guichets ouverts", 1, 10, 4)

# ------------------------------------------------------------------------------
# 4. CALCULS ET MÉTIER
# ------------------------------------------------------------------------------
df['Passagers_Transit'] = (df['Passagers'] * df['Taux_Transit']).astype(int)
df['Passagers_Terminus'] = df['Passagers'] - df['Passagers_Transit']
vols_critiques = df[df['Temps_Escale_Min'] <= 45]

# ------------------------------------------------------------------------------
# 5. CARTES D'INDICATEURS (KPIs)
# ------------------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f'''
    <div class="kpi-container">
        <div class="kpi-label">Passagers Attendus</div>
        <div class="kpi-val">{df["Passagers"].sum():,} pax</div>
    </div>
    ''', unsafe_allow_html=True)

with c2:
    st.markdown(f'''
    <div class="kpi-container">
        <div class="kpi-label">Flux Transit</div>
        <div class="kpi-val">{df["Passagers_Transit"].sum():,} pax</div>
    </div>
    ''', unsafe_allow_html=True)

with c3:
    st.markdown(f'''
    <div class="kpi-container">
        <div class="kpi-label">Capacité Traitement</div>
        <div class="kpi-val">{guichets_ouverts * capacite_agent_heure} pax/h</div>
    </div>
    ''', unsafe_allow_html=True)

with c4:
    alert_style = "kpi-container-alert" if len(vols_critiques) > 0 else ""
    color_val = "#EF4444" if len(vols_critiques) > 0 else "#10B981"
    st.markdown(f'''
    <div class="kpi-container {alert_style}">
        <div class="kpi-label">Vols Critiques (≤45 min)</div>
        <div class="kpi-val" style="color: {color_val};">{len(vols_critiques)} Vol(s)</div>
    </div>
    ''', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 6. GRAPHIQUES PRO (PALETTE BLEU / AMBRE)
# ------------------------------------------------------------------------------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Affluence par Heure d'Arrivée")
    fig_affluence = px.bar(
        df,
        x="Heure_Arrivee",
        y="Passagers",
        color="Vol",
        text_auto=True,
        color_discrete_sequence=px.colors.sequential.Blues_r,
        template="plotly_white"
    )
    fig_affluence.update_layout(
        xaxis_title="Heure d'arrivée",
        yaxis_title="Nombre de passagers",
        margin=dict(l=10, r=10, t=30, b=10)
    )
    st.plotly_chart(fig_affluence, use_container_width=True)

with col_right:
    st.subheader("⏱️ Escale & Correspondances")
    fig_transit = px.bar(
        df,
        x="Vol",
        y="Temps_Escale_Min",
        color="Temps_Escale_Min",
        color_continuous_scale="Reds_r",
        text_auto=True,
        template="plotly_white"
    )
    fig_transit.add_hline(y=45, line_dash="dash", line_color="#EF4444", annotation_text="Seuil 45 min")
    fig_transit.update_layout(
        xaxis_title="Vol",
        yaxis_title="Temps escale (min)",
        margin=dict(l=10, r=10, t=30, b=10)
    )
    st.plotly_chart(fig_transit, use_container_width=True)

# ------------------------------------------------------------------------------
# 7. GESTION DES ALERTES ET SYNTHÈSE VOCALE SÉCURISÉE
# ------------------------------------------------------------------------------
st.markdown("---")
st.subheader("⚠️ Centre d'Alertes et Annonces")

if len(vols_critiques) > 0:
    for _, vol in vols_critiques.iterrows():
        st.error(
            f"🔴 **ALERTE CORRESPONDANCE [Vol {vol['Vol']} - {vol['Compagnie']}]** : "
            f"Arrivée à **{vol['Heure_Arrivee']}**. "
            f"**{vol['Passagers_Transit']} passagers en transit** avec seulement **{vol['Temps_Escale_Min']} min** d'escale."
        )
    
    col_btn, _ = st.columns([1, 1])
    with col_btn:
        if st.button("🔊 Diffuser l'Annonce Vocale Globale"):
            phrases_vols = []
            for _, vol in vols_critiques.iterrows():
                phrases_vols.append(
                    f"vol {vol['Vol']}, {vol['Passagers_Transit']} passagers en transit, escale de {vol['Temps_Escale_Min']} minutes."
                )
            
            message = f"Attention PC Sécurité. Alerte correspondance urgente sur {len(vols_critiques)} vol{'s' if len(vols_critiques) > 1 else ''}. " + " ".join(phrases_vols)
            fichier_audio = generer_annonce_vocale(message)
            
            # Correction de la ligne qui causait l'erreur (st.audio standard compatible)
            with open(fichier_audio, "rb") as f:
                audio_bytes = f.read()
            st.audio(audio_bytes, format="audio/mp3")
            st.info(f"Annonce diffusée : « {message} »")
else:
    st.success("✅ Aucun risque de correspondance détecté pour le moment.")

# ------------------------------------------------------------------------------
# 8. TABLEAU DE DONNÉES
# ------------------------------------------------------------------------------
with st.expander("📄 Voir le programme détaillé des vols (AIGE)"):
    st.dataframe(df, use_container_width=True)
