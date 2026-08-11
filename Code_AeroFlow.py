# ==============================================================================
# PROJET : AeroFlow - Control Center (AIGE)
# APPLICATION WEB STREAMLIT - DESIGN EXECUTIVE & CORRECTION AUDIO
# ==============================================================================

import io
import os
import time
from gtts import gTTS
import pandas as pd
import plotly.express as px
import streamlit as st

# ------------------------------------------------------------------------------
# 1. CONFIGURATION DE LA PAGE & DESIGN PREMIUM LIGHT / AÉRO
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="AeroFlow — Control Center AIGE",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Style CSS Avancé (Design Aéro Pro - Bleu Aviation, Blanc Épuré & Cartes Relief)
st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------------------
# FONCTION UNIVERSELLE DE CHARGEMENT ET NETTOYAGE DES DONNÉES
# ------------------------------------------------------------------------------
def charger_et_nettoyer_donnees(source_fichier):
    """Charge et nettoie le CSV en s'adaptant à n'importe quel séparateur,

    encodage ou espace parasite dans les entêtes.
    """
    if isinstance(source_fichier, str):
        with open(source_fichier, "rb") as f:
            contenu_octets = f.read()
    else:
        contenu_octets = source_fichier.read()

    # Détection et suppression du BOM UTF-8 (\ufeff) s'il existe
    if contenu_octets.startswith(b"\xef\xbb\xbf"):
        contenu_octets = contenu_octets[3:]

    contenu_texte = contenu_octets.decode("utf-8", errors="ignore")

    # Détection automatique du séparateur (virgule, point-virgule, tabulation)
    premiere_ligne = contenu_texte.splitlines()[0] if contenu_texte else ""
    nb_virgules = premiere_ligne.count(",")
    nb_points_virgules = premiere_ligne.count(";")
    nb_tabs = premiere_ligne.count("\t")

    separateur = ","
    if nb_points_virgules > nb_virgules and nb_points_virgules > nb_tabs:
        separateur = ";"
    elif nb_tabs > nb_virgules and nb_tabs > nb_points_virgules:
        separateur = "\t"

    # Lecture via Pandas
    df_temp = pd.read_csv(io.StringIO(contenu_texte), sep=separateur)

    # Nettoyage des noms de colonnes (élimine les espaces invisibles)
    df_temp.columns = df_temp.columns.str.strip()

    # Correction automatique des fautes d'encodage sur la compagnie
    if "Compagnie" in df_temp.columns:
        df_temp["Compagnie"] = df_temp["Compagnie"].astype(str)
        df_temp["Compagnie"] = df_temp["Compagnie"].str.replace(
            r"Air C[ÃâÂ]te d['’]Ivoire", "Air Cote d'Ivoire", regex=True
        )

    # Convertir 'Passagers', 'Taux_Transit' et 'Temps_Escale_Min' en types numériques
    for col in ["Passagers", "Taux_Transit", "Temps_Escale_Min"]:
        if col in df_temp.columns:
            df_temp[col] = pd.to_numeric(df_temp[col], errors="coerce")

    # Calcul dynamique des passagers en transit et terminus
    if "Passagers" in df_temp.columns and "Taux_Transit" in df_temp.columns:
        df_temp["Passagers_Transit"] = (
            (df_temp["Passagers"] * df_temp["Taux_Transit"])
            .fillna(0)
            .astype(int)
        )
        df_temp["Passagers_Terminus"] = (
            df_temp["Passagers"] - df_temp["Passagers_Transit"]
        )

    return df_temp


# Fonction de génération d'annonce vocale sécurisée
def generer_annonce_vocale(texte):
    # Nettoyage des anciens fichiers audio
    for file in os.listdir("."):
        if file.startswith("annonce_") and file.endswith(".mp3"):
            try:
                os.remove(file)
            except Exception:
                pass

    timestamp = int(time.time())
    nom_fichier = f"annonce_{timestamp}.mp3"
    tts = gTTS(text=texte, lang="fr")
    tts.save(nom_fichier)
    return nom_fichier


