# ==============================================================================
# PROJET : AeroFlow - Control Center (AIGE)
# APPLICATION WEB STREAMLIT - DESIGN DYNAMIQUE (MODE CLAIR / SOMBRE FIXÉ)
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

# Imports pour la reconnaissance vocale et le micro
try:
    from streamlit_mic_recorder import mic_recorder
    import speech_recognition as sr
    VOICE_INPUT_AVAILABLE = True
except ImportError:
    VOICE_INPUT_AVAILABLE = False


# ------------------------------------------------------------------------------
# 1. CONFIGURATION DE LA PAGE
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="AeroFlow — Control Center AIGE",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialisation du thème dans le Session State (par défaut : Clair)
if "theme_sombre" not in st.session_state:
    st.session_state["theme_sombre"] = False

# ------------------------------------------------------------------------------
# 2. SELECTION DU THÈME DANS LA SIDEBAR & CSS DYNAMIQUE
# ------------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Configuration")
    
    # Bouton bascule du Mode Nuit / Mode Clair
    mode_nuit = st.toggle("🌙 Mode Nuit (Sombre)", value=st.session_state["theme_sombre"])
    st.session_state["theme_sombre"] = mode_nuit

# Injection CSS dynamique selon le mode choisi
if st.session_state["theme_sombre"]:
    # THÈME SOMBRE
    bg_app = "#131314"
    text_main = "#E3E3E3"
    card_bg = "#1E1F20"
    border_color = "#444746"
    title_color = "#FFFFFF"
    plotly_template = "plotly_dark"
    radio_text_color = "#E3E3E3"
    
    # Zone de saisie
    input_box_bg = "#242731"
    input_text_color = "#FFFFFF"
    placeholder_color = "#9CA3AF"
    
    # Bulle Chat
    chat_bg = "#2D2E30"
    chat_text = "#E3E3E3"
    avatar_bg = "#EF4444"
else:
    # THÈME CLAIR (Optimisé pour la lisibilité)
    bg_app = "#F8FAFC"
    text_main = "#0F172A"
    card_bg = "#FFFFFF"
    border_color = "#CBD5E1"
    title_color = "#0F172A"
    plotly_template = "plotly_white"
    radio_text_color = "#0F172A"
    
    # Zone de saisie (Fond sombre interne pour faire ressortir la saisie en Blanc très net)
    input_box_bg = "#1E293B"
    input_text_color = "#FFFFFF"
    placeholder_color = "#94A3B8"
    
    # Bulle Chat
    chat_bg = "#9399A0"
    chat_text = "#0F172A"
    avatar_bg = "#FF2A2A"

