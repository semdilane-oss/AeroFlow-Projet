# ==============================================================================
# PROJET : AeroFlow - Control Center (AIGE)
# APPLICATION WEB STREAMLIT - CODE COMPLET, BILINGUE & INTELLIGENT (FR / EN)
# ==============================================================================

import glob
import io
import math
import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

# Gestion optionnelle de gTTS et speech_to_text
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    from streamlit_mic_recorder import speech_to_text
    STT_AVAILABLE = True
except ImportError:
    STT_AVAILABLE = False

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
# 1. CONFIGURATION DE LA PAGE & GESTION DES THÈMES
# ------------------------------------------------------------------------------

st.set_page_config(
    page_title="AeroFlow — Control Center AIGE",
    page_icon="✈️",
    layout="wide",
)

# Initialisation des états de session
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None
if "current_user" not in st.session_state:
    st.session_state["current_user"] = ""
if "messages_chat" not in st.session_state:
    st.session_state["messages_chat"] = []
if "messages_chat_pax" not in st.session_state:
    st.session_state["messages_chat_pax"] = []
if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "Clair"

# Barre latérale pour les paramètres globaux (Thème et Langue)
st.sidebar.title("⚙️ Paramètres / Settings")

theme_choisi = st.sidebar.radio(
    "🎨 Thème de l'interface",
    ["Clair ☀️", "Sombre 🌙"],
    index=0 if st.session_state["theme_mode"] == "Clair" else 1,
    key="select_theme_radio"
)
st.session_state["theme_mode"] = "Clair" if "Clair" in theme_choisi else "Sombre"

langue_interface = st.sidebar.selectbox(
    "🌐 Langue / Language",
    ["Français", "English"],
    index=0
)

def t(fr, en):
    return fr if langue_interface == "Français" else en

# Application des styles CSS globaux (Correction Mode Clair pour visibilité parfaite des textes et labels)
if st.session_state["theme_mode"] == "Clair":
    bg_color = "#F8FAFC"
    text_color = "#0F172A"
    card_bg = "#FFFFFF"
    border_color = "#E2E8F0"
    success_bg = "#E0F2FE"
    success_text = "#0369A1"
    alert_bg = "#FEE2E2"
    alert_text = "#991B1B"
    plotly_template = "plotly"
