
# ==============================================================================
# PROJET : AeroFlow - Control Center (AIGE)
# APPLICATION WEB STREAMLIT - CODE COMPLET, BILINGUE & INTELLIGENT (FR / EN)
# ==============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import math
import io

# Importation conditionnelle de gTTS pour la synthèse vocale
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

# Importation conditionnelle de streamlit_mic_recorder pour la saisie vocale
try:
    from streamlit_mic_recorder import speech_to_text
    MIC_RECORDER_AVAILABLE = True
except ImportError:
    MIC_RECORDER_AVAILABLE = False

# Importation conditionnelle de ReportLab pour la génération de PDF
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# ------------------------------------------------------------------------------
# 1. CONFIGURATION DE LA PAGE & STYLE GLOBAL
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="AeroFlow — AIGE Lomé",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisation des états de session
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None
if "current_user" not in st.session_state:
    st.session_state["current_user"] = "Voyageur"
if "messages_chat_pax" not in st.session_state:
    st.session_state["messages_chat_pax"] = []
if "messages_chat" not in st.session_state:
    st.session_state["messages_chat"] = []

# Gestion du thème sombre / clair et styles CSS
theme_mode = st.sidebar.selectbox("🎨 Thème de l'interface / Interface Theme", ["Clair (Light)", "Sombre (Dark)"], index=0)
is_dark = "Sombre" in theme_mode

if is_dark:
    bg_color = "#0F172A"
    card_bg = "#1E293B"
    text_color = "#F8FAFC"
    subtext = "#94A3B8"
    border_color = "#334155"
    plotly_template = "plotly_dark"
    success_bg = "#064E3B"
    success_text = "#A7F3D0"
    alert_bg = "#7F1D1D"
    alert_text = "#FECACA"
else:
    bg_color = "#F8FAFC"
    card_bg = "#FFFFFF"
    text_color = "#0F172A"
    subtext = "#64748B"
    border_color = "#E2E8F0"
    plotly_template = "plotly"
    success_bg = "#ECFDF5"
    success_text = "#065F46"
    alert_bg = "#FEF2F2"
    alert_text = "#991B1B"

st.markdown(f"""
    <style>
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}
    .kpi-container {{
        background-color: {card_bg};
        border: 1px solid {border_color};
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }}
    .kpi-container-alert {{
        background-color: {alert_bg};
        border: 1px solid #EF4444;
        padding: 20px;
        border-radius: 12px;
    }}
    .kpi-label {{
        font-size: 0.85rem;
        color: {subtext};
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    .kpi-val {{
        font-size: 1.8rem;
        font-weight: 800;
        color: {text_color};
        margin-top: 5px;
    }}
    .header-title {{
        font-size: 2.2rem;
        font-weight: 800;
        color: {text_color};
        margin-bottom: 0px;
    }}
    .header-subtitle {{
        font-size: 1.1rem;
        color: {subtext};
        margin-bottom: 25px;
    }}
    </style>
""", unsafe_allow_html=True)

# Sélection de la langue globale
langue_interface = st.sidebar.radio("🌐 Langue / Language", ["Français", "English"], horizontal=True)

def t(fr, en):
    return fr if langue_interface == "Français" else en


# ------------------------------------------------------------------------------
# 2. CHARGEMENT & NETTOYAGE DES DONNÉES VOLS (AIGE LOMÉ)
# ------------------------------------------------------------------------------
@st.cache_data
def charger_donnees_defaut():
    data = {
        "Vol": ["KP010", "AF850", "ET901", "AT562", "TK589", "WB204", "KQ552"],
        "Compagnie": ["ASKY", "Air France", "Ethiopian Airlines", "Royal Air Maroc", "Turkish Airlines", "RwandAir", "Kenya Airways"],
        "Heure_Arrivee": ["08:30", "10:15", "12:00", "13:45", "15:30", "17:15", "19:00"],
        "Passagers": [140, 260, 180, 110, 210, 95, 150],
        "Temps_Escale_Min": [40, 120, 45, 90, 35, 110, 50],
        "Taux_Transit": [0.55, 0.20, 0.45, 0.30, 0.60, 0.25, 0.40]
    }
    return pd.DataFrame(data)