st.markdown(
    f"""
<style>
    /* Application du thème global */
    .stApp {{ background-color: {bg_app} !important; color: {text_main} !important; }}
    
    .header-title {{ font-family: 'Segoe UI', sans-serif; font-weight: 800; font-size: 2.2rem; color: {title_color}; }}
    .header-subtitle {{ color: #0284C7; font-weight: 600; font-size: 1rem; margin-bottom: 20px; }}
    
    /* KPI Containers */
    .kpi-container {{
        background-color: {card_bg}; border: 1px solid {border_color}; border-radius: 12px;
        padding: 18px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); border-top: 4px solid #0284C7;
    }}
    .kpi-container-alert {{ border-top: 4px solid #EF4444 !important; background-color: {'#2D1517' if st.session_state['theme_sombre'] else '#FEF2F2'}; }}
    .kpi-label {{ font-size: 0.8rem; font-weight: 700; color: {'#9CA3AF' if st.session_state['theme_sombre'] else '#64748B'}; text-transform: uppercase; }}
    .kpi-val {{ font-size: 1.8rem; font-weight: 800; color: {title_color}; margin-top: 4px; }}
    
    /* Visibilité Boutons Radio */
    div[data-testid="stRadio"] label, div[data-testid="stRadio"] p {{
        color: {radio_text_color} !important;
        font-weight: 600 !important;
    }}
    
    /* Boutons Généraux */
    div.stButton > button {{
        background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important;
        color: white !important; font-weight: 700 !important; border-radius: 8px !important;
        border: none !important; padding: 10px 20px !important; width: 100%;
    }}
    
    /* Bulle de Chat */
    div[data-testid="stChatMessage"] {{
        background-color: {chat_bg} !important;
        border-radius: 8px !important;
        padding: 8px 14px !important;
        margin-bottom: 10px !important;
        border: none !important;
    }}

    div[data-testid="stChatMessage"] div[data-testid="stChatMessageAvatar"] {{
        background-color: {avatar_bg} !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
    }}

    div[data-testid="stChatMessage"] p, 
    div[data-testid="stChatMessageContent"] p,
    div[data-testid="stChatMessageContent"] {{
        color: {chat_text} !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
    }}

    /* --- FIX LISIBILITÉ CHAMP DE SAISIE (CAPSULE PILULE) --- */
    
    /* Conteneur Extérieur Formulaire */
    div[data-testid="stForm"] {{
        background-color: #FFFFFF !important;
        border: 1px solid {border_color} !important;
        border-radius: 50px !important;
        padding: 4px 16px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
    }}
    
    /* Boîte de saisie interne noire/sombre */
    div[data-testid="stForm"] div[data-baseweb="input"],
    div[data-testid="stForm"] div[data-baseweb="base-input"] {{
        background-color: {input_box_bg} !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 2px 8px !important;
    }}
    
    /* Correctif du texte saisi (Blanc bien visible) */
    div[data-testid="stForm"] input {{
        color: {input_text_color} !important;
        -webkit-text-fill-color: {input_text_color} !important;
        background-color: transparent !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px !important;
    }}

    /* Placeholder quand vide */
    div[data-testid="stForm"] input::placeholder {{
        color: {placeholder_color} !important;
        -webkit-text-fill-color: {placeholder_color} !important;
        opacity: 1 !important;
        font-weight: 500 !important;
    }}

    /* Boutons Icônes (Micro et Envoi) */
    div[data-testid="stForm"] button {{
        background: transparent !important;
        border: none !important;
        color: #0F172A !important;
        font-size: 1.3rem !important;
        box-shadow: none !important;
    }}
</style>
""",
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------------------
# 3. FONCTIONS LOGIQUES ET TRAITEMENT DES DONNÉES
# ------------------------------------------------------------------------------
def calculer_capacite_dynamique(df_vols):
    if df_vols.empty or "Compagnie" not in df_vols.columns:
        return 40.0

    capacites = []
    for _, row in df_vols.iterrows():
        compagnie = str(row.get("Compagnie", "")).upper()

        if any(c in compagnie for c in ["ASKY", "CEIBA", "AIR COTE", "OVERLAND", "AIR PEACE"]):
            cap_base = 50.0
        elif any(c in compagnie for c in ["AIR FRANCE", "TURKISH", "BRUSSELS", "ROYAL AIR MAROC"]):
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
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#0F172A'), spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#0284C7'), spaceAfter=15
    )
    normal_bold = ParagraphStyle(
        'NormalBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#0F172A')
    )

    date_str = datetime.datetime.now().strftime("%d/%m/%Y à %H:%M")
    story.append(Paragraph("✈️ AeroFlow — Control Center AIGE", title_style))
    story.append(Paragraph(f"Aéroport International Gnassingbé Eyadéma (AIGE) | Rapport Opérationnel du {date_str}", subtitle_style))
    story.append(Spacer(1, 10))

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
# 4. EN-TÊTE DE L'APPLICATION
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
# 5. CONTINUATION SIDEBAR (CHARGEMENT DONNÉES & SLIDERS)
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("---")
    st.subheader("📂 Données de vol")
    fichier_importe = st.file_uploader(
        "Charger le programme des vols (CSV)", type=["csv"]
    )

    csv_modele_exemple = "Vol,Compagnie,Heure_Arrivee,Passagers,Temps_Escale_Min,Taux_Transit\nKP010,ASKY,11:30,120,40,0.45\nAF850,Air France,14:15,280,90,0.15\nET901,Ethiopian Airlines,16:45,190,35,0.30"
    st.download_button(
        label="📥 Télécharger le modèle CSV exemple",
        data=csv_modele_exemple,
        file_name="modele_vols_aige.csv",
        mime="text/csv",
    )

    if fichier_importe is not None:
        try:
            st.session_state["df_vols"] = charger_et_nettoyer_donnees(
                fichier_importe
            )
            st.success("Fichier personnalisé actif")
        except Exception as e:
            st.error(f"Erreur de lecture : {e}")

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
# 6. KPIS & INDICATEURS CLÉS
# ------------------------------------------------------------------------------
vols_critiques = (
    df[df["Temps_Escale_Min"] <= 45]
    if "Temps_Escale_Min" in df.columns
    else pd.DataFrame()
)

