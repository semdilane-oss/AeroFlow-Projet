# ==============================================================================
# PROJET : AeroFlow - Control Center (AIGE)
# APPLICATION WEB STREAMLIT - CODE COMPLET & BILINGUE (FR / EN)
# ==============================================================================

import glob
import io
import math
import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from gtts import gTTS
from streamlit_mic_recorder import speech_to_text

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
# 1. CONFIGURATION DE LA PAGE & INITIALISATION
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="AeroFlow — Control Center AIGE",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "theme_sombre" not in st.session_state:
    st.session_state["theme_sombre"] = False

if "user_role" not in st.session_state:
    st.session_state["user_role"] = None  # 'passager', 'agent', None

if "current_user" not in st.session_state:
    st.session_state["current_user"] = ""

if "db_passagers" not in st.session_state:
    st.session_state["db_passagers"] = {}

if "messages_chat_pax" not in st.session_state:
    st.session_state["messages_chat_pax"] = []

if "messages_chat" not in st.session_state:
    st.session_state["messages_chat"] = []

# Identifiants STRICTS des agents ANAC / PC Sécurité (Mots de passe >= 6 caractères)
AGENT_CREDENTIALS = {
    "admin_anac": "anac2026",
    "agent_p2": "lome2026"
}


# ------------------------------------------------------------------------------
# 2. SELECTION DU THÈME, DE LA LANGUE & CSS DYNAMIQUE
# ------------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Configuration")
    
    # Sélecteur de langue global
    langue_interface = st.selectbox("🌐 Langue / Language", ["Français", "English"])
    
    mode_nuit = st.toggle("🌙 Mode Nuit (Sombre)", value=st.session_state["theme_sombre"])
    st.session_state["theme_sombre"] = mode_nuit

# Fonction de traduction rapide (i18n)
def t(texte_fr, texte_en):
    return texte_fr if langue_interface == "Français" else texte_en

if st.session_state["theme_sombre"]:
    bg_app = "#131314"
    text_main = "#E3E3E3"
    card_bg = "#1E1F20"
    border_color = "#444746"
    title_color = "#FFFFFF"
    plotly_template = "plotly_dark"
    
    input_box_bg = "#242731"
    input_text_color = "#FFFFFF"
    placeholder_color = "#9CA3AF"
    
    chat_bg = "#2D2E30"
    chat_text = "#E3E3E3"
    avatar_bg = "#EF4444"
    
    success_bg = "#064E3B"
    success_text = "#ECFDF5"
    alert_bg = "#2D1517"
    alert_text = "#FCA5A5"
    
    btn_bg_gradient = "linear-gradient(135deg, #059669 0%, #047857 100%)"
    banner_bg = "#2D1517"
    banner_border = "#EF4444"
    banner_text = "#FCA5A5"
else:
    bg_app = "#F8FAFC"
    text_main = "#0F172A"
    card_bg = "#FFFFFF"
    border_color = "#CBD5E1"
    title_color = "#0F172A"
    plotly_template = "plotly_white"
    
    input_box_bg = "#FFFFFF"
    input_text_color = "#0F172A"
    placeholder_color = "#64748B"
    
    chat_bg = "#E2E8F0"
    chat_text = "#0F172A"
    avatar_bg = "#0284C7"
    
    success_bg = "#DCFCE7"
    success_text = "#166534"
    alert_bg = "#FEF2F2"
    alert_text = "#991B1B"
    
    btn_bg_gradient = "linear-gradient(135deg, #10B981 0%, #059669 100%)"
    banner_bg = "#FEE2E2"
    banner_border = "#EF4444"
    banner_text = "#991B1B"