def charger_et_nettoyer_donnees(fichier):
    try:
        df = pd.read_csv(fichier)
    except Exception:
        df = pd.read_excel(fichier)
    
    colonnes_requises = ["Vol", "Compagnie", "Heure_Arrivee", "Passagers", "Temps_Escale_Min"]
    for col in colonnes_requises:
        if col not in df.columns:
            raise ValueError(f"Colonne requise manquante : {col}")
            
    df["Passagers"] = pd.to_numeric(df["Passagers"], errors="coerce").fillna(0).astype(int)
    df["Temps_Escale_Min"] = pd.to_numeric(df["Temps_Escale_Min"], errors="coerce").fillna(45).astype(int)
    
    if "Taux_Transit" in df.columns:
        df["Taux_Transit"] = pd.to_numeric(df["Taux_Transit"], errors="coerce").fillna(0.3)
    else:
        df["Taux_Transit"] = 0.3
        
    df["Passagers_Transit"] = (df["Passagers"] * df["Taux_Transit"]).astype(int)
    
    def attribuer_tranche(heure_str):
        try:
            h = int(str(heure_str).split(":")[0])
            return f"{h:02d}h-{(h+1)%24:02d}h"
        except:
            return "12h-13h"
            
    df["Tranche_Horaire"] = df["Heure_Arrivee"].apply(attribuer_tranche)
    return df

if "df_vols" not in st.session_state:
    st.session_state["df_vols"] = charger_donnees_defaut()


# ------------------------------------------------------------------------------
# 3. FONCTIONS UTILITAIRES & RAPPORT PDF
# ------------------------------------------------------------------------------
def calculer_capacite_dynamique(df):
    if df.empty:
        return 35
    moyen_escale = df["Temps_Escale_Min"].mean()
    if moyen_escale < 45:
        return 28  # Stress opérationnel élevé -> agents un peu plus sollicités
    elif moyen_escale > 90:
        return 45  # Flux lissé
    return 35

def generer_pdf_rapport(df, vols_critiques, total_passagers, total_transit, guichets_ouverts):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#0284C7'), spaceAfter=6, alignment=1)
    subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#64748B'), spaceAfter=15, alignment=1)
    heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#0F172A'), spaceAfter=8, spaceBefore=12)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#334155'), spaceAfter=4)
    
    elements = []
    elements.append(Paragraph("AEROPORT INTERNATIONAL GNASSINGBE EYADEMA (AIGE) - LOME", title_style))
    elements.append(Paragraph(f"Rapport Officiel d'Exploitation & Régulation - {datetime.date.today()}", subtitle_style))
    elements.append(Spacer(1, 10))
    
    elements.append(Paragraph("1. Indicateurs Clés de l'Exploitation", heading_style))
    kpi_data = [
        ["Passagers Attendus", f"{total_passagers:,} pax"],
        ["Flux en Transit", f"{total_transit:,} pax"],
        ["Guichets Actifs", f"{guichets_ouverts} guichets"],
        ["Vols Critiques (<=45 min)", f"{len(vols_critiques)} vol(s)"]
    ]
    t_kpi = Table(kpi_data, colWidths=[200, 300])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#0F172A')),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1'))
    ]))
    elements.append(t_kpi)
    elements.append(Spacer(1, 15))
    
    elements.append(Paragraph("2. Programme Complet des Vols Enregistrés", heading_style))
    vols_data = [["Vol", "Compagnie", "Arrivée", "Passagers", "Escale", "Transit"]]
    for _, r in df.iterrows():
        vols_data.append([str(r.get("Vol")), str(r.get("Compagnie")), str(r.get("Heure_Arrivee")), str(r.get("Passagers")), f"{r.get('Temps_Escale_Min')} min", str(r.get("Passagers_Transit"))])
        
    t_vols = Table(vols_data, colWidths=[65, 120, 75, 75, 80, 85])
    t_vols.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0284C7')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0'))
    ]))
    elements.append(t_vols)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.read()