c1, c2, c3, c4 = st.columns(4)

total_passagers = int(df["Passagers"].sum()) if "Passagers" in df.columns else 0
total_transit = int(df["Passagers_Transit"].sum()) if "Passagers_Transit" in df.columns else 0
capacite_totale = int(guichets_ouverts * capacite_agent_heure)

with c1:
    st.markdown(f'<div class="kpi-container"><div class="kpi-label">Passagers Attendus</div><div class="kpi-val">{total_passagers:,} pax</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="kpi-container"><div class="kpi-label">Flux Transit</div><div class="kpi-val">{total_transit:,} pax</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="kpi-container"><div class="kpi-label">Capacité Traitement</div><div class="kpi-val">{capacite_totale:,} pax/h</div></div>', unsafe_allow_html=True)
with c4:
    alert_style = "kpi-container-alert" if len(vols_critiques) > 0 else ""
    color_val = "#EF4444" if len(vols_critiques) > 0 else "#10B981"
    st.markdown(f'<div class="kpi-container {alert_style}"><div class="kpi-label">Vols Critiques (≤45 min)</div><div class="kpi-val" style="color: {color_val};">{len(vols_critiques):,} Vol(s)</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 7. GRAPHIQUES ET ANALYSE
# ------------------------------------------------------------------------------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Affluence Globale par Tranche Horaire")
    if "Tranche_Horaire" in df.columns and "Passagers" in df.columns:
        df_affluence_heure = df.groupby("Tranche_Horaire")["Passagers"].sum().reset_index()
        fig_affluence = px.bar(df_affluence_heure, x="Tranche_Horaire", y="Passagers", text_auto=True, color="Passagers", color_continuous_scale="Blues", template=plotly_template)
        fig_affluence.update_layout(xaxis_title="Tranche Horaire", yaxis_title="Total Passagers", margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_affluence, use_container_width=True)

with col_right:
    st.subheader("⏱️ Répartition des Temps d'Escale (Distribution)")
    if "Temps_Escale_Min" in df.columns:
        bins = [0, 30, 45, 60, 90, 120, 999]
        labels = ["< 30 min", "30-45 min (Critique)", "45-60 min", "60-90 min", "90-120 min", "> 120 min"]
        df["Plage_Escale"] = pd.cut(df["Temps_Escale_Min"], bins=bins, labels=labels)
        df_escale_group = df["Plage_Escale"].value_counts().reset_index()
        df_escale_group.columns = ["Plage_Escale", "Nombre_de_Vols"]

        fig_transit = px.bar(df_escale_group, x="Plage_Escale", y="Nombre_de_Vols", color="Nombre_de_Vols", color_continuous_scale="Reds_r", text_auto=True, template=plotly_template)
        fig_transit.update_layout(xaxis_title="Plage de Temps d'Escale", yaxis_title="Nombre de Vols", margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_transit, use_container_width=True)

# ------------------------------------------------------------------------------
# 8. CENTRE D'ALERTES & LECTEUR AUDIO INTERACTIF
# ------------------------------------------------------------------------------
st.markdown("---")
st.subheader("⚠️ Centre d'Alertes et Annonces")

if len(vols_critiques) > 0:
    col_btn, col_info = st.columns([1, 2])

    with col_btn:
        langue_choisie = st.radio("🌐 Langue de l'annonce vocale :", options=["Français", "English"], horizontal=True, key="choix_langue_audio")
        nb_crit = len(vols_critiques)
        total_pax_crit = int(vols_critiques["Passagers_Transit"].sum())

        if langue_choisie == "English":
            code_lang, message = "en", f"Attention Security Control. General alert. A total of {nb_crit} critical flights have been detected, representing {total_pax_crit} passengers in tight connections."
        else:
            code_lang, message = "fr", f"Attention PC Sécurité. Alerte générale. Un total de {nb_crit} vols critiques a été détecté, représentant {total_pax_crit} passagers en correspondance rapide."

        try:
            fp = io.BytesIO()
            tts = gTTS(text=message, lang=code_lang)
            tts.write_to_fp(fp)
            fp.seek(0)
            st.audio(fp.read(), format="audio/mp3")
            st.info(f"Annonce disponible : « {message} »")
        except Exception as e:
            st.error(f"Erreur de génération vocale : {e}")

    with col_info:
        s = "s" if len(vols_critiques) > 1 else ""
        st.markdown(f'<div style="background-color: #DC2626; color: #FFFFFF; padding: 14px 18px; border-radius: 8px; font-weight: 700; font-size: 1.05rem; margin-bottom: 15px;">⚠️ {len(vols_critiques):,} vol{s} critique{s} détecté{s} (Escale ≤ 45 min)</div>', unsafe_allow_html=True)

    with st.container(height=280):
        for _, vol in vols_critiques.iterrows():
            st.error(f"🔴 **[Vol {vol.get('Vol', 'N/A')} - {vol.get('Compagnie', 'N/A')}]** : Arrivée à **{vol.get('Heure_Arrivee', 'N/A')}** | **{vol.get('Passagers_Transit', 0)} pax transit** | Escale: **{vol.get('Temps_Escale_Min', 0)} min**")
else:
    st.success("✅ Aucun risque de correspondance détecté pour le moment.")

# ------------------------------------------------------------------------------
# 9. TABLEAU DE DONNÉES DÉTAILLÉ
# ------------------------------------------------------------------------------
with st.expander("📄 Voir le programme détaillé des vols (AIGE)"):
    st.dataframe(df, height=400, hide_index=True)

# ------------------------------------------------------------------------------
# 10. CENTRE D'EXPORTATION & RAPPORTS
# ------------------------------------------------------------------------------
st.markdown("---")
st.subheader("📥 Exportation & Rapports d'Exploitation")

exp_col1, exp_col2, exp_col3 = st.columns(3)

with exp_col1:
    st.markdown("**1. Données des Vols Critiques (CSV)**")
    if not vols_critiques.empty:
        st.download_button(label="📄 Télécharger Vols Critiques (.csv)", data=vols_critiques.to_csv(index=False, encoding="utf-8-sig"), file_name=f"vols_critiques_AIGE_{datetime.date.today()}.csv", mime="text/csv")
    else:
        st.info("Aucun vol critique à exporter.")

with exp_col2:
    st.markdown("**2. Programme Complet des Vols (CSV)**")
    st.download_button(label="📊 Télécharger Programme Complet (.csv)", data=df.to_csv(index=False, encoding="utf-8-sig"), file_name=f"programme_vols_AIGE_{datetime.date.today()}.csv", mime="text/csv")

with exp_col3:
    st.markdown("**3. Rapport Synthétique Officiel (PDF)**")
    if REPORTLAB_AVAILABLE:
        st.download_button(label="📑 Télécharger le Rapport (.pdf)", data=generer_pdf_rapport(df, vols_critiques, total_passagers, total_transit, guichets_ouverts), file_name=f"Rapport_Exploitation_AIGE_{datetime.date.today()}.pdf", mime="application/pdf")
    else:
        st.warning("Module ReportLab indisponible pour l'export PDF.")

# ==============================================================================
# 11. ASSISTANT VIRTUEL D'EXPLOITATION INTELLIGENT (AeroBot)
# ==============================================================================
st.markdown("---")
st.subheader("🤖 AeroBot — Assistant Virtuel d'Exploitation")

# 1. Initialisation de l'historique
if "messages_chat" not in st.session_state:
    st.session_state["messages_chat"] = [
        {"role": "assistant", "content": "Salut ! Je suis AeroBot, votre assistant d'exploitation pour l'AIGE. Comment puis-je vous aider ?"}
    ]

prompt_utilisateur = None
mode_vocal = False

# Zone conteneur pour l'historique des messages (AFFICHER EN HAUT)
chat_container = st.container()

# Formulaire de saisie (AFFICHER EN BAS)
with st.form(key="gemini_chat_form", clear_on_submit=True):
    col_input, col_mic, col_send = st.columns([10, 1, 1])
    
    with col_input:
        prompt_texte = st.text_input(
            "", 
            placeholder="Posez votre question à AeroBot...", 
            label_visibility="collapsed",
            key="input_gemini_style"
        )
    
    with col_mic:
        if VOICE_INPUT_AVAILABLE:
            audio_recorded = mic_recorder(
                start_prompt="🎙️",
                stop_prompt="⏹️",
                key="mic_gemini_bar"
            )
            if audio_recorded and "bytes" in audio_recorded:
                audio_bytes = audio_recorded["bytes"]
                recognizer = sr.Recognizer()
                try:
                    audio_file = io.BytesIO(audio_bytes)
                    with sr.AudioFile(audio_file) as source:
                        audio_data = recognizer.record(source)
                        prompt_utilisateur = recognizer.recognize_google(audio_data, language="fr-FR")
                except Exception:
                    try:
                        audio_file.seek(0)
                        with sr.AudioFile(audio_file) as source:
                            audio_data = recognizer.record(source)
                            prompt_utilisateur = recognizer.recognize_google(audio_data, language="en-US")
                    except Exception:
                        st.error("Rien n'a été entendu.")
                
                if prompt_utilisateur:
                    mode_vocal = True
        else:
            st.write("🎙️")

    with col_send:
        submit_btn = st.form_submit_button("➔")

    if submit_btn and prompt_texte:
        prompt_utilisateur = prompt_texte
        mode_vocal = False

# 2. Traitement de la logique de réponse avec filtrage intelligent
if prompt_utilisateur:
    # Ajouter le message utilisateur à l'historique
    st.session_state["messages_chat"].append({"role": "user", "content": prompt_utilisateur})

    q = prompt_utilisateur.lower().strip()
    reponse = ""
    lang_rep = "fr"

    # LISTES DE DÉTECTION

    # 1. Mots / Expressions de Salutation & Politesse
    salutations_fr = [
        "salut", "bonjour", "bonsoir", "coucou", "yo", "cc", "hello", "hi", "hey",
        "ça va", "ca va", "comment vas", "comment tu vas", "tu vas bien", "vas bien",
        "forme", "bien ?", "bien?", "sava", "sa va", "qui es tu", "qui es-tu",
        "merci", "meci", "thx", "thanks", "super", "parfait", "cool", "au revoir", "bye"
    ]
    
    salutations_en = [
        "hello", "hi", "hey", "good morning", "good evening", "how are you", 
        "how do you do", "whats up", "what's up", "how is it going", "thanks", "thank you"
    ]

    # 2. Mots-clés Métier (Aéroport, Vols, Passagers, etc.)
    mots_metier = [
        "vol", "vols", "critique", "critiques", "risque", "alerte", "retard", "escale",
        "guichet", "guichets", "agent", "agents", "ouvrir", "capacite", "capacité",
        "passager", "passagers", "pax", "flux", "transit", "total", "affluence",
        "compagnie", "compagnies", "aige", "aeroflow", "aerobot", "rapport", "pdf",
        "flight", "flights", "counter", "counters", "passenger", "passengers"
    ]

    # VÉRIFICATION DE LA NATURE DE LA QUESTION
    est_salutation_fr = any(s in q for s in salutations_fr)
    est_salutation_en = any(s in q for s in salutations_en)
    est_metier = any(m in q for m in mots_metier)

    # 3. LOGIQUE D'AIGUILLAGE DES RÉPONSES

    # CAS A : C'est une salutation ou de la politesse
    if est_salutation_fr or est_salutation_en:
        if est_salutation_en and not est_salutation_fr:
            lang_rep = "en"
            if any(k in q for k in ["how are you", "how is it going", "whats up", "what's up"]):
                reponse = "I'm doing great, thank you! Ready to help with flight operations. How can I assist you today?"
            elif any(k in q for k in ["thanks", "thank you"]):
                reponse = "You're welcome! Let me know if you need any other operational details."
            else:
                reponse = "Hello! How can I help you today with airport operations?"
        else:
            lang_rep = "fr"
            if any(k in q for k in ["ça va", "ca va", "comment vas", "tu vas bien", "forme", "sava", "sa va"]):
                reponse = "Je vais très bien, merci ! Prêt pour le suivi des vols. Que puis-je faire pour vous ?"
            elif any(k in q for k in ["merci", "super", "parfait", "cool"]):
                reponse = "Avec plaisir ! N'hésitez pas si vous avez d'autres questions sur l'exploitation."
            elif any(k in q for k in ["qui es tu", "qui es-tu"]):
                reponse = "Je suis **AeroBot**, l'assistant virtuel d'exploitation de l'AIGE. Je vous aide à surveiller les vols critiques et à gérer les flux !"
            else:
                reponse = "Salut ! Comment puis-je vous aider aujourd'hui sur l'exploitation des vols ?"

    # CAS B : C'est une question métier (Aéroport / Vols)
    elif est_metier:
        is_english = any(w in q for w in ["flight", "critical", "counter", "agent", "passenger"])
        
        if is_english:
            lang_rep = "en"
            if any(k in q for k in ["critical", "risk", "alert"]):
                if not vols_critiques.empty:
                    nb = len(vols_critiques)
                    pax_t = int(vols_critiques["Passagers_Transit"].sum())
                    reponse = f"⚠️ We have {nb} critical flight(s) representing {pax_t} transit passengers."
                else:
                    reponse = "🟢 Everything is clear! No critical flights reported."
            else:
                reponse = f"🤖 Current status: {guichets_ouverts} counters open, {total_passagers:,} expected passengers."
        else:
            lang_rep = "fr"
            if any(k in q for k in ["critique", "risque", "alerte", "retard", "vol", "escale"]):
                if not vols_critiques.empty:
                    nb = len(vols_critiques)
                    pax_t = int(vols_critiques["Passagers_Transit"].sum())
                    reponse = f"⚠️ Nous avons {nb} vol(s) critique(s) représentant {pax_t} passagers en transit rapide."
                else:
                    reponse = "🟢 Aucun vol critique n'est à signaler. La situation est sous contrôle !"
            elif any(k in q for k in ["guichet", "agent", "ouvrir", "capacite"]):
                reponse = f"💡 Actuellement, {guichets_ouverts} guichet(s) ouvert(s). Il est recommandé d'en ouvrir au moins {guichets_recommandes}."
            elif any(k in q for k in ["passager", "flux", "total", "transit", "affluence"]):
                reponse = f"📊 Passagers attendus aujourd'hui : {total_passagers:,} (dont {total_transit:,} en transit)."
            else:
                reponse = "🤖 Je peux vous renseigner sur les **vols critiques**, le nombre de **guichets** ou les **flux de passagers**."

    # CAS C : C'est totalement hors-sujet (Ex: devoirs, recettes, météo, etc.)
    else:
        lang_rep = "fr"
        reponse = (
            "Je ne peux pas vous aider pour cette question. "
            "Cependant, je peux vous renseigner sur la gestion des vols critiques, "
            "l'estimation des guichets à ouvrir ou le suivi des flux de passagers à l'AIGE."
        )

    # Ajouter la réponse du bot à l'historique
    st.session_state["messages_chat"].append({"role": "assistant", "content": reponse})

    if mode_vocal:
        try:
            texte_audio = reponse.replace("*", "").replace("#", "")
            tts_bot = gTTS(text=texte_audio, lang=lang_rep)
            fp_bot = io.BytesIO()
            tts_bot.write_to_fp(fp_bot)
            fp_bot.seek(0)
            st.audio(fp_bot.read(), format="audio/mp3", autoplay=True)
        except Exception:
            pass

# 3. Rendu de tous les messages dans le conteneur du HAUT
with chat_container:
    for msg in st.session_state["messages_chat"]:
        st.chat_message(msg["role"]).write(msg["content"])
