# ==============================================================================
# PROJET : AeroFlow - Control Center (AIGE)
# APPLICATION WEB STREAMLIT - DESIGN EXECUTIVE & OPTIMISATION HAUT VOLUME
# ==============================================================================

import glob
import io
import math
import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from gtts import gTTS

# Imports ReportLab pour la génération de rapports PDF
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

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

    for col in ["Passagers", "Temps_Escale_Min"]:
        if col in df_temp.columns:
            df_temp[col] = pd.to_numeric(df_temp[col], errors="coerce")

    # --------------------------------------------------------------------------
    # CALCUL AUTOMATIQUE DU TAUX DE TRANSIT (FALLBACK SI ABSENT OU NON RENSEIGNÉ)
    # --------------------------------------------------------------------------
    if "Taux_Transit" not in df_temp.columns or df_temp["Taux_Transit"].isnull().all():
        taux_calcules = []
        for _, row in df_temp.iterrows():
            compagnie = str(row.get("Compagnie", "")).upper()
            if "ASKY" in compagnie:
                taux = 0.45
            elif any(c in compagnie for c in ["AIR COTE", "CEIBA", "OVERLAND", "AIR PEACE"]):
                taux = 0.35
            elif any(c in compagnie for c in ["AIR FRANCE", "TURKISH", "BRUSSELS"]):
                taux = 0.15
            else:
                taux = 0.25
            taux_calcules.append(taux)
        df_temp["Taux_Transit"] = taux_calcules
    else:
        df_temp["Taux_Transit"] = pd.to_numeric(df_temp["Taux_Transit"], errors="coerce").fillna(0.25)

    # Calcul des effectifs transit et terminus
    if "Passagers" in df_temp.columns:
        df_temp["Passagers_Transit"] = (
            (df_temp["Passagers"] * df_temp["Taux_Transit"]).fillna(0).round().astype(int)
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


def generer_pdf_rapport(df_complet, df_critiques, total_pax, total_trans, guichets):
    """Génère un rapport synthétique professionnel au format PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#0284C7'),
        spaceAfter=15
    )
    normal_bold = ParagraphStyle(
        'NormalBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.HexColor('#0F172A')
    )

    # En-tête
    date_str = datetime.datetime.now().strftime("%d/%m/%Y à %H:%M")
    story.append(Paragraph("✈️ AeroFlow — Control Center AIGE", title_style))
    story.append(Paragraph(f"Aéroport International Gnassingbé Eyadéma (AIGE) | Rapport Opérationnel du {date_str}", subtitle_style))
    story.append(Spacer(1, 10))

    # Résumé KPI
    nb_crit = len(df_critiques)
    kpi_data = [
        ["Passagers Attendus", "Flux Transit", "Guichets Ouverts", "Vols Critiques (≤45m)"],
        [f"{total_pax:,} pax", f"{total_trans:,} pax", f"{guichets}", f"{nb_crit} vol(s)"]
    ]
    t_kpi = Table(kpi_data, colWidths=[130, 130, 130, 130])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0284C7')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F1F5F9')),
        ('TEXTCOLOR', (0,1), (-1,1), colors.HexColor('#0F172A')),
        ('FONTSIZE', (0,1), (-1,1), 11),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 20))

    # Section Vols Critiques
    story.append(Paragraph("⚠️ Tableau des Vols Critiques et Correspondances Rapides", normal_bold))
    story.append(Spacer(1, 8))

    if not df_critiques.empty:
        cols_a_garder = [c for c in ["Vol", "Compagnie", "Heure_Arrivee", "Passagers", "Passagers_Transit", "Temps_Escale_Min"] if c in df_critiques.columns]
        crit_data = [cols_a_garder]
        for _, r in df_critiques[cols_a_garder].iterrows():
            crit_data.append([str(r[c]) for c in cols_a_garder])

        t_crit = Table(crit_data, colWidths=[80, 120, 90, 80, 80, 90])
        t_crit.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#DC2626')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#FECACA')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#FEF2F2')]),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_crit)
    else:
        story.append(Paragraph("✅ Aucun vol critique n'est signalé pour cette tranche d'exploitation.", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


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
# 4. SIDEBAR ET CHARGEMENT AUTOMATIQUE / MULTI-DÉTECTION CSV & MODÈLE
# ------------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Configuration")

    st.subheader("📂 Données de vol")
    fichier_importe = st.file_uploader(
        "Charger le programme des vols (CSV)", type=["csv"]
    )

    # Modèle CSV exemple à télécharger
    csv_modele_exemple = "Vol,Compagnie,Heure_Arrivee,Passagers,Temps_Escale_Min,Taux_Transit\nKP010,ASKY,11:30,120,40,0.45\nAF850,Air France,14:15,280,90,0.15\nET901,Ethiopian Airlines,16:45,190,35,0.30"
    st.download_button(
        label="📥 Télécharger le modèle CSV exemple",
        data=csv_modele_exemple,
        file_name="modele_vols_aige.csv",
        mime="text/csv",
        help="Téléchargez ce fichier modèle vierge à remplir si vous n'avez pas de fichier prêt."
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
# 7. CENTRE D'ALERTES & LECTEUR AUDIO INTERACTIF MULTILINGUE
# ------------------------------------------------------------------------------
st.markdown("---")
st.subheader("⚠️ Centre d'Alertes et Annonces")

if len(vols_critiques) > 0:
    col_btn, col_info = st.columns([1, 2])

    with col_btn:
        # Style CSS pour rendre le choix sélectionné ROUGE et bien visible
        st.markdown(
            """
            <style>
            div[data-testid="stRadio"] {
                background-color: #FFFFFF;
                padding: 10px 14px;
                border-radius: 8px;
                border: 1px solid #CBD5E1;
                margin-bottom: 12px;
            }
            div[data-testid="stRadio"] label p {
                color: #0F172A !important;
                font-weight: 600 !important;
                font-size: 0.95rem !important;
            }
            div[data-testid="stRadio"] label:has(input:checked) p {
                color: #DC2626 !important;
                font-weight: 800 !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # 1. Sélecteur de langue
        langue_choisie = st.radio(
            "🌐 Langue de l'annonce vocale :",
            options=["Français", "English"],
            horizontal=True,
            key="choix_langue_audio"
        )

        # 2. Génération AUTOMATIQUE de l'audio et du message selon la langue sélectionnée
        nb_crit = len(vols_critiques)
        total_pax_crit = int(vols_critiques["Passagers_Transit"].sum())

        if langue_choisie == "English":
            code_lang = "en"
            message = (
                f"Attention Security Control. General alert. A total of"
                f" {nb_crit} critical flights have been detected, representing"
                f" {total_pax_crit} passengers in tight connections."
                " Please check the control dashboard."
            )
        else:
            code_lang = "fr"
            message = (
                f"Attention PC Sécurité. Alerte générale. Un total de"
                f" {nb_crit} vols critiques a été détecté, représentant"
                f" {total_pax_crit} passagers en correspondance rapide."
                " Veuillez consulter le tableau de bord."
            )

        # Génération dynamique à chaque changement de radio
        try:
            fp = io.BytesIO()
            tts = gTTS(text=message, lang=code_lang)
            tts.write_to_fp(fp)
            fp.seek(0)
            
            audio_bytes = fp.read()

            # Affichage direct et instantané de l'audio et du texte
            st.audio(audio_bytes, format="audio/mp3")
            st.info(f"Annonce disponible : « {message} »")

        except Exception as e:
            st.error(f"Erreur de génération vocale : {e}")

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
    st.success("✅ Aucun risque de correspondance détecté pour le moment.")

# ------------------------------------------------------------------------------
# 8. TABLEAU DE DONNÉES DÉTAILLÉ AVEC DÉFILEMENT (SCROLLBARS)
# ------------------------------------------------------------------------------
with st.expander("📄 Voir le programme détaillé des vols (AIGE)"):
    st.dataframe(df, height=400, hide_index=True)

# ------------------------------------------------------------------------------
# 9. CENTRE D'EXPORTATION & RAPPORTS (CSV, EXCEL, PDF)
# ------------------------------------------------------------------------------
st.markdown("---")
st.subheader("📥 Exportation & Rapports d'Exploitation")

exp_col1, exp_col2, exp_col3 = st.columns(3)

# 1. Export CSV des Vols Critiques Filtrés
with exp_col1:
    st.markdown("**1. Données des Vols Critiques (CSV)**")
    if not vols_critiques.empty:
        csv_critiques = vols_critiques.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📄 Télécharger Vols Critiques (.csv)",
            data=csv_critiques,
            file_name=f"vols_critiques_AIGE_{datetime.date.today()}.csv",
            mime="text/csv",
        )
    else:
        st.info("Aucun vol critique à exporter.")

# 2. Export CSV du Programme Complet
with exp_col2:
    st.markdown("**2. Programme Complet des Vols (CSV)**")
    csv_complet = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="📊 Télécharger Programme Complet (.csv)",
        data=csv_complet,
        file_name=f"programme_vols_AIGE_{datetime.date.today()}.csv",
        mime="text/csv",
    )

