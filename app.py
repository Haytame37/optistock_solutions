import streamlit as st
import base64
import os
from dotenv import load_dotenv
load_dotenv()  # Charge les variables SMTP depuis .env

# Configuration de la page
st.set_page_config(
    page_title="OptiStock Solutions",
    page_icon="📦",
    layout="wide"
)

from utils.ui import hide_sidebar
hide_sidebar()

# --- Auto-initialisation de la base de données au démarrage ---
import sqlite3
_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "database", "optistock.db"))
try:
    _conn = sqlite3.connect(_DB_PATH)
    _cur = _conn.cursor()
    _cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if _cur.fetchone() is None:
        _conn.close()
        from database.init_db import create_database
        create_database()
    else:
        _conn.close()
except Exception as _e:
    st.error(f"Erreur d'initialisation de la base de données : {_e}")

# Injection du CSS personnalisé pour correspondre au design HTML
st.markdown("""
    <style>
    /* Import des polices */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Work+Sans:wght@600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

    /* Variables de couleurs */
    :root {
        --primary: #005da7;
        --secondary-container: #fe893a;
        --background: #f4fafd;
        --text-main: #161d1f;
    }

    /* Arrière-plan "Circuit" */
    .stApp {
        background-color: #f4fafd;
        background-image: 
            radial-gradient(#d1e2f3 1px, transparent 1px),
            linear-gradient(to right, #d1e2f3 1px, transparent 1px),
            linear-gradient(to bottom, #d1e2f3 1px, transparent 1px);
        background-size: 40px 40px, 80px 80px, 80px 80px;
    }

    /* Style du titre */
    .hero-title {
        font-family: 'Work Sans', sans-serif;
        color: var(--primary);
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        line-height: 1.2;
        margin-bottom: 0.5rem;
    }

    .hero-subtitle {
        font-family: 'Inter', sans-serif;
        color: #555d64;
        font-size: 1.2rem;
        text-align: center;
        margin-bottom: 2rem;
    }

    /* Cartes de fonctionnalités */
    .feature-card {
        background: white;
        border: 1px solid #D1E2F3;
        padding: 24px;
        border-radius: 12px;
        text-align: center;
        height: 100%;
        transition: transform 0.2s;
    }
    
    .feature-icon {
        background: #d4e3ff;
        color: var(--primary);
        width: 48px;
        height: 48px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        margin: 0 auto 15px auto;
    }

    /* Boutons personnalisés */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.6rem 2rem;
        transition: all 0.2s;
    }

    .btn-login > div > button {
        background-color: var(--primary) !important;
        color: white !important;
        border: none !important;
    }

    .btn-signup > div > button {
        background-color: var(--secondary-container) !important;
        color: #672d00 !important;
        border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Header ---
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

col_logo, _ = st.columns([2, 3])
with col_logo:
    img_path = "image_6c8213.png"
    if os.path.exists(img_path):
        b64_logo = get_base64_image(img_path)
        logo_html = f'<img src="data:image/png;base64,{b64_logo}" style="height: 40px; margin-right: 10px;">'
    else:
        logo_html = '<span class="material-symbols-outlined" style="color: #005da7; font-size: 32px; margin-right: 10px;">hub</span>'

    st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 20px;">
            {logo_html}
            <span style="font-weight: bold; font-size: 20px; color: #005da7;">OptiStock Solutions</span>
        </div>
    """, unsafe_allow_html=True)

# --- Hero Section ---
st.markdown('<h1 class="hero-title">Optimisation intelligente des centres de stockage logistique</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Gestion intelligente des entrepôts</p>', unsafe_allow_html=True)

# --- Feature Grid (2x2) ---
features = [
    {"icon": "sensors", "text": "Surveillance d'entrepôt en temps réel"},
    {"icon": "hub", "text": "Optimisation de la logistique"},
    {"icon": "ac_unit", "text": "Contrôle de l'intégrité des produits"},
    {"icon": "inventory_2", "text": "Gestion des actifs d'entrepôt"}
]

# Création de la grille avec les colonnes Streamlit
col1, col2 = st.columns(2)