st.markdown(
    f"""
<style>
    .stApp {{ background-color: {bg_app} !important; color: {text_main} !important; }}
    
    .header-title {{ font-family: 'Segoe UI', sans-serif; font-weight: 800; font-size: 2.2rem; color: {title_color}; }}
    .header-subtitle {{ color: #0284C7; font-weight: 600; font-size: 1rem; margin-bottom: 20px; }}
    
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {{
        color: {text_main} !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
    }}
    .stTabs [data-baseweb="tab-list"] button {{
        background-color: {card_bg} !important;
        border: 1px solid {border_color} !important;
        border-radius: 8px 8px 0 0 !important;
        margin-right: 4px;
    }}
    .stTabs [data-baseweb="tab"] {{ height: 50px; white-space: pre-wrap; }}

    .kpi-container {{
        background-color: {card_bg}; border: 1px solid {border_color}; border-radius: 12px;
        padding: 18px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); border-top: 4px solid #0284C7;
    }}
    .kpi-container-alert {{ border-top: 4px solid #EF4444 !important; background-color: {alert_bg}; }}
    .kpi-label {{ font-size: 0.8rem; font-weight: 700; color: {'#9CA3AF' if st.session_state['theme_sombre'] else '#475569'}; text-transform: uppercase; }}
    .kpi-val {{ font-size: 1.8rem; font-weight: 800; color: {title_color}; margin-top: 4px; }}
    
    div[data-testid="stRadio"] label, div[data-testid="stRadio"] p,
    .stTextInput label, .stSelectbox label, .stCheckbox label {{
        color: {text_main} !important;
        font-weight: 600 !important;
    }}
    
    div.stButton > button, div[data-testid="stFormSubmitButton"] > button {{
        background: {btn_bg_gradient} !important;
        color: #FFFFFF !important; 
        font-weight: 700 !important; 
        border-radius: 8px !important;
        border: none !important; 
        padding: 10px 20px !important; 
        width: 100%;
    }}
    
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

    div[data-testid="stForm"] {{
        background-color: {card_bg} !important;
        border: 1px solid {border_color} !important;
        border-radius: 16px !important;
        padding: 20px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
    }}
    
    div[data-testid="stForm"] input, .stTextInput input {{
        color: {input_text_color} !important;
        -webkit-text-fill-color: {input_text_color} !important;
        background-color: {input_box_bg} !important;
        font-weight: 600 !important;
        border: 1px solid {border_color} !important;
    }}

    div[data-testid="stForm"] input::placeholder, .stTextInput input::placeholder {{
        color: {placeholder_color} !important;
        -webkit-text-fill-color: {placeholder_color} !important;
        opacity: 1 !important;
    }}

    div[data-testid="stChatInput"] textarea {{
        color: {input_text_color} !important;
        -webkit-text-fill-color: {input_text_color} !important;
        background-color: {input_box_bg} !important;
        font-weight: 600 !important;
    }}
    div[data-testid="stChatInput"] textarea::placeholder {{
        color: {placeholder_color} !important;
        -webkit-text-fill-color: {placeholder_color} !important;
        opacity: 1 !important;
    }}
    div[data-testid="stChatInput"] {{
        background-color: {input_box_bg} !important;
        border: 1px solid #EF4444 !important;
        border-radius: 12px !important;
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
# 4. GESTION DES ACCÈS / AUTHENTIFICATION
# ------------------------------------------------------------------------------

if st.session_state["user_role"] is None:
    st.markdown(f'<div class="header-title">{t("🛫 Bienvenue sur AeroFlow — AIGE Lomé", "🛫 Welcome to AeroFlow — AIGE Lomé")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="header-subtitle">{t("Veuillez choisir votre espace pour accéder à la plateforme.", "Please choose your space to access the platform.")}</div>', unsafe_allow_html=True)

    tab_passager, tab_agent = st.tabs([
        t("👤 Espace Passager", "👤 Passenger Area"), 
        t("🛡️ Espace Sécurité & Régulation AIGE", "🛡️ AIGE Security & Regulation Area")
    ])

    with tab_passager:
        st.subheader(t("Accès Voyageurs & Passagers", "Traveler & Passenger Access"))
        
        mode_passager = st.radio(
            t("Action :", "Action:"), 
            [
                t("Se connecter", "Sign In"), 
                t("Première connexion (Activer mon compte)", "First login (Activate my account)"), 
                t("Mot de passe oublié ?", "Forgot password?")
            ],
            horizontal=True,
            key="radio_mode_pax"
        )

        afficher_mdp_pax = st.checkbox(t("👁️ Afficher les caractères en clair", "👁️ Show plain text characters"), key="chk_pax_visible")
        input_type_pax = "default" if afficher_mdp_pax else "password"

        if mode_passager == t("Première connexion (Activer mon compte)", "First login (Activate my account)"):
            st.info(t("💡 Indiquez votre numéro de vol ou email, puis définissez votre mot de passe (6 caractères minimum).", "💡 Enter your flight number or email, then set your password (minimum 6 characters)."))
            with st.form("form_inscription_pax"):
                pax_id = st.text_input(t("Numéro de Vol ou Email", "Flight Number or Email"), placeholder="ex: KP010 ou passager@gmail.com")
                pax_pass1 = st.text_input(t("Créer un mot de passe (min. 6 caractères)", "Create a password (min. 6 chars)"), type=input_type_pax)
                pax_pass2 = st.text_input(t("Confirmer le mot de passe", "Confirm password"), type=input_type_pax)
                btn_creer = st.form_submit_button(t("Se connecter", "Sign In"))

                if btn_creer:
                    if not pax_id or not pax_pass1:
                        st.error(t("Veuillez remplir tous les champs.", "Please fill in all fields."))
                    elif len(pax_pass1) < 6:
                        st.error(t("⚠️ Le mot de passe doit contenir au moins 6 caractères.", "⚠️ Password must contain at least 6 characters."))
                    elif pax_pass1 != pax_pass2:
                        st.error(t("Les mots de passe ne correspondent pas.", "Passwords do not match."))
                    else:
                        st.session_state["db_passagers"][pax_id] = pax_pass1
                        st.session_state["user_role"] = "passager"
                        st.session_state["current_user"] = pax_id
                        st.success(t("Compte activé avec succès !", "Account successfully activated!"))
                        st.rerun()

        elif mode_passager == t("Se connecter", "Sign In"):
            with st.form("form_login_pax"):
                pax_id = st.text_input(t("Numéro de Vol ou Email", "Flight Number or Email"))
                pax_pass = st.text_input(t("Mot de passe", "Password"), type=input_type_pax)
                btn_login_pax = st.form_submit_button(t("Se connecter", "Sign In"))

                if btn_login_pax:
                    if pax_id in st.session_state["db_passagers"] and st.session_state["db_passagers"][pax_id] == pax_pass:
                        st.session_state["user_role"] = "passager"
                        st.session_state["current_user"] = pax_id
                        st.rerun()
                    else:
                        st.error(t("Identifiant ou mot de passe incorrect.", "Incorrect ID or password."))

        else:  
            st.warning(t("🔄 Réinitialisation de votre mot de passe voyageur (6 caractères minimum)", "🔄 Reset your traveler password (minimum 6 characters)"))
            with st.form("form_oubli_pax"):
                pax_id_reset = st.text_input(t("Votre Numéro de Vol ou Email enregistré", "Your registered Flight Number or Email"))
                pax_nouveau_pass = st.text_input(t("Nouveau mot de passe (min. 6 caractères)", "New password (min. 6 chars)"), type=input_type_pax)
                btn_reset_pax = st.form_submit_button(t("Mettre à jour mon mot de passe", "Update my password"))

                if btn_reset_pax:
                    if pax_id_reset not in st.session_state["db_passagers"]:
                        st.error(t("Cet identifiant n'est associé à aucun compte enregistré.", "This ID is not associated with any registered account."))
                    elif len(pax_nouveau_pass) < 6:
                        st.error(t("⚠️ Le nouveau mot de passe doit contenir au moins 6 caractères.", "⚠️ The new password must contain at least 6 characters."))
                    else:
                        st.session_state["db_passagers"][pax_id_reset] = pax_nouveau_pass
                        st.success(t("Mot de passe modifié avec succès ! Vous pouvez vous connecter.", "Password updated successfully! You can now log in."))

    with tab_agent:
        st.subheader(t("Portail Opérationnel — Aérodrome International Gnassingbé Eyadéma", "Operational Portal — Gnassingbé Eyadéma International Aerodrome"))
        st.markdown(f'<div style="background-color: {banner_bg}; color: {banner_text}; padding: 12px 16px; border-radius: 8px; font-weight: 700; margin-bottom: 15px; border: 1px solid {banner_border};">⚠️ {t("Zone protégée réservée aux agents habilités de l\'ANAC. Les identifiants sont strictement contrôlés.", "Protected area reserved for authorized ANAC agents. Credentials are strictly controlled.")}</div>', unsafe_allow_html=True)

        afficher_mdp_agent = st.checkbox(t("👁️ Afficher les caractères en clair", "👁️ Show plain text characters"), key="chk_agent_visible")
        input_type_agent = "default" if afficher_mdp_agent else "password"

        mode_agent = st.radio(t("Option agent :", "Agent option:"), [t("Connexion", "Sign In"), t("Modifier mon mot de passe agent", "Change agent password")], horizontal=True)

        if mode_agent == t("Connexion", "Sign In"):
            with st.form("form_login_agent"):
                agent_user = st.text_input(t("Identifiant Agent officiel (ex: admin_anac)", "Official Agent ID (e.g. admin_anac)"))
                agent_pass = st.text_input(t("Mot de passe", "Password"), type=input_type_agent)
                btn_login_agent = st.form_submit_button(t("Se connecter", "Sign In"))

                if btn_login_agent:
                    if agent_user in AGENT_CREDENTIALS and AGENT_CREDENTIALS[agent_user] == agent_pass:
                        st.session_state["user_role"] = "agent"
                        st.session_state["current_user"] = agent_user
                        st.rerun()
                    else:
                        st.error(t("⚠️ Accès refusé. Identifiant ou mot de passe agent invalide.", "⚠️ Access denied. Invalid agent ID or password."))
        else:
            with st.form("form_reset_agent"):
                st.info(t("Modifiez votre mot de passe agent (6 caractères minimum requis).", "Update your agent password (minimum 6 characters required)."))
                agent_user_r = st.text_input(t("Identifiant Agent officiel", "Official Agent ID"))
                ancien_p = st.text_input(t("Ancien mot de passe", "Old password"), type=input_type_agent)
                nouveau_p = st.text_input(t("Nouveau mot de passe (min. 6 caractères)", "New password (min. 6 chars)"), type=input_type_agent)
                btn_chg_agent = st.form_submit_button(t("Changer mon mot de passe", "Change my password"))

                if btn_chg_agent:
                    if agent_user_r not in AGENT_CREDENTIALS or AGENT_CREDENTIALS[agent_user_r] != ancien_p:
                        st.error(t("Identifiant ou ancien mot de passe incorrect.", "Incorrect ID or old password."))
                    elif len(nouveau_p) < 6:
                        st.error(t("⚠️ Le nouveau mot de passe doit contenir au moins 6 caractères.", "⚠️ The new password must contain at least 6 characters."))
                    else:
                        AGENT_CREDENTIALS[agent_user_r] = nouveau_p
                        st.success(t("Mot de passe agent mis à jour avec succès !", "Agent password successfully updated!"))

    st.stop()


# ------------------------------------------------------------------------------
# 5. VUE ESPACE PASSAGER
# ------------------------------------------------------------------------------

if st.session_state["user_role"] == "passager":
    st.sidebar.title(t("👤 Espace Voyageur", "👤 Traveler Area"))
    st.sidebar.write(f"{t('Passager connecté :', 'Logged-in passenger:')} **{st.session_state['current_user']}**")
    if st.sidebar.button(t("Déconnexion", "Sign Out")):
        st.session_state["user_role"] = None
        st.rerun()

    st.markdown(f'<div class="header-title">{t("✈️ Votre Espace Voyage — AIGE Lomé", "✈️ Your Travel Space — AIGE Lomé")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="background-color: {success_bg}; color: {success_text}; padding: 12px 16px; border-radius: 8px; font-weight: 600; margin-bottom: 20px;">{t("Bienvenue ! Retrouvez ici les informations de vol et services utiles.", "Welcome! Find your flight information and useful services here.")}</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="kpi-container"><div class="kpi-label">{t("Statut du Vol", "Flight Status")}</div><div class="kpi-val" style="color: #0284C7;">{t("À l\'heure 🟢", "On Time 🟢")}</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-container"><div class="kpi-label">{t("Porte d\'Embarquement", "Boarding Gate")}</div><div class="kpi-val">{t("Porte 02", "Gate 02")}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kpi-container"><div class="kpi-label">{t("Zone d\'Enregistrement", "Check-in Zone")}</div><div class="kpi-val">{t("Guichets 01 à 04", "Counters 01 to 04")}</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-container"><div class="kpi-label">{t("Livraison Bagages", "Baggage Claim")}</div><div class="kpi-val">{t("Tapis 1", "Belt 1")}</div></div>', unsafe_allow_html=True)

    # Chatbot intégré pour l'espace passager
    st.markdown("---")
    st.subheader(t("💬 Assistant Virtuel AeroFlow", "💬 AeroFlow Virtual Assistant"))
    st.markdown(t("Posez vos questions concernant votre vol, l'embarquement ou les services de l'AIGE (par écrit ou par la voix).", "Ask your questions regarding your flight, boarding, or AIGE services (by text or voice)."))

    if not st.session_state["messages_chat_pax"]:
        st.session_state["messages_chat_pax"] = [
            {"role": "assistant", "content": t("Bonjour ! Je suis l'assistant virtuel d'AeroFlow. Comment puis-je vous aider pour votre voyage aujourd'hui ?", "Hello! I am AeroFlow's virtual assistant. How can I help you with your trip today?")}
        ]

    # Conteneur pour afficher l'historique du chat en haut
    chat_container = st.container()
    with chat_container:
        for message in st.session_state["messages_chat_pax"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Disposition intégrée (Zone de texte + Bouton micro côte à côte)
    col_input_pax, col_mic_pax = st.columns([12, 1])
    
    with col_mic_pax:
        langue_stt = "fr-FR" if langue_interface == "Français" else "en-US"
        texte_vocal_pax = speech_to_text(
            start_prompt="🎙️",
            stop_prompt="⏹️",
            language=langue_stt,
            key="mic_pax_inline"
        )

    with col_input_pax:
        prompt_saisi_pax = st.chat_input(t("Tapez votre question ici...", "Type your question here..."))

    prompt_pax = texte_vocal_pax if texte_vocal_pax else prompt_saisi_pax

    if prompt_pax:
        st.session_state["messages_chat_pax"].append({"role": "user", "content": prompt_pax})
        
        p_low = prompt_pax.lower()
        est_ang_pax = any(w in p_low for w in ["flight", "gate", "baggage", "status", "time", "where", "how", "help", "hello", "hi", "available"]) or langue_interface == "English"

        # Traitement intelligent et dynamique des questions
        if any(w in p_low for w in ["salut", "bonjour", "hello", "hi", "coucou"]):
            rep_pax = "Bonjour ! Je suis l'assistant AeroFlow de l'AIGE. Que puis-je faire pour vous ?" if not est_ang_pax else "Hello! I am the AeroFlow assistant at AIGE. How can I help you?"
        elif any(w in p_low for w in ["vol", "vols", "disponible", "disponibles", "flight", "flights", "available"]):
            rep_pax = "Voici les principaux vols disponibles aujourd'hui à l'AIGE : ASKY (vols régionaux fréquents), Air France, Ethiopian Airlines et Turkish Airlines." if not est_ang_pax else "Here are the main flights available today at AIGE: ASKY (frequent regional flights), Air France, Ethiopian Airlines, and Turkish Airlines."
        elif any(w in p_low for w in ["porte", "gate", "embarquement", "boarding"]):
            rep_pax = "Votre vol embarque actuellement depuis la **Porte 02**." if not est_ang_pax else "Your flight is currently boarding from **Gate 02**."
        elif any(w in p_low for w in ["bagage", "baggage", "tapis", "belt"]):
            rep_pax = "La livraison de vos bagages s'effectue sur le **Tapis 1**." if not est_ang_pax else "Your baggage claim is at **Belt 1**."
        elif any(w in p_low for w in ["statut", "status", "heure", "time", "retard"]):
            rep_pax = "Votre vol est actuellement affiché **À l'heure 🟢**." if not est_ang_pax else "Your flight is currently displayed as **On Time 🟢**."
        else:
            rep_pax = f"Je suis l'assistant AeroFlow. Vous m'avez posé la question : '{prompt_pax}'. Vous pouvez me demander les vols disponibles, votre porte d'embarquement, le statut du vol ou la récupération des bagages !" if not est_ang_pax else f"I am the AeroFlow assistant. You asked: '{prompt_pax}'. You can ask me about available flights, your boarding gate, flight status, or baggage claim!"

        st.session_state["messages_chat_pax"].append({"role": "assistant", "content": rep_pax})
        st.rerun()