# ------------------------------------------------------------------------------
# 2. EN-TÊTE DU DASHBOARD
# ------------------------------------------------------------------------------
st.markdown(
    '<div class="header-title">✈️ AeroFlow — Operations Control Center</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="header-subtitle">Aéroport International Gnassingbé Eyadéma'
    " (AIGE) | Plateforme de suivi & régulation des flux</div>",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------------------
# 3. BARRE LATÉRALE (SIDEBAR)
# ------------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Configuration")

    fichier_importe = st.file_uploader(
        "Charger programme vols (CSV)", type=["csv"]
    )

    if fichier_importe is not None:
        try:
            df = charger_et_nettoyer_donnees(fichier_importe)
            st.success("Fichier chargé avec succès")
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier : {e}")
            st.stop()
    else:
        try:
            df = charger_et_nettoyer_donnees("vols_aige.csv")
            st.info("Source : vols_aige.csv")
        except Exception:
            st.error("Fichier 'vols_aige.csv' introuvable.")
            st.stop()

    st.markdown("---")
    capacite_agent_heure = st.slider(
        "Capacité traitement (pax/agent/h)", 20, 60, 40
    )
    guichets_ouverts = st.slider("Guichets ouverts", 1, 10, 4)

# ------------------------------------------------------------------------------
# 4. CALCULS ET MÉTIER
# ------------------------------------------------------------------------------
vols_critiques = (
    df[df["Temps_Escale_Min"] <= 45]
    if "Temps_Escale_Min" in df.columns
    else pd.DataFrame()
)

# ------------------------------------------------------------------------------
# 5. CARTES D'INDICATEURS (KPIs)
# ------------------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)

total_passagers = (
    int(df["Passagers"].sum()) if "Passagers" in df.columns else 0
)
total_transit = (
    int(df["Passagers_Transit"].sum()) if "Passagers_Transit" in df.columns else 0
)

with c1:
    st.markdown(
        f"""
    <div class="kpi-container">
        <div class="kpi-label">Passagers Attendus</div>
        <div class="kpi-val">{total_passagers:,} pax</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
    <div class="kpi-container">
        <div class="kpi-label">Flux Transit</div>
        <div class="kpi-val">{total_transit:,} pax</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        f"""
    <div class="kpi-container">
        <div class="kpi-label">Capacité Traitement</div>
        <div class="kpi-val">{guichets_ouverts * capacite_agent_heure} pax/h</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with c4:
    alert_style = "kpi-container-alert" if len(vols_critiques) > 0 else ""
    color_val = "#EF4444" if len(vols_critiques) > 0 else "#10B981"
    st.markdown(
        f"""
    <div class="kpi-container {alert_style}">
        <div class="kpi-label">Vols Critiques (≤45 min)</div>
        <div class="kpi-val" style="color: {color_val};">{len(vols_critiques)} Vol(s)</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 6. GRAPHIQUES PRO (PALETTE BLEU / AMBRE)
# ------------------------------------------------------------------------------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Affluence par Heure d'Arrivée")
    if "Heure_Arrivee" in df.columns and "Passagers" in df.columns:
        fig_affluence = px.bar(
            df,
            x="Heure_Arrivee",
            y="Passagers",
            color="Vol" if "Vol" in df.columns else None,
            text_auto=True,
            color_discrete_sequence=px.colors.sequential.Blues_r,
            template="plotly_white",
        )
        fig_affluence.update_layout(
            xaxis_title="Heure d'arrivée",
            yaxis_title="Nombre de passagers",
            margin=dict(l=10, r=10, t=30, b=10),
        )
        st.plotly_chart(fig_affluence, use_container_width=True)

with col_right:
    st.subheader("⏱️ Escale & Correspondances")
    if "Vol" in df.columns and "Temps_Escale_Min" in df.columns:
        fig_transit = px.bar(
            df,
            x="Vol",
            y="Temps_Escale_Min",
            color="Temps_Escale_Min",
            color_continuous_scale="Reds_r",
            text_auto=True,
            template="plotly_white",
        )
        fig_transit.add_hline(
            y=45,
            line_dash="dash",
            line_color="#EF4444",
            annotation_text="Seuil 45 min",
        )
        fig_transit.update_layout(
            xaxis_title="Vol",
            yaxis_title="Temps escale (min)",
            margin=dict(l=10, r=10, t=30, b=10),
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
            f"🔴 **ALERTE CORRESPONDANCE [Vol {vol.get('Vol', 'N/A')} -"
            f" {vol.get('Compagnie', 'N/A')}]** : Arrivée à"
            f" **{vol.get('Heure_Arrivee', 'N/A')}**. "
            f"**{vol.get('Passagers_Transit', 0)} passagers en transit** avec"
            f" seulement **{vol.get('Temps_Escale_Min', 0)} min** d'escale."
        )

    col_btn, _ = st.columns([1, 1])
    with col_btn:
        if st.button("🔊 Diffuser l'Annonce Vocale Globale"):
            phrases_vols = []
            for _, vol in vols_critiques.iterrows():
                phrases_vols.append(
                    f"vol {vol.get('Vol', '')}, {vol.get('Passagers_Transit', 0)} passagers en transit, escale de {vol.get('Temps_Escale_Min', 0)} minutes."
                )

            message = (
                f"Attention PC Sécurité. Alerte correspondance urgente sur"
                f" {len(vols_critiques)} vol{'s' if len(vols_critiques) > 1 else ''}."
                " " + " ".join(phrases_vols)
            )
            fichier_audio = generer_annonce_vocale(message)

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