else:
    bg_color = "#0E1117"
    text_color = "#FAFAFA"
    card_bg = "#1E293B"
    border_color = "#334155"
    success_bg = "#0C4A6E"
    success_text = "#38BDF8"
    alert_bg = "#7F1D1D"
    alert_text = "#FCA5A5"
    plotly_template = "plotly_dark"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}
    label, .stRadio label, .stTextInput label, .stSelectbox label, .stFileUploader label, .stNumberInput label {{
        color: {text_color} !important;
        font-weight: 600 !important;
    }}
    .stRadio div[data-baseweb="radio"] div {{
        color: {text_color} !important;
    }}
    .header-title {{
        font-size: 2.2rem;
        font-weight: 800;
        color: {text_color};
        margin-bottom: 0px;
    }}
    .header-subtitle {{
        font-size: 1.1rem;
        color: #64748B;
        margin-bottom: 25px;
    }}
    .kpi-container {{
        background-color: {card_bg};
        border: 1px solid {border_color};
        padding: 16px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    .kpi-container-alert {{
        background-color: {alert_bg};
        border: 1px solid #EF4444;
    }}
    .kpi-label {{
        font-size: 0.85rem;
        color: #64748B;
        font-weight: 600;
    }}
    .kpi-val {{
        font-size: 1.5rem;
        font-weight: 700;
        color: {text_color};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------------------
# 2. FONCTIONS UTILITAIRES ET DE CALCUL
# ------------------------------------------------------------------------------

@st.cache_data
def charger_et_nettoyer_donnees(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file)
    except Exception:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding="latin1")

    df.columns = df.columns.str.strip()
    
    if "Passagers" in df.columns:
        df["Passagers"] = pd.to_numeric(df["Passagers"], errors="coerce").fillna(100).astype(int)
    else:
        df["Passagers"] = 100

    if "Temps_Escale_Min" in df.columns:
        df["Temps_Escale_Min"] = pd.to_numeric(df["Temps_Escale_Min"], errors="coerce").fillna(45).astype(int)
    else:
        df["Temps_Escale_Min"] = 45

    if "Taux_Transit" in df.columns:
        df["Taux_Transit"] = pd.to_numeric(df["Taux_Transit"], errors="coerce").fillna(0.3)
    else:
        df["Taux_Transit"] = 0.3

    df["Passagers_Transit"] = (df["Passagers"] * df["Taux_Transit"]).astype(int)

    if "Heure_Arrivee" in df.columns:
        def extraire_tranche(h_str):
            try:
                h_dt = datetime.datetime.strptime(str(h_str).strip(), "%H:%M")
                h_arrondie = h_dt.hour
                return f"{h_arrondie:02d}:00 - {(h_arrondie+1)%24:02d}:00"
            except:
                return "12:00 - 13:00"
        df["Tranche_Horaire"] = df["Heure_Arrivee"].apply(extraire_tranche)
    else:
        df["Heure_Arrivee"] = "12:00"
        df["Tranche_Horaire"] = "12:00 - 13:00"

    return df


def calculer_capacite_dynamique(df):
    if "Temps_Escale_Min" not in df.columns:
        return 45
    moy_escale = df["Temps_Escale_Min"].mean()
    if moy_escale < 40:
        return 35
    elif moy_escale > 90:
        return 55
    else:
        return 45


def generer_pdf_rapport(df, vols_critiques, total_pax, total_transit, guichets):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "AEROPORT INTERNATIONAL GNASSINGBE EYADEMA (AIGE)")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 70, f"Rapport d'Exploitation & Regulation - {datetime.date.today()}")
    
    c.line(50, height - 85, width - 50, height - 85)

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 120, "SYNTHESE DES FLUX OPERATIONNELS")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 140, f"- Passagers Totaux Attendus : {total_pax:,} pax")
    c.drawString(50, height - 160, f"- Flux en Transit Global : {total_transit:,} pax")
    c.drawString(50, height - 180, f"- Guichets Actifs sur le Terrain : {guichets} guichets")
    c.drawString(50, height - 200, f"- Nombre de Vols Critiques (Escale <= 45 min) : {len(vols_critiques)}")

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 240, "DETAILS DES VOLS CRITIQUES NECESSITANT UNE ACTION RAPIDE :")
    
    y = height - 265
    for _, row in vols_critiques.iterrows():
        if y < 100:
            c.showPage()
            y = height - 50
        ligne_txt = f"Vol {row.get('Vol', 'N/A')} ({row.get('Compagnie', 'N/A')}) - Arrivée: {row.get('Heure_Arrivee', 'N/A')} - Escale: {row.get('Temps_Escale_Min', 0)} min"
        c.drawString(60, y, ligne_txt)
        y = y - 20

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


if "df_vols" not in st.session_state:
    data_defaut = pd.DataFrame({
        "Vol": ["KP010", "AF850", "ET901", "AT522", "KQ554"],
        "Compagnie": ["ASKY", "Air France", "Ethiopian Airlines", "Royal Air Maroc", "Kenya Airways"],
        "Heure_Arrivee": ["11:30", "14:15", "16:45", "18:00", "20:30"],
        "Passagers": [120, 280, 190, 150, 210],
        "Temps_Escale_Min": [40, 90, 35, 110, 50],
        "Taux_Transit": [0.45, 0.15, 0.30, 0.20, 0.25]
    })
    st.session_state["df_vols"] = charger_et_nettoyer_donnees(data_defaut)


# ------------------------------------------------------------------------------
# 3. ÉCRAN D'AUTHENTIFICATION UNIQUE
# ------------------------------------------------------------------------------