# ------------------------------------------------------------------------------
# 4. ÉCRAN DE CONNEXION / SÉLECTION DES RÔLES
# ------------------------------------------------------------------------------
if st.session_state["user_role"] is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_centered_1, col_centered_2, col_centered_3 = st.columns([1, 2, 1])
    
    with col_centered_2:
        st.markdown(f'<div style="text-align: center;"><div class="header-title">✈️ AeroFlow AIGE</div><div class="header-subtitle">{t("Système Intelligent de Gestion des Flux et Correspondances Aéroportuaires", "Intelligent Airport Passenger Flow and Connection Management System")}</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        choix_role = st.selectbox(
            t("Sélectionnez votre profil d'accès :", "Select your access profile:"),
            options=[
                t("👤 Passager / Voyageur (AIGE)", "👤 Passenger / Traveler (AIGE)"),
                t("🛡️ Agent ANAC / PC Sécurité & Régulation", "🛡️ ANAC Agent / Security & Regulation PC")
            ]
        )
        
        nom_saisi = st.text_input(t("Nom et Prénom :", "Full Name:"), value="SEMONDJI Hounou Enoc Dilan")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(t("🚀 Accéder à l'Espace Dédié", "🚀 Access Dedicated Area"), use_container_width=True):
            if "Passager" in choix_role:
                st.session_state["user_role"] = "passager"
            else:
                st.session_state["user_role"] = "agent"
            st.session_state["current_user"] = nom_saisi if nom_saisi else "Utilisateur"
            st.rerun()
            
    st.stop()


# ------------------------------------------------------------------------------
# 5. VUE ESPACE PASSAGER (AVEC CHATBOT ULTRA-INTELLIGENT CONNECTÉ AUX VOLS)
# ------------------------------------------------------------------------------