# 3. Export Rapport Officiel PDF
with exp_col3:
    st.markdown("**3. Rapport Synthétique Officiel (PDF)**")
    if REPORTLAB_AVAILABLE:
        pdf_bytes = generer_pdf_rapport(
            df, vols_critiques, total_passagers, total_transit, guichets_ouverts
        )
        st.download_button(
            label="📑 Télécharger le Rapport (.pdf)",
            data=pdf_bytes,
            file_name=f"Rapport_Exploitation_AIGE_{datetime.date.today()}.pdf",
            mime="application/pdf",
        )
    else:
        st.warning("Module ReportLab indisponible. Ajoutez `reportlab` à votre environnement pour débloquer l'export PDF.")
# ------------------------------------------------------------------------------
# 10. ASSISTANT VIRTUEL D'EXPLOITATION VOCAL & TEXTE (AeroBot)
# ------------------------------------------------------------------------------
st.markdown("---")
st.subheader("🤖 AeroBot — Assistant Virtuel d'Exploitation (Vocal & Texte)")

# Imports spécifiques pour la reconnaissance vocale
try:
    from streamlit_mic_recorder import mic_recorder
    import speech_recognition as sr
    VOICE_INPUT_AVAILABLE = True
except ImportError:
    VOICE_INPUT_AVAILABLE = False