if st.session_state["user_role"] is None:
    st.markdown(f'<div class="header-title">{t("✈️ AeroFlow — Portail d\'Accès AIGE", "✈️ AeroFlow — AIGE Access Portal")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="header-subtitle">{t("Veuillez vous identifier pour accéder à votre espace dédié.", "Please authenticate to access your dedicated space.")}</div>', unsafe_allow_html=True)

    with st.form("form_auth"):
        st.subheader(t("🔐 Connexion Sécurisée", "🔐 Secure Login"))
        id_saisi = st.text_input(t("Numéro de Vol ou Email de l'Agent", "Flight Number or Agent Email"))
        mdp_saisi = st.text_input(t("Mot de passe", "Password"), type="password")
        
        btn_valider = st.form_submit_button(t("Se connecter", "Sign In"))

        if btn_valider:
            id_propre = id_saisi.strip()
            if id_propre.upper().startswith("KP") or id_propre.upper().startswith("AF") or id_propre.upper().startswith("ET") or id_propre.upper().startswith("AT") or id_propre.upper().startswith("KQ") or "@" not in id_propre:
                st.session_state["user_role"] = "passager"
                st.session_state["current_user"] = id_propre.upper() if id_propre else "Voyageur AIGE"
                st.rerun()
            elif "@" in id_propre or "agent" in id_propre.lower() or "admin" in id_propre.lower() or len(id_propre) > 0:
                st.session_state["user_role"] = "agent"
                st.session_state["current_user"] = id_propre if id_propre else "Agent Anac"
                st.rerun()
            else:
                st.error(t("Identifiant non reconnu. Veuillez réessayer.", "Unrecognized identifier. Please try again."))


# ------------------------------------------------------------------------------
# 4. VUE ESPACE PASSAGER
# ------------------------------------------------------------------------------

