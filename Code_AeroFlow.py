# ==============================================================================
# PROJET : AeroFlow - Control Center (AIGE)
# APPLICATION WEB STREAMLIT - DESIGN EXECUTIVE & OPTIMISATION HAUT VOLUME
# ==============================================================================

import glob
import io
import math
import pandas as pd
import plotly.express as px
import streamlit as st
from gtts import gTTS

# ------------------------------------------------------------------------------
# 1. CONFIGURATION DE LA PAGE & DESIGN PREMIUM LIGHT / AÉRO
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="AeroFlow — Control Center AIGE",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .stApp { background-color: #F8FAFC; color: #1E293B; }
    .header-title { font-family: 'Segoe UI', sans-serif; font-weight: 800; font-size: 2.2rem; color: #0F172A; }
    .header-subtitle { color: #0284C7; font-weight: 600; font-size: 1rem; margin-bottom: 20px; }
    .kpi-container {
        background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
        padding: 18px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); border-top: 4px solid #0284C7;
    }
    .kpi-container-alert { border-top: 4px solid #EF4444 !important; background-color: #FEF2F2; }
    .kpi-label { font-size: 0.8rem; font-weight: 700; color: #64748B; text-transform: uppercase; }
    .kpi-val { font-size: 1.8rem; font-weight: 800; color: #0F172A; margin-top: 4px; }
    div.stButton > button {
        background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important;
        color: white !important; font-weight: 700 !important; border-radius: 8px !important;
        border: none !important; padding: 10px 20px !important; width: 100%;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------------------
# 2. FONCTIONS LOGIQUES ET TRAITEMENT DES DONNÉES
# ------------------------------------------------------------------------------
def calculer_capacite_dynamique(df_vols):
    """Calcule automatiquement la capacité moyenne de traitement (pax/agent/h)

    en analysant la typologie des vols.
    """
    if df_vols.empty or "Compagnie" not in df_vols.columns:
        return 40.0

    capacites = []
    for _, row in df_vols.iterrows():
        compagnie = str(row.get("Compagnie", "")).upper()

        if any(
            c in compagnie
            for c in ["ASKY", "CEIBA", "AIR COTE", "OVERLAND", "AIR PEACE"]
        ):
            cap_base = 50.0
        elif any(
            c in compagnie
            for c in ["AIR FRANCE", "TURKISH", "BRUSSELS", "ROYAL AIR MAROC"]
        ):
            cap_base = 30.0
        elif "ETHIOPIAN" in compagnie:
            cap_base = 35.0
        else:
            cap_base = 40.0

        taux_t = row.get("Taux_Transit", 0.2)
        if taux_t > 0.35:
            cap_base += 5.0

        capacites.append(cap_base)

    df_vols["Capacite_Estimee"] = capacites
    return round(float(pd.Series(capacites).mean()), 1)


def charger_et_nettoyer_donnees(source_fichier):
    if isinstance(source_fichier, str):
        with open(source_fichier, "rb") as f:
            contenu_octets = f.read()
    else:
        contenu_octets = source_fichier.read()

    if contenu_octets.startswith(b"\xef\xbb\xbf"):
        contenu_octets = contenu_octets[3:]

    contenu_texte = contenu_octets.decode("utf-8", errors="ignore")

    premiere_ligne = contenu_texte.splitlines()[0] if contenu_texte else ""
    separateur = ","
    if premiere_ligne.count(";") > premiere_ligne.count(","):
        separateur = ";"
    elif premiere_ligne.count("\t") > premiere_ligne.count(","):
        separateur = "\t"

    df_temp = pd.read_csv(io.StringIO(contenu_texte), sep=separateur)
    df_temp.columns = df_temp.columns.str.strip()

    if "Compagnie" in df_temp.columns:
        df_temp["Compagnie"] = df_temp["Compagnie"].astype(str)
        df_temp["Compagnie"] = df_temp["Compagnie"].str.replace(
            r"Air C[ÃâÂ]te d['’]Ivoire", "Air Cote d'Ivoire", regex=True
        )

    for col in ["Passagers", "Taux_Transit", "Temps_Escale_Min"]:
        if col in df_temp.columns:
            df_temp[col] = pd.to_numeric(df_temp[col], errors="coerce")

    if "Passagers" in df_temp.columns and "Taux_Transit" in df_temp.columns:
        df_temp["Passagers_Transit"] = (
            (df_temp["Passagers"] * df_temp["Taux_Transit"])
            .fillna(0)
            .astype(int)
        )
        df_temp["Passagers_Terminus"] = (
            df_temp["Passagers"] - df_temp["Passagers_Transit"]
        )

    if "Heure_Arrivee" in df_temp.columns:
        df_temp["Tranche_Horaire"] = (
            df_temp["Heure_Arrivee"].astype(str).str.split(":").str[0]
            + "h00 - "
            + df_temp["Heure_Arrivee"].astype(str).str.split(":").str[0]
            + "h59"
        )

    return df_temp


# ------------------------------------------------------------------------------
# 3. EN-TÊTE DE L'APPLICATION
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
# 4. SIDEBAR ET CHARGEMENT AUTOMATIQUE / MULTI-DÉTECTION CSV
# ------------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Configuration")

    fichier_importe = st.file_uploader(
        "Charger programme vols (CSV)", type=["csv"]
    )

    # 1. Si un utilisateur téléverse manuellement un fichier
    if fichier_importe is not None:
        try:
            st.session_state["df_vols"] = charger_et_nettoyer_donnees(
                fichier_importe
            )
            st.success("Fichier personnalisé actif")
        except Exception as e:
            st.error(f"Erreur de lecture : {e}")

    # 2. Détection automatique de n'importe quel CSV présent dans le projet
    if "df_vols" not in st.session_state:
        fichiers_csv_locaux = glob.glob("*.csv")

        if fichiers_csv_locaux:
            fichier_trouve = fichiers_csv_locaux[0]
            try:
                st.session_state["df_vols"] = charger_et_nettoyer_donnees(
                    fichier_trouve
                )
                st.info(f"Source détectée : {fichier_trouve}")
            except Exception as e:
                st.error(f"Erreur lors de la lecture de {fichier_trouve} : {e}")
                st.stop()
        else:
            st.error("⚠️ Aucun fichier CSV trouvé dans le dépôt GitHub.")
            st.stop()

    df = st.session_state["df_vols"]

    st.markdown("---")

    capacite_agent_heure = calculer_capacite_dynamique(df)

    if "Tranche_Horaire" in df.columns and "Passagers" in df.columns:
        max_pax_heure = df.groupby("Tranche_Horaire")["Passagers"].sum().max()
        guichets_recommandes = max(
            1, math.ceil(max_pax_heure / capacite_agent_heure)
        )
    else:
        guichets_recommandes = 4

    st.metric(
        label="🤖 Capacité Estimée (Automatique)",
        value=f"{capacite_agent_heure} pax/h/agent",
        help="Calculé automatiquement selon la typologie des vols et des compagnies.",
    )

    guichets_ouverts = st.slider(
        "Guichets ouverts sur le terrain",
        1,
        max(50, guichets_recommandes + 10),
        guichets_recommandes,
    )

    if guichets_ouverts < guichets_recommandes:
        st.warning(
            f"💡 **Recommandation :** Ouvrir au moins **{guichets_recommandes}"
            " guichets** pour absorber la pointe de trafic."
        )

# ------------------------------------------------------------------------------
# 5. KPIS & INDICATEURS CLÉS
# ------------------------------------------------------------------------------
vols_critiques = (
    df[df["Temps_Escale_Min"] <= 45]
    if "Temps_Escale_Min" in df.columns
    else pd.DataFrame()
)

c1, c2, c3, c4 = st.columns(4)

total_passagers = (
    int(df["Passagers"].sum()) if "Passagers" in df.columns else 0
)
total_transit = (
    int(df["Passagers_Transit"].sum()) if "Passagers_Transit" in df.columns else 0
)
capacite_totale = int(guichets_ouverts * capacite_agent_heure)

with c1:
    st.markdown(
        f'<div class="kpi-container"><div class="kpi-label">Passagers Attendus</div><div class="kpi-val">{total_passagers:,} pax</div></div>',
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f'<div class="kpi-container"><div class="kpi-label">Flux Transit</div><div class="kpi-val">{total_transit:,} pax</div></div>',
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f'<div class="kpi-container"><div class="kpi-label">Capacité Traitement</div><div class="kpi-val">{capacite_totale:,} pax/h</div></div>',
        unsafe_allow_html=True,
    )
with c4:
    alert_style = "kpi-container-alert" if len(vols_critiques) > 0 else ""
    color_val = "#EF4444" if len(vols_critiques) > 0 else "#10B981"
    st.markdown(
        f'<div class="kpi-container {alert_style}"><div class="kpi-label">Vols Critiques (≤45 min)</div><div class="kpi-val" style="color: {color_val};">{len(vols_critiques):,} Vol(s)</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 6. GRAPHIQUES ET ANALYSE
# ------------------------------------------------------------------------------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Affluence Globale par Tranche Horaire")
    if "Tranche_Horaire" in df.columns and "Passagers" in df.columns:
        df_affluence_heure = (
            df.groupby("Tranche_Horaire")["Passagers"].sum().reset_index()
        )
        fig_affluence = px.bar(
            df_affluence_heure,
            x="Tranche_Horaire",
            y="Passagers",
            text_auto=True,
            color="Passagers",
            color_continuous_scale="Blues",
            template="plotly_white",
        )
        fig_affluence.update_layout(
            xaxis_title="Tranche Horaire",
            yaxis_title="Total Passagers",
            margin=dict(l=10, r=10, t=30, b=10),
        )
        st.plotly_chart(fig_affluence, use_container_width=True)

with col_right:
    st.subheader("⏱️ Répartition des Temps d'Escale (Distribution)")
    if "Temps_Escale_Min" in df.columns:
        bins = [0, 30, 45, 60, 90, 120, 999]
        labels = [
            "< 30 min",
            "30-45 min (Critique)",
            "45-60 min",
            "60-90 min",
            "90-120 min",
            "> 120 min",
        ]
        df["Plage_Escale"] = pd.cut(
            df["Temps_Escale_Min"], bins=bins, labels=labels
        )
        df_escale_group = df["Plage_Escale"].value_counts().reset_index()
        df_escale_group.columns = ["Plage_Escale", "Nombre_de_Vols"]

        fig_transit = px.bar(
            df_escale_group,
            x="Plage_Escale",
            y="Nombre_de_Vols",
            color="Nombre_de_Vols",
            color_continuous_scale="Reds_r",
            text_auto=True,
            template="plotly_white",
        )
        fig_transit.update_layout(
            xaxis_title="Plage de Temps d'Escale",
            yaxis_title="Nombre de Vols",
            margin=dict(l=10, r=10, t=30, b=10),
        )
        st.plotly_chart(fig_transit, use_container_width=True)

# ------------------------------------------------------------------------------
# 7. CENTRE D'ALERTES & LECTEUR AUDIO INTERACTIF
# ------------------------------------------------------------------------------
st.markdown("---")
st.subheader("⚠️ Centre d'Alertes et Annonces")

if len(vols_critiques) > 0:
    col_btn, col_info = st.columns([1, 2])

    with col_btn:
        if st.button("🔊 Générer / Réinitialiser l'Annonce Vocale"):
            nb_crit = len(vols_critiques)
            total_pax_crit = int(vols_critiques["Passagers_Transit"].sum())
            message = (
                f"Attention PC Sécurité. Alerte générale. Un total de"
                f" {nb_crit} vols critiques a été détecté, représentant"
                f" {total_pax_crit} passagers en correspondance rapide."
                " Veuillez consulter le tableau de bord."
            )

            try:
                fp = io.BytesIO()
                tts = gTTS(text=message, lang="fr")
                tts.write_to_fp(fp)
                fp.seek(0)

                st.session_state["audio_bytes"] = fp.read()
                st.session_state["message_texte"] = message
            except Exception as e:
                st.error(f"Erreur de génération vocale : {e}")

        if "audio_bytes" in st.session_state:
            st.audio(st.session_state["audio_bytes"], format="audio/mp3")
            st.info(
                f"Annonce disponible : « {st.session_state['message_texte']} »"
            )

    with col_info:
     s = "s" if len(vols_critiques) > 1 else ""
st.markdown(
    f"""
    <div style="
        background-color: #DC2626; 
        color: #FFFFFF; 
        padding: 14px 18px; 
        border-radius: 8px; 
        font-weight: 700; 
        font-size: 1.05rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 15px;">
        ⚠️ {len(vols_critiques):,} vol{s} critique{s} détecté{s} (Escale ≤ 45 min)
    </div>
    """,
    unsafe_allow_html=True,
)

    with st.container(height=280):
        for _, vol in vols_critiques.iterrows():
            st.error(
                f"🔴 **[Vol {vol.get('Vol', 'N/A')} -"
                f" {vol.get('Compagnie', 'N/A')}]** : Arrivée à"
                f" **{vol.get('Heure_Arrivee', 'N/A')}** |"
                f" **{vol.get('Passagers_Transit', 0)} pax transit** | Escale:"
                f" **{vol.get('Temps_Escale_Min', 0)} min**"
            )
else:
    if "audio_bytes" in st.session_state:
        del st.session_state["audio_bytes"]
    st.success("✅ Aucun risque de correspondance détecté pour le moment.")

# ------------------------------------------------------------------------------
# 8. TABLEAU DE DONNÉES DÉTAILLÉ AVEC DÉFILEMENT (SCROLLBARS)
# ------------------------------------------------------------------------------
with st.expander("📄 Voir le programme détaillé des vols (AIGE)"):
    st.dataframe(df, height=400, hide_index=True)
