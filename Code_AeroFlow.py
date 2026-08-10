# ==============================================================================
# PROJET : AeroFlow - Gestion Intelligente des Flux de Passagers (AIGE)
# APPLICATION WEB STREAMLIT
# ==============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
from gtts import gTTS
import os

# ------------------------------------------------------------------------------
# 1. CONFIGURATION DE LA PAGE WEB
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="AeroFlow - Dashboard AIGE",
    page_icon="✈️",
    layout="wide"
)

# Fonction pour générer l'annonce vocale en fichier MP3
def generer_annonce_vocale(texte):
    tts = gTTS(text=texte, lang='fr')
    nom_fichier = "alerte_temp.mp3"
    tts.save(nom_fichier)
    return nom_fichier

# ------------------------------------------------------------------------------
# 2. EN-TÊTE DU DASHBOARD
# ------------------------------------------------------------------------------
st.title("✈️ AeroFlow — Plateforme d'Anticipation des Flux AIGE")
st.caption("Système intelligent d'optimisation des contrôles et de gestion des correspondances")

# ------------------------------------------------------------------------------
# 3. BARRE LATÉRALE (SIDEBAR) : DONNÉES ET RÉGLAGES TEMPS RÉEL
# ------------------------------------------------------------------------------
st.sidebar.header("📥 Chargement des Données")

# Importation d'un fichier de vols réel ou fictif
fichier_importe = st.sidebar.file_uploader("Importer un fichier de vols (CSV)", type=["csv"])

if fichier_importe is not None:
    df = pd.read_csv(fichier_importe)
    st.sidebar.success("Fichier importé avec succès !")
else:
    try:
        df = pd.read_csv("vols_aige.csv")
    except Exception:
        st.error("Le fichier 'vols_aige.csv' est introuvable dans le dossier du projet.")
        st.stop()

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Paramètres Opérationnels")
capacite_agent_heure = st.sidebar.slider("Capacité de traitement (pax/agent/heure)", 20, 60, 40)
guichets_ouverts = st.sidebar.slider("Nombre de guichets ouverts", 1, 10, 3)

# ------------------------------------------------------------------------------
# 4. CALCULS ET LOGIQUE MÉTIER
# ------------------------------------------------------------------------------
df['Passagers_Transit'] = (df['Passagers'] * df['Taux_Transit']).astype(int)
df['Passagers_Terminus'] = df['Passagers'] - df['Passagers_Transit']

# Identification des vols à risque (Escale <= 45 min)
vols_critiques = df[df['Temps_Escale_Min'] <= 45]

# ------------------------------------------------------------------------------
# 5. AFFICHAGE DES INDICATEURS CLÉS (KPIs)
# ------------------------------------------------------------------------------
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric("Total Passagers Attendus", f"{df['Passagers'].sum()} pax")
kpi2.metric("Passagers en Transit", f"{df['Passagers_Transit'].sum()} pax")
kpi3.metric("Guichets Actifs", f"{guichets_ouverts} / 10")
kpi4.metric(
    "Alertes Correspondance", 
    f"{len(vols_critiques)} vol(s)", 
    delta="- Risque" if len(vols_critiques) > 0 else "Normal",
    delta_color="inverse"
)

st.markdown("---")

# ------------------------------------------------------------------------------
# 6. GRAPHIQUES INTERACTIFS
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
        labels={"Heure_Arrivee": "Heure d'arrivée", "Passagers": "Nombre de passagers"},
        title="Répartition des flux à l'arrivée"
    )
    st.plotly_chart(fig_affluence, use_container_width=True)

with col_right:
    st.subheader("⏱️ Temps d'Escale pour Correspondances")
    fig_transit = px.bar(
        df,
        x="Vol",
        y="Temps_Escale_Min",
        color="Temps_Escale_Min",
        color_continuous_scale="Reds_r",
        labels={"Temps_Escale_Min": "Temps disponible (min)"},
        title="Seuil de sécurité fixé à 45 minutes"
    )
    st.plotly_chart(fig_transit, use_container_width=True)

# ------------------------------------------------------------------------------
# 7. SECTION ALERTES EN TEMPS RÉEL ET SYNTHÈSE VOCALE
# ------------------------------------------------------------------------------
st.subheader("⚠️ Alertes et Actions Prioritaires")

if len(vols_critiques) > 0:
    for _, vol in vols_critiques.iterrows():
        st.error(
            f"🔴 **ALERTE CORRESPONDANCE [Vol {vol['Vol']} - {vol['Compagnie']}]** : "
            f"Arrivée prévue à **{vol['Heure_Arrivee']}**. "
            f"**{vol['Passagers_Transit']} passagers en transit** disposent de seulement **{vol['Temps_Escale_Min']} min** pour leur correspondance."
        )
    
    if st.button("🔊 Générer et diffuser l'annonce vocale"):
        premier_vol = vols_critiques.iloc[0]
        message_audio = (
            f"Attention. Alerte correspondance sur le vol {premier_vol['Vol']}. "
            f"{premier_vol['Passagers_Transit']} passagers en transit prioritaire."
        )
        fichier_mp3 = generer_annonce_vocale(message_audio)
        
        # Lecteur audio officiel Streamlit
        st.audio(fichier_mp3, format="audio/mp3", autoplay=True)
        st.info(f"Annonce : « {message_audio} »")
else:
    st.success("✅ Aucun risque de correspondance critique détecté pour le moment.")

# ------------------------------------------------------------------------------
# 8. TABLEAU DE DONNÉES
# ------------------------------------------------------------------------------
with st.expander("📄 Consulter le programme détaillé des vols"):
    st.dataframe(df, use_container_width=True)