elif st.session_state["user_role"] == "passager":
    st.sidebar.title(t("👤 Espace Voyageur", "👤 Traveler Area"))
    st.sidebar.write(f"{t('Passager connecté :', 'Logged-in passenger:')} **{st.session_state['current_user']}**")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader(t("📂 Info Vols AIGE", "📂 AIGE Flight Info"))
    f_pax = st.sidebar.file_uploader(t("Mettre à jour le planning (CSV)", "Update flight schedule (CSV)"), type=["csv"], key="upload_pax_csv")
    if f_pax is not None:
        try:
            st.session_state["df_vols"] = charger_et_nettoyer_donnees(f_pax)
            st.sidebar.success(t("Planning des vols mis à jour !", "Flight schedule updated!"))
        except Exception as e:
            st.sidebar.error(f"Erreur : {e}")

    if st.sidebar.button(t("Déconnexion", "Sign Out")):
        st.session_state["user_role"] = None
        st.rerun()

    st.markdown(f'<div class="header-title">{t("✈️ Votre Espace Voyage — AIGE Lomé", "✈️ Your Travel Space — AIGE Lomé")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="background-color: {success_bg}; color: {success_text}; padding: 12px 16px; border-radius: 8px; font-weight: 600; margin-bottom: 20px;">{t("Bienvenue ! Consultez ci-dessous vos informations et posez toutes vos questions à notre assistant intelligent.", "Welcome! Check your information below and ask any questions to our intelligent assistant.")}</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="kpi-container"><div class="kpi-label">{t("Statut du Vol", "Flight Status")}</div><div class="kpi-val" style="color: #0284C7;">{t("À l\'heure 🟢", "On Time 🟢")}</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-container"><div class="kpi-label">{t("Porte d\'Embarquement", "Boarding Gate")}</div><div class="kpi-val">{t("Porte 02", "Gate 02")}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kpi-container"><div class="kpi-label">{t("Zone d\'Enregistrement", "Check-in Zone")}</div><div class="kpi-val">{t("Guichets 01 à 04", "Counters 01 to 04")}</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-container"><div class="kpi-label">{t("Livraison Bagages", "Baggage Claim")}</div><div class="kpi-val">{t("Tapis 1", "Belt 1")}</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader(t("💬 Assistant Virtuel Intelligent AeroFlow", "💬 AeroFlow Intelligent Virtual Assistant"))

    if not st.session_state["messages_chat_pax"]:
        st.session_state["messages_chat_pax"] = [
            {"role": "assistant", "content": t("Bonjour ! Je suis l'assistant intelligent d'AeroFlow. Je peux lister tous les vols disponibles, vous donner leurs heures exactes de départ et calculer en temps réel le temps exact qu'il reste avant le départ de votre vol. Que souhaitez-vous savoir ?", "Hello! I am AeroFlow's intelligent assistant. I can list all available flights, give you their exact departure times, and calculate in real-time the exact time remaining before your flight departs. What would you like to know?")}
        ]

    for message in st.session_state["messages_chat_pax"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    col_input_pax, col_mic_pax = st.columns([12, 1])
    
    with col_mic_pax:
        if STT_AVAILABLE:
            langue_stt = "fr-FR" if langue_interface == "Français" else "en-US"
            texte_vocal_pax = speech_to_text(start_prompt="🎙️", stop_prompt="⏹️", language=langue_stt, key="mic_pax_inline")
        else:
            texte_vocal_pax = None

    with col_input_pax:
        prompt_saisi_pax = st.chat_input(t("Ex: Liste des vols, heure de départ KP010...", "E.g. List flights, departure time KP010..."), key="chat_input_pax")

    prompt_pax = texte_vocal_pax if texte_vocal_pax else prompt_saisi_pax

    if prompt_pax:
        st.session_state["messages_chat_pax"].append({"role": "user", "content": prompt_pax})
        p_low = prompt_pax.lower()
        est_ang_pax = any(w in p_low for w in ["flight", "gate", "baggage", "status", "time", "where", "how", "help", "list", "remaining", "left", "departure"]) or langue_interface == "English"
        
        maintenant = datetime.datetime.now()
        heure_actuelle_str = maintenant.strftime("%H:%M")
        df_pax_vols = st.session_state.get("df_vols", pd.DataFrame())
        rep_pax = ""

        if any(w in p_low for w in ["liste", "tous", "vols", "disponible", "programme", "list", "all", "flights", "schedule"]):
            if not df_pax_vols.empty:
                l_vols = []
                for _, r in df_pax_vols.iterrows():
                    v_num = r.get("Vol", "N/A")
                    v_comp = r.get("Compagnie", "N/A")
                    v_arr = r.get("Heure_Arrivee", "N/A")
                    v_esc = r.get("Temps_Escale_Min", 45)
                    try:
                        h_arr_dt = datetime.datetime.strptime(str(v_arr), "%H:%M").time()
                        dt_dep = datetime.datetime.combine(datetime.date.today(), h_arr_dt) + datetime.timedelta(minutes=int(v_esc))
                        v_dep_str = dt_dep.strftime("%H:%M")
                    except:
                        v_dep_str = "N/A"
                    l_vols.append(f"- **Vol {v_num}** ({v_comp}) | Arrivée : **{v_arr}** | Départ : **{v_dep_str}**")
                liste_str = "\n".join(l_vols)
                rep_pax = f"📋 **Liste des vols disponibles :**\n\n{liste_str}"
            else:
                rep_pax = "⚠️ Aucun programme de vol chargé."
        else:
            rep_pax = "Je suis l'assistant voyageur. Demandez-moi la liste des vols ou les informations sur votre voyage."

        st.session_state["messages_chat_pax"].append({"role": "assistant", "content": rep_pax})
        st.rerun()


# ------------------------------------------------------------------------------
# 5. VUE ESPACE AGENT ANAC / PC SÉCURITÉ
# ------------------------------------------------------------------------------

elif st.session_state["user_role"] == "agent":
    
    with st.sidebar:
        st.markdown("---")
        st.write(f"🛡️ Agent : **{st.session_state['current_user']}**")
        if st.button(t("Déconnexion Sécurisée", "Secure Sign Out")):
            st.session_state["user_role"] = None
            st.rerun()

        st.markdown("---")
        st.subheader(t("📂 Données de vol", "📂 Flight Data"))
        fichier_importe = st.file_uploader(t("Charger le programme des vols (CSV)", "Upload flight schedule (CSV)"), type=["csv"], key="upload_agent_csv")

        csv_modele_exemple = "Vol,Compagnie,Heure_Arrivee,Passagers,Temps_Escale_Min,Taux_Transit\nKP010,ASKY,11:30,120,40,0.45\nAF850,Air France,14:15,280,90,0.15\nET901,Ethiopian Airlines,16:45,190,35,0.30"
        st.download_button(
            label=t("📥 Télécharger le modèle CSV exemple", "📥 Download sample CSV template"),
            data=csv_modele_exemple,
            file_name="modele_vols_aige.csv",
            mime="text/csv",
        )

        if fichier_importe is not None:
            try:
                st.session_state["df_vols"] = charger_et_nettoyer_donnees(fichier_importe)
                st.success(t("Fichier personnalisé actif", "Custom file active"))
            except Exception as e:
                st.error(f"{t('Erreur de lecture :', 'Reading error:')} {e}")

        df = st.session_state["df_vols"]

        st.markdown("---")
        capacite_agent_heure = calculer_capacite_dynamique(df)
        max_pax_heure = df.groupby("Tranche_Horaire")["Passagers"].sum().max() if "Tranche_Horaire" in df.columns else 200
        guichets_recommandes = max(1, math.ceil(max_pax_heure / capacite_agent_heure))

        st.metric(label=t("🤖 Capacité Estimée", "🤖 Estimated Capacity"), value=f"{capacite_agent_heure} pax/h/agent")

        guichets_ouverts = st.slider(
            t("Guichets ouverts sur le terrain", "Counters open on site"),
            1,
            max(50, guichets_recommandes + 10),
            guichets_recommandes,
        )

    st.markdown(f'<div class="header-title">{t("✈️ AeroFlow — Operations Control Center", "✈️ AeroFlow — Operations Control Center")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="header-subtitle">{t("Aéroport International Gnassingbé Eyadéma (AIGE) | PC Sécurité & Régulation", "Gnassingbé Eyadéma International Airport (AIGE) | Security PC & Regulation")}</div>', unsafe_allow_html=True)

    df = st.session_state["df_vols"]
    vols_critiques = df[df["Temps_Escale_Min"] <= 45] if "Temps_Escale_Min" in df.columns else pd.DataFrame()

    c1, c2, c3, c4 = st.columns(4)
    total_passagers = int(df["Passagers"].sum()) if "Passagers" in df.columns else 0
    total_transit = int(df["Passagers_Transit"].sum()) if "Passagers_Transit" in df.columns else 0
    capacite_totale = int(guichets_ouverts * capacite_agent_heure)

    with c1:
        st.markdown(f'<div class="kpi-container"><div class="kpi-label">{t("Passagers Attendus", "Expected Passengers")}</div><div class="kpi-val">{total_passagers:,} pax</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kpi-container"><div class="kpi-label">{t("Flux Transit", "Transit Flow")}</div><div class="kpi-val">{total_transit:,} pax</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="kpi-container"><div class="kpi-label">{t("Capacité Traitement", "Processing Capacity")}</div><div class="kpi-val">{capacite_totale:,} pax/h</div></div>', unsafe_allow_html=True)
    with c4:
        alert_style = "kpi-container-alert" if len(vols_critiques) > 0 else ""
        color_val = "#EF4444" if len(vols_critiques) > 0 else "#0284C7"
        st.markdown(f'<div class="kpi-container {alert_style}"><div class="kpi-label">{t("Vols Critiques (≤45 min)", "Critical Flights (≤45 min)")}</div><div class="kpi-val" style="color: {color_val};">{len(vols_critiques):,} {t("Vol(s)", "Flight(s)")}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader(t("📊 Affluence Globale par Tranche Horaire", "📊 Overall Traffic by Time Slot"))
        if "Tranche_Horaire" in df.columns and "Passagers" in df.columns:
            df_affluence_heure = df.groupby("Tranche_Horaire")["Passagers"].sum().reset_index()
            fig_affluence = px.bar(df_affluence_heure, x="Tranche_Horaire", y="Passagers", text_auto=True, color="Passagers", color_continuous_scale="Blues", template=plotly_template)
            st.plotly_chart(fig_affluence, use_container_width=True)

    with col_right:
        st.subheader(t("⏱️ Répartition des Temps d'Escale", "⏱️ Layover Time Distribution"))
        if "Temps_Escale_Min" in df.columns:
            bins = [0, 30, 45, 60, 90, 120, 999]
            labels = ["< 30 min", "30-45 min (Critique)", "45-60 min", "60-90 min", "90-120 min", "> 120 min"]
            df["Plage_Escale"] = pd.cut(df["Temps_Escale_Min"], bins=bins, labels=labels)
            df_escale_group = df["Plage_Escale"].value_counts().reset_index()
            df_escale_group.columns = ["Plage_Escale", "Nombre_de_Vols"]
            fig_transit = px.bar(df_escale_group, x="Plage_Escale", y="Nombre_de_Vols", color="Nombre_de_Vols", color_continuous_scale="Reds_r", text_auto=True, template=plotly_template)
            st.plotly_chart(fig_transit, use_container_width=True)

    st.markdown("---")
    st.subheader(t("⚠️ Centre d'Alertes et Annonces", "⚠️ Alerts & Announcements Center"))

    if len(vols_critiques) > 0:
        col_btn, col_info = st.columns([1, 2])
        with col_btn:
            langue_choisie = st.radio(t("🌐 Langue de l'annonce vocale :", "🌐 Voice announcement language:"), options=["Français", "English"], horizontal=True, key="choix_langue_audio")
            nb_crit = len(vols_critiques)
            total_pax_crit = int(vols_critiques["Passagers_Transit"].sum())
            code_lang = "en" if langue_choisie == "English" else "fr"
            message = f"Attention Security Control. {nb_crit} critical flights detected." if code_lang == "en" else f"Attention PC Sécurité. {nb_crit} vols critiques détectés."

            if GTTS_AVAILABLE:
                try:
                    fp = io.BytesIO()
                    tts = gTTS(text=message, lang=code_lang)
                    tts.write_to_fp(fp)
                    fp.seek(0)
                    st.audio(fp.read(), format="audio/mp3")
                except:
                    pass

        with col_info:
            st.markdown(f'<div style="background-color: {alert_bg}; color: {alert_text}; padding: 14px 18px; border-radius: 8px; font-weight: 700; border: 1px solid #EF4444;">⚠️ {len(vols_critiques):,} {t("vol(s) critique(s) détecté(s)", "critical flight(s) detected")}</div>', unsafe_allow_html=True)
    else:
        st.success(t("✅ Aucun risque de correspondance détecté.", "✅ No connection risk detected."))

    st.markdown("---")
    st.subheader(t("💬 Assistant Virtuel AeroFlow (Chatbot Expert)", "💬 AeroFlow Virtual Assistant (Expert Chatbot)"))
    
    if not st.session_state["messages_chat"]:
        st.session_state["messages_chat"] = [
            {"role": "assistant", "content": t("Bonjour l'expert ! Je suis votre assistant opérationnel AeroFlow. Posez vos questions sur le trafic ou la régulation.", "Hello expert! I am your AeroFlow operational assistant. Ask your questions about traffic or regulation.")}
        ]

    for message in st.session_state["messages_chat"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt_utilisateur = st.chat_input(t("Tapez votre question ici...", "Type your question here..."), key="chat_input_agent")

    if prompt_utilisateur:
        st.session_state["messages_chat"].append({"role": "user", "content": prompt_utilisateur})
        reponse_bot = f"Analyse de votre requête : **{prompt_utilisateur}**. Les guichets recommandés sont au nombre de {guichets_recommandes}."
        st.session_state["messages_chat"].append({"role": "assistant", "content": reponse_bot})
        st.rerun()