# Initialisation de l'historique de discussion
if "messages_chat" not in st.session_state:
    st.session_state["messages_chat"] = [
        {"role": "assistant", "content": "Bonjour ! Je suis AeroBot. Posez-moi votre question par écrit ou cliquez sur le micro pour me parler !"}
    ]

# Affichage des anciens messages
for msg in st.session_state["messages_chat"]:
    st.chat_message(msg["role"]).write(msg["content"])

prompt_utilisateur = None

# Interface d'entrée (Micro + Texte)
col_mic, col_txt = st.columns([1, 4])

with col_mic:
    if VOICE_INPUT_AVAILABLE:
        st.write("🎙️ **Parler à AeroBot :**")
        audio_recorded = mic_recorder(
            start_prompt="🔴 Parler",
            stop_prompt="⬛ Stopper",
            key="mic_chat"
        )
        if audio_recorded and "bytes" in audio_recorded:
            audio_bytes = audio_recorded["bytes"]
            recognizer = sr.Recognizer()
            try:
                audio_file = io.BytesIO(audio_bytes)
                with sr.AudioFile(audio_file) as source:
                    audio_data = recognizer.record(source)
                    prompt_utilisateur = recognizer.recognize_google(audio_data, language="fr-FR")
                    st.success(f"🗣️ Entendu : « {prompt_utilisateur} »")
            except Exception as e:
                st.error("Désolé, je n'ai pas bien compris votre message vocal.")
    else:
        st.caption("🎙️ Installez `streamlit-mic-recorder` et `SpeechRecognition` pour activer le micro.")

with col_txt:
    prompt_texte = st.chat_input("Ou tapez votre question ici (ex: Quels sont les vols critiques ?)...")
    if prompt_texte:
        prompt_utilisateur = prompt_texte

# Traitement de la question (Textuelle ou Vocale)
if prompt_utilisateur:
    # 1. Enregistrer la question utilisateur
    st.session_state["messages_chat"].append({"role": "user", "content": prompt_utilisateur})
    st.chat_message("user").write(prompt_utilisateur)

    question = prompt_utilisateur.lower()
    reponse = ""

    # 2. Logique de réponse
    if any(k in question for k in ["critique", "risque", "alerte", "retard"]):
        if not vols_critiques.empty:
            nb = len(vols_critiques)
            pax_t = int(vols_critiques["Passagers_Transit"].sum())
            reponse = f"⚠️ Nous avons {nb} vol(s) critique(s) représentant {pax_t} passagers en transit rapide.\n\n"
            for _, v in vols_critiques.iterrows():
                reponse += f"- Vol {v.get('Vol')} ({v.get('Compagnie')}) : Arrivée à {v.get('Heure_Arrivee')}, Escale : {v.get('Temps_Escale_Min')} min.\n"
        else:
            reponse = "🟢 Aucun vol critique n'est à signaler. La situation est fluide !"

    elif any(k in question for k in ["guichet", "agent", "capacit", "ouvrir"]):
        reponse = f"💡 **Recommandation Guichets :** Actuellement, vous avez {guichets_ouverts} guichet(s) ouvert(s).\n\nPour la pointe de trafic, il est conseillé d'ouvrir au moins {guichets_recommandes} guichets."

    elif any(k in question for k in ["passager", "flux", "total", "monde"]):
        reponse = f"📊 **Bilan du trafic du jour :**\n- Passagers totaux attendus : {total_passagers:,} pax\n- Dont passagers en transit : {total_transit:,} pax"

    else:
        reponse = "🤖 Je peux vous informer sur : les vols critiques, la recommandation de guichets, ou le total des passagers attendus."

    # 3. Afficher et enregistrer la réponse
    st.session_state["messages_chat"].append({"role": "assistant", "content": reponse})
    st.chat_message("assistant").write(reponse)

    # 4. Lecture vocale de la réponse d'AeroBot (Optionnel mais très classe !)
    try:
        tts_bot = gTTS(text=reponse.replace("*", ""), lang="fr")
        fp_bot = io.BytesIO()
        tts_bot.write_to_fp(fp_bot)
        fp_bot.seek(0)
        st.audio(fp_bot.read(), format="audio/mp3", autoplay=True)
    except Exception:
        pass