if st.session_state["user_role"] == "passager":
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

    # --------------------------------------------------------------------------
    # CHATBOT INTELLIGENT POUR LE PASSAGER (AVEC SIGNAL AUDIO & ANTI-DOUBLON)
    # --------------------------------------------------------------------------
    st.markdown("---")
    st.subheader(t("💬 Assistant Virtuel Intelligent AeroFlow", "💬 AeroFlow Intelligent Virtual Assistant"))
    st.markdown(t("Posez n'importe quelle question sur les vols disponibles, l'heure de départ, le temps restant en direct, les portes d'embarquement ou les services de l'AIGE.", "Ask any question about available flights, departure times, live remaining time, boarding gates, or AIGE services."))

    if not st.session_state["messages_chat_pax"]:
        st.session_state["messages_chat_pax"] = [
            {"role": "assistant", "content": t("Bonjour ! Je suis l'assistant intelligent d'AeroFlow. Je peux vous lister tous les vols disponibles, vous donner leurs heures exactes de départ et calculer en temps réel le temps exact qu'il reste avant le départ de votre vol. Que souhaitez-vous savoir ?", "Hello! I am AeroFlow's intelligent assistant. I can list all available flights, give you their exact departure times, and calculate in real-time the exact time remaining before your flight departs. What would you like to know?")}
        ]

    for message in st.session_state["messages_chat_pax"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

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
        prompt_saisi_pax = st.chat_input(t("Ex: Liste des vols, heure de départ KP010, combien de temps reste-t-il...", "E.g. List flights, departure time KP010, how much time is left..."), key="chat_input_pax")

    # Signal visuel clair si l'utilisateur est en train de parler/transcrire en audio
    if texte_vocal_pax:
        st.info(f"🎙️ **{t('Signal vocal capté avec succès :', 'Voice signal successfully captured:')}** « {texte_vocal_pax} » — {t('Traitement par l\'assistant en cours...', 'Processing by assistant...')}")

    prompt_pax = texte_vocal_pax if texte_vocal_pax else prompt_saisi_pax

    if prompt_pax:
        # Sécurité Anti-Doublon : On vérifie que le message n'est pas rigoureusement identique au dernier message utilisateur enregistré
        dernier_msg_user = [m["content"] for m in st.session_state["messages_chat_pax"] if m["role"] == "user"]
        if not dernier_msg_user or dernier_msg_user[-1] != prompt_pax:
            st.session_state["messages_chat_pax"].append({"role": "user", "content": prompt_pax})

            p_low = prompt_pax.lower()
            est_ang_pax = any(w in p_low for w in ["flight", "gate", "baggage", "status", "time", "where", "how", "help", "list", "remaining", "left", "departure"]) or langue_interface == "English"
            
            maintenant = datetime.datetime.now()
            heure_actuelle_str = maintenant.strftime("%H:%M")
            df_pax_vols = st.session_state.get("df_vols", pd.DataFrame())

            rep_pax = ""

            # CAS 1 : LISTE DE TOUS LES VOLS DISPONIBLES
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
                        l_vols.append(f"- **Vol {v_num}** ({v_comp}) | Arrivée : **{v_arr}** | Départ prévu : **{v_dep_str}**")
                    
                    liste_str = "\n".join(l_vols)
                    if est_ang_pax:
                        rep_pax = f"📋 **Here is the complete list of available flights at AIGE with their departure times:**\n\n{liste_str}\n\n*(You can ask for the remaining time of any specific flight by typing its number, e.g., 'KP010')*"
                    else:
                        rep_pax = f"📋 **Voici la liste complète des vols disponibles aujourd'hui à l'AIGE avec leurs heures de départ :**\n\n{liste_str}\n\n*(Vous pouvez me demander le temps restant exact pour un vol particulier en tapant son numéro, ex: 'KP010')*"
                else:
                    rep_pax = "⚠️ Aucun programme de vol n'est actuellement chargé dans le système par l'administration."

            # CAS 2 : TEMPS RESTANT OU HEURE DE DÉPART D'UN VOL SPÉCIFIQUE OU GÉNÉRAL
            elif any(w in p_low for w in ["temps", "restant", "reste", "combien", "heure", "depart", "part", "remaining", "left", "time", "when"]):
                vol_trouve = None
                for _, r in df_pax_vols.iterrows():
                    v_code = str(r.get("Vol", "")).upper()
                    if v_code and v_code in p_low.upper():
                        vol_trouve = r
                        break
                
                if vol_trouve is not None:
                    v_num = vol_trouve.get("Vol")
                    v_arr = str(vol_trouve.get("Heure_Arrivee", "12:00"))
                    v_esc = int(vol_trouve.get("Temps_Escale_Min", 45))
                    v_comp = vol_trouve.get("Compagnie")
                    
                    try:
                        h_arr_dt = datetime.datetime.strptime(v_arr, "%H:%M").time()
                        dt_arrivee_complet = datetime.datetime.combine(datetime.date.today(), h_arr_dt)
                        dt_depart_complet = dt_arrivee_complet + datetime.timedelta(minutes=v_esc)
                        
                        delta = dt_depart_complet - maintenant
                        minutes_restantes = int(delta.total_seconds() / 60)
                        
                        if minutes_restantes > 0:
                            heures_r = minutes_restantes // 60
                            mins_r = minutes_restantes % 60
                            temps_str = f"{heures_r}h {mins_r}min" if heures_r > 0 else f"{mins_r} minutes"
                        else:
                            temps_str = "Vol déjà parti ou échéance dépassée"

                        if est_ang_pax:
                            rep_pax = f"⏱️ **Flight Details — {v_num} ({v_comp}):**\n- Arrival Time: **{v_arr}**\n- Layover / Stop duration: **{v_esc} min**\n- **Exact Departure Time:** **{dt_depart_complet.strftime('%H:%M')}**\n- **Time remaining until departure:** ⏳ **{temps_str}** (Current time: {heure_actuelle_str})"
                        else:
                            rep_pax = f"⏱️ **Informations Vol — {v_num} ({v_comp}) :**\n- Heure d'arrivée : **{v_arr}**\n- Temps d'escale : **{v_esc} min**\n- **Heure exacte de départ :** **{dt_depart_complet.strftime('%H:%M')}**\n- **Temps restant exact avant le départ :** ⏳ **{temps_str}** (Heure actuelle : {heure_actuelle_str})"
                    except Exception:
                        rep_pax = f"Le vol {v_num} de la compagnie {v_comp} arrive à {v_arr}."
                else:
                    if not df_pax_vols.empty:
                        l_temps = []
                        for _, r in df_pax_vols.iterrows():
                            v_num = r.get("Vol")
                            v_comp = r.get("Compagnie")
                            v_arr = str(r.get("Heure_Arrivee", "12:00"))
                            v_esc = int(r.get("Temps_Escale_Min", 45))
                            try:
                                h_arr_dt = datetime.datetime.strptime(v_arr, "%H:%M").time()
                                dt_dep = datetime.datetime.combine(datetime.date.today(), h_arr_dt) + datetime.timedelta(minutes=v_esc)
                                delta = dt_dep - maintenant
                                m_rest = int(delta.total_seconds() / 60)
                                statut_t = f"Reste **{m_rest} min**" if m_rest > 0 else "Départ imminent / Parti"
                                l_temps.append(f"- **Vol {v_num}** ({v_comp}) | Départ : **{dt_dep.strftime('%H:%M')}** | ⏱️ {statut_t}")
                            except:
                                pass
                        t_str = "\n".join(l_temps)
                        if est_ang_pax:
                            rep_pax = f"⏱️ **Live departure countdown for all flights (Current time: {heure_actuelle_str}):**\n\n{t_str}\n\n*(Tip: Type a specific flight number like 'KP010' for more details)*"
                        else:
                            rep_pax = f"⏱️ **Décompte en temps réel de tous les vols (Heure actuelle : {heure_actuelle_str}) :**\n\n{t_str}\n\n*(Astuce : Précisez un numéro de vol comme 'KP010' pour un focus immédiat)*"
                    else:
                        rep_pax = "⚠️ Aucun vol n'est actuellement disponible dans la base de données."

            # CAS 3 : PORTE D'EMBARQUEMENT / ENREGISTREMENT / BAGAGES
            elif any(w in p_low for w in ["porte", "gate", "embarquement", "boarding"]):
                rep_pax = "Votre vol embarque depuis la **Porte 02**. Présentez-vous en zone d'embarquement 30 minutes avant le départ." if not est_ang_pax else "Your flight is boarding from **Gate 02**. Please arrive at the boarding area 30 minutes before departure."
            elif any(w in p_low for w in ["bagage", "baggage", "tapis", "belt", "valise"]):
                rep_pax = "La livraison de vos bagages s'effectue sur le **Tapis 1** dans le hall des arrivées de l'AIGE." if not est_ang_pax else "Your baggage claim is at **Belt 1** in the AIGE arrival hall."
            elif any(w in p_low for w in ["bonjour", "salut", "bonsoir", "hello", "hi", "hey"]):
                rep_pax = "Bonjour et bienvenue à l'Aéroport International Gnassingbé Eyadéma (AIGE) ! Je suis prêt à vous donner toutes les informations sur les vols, les heures de départ et le temps restant en direct." if not est_ang_pax else "Hello and welcome to Gnassingbé Eyadéma International Airport (AIGE)! I am ready to provide all flight info, departure times, and live remaining time."
            elif any(w in p_low for w in ["merci", "thank"]):
                rep_pax = "Je vous en prie ! Bon voyage avec AeroFlow." if not est_ang_pax else "You're very welcome! Have a great trip with AeroFlow."
            else:
                rep_pax = "Je suis l'assistant voyageur d'AeroFlow. Vous pouvez me demander :\n1. **« Liste tous les vols »** pour voir tous les départs.\n2. **« Temps restant pour le vol [Numéro] »** pour connaître l'heure exacte de départ et le décompte en direct.\n3. **« Porte d'embarquement »** ou **« Bagages »**." if not est_ang_pax else "I am AeroFlow's traveler assistant. You can ask me to list all flights, check departure times and live countdowns, or ask about gates and baggage."

            st.session_state["messages_chat_pax"].append({"role": "assistant", "content": rep_pax})
            st.rerun()


# ------------------------------------------------------------------------------
# 6. VUE ESPACE AGENT ANAC / PC SÉCURITÉ
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

        if "df_vols" not in st.session_state:
            st.error(t("⚠️ Aucun fichier CSV chargé. Veuillez charger un fichier CSV.", "⚠️ No CSV file loaded. Please upload a CSV file."))
            st.stop()

        df = st.session_state["df_vols"]

        st.markdown("---")
        capacite_agent_heure = calculer_capacite_dynamique(df)

        if "Tranche_Horaire" in df.columns and "Passagers" in df.columns:
            max_pax_heure = df.groupby("Tranche_Horaire")["Passagers"].sum().max()
            guichets_recommandes = max(1, math.ceil(max_pax_heure / capacite_agent_heure))
        else:
            guichets_recommandes = 4

        st.metric(label=t("🤖 Capacité Estimée (Automatique)", "🤖 Estimated Capacity (Automatic)"), value=f"{capacite_agent_heure} {t('pax/h/agent', 'pax/h/agent')}")

        guichets_ouverts = st.slider(
            t("Guichets ouverts sur le terrain", "Counters open on site"),
            1,
            max(50, guichets_recommandes + 10),
            guichets_recommandes,
        )

        if guichets_ouverts < guichets_recommandes:
            st.warning(f"💡 **{t('Recommandation :', 'Recommendation:')}** {t('Ouvrir au moins', 'Open at least')} **{guichets_recommandes} {t('guichets', 'counters')}** {t('pour absorber la pointe.', 'to handle the peak.')}")

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
            fig_affluence.update_layout(xaxis_title=t("Tranche Horaire", "Time Slot"), yaxis_title=t("Total Passagers", "Total Passengers"), margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_affluence, use_container_width=True)

    with col_right:
        st.subheader(t("⏱️ Répartition des Temps d'Escale", "⏱️ Layover Time Distribution"))
        if "Temps_Escale_Min" in df.columns:
            bins = [0, 30, 45, 60, 90, 120, 999]
            labels_fr = ["< 30 min", "30-45 min (Critique)", "45-60 min", "60-90 min", "90-120 min", "> 120 min"]
            labels_en = ["< 30 min", "30-45 min (Critical)", "45-60 min", "60-90 min", "90-120 min", "> 120 min"]
            labels = labels_fr if langue_interface == "Français" else labels_en
            
            df["Plage_Escale"] = pd.cut(df["Temps_Escale_Min"], bins=bins, labels=labels)
            df_escale_group = df["Plage_Escale"].value_counts().reset_index()
            df_escale_group.columns = ["Plage_Escale", "Nombre_de_Vols"]

            fig_transit = px.bar(df_escale_group, x="Plage_Escale", y="Nombre_de_Vols", color="Nombre_de_Vols", color_continuous_scale="Reds_r", text_auto=True, template=plotly_template)
            fig_transit.update_layout(xaxis_title=t("Plage de Temps d'Escale", "Layover Time Range"), yaxis_title=t("Nombre de Vols", "Number of Flights"), margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_transit, use_container_width=True)

    st.markdown("---")
    st.subheader(t("⚠️ Centre d'Alertes et Annonces", "⚠️ Alerts & Announcements Center"))

    if len(vols_critiques) > 0:
        col_btn, col_info = st.columns([1, 2])

        with col_btn:
            langue_choisie = st.radio(t("🌐 Langue de l'annonce vocale :", "🌐 Voice announcement language:"), options=["Français", "English"], horizontal=True, key="choix_langue_audio")
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
                st.info(f"{t('Annonce disponible :', 'Announcement available:')} « {message} »")
            except Exception as e:
                st.error(f"{t('Erreur de génération vocale :', 'Voice generation error:')} {e}")

        with col_info:
            st.markdown(f'<div style="background-color: {alert_bg}; color: {alert_text}; padding: 14px 18px; border-radius: 8px; font-weight: 700; font-size: 1.05rem; margin-bottom: 15px; border: 1px solid #EF4444;">⚠️ {len(vols_critiques):,} {t("vol(s) critique(s) détecté(s) (Escale ≤ 45 min)", "critical flight(s) detected (Layover ≤ 45 min)")}</div>', unsafe_allow_html=True)

        with st.container(height=280):
            for _, vol in vols_critiques.iterrows():
                st.error(f"🔴 **[Vol {vol.get('Vol', 'N/A')} - {vol.get('Compagnie', 'N/A')}]** : {t('Arrivée à', 'Arrival at')} **{vol.get('Heure_Arrivee', 'N/A')}** | **{vol.get('Passagers_Transit', 0)} pax transit** | {t('Escale :', 'Layover:')} **{vol.get('Temps_Escale_Min', 0)} min**")
    else:
        st.success(t("✅ Aucun risque de correspondance détecté pour le moment.", "✅ No connection risk detected at the moment."))

    with st.expander(t("📄 Voir le programme détaillé des vols (AIGE)", "📄 View detailed flight schedule (AIGE)")):
        st.dataframe(df, height=400, hide_index=True)

    st.markdown("---")
    st.subheader(t("📥 Exportation & Rapports d'Exploitation", "📥 Export & Operational Reports"))
    exp_col1, exp_col2, exp_col3 = st.columns(3)

    with exp_col1:
        st.markdown(f"**1. {t('Données des Vols Critiques (CSV)', 'Critical Flights Data (CSV)')}**")
        if not vols_critiques.empty:
            st.download_button(label=t("📄 Télécharger Vols Critiques (.csv)", "📄 Download Critical Flights (.csv)"), data=vols_critiques.to_csv(index=False, encoding="utf-8-sig"), file_name=f"vols_critiques_AIGE_{datetime.date.today()}.csv", mime="text/csv")
        else:
            st.info(t("Aucun vol critique à exporter.", "No critical flights to export."))

    with exp_col2:
        st.markdown(f"**2. {t('Programme Complet des Vols (CSV)', 'Full Flight Schedule (CSV)')}**")
        st.download_button(label=t("📊 Télécharger Programme Complet (.csv)", "📊 Download Full Schedule (.csv)"), data=df.to_csv(index=False, encoding="utf-8-sig"), file_name=f"programme_vols_AIGE_{datetime.date.today()}.csv", mime="text/csv")

    with exp_col3:
        st.markdown(f"**3. {t('Rapport Synthétique Officiel (PDF)', 'Official Summary Report (PDF)')}**")
        if REPORTLAB_AVAILABLE:
            st.download_button(label=t("📑 Télécharger le Rapport (.pdf)", "📑 Download Report (.pdf)"), data=generer_pdf_rapport(df, vols_critiques, total_passagers, total_transit, guichets_ouverts), file_name=f"Rapport_Exploitation_AIGE_{datetime.date.today()}.pdf", mime="application/pdf")
        else:
            st.warning(f"⚠️ Module ReportLab non disponible.")

    # --------------------------------------------------------------------------
    # 7. SECTION CHATBOT AGENT (EXPERT AVEC SIGNAL AUDIO & ANTI-DOUBLON)
    # --------------------------------------------------------------------------
    st.markdown("---")
    st.subheader(t("💬 Assistant Virtuel AeroFlow (Chatbot Expert — Trafic & Régulation)", "💬 AeroFlow Virtual Assistant (Expert Chatbot — Traffic & Regulation)"))
    st.markdown(t("Posez vos questions sur le trafic, les solutions en cas critique, la liste complète des vols de la journée, les heures de départ, ou le temps restant avant le départ.", "Ask your questions about traffic, solutions for critical cases, the complete list of daily flights, departure times, or remaining time before departure."))

    if not st.session_state["messages_chat"]:
        st.session_state["messages_chat"] = [
            {"role": "assistant", "content": t("Bonjour l'expert ! Je suis votre assistant opérationnel AeroFlow. Je peux lister tous les vols de la journée, calculer le temps restant avant le départ en temps réel, analyser les situations critiques et vous fournir des solutions immédiates. Que souhaitez-vous savoir ?", "Hello expert! I am your AeroFlow operational assistant. I can list all daily flights, calculate the time remaining before departure in real-time, analyze critical situations, and provide immediate solutions. What would you like to know?")}
        ]

    for message in st.session_state["messages_chat"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    col_input_agent, col_mic_agent = st.columns([12, 1])

    with col_mic_agent:
        langue_stt_agent = "fr-FR" if langue_interface == "Français" else "en-US"
        texte_vocal_agent = speech_to_text(
            start_prompt="🎙️",
            stop_prompt="⏹️",
            language=langue_stt_agent,
            key="mic_agent_inline"
        )

    with col_input_agent:
        prompt_saisi_agent = st.chat_input(t("Tapez votre question ici...", "Type your question here..."), key="chat_input_agent")

    # Signal visuel clair si l'agent est en train de parler/transcrire en audio
    if texte_vocal_agent:
        st.info(f"🎙️ **{t('Signal vocal capté avec succès :', 'Voice signal successfully captured:')}** « {texte_vocal_agent} » — {t('Analyse experte en cours...', 'Running expert analysis...')}")

    prompt_utilisateur = texte_vocal_agent if texte_vocal_agent else prompt_saisi_agent

    if prompt_utilisateur:
        # Sécurité Anti-Doublon : On s'assure de ne pas dupliquer la réponse si le message vient d'être traité
        dernier_msg_agent = [m["content"] for m in st.session_state["messages_chat"] if m["role"] == "user"]
        if not dernier_msg_agent or dernier_msg_agent[-1] != prompt_utilisateur:
            st.session_state["messages_chat"].append({"role": "user", "content": prompt_utilisateur})

            p_lower = prompt_utilisateur.lower()
            est_anglais = any(w in p_lower for w in ["flight", "delay", "passenger", "gate", "status", "how", "what", "many", "critical", "help", "list", "time", "remaining", "solution", "counters"]) or langue_interface == "English"

            reponse_bot = ""

            if any(w in p_lower for w in ["guichet", "guichets", "ouvrir", "combien", "counters", "open", "how many"]):
                reponse_bot = f"🧮 **Analyse et Recommandation des Guichets :**\nEn fonction du pic d'affluence et de la capacité dynamique estimée ({capacite_agent_heure} pax/h/agent), vous devez ouvrir **au minimum {guichets_recommandes} guichets** pour absorber la pointe. Actuellement, vous avez configuré **{guichets_ouverts} guichets** ouverts sur le terrain."
            elif any(w in p_lower for w in ["liste", "vol", "vols", "journee", "programme", "tous", "flight", "schedule", "all"]):
                if not df.empty:
                    l_vols = []
                    for _, r in df.iterrows():
                        v_num = r.get("Vol", "N/A")
                        v_comp = r.get("Compagnie", "N/A")
                        v_arr = r.get("Heure_Arrivee", "N/A")
                        v_pax = r.get("Passagers", 0)
                        v_esc = r.get("Temps_Escale_Min", "N/A")
                        l_vols.append(f"- **Vol {v_num}** ({v_comp}) | Arrivée : **{v_arr}** | Passagers : **{v_pax} pax** | Escale : **{v_esc} min**")
                    reponse_bot = f"📋 **Programme complet des vols de la journée à l'AIGE :**\n\n" + "\n".join(l_vols)
                else:
                    reponse_bot = "⚠️ Aucun vol n'est actuellement chargé dans le système."
            elif any(w in p_lower for w in ["temps", "restant", "reste", "combien de temps", "heure", "depart", "remaining", "time", "left"]):
                vol_trouve = None
                for _, r in df.iterrows():
                    v_code = str(r.get("Vol", "")).upper()
                    if v_code and v_code in p_lower.upper():
                        vol_trouve = r
                        break
                
                if vol_trouve is not None:
                    v_num = vol_trouve.get("Vol")
                    v_arr = str(vol_trouve.get("Heure_Arrivee", "12:00"))
                    v_esc = int(vol_trouve.get("Temps_Escale_Min", 45))
                    v_comp = vol_trouve.get("Compagnie")
                    try:
                        h_arr_dt = datetime.datetime.strptime(v_arr, "%H:%M").time()
                        dt_arrivee_complet = datetime.datetime.combine(datetime.date.today(), h_arr_dt)
                        dt_depart_complet = dt_arrivee_complet + datetime.timedelta(minutes=v_esc)
                        delta = dt_depart_complet - maintenant
                        minutes_restantes = int(delta.total_seconds() / 60)
                        temps_str = f"{minutes_restantes // 60}h {minutes_restantes % 60}min" if minutes_restantes > 0 else "Parti"
                        reponse_bot = f"⏱️ **État — Vol {v_num} ({v_comp}) :**\n- Arrivée : {v_arr} | Escale : {v_esc} min\n- Départ estimé : **{dt_depart_complet.strftime('%H:%M')}**\n- **Temps restant avant le départ :** ⏳ **{temps_str}**"
                    except:
                        reponse_bot = f"Vol {v_num} arrive à {v_arr}."
                else:
                    l_temps = []
                    for _, r in df.iterrows():
                        v_num = r.get("Vol")
                        v_arr = str(r.get("Heure_Arrivee", "12:00"))
                        v_esc = int(r.get("Temps_Escale_Min", 45))
                        try:
                            h_arr_dt = datetime.datetime.strptime(v_arr, "%H:%M").time()
                            dt_dep = datetime.datetime.combine(datetime.date.today(), h_arr_dt) + datetime.timedelta(minutes=v_esc)
                            delta = dt_dep - maintenant
                            m_rest = int(delta.total_seconds() / 60)
                            l_temps.append(f"- **Vol {v_num}** : Départ à {dt_dep.strftime('%H:%M')} (Reste : **{m_rest} min**)")
                        except:
                            pass
                    reponse_bot = f"⏱️ **Temps restant pour les vols du jour :**\n\n" + "\n".join(l_temps)
            elif any(w in p_lower for w in ["critique", "solution", "difficile", "probleme", "panne", "retard", "urgence", "bloque"]):
                nb_c = len(vols_critiques)
                reponse_bot = f"🚨 **Protocoles d'Urgence ({nb_c} vol(s) critique(s)) :**\n1. Ouvrir au minimum **{guichets_recommandes} guichets**.\n2. Dépêcher une équipe mobile pour escorter les passagers.\n3. Prioriser les conteneurs de bagages en soute (Tapis 1)."
            else:
                reponse_bot = "Je suis l'assistant expert d'AeroFlow. Demandez-moi la liste des vols, le nombre de guichets à ouvrir ou le temps restant avant le départ."

            st.session_state["messages_chat"].append({"role": "assistant", "content": reponse_bot})
            st.rerun()