for i, feature in enumerate(features):
    target_col = col1 if i % 2 == 0 else col2
    with target_col:
        st.markdown(f"""
            <div class="feature-card">
                <div class="feature-icon">
                    <span class="material-symbols-outlined" style="font-size: 30px;">{feature['icon']}</span>
                </div>
                <div style="font-weight: 600; font-size: 14px; line-height: 1.4;">{feature['text']}</div>
            </div>
        """, unsafe_allow_html=True)
        st.write("") # Espacement vertical

# --- Illustration Section ---
st.write("")
st.markdown("""
<div style="
    display: flex;
    justify-content: center;
    margin: 10px 0 20px 0;
">
    <div style="
        width: 80%;
        max-width: 860px;
        border-radius: 18px;
        overflow: hidden;
        box-shadow: 0 12px 40px rgba(0, 93, 167, 0.18);
        border: 1px solid #d1e2f3;
    ">
        <img
            src="https://images.unsplash.com/photo-1553413077-190dd305871c?q=80&w=1600&auto=format&fit=crop"
            style="
                width: 100%;
                height: 300px;
                object-fit: cover;
                object-position: center;
                display: block;
            "
        />
    </div>
</div>
""", unsafe_allow_html=True)



# --- Bottom Navigation / Actions ---
st.markdown("---")
col_login, col_signup = st.columns(2)

with col_login:
    if st.button("Commencer", type="primary", use_container_width=True):
        st.switch_page("pages/6_Welcome.py")

with col_signup:
    if st.button("📘 Guide", use_container_width=True):
        st.session_state.show_demo = not st.session_state.get('show_demo', False)

# --- Help Guide Section ---
if st.session_state.get('show_demo', False):
    st.markdown("""
        <div style="background-color: white; padding: 25px; border-radius: 15px; border: 1px solid #D1E2F3; margin-top: 30px; box-shadow: 0 10px 25px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2 style="color: #005da7; margin: 0; font-family: 'Work Sans', sans-serif;">📘 Guide d'utilisation OptiStock</h2>
            </div>
            <p style="color: #555d64; font-size: 16px; margin-bottom: 25px;">
                Bienvenue sur OptiStock. Notre plateforme connecte les chercheurs logistiques et les propriétaires d'entrepôts via une interface intelligente et connectée.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔬 Espace Chercheur", "🏢 Espace Propriétaire"])
    
    with tab1:
        st.markdown("""
        <div style="padding: 20px; background: #f8fafc; border-radius: 10px; border-left: 5px solid #005da7;">
            <p style="color: #334155; line-height: 1.6;">
                <strong>Bienvenue dans votre espace chercheur !</strong> Voici comment naviguer :<br><br>
                • <strong>Recherche d'entrepôt :</strong> définit votre produit, importer vos propres entrepôts ou clients, et lancer l'algorithme d'optimisation.<br>
                • <strong>Mes résultats :</strong> Consultez la liste des entrepôts recommandés avec leur score de performance logistique.<br>
                • <strong>Monitoring IoT :</strong> Si un entrepôt est équipé, vous pourrez voir les données de température/humidité en temps réel.<br>
                • <strong>Réservations :</strong> Une fois un entrepôt trouvé, envoyez une demande au propriétaire. Suivez l'état de vos demandes dans l'onglet "Réponses".
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with tab2:
        st.markdown("""
        <div style="padding: 20px; background: #fff7ed; border-radius: 10px; border-left: 5px solid #fe893a;">
            <p style="color: #431407; line-height: 1.6;">
                <strong>Bienvenue dans votre espace propriétaire !</strong> Voici vos outils principaux :<br><br>
                • <strong>Gestion de Parc :</strong> Listez vos entrepôts et suivez leur état d'occupation (disponible, maintenance, occupé).<br>
                • <strong>Dashboard IoT :</strong> Surveillez l'intégrité de vos stocks grâce aux alertes de capteurs connectés en temps réel.<br>
                • <strong>Visibilité Maximale :</strong> Vos espaces sont suggérés automatiquement aux chercheurs les plus pertinents.<br>
                • <strong>Gestion des Demandes :</strong> Répondez aux demandes de contact et gérez vos échanges via la messagerie intégrée.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("Fermer le guide"):
        st.session_state.show_demo = False
        st.rerun()
# --- Chatbot Flottant ---
from components.chatbot import render_optibot
render_optibot()
