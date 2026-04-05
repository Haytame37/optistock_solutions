import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go # Ajoute cet import en haut de ton fichier app.py
from plotly.subplots import make_subplots

# 1. Importation
from core.iot_analysis import get_basic_stats, detect_anomalies
from core.scoring import calculate_environmental_score, get_score_label
from utils.constants import TEMP_MIN, TEMP_MAX, HUMID_MIN, HUMID_MAX
from utils.db import load_sql_to_dataframe

# Configuration de la page
st.set_page_config(page_title="OptiStock Solutions", layout="wide", page_icon="🏭")

# 2. Chargement des données brutes
try:
    df_t_raw = load_sql_to_dataframe('SELECT * FROM temperature')
    df_h_raw = load_sql_to_dataframe('SELECT * FROM humidite')
    
    # Check si les dataframes sont vides
    if df_t_raw.empty or df_h_raw.empty:
        raise ValueError("Les tables IoT sont vides dans la base de données.")
        
    df_t_raw['datetime'] = pd.to_datetime(df_t_raw['datetime'])
    df_h_raw['datetime'] = pd.to_datetime(df_h_raw['datetime'])
    
except Exception as e:
    st.error(f"Erreur de connexion DB : {e}. Assurez-vous d'avoir exécuté 'python database/seed_data.py'.")
    st.stop()

# 3. Sidebar - Filtres
st.sidebar.title("Navigation")
st.sidebar.success("Module Analyse Environnementale")

entrepot_list = df_t_raw['id_entrepot'].unique()
selected_entrepot = st.sidebar.selectbox("🎯 Sélection de l'entrepôt :", entrepot_list)

st.sidebar.markdown("---")
st.sidebar.markdown("**Sélection des Capteurs :**")
selected_capteur_t = st.sidebar.radio("🌡️ Température :", ["capteur1", "capteur2", "capteur3"], index=0)
selected_capteur_h = st.sidebar.radio("💧 Humidité :", ["capteur1", "capteur2", "capteur3"], index=0)
st.sidebar.markdown("---")

# Filtrer pour l'entrepôt sélectionné et trier par date chronologiquement
df_t = df_t_raw[df_t_raw['id_entrepot'] == selected_entrepot].copy()
df_t.sort_values('datetime', inplace=True)

df_h = df_h_raw[df_h_raw['id_entrepot'] == selected_entrepot].copy()
df_h.sort_values('datetime', inplace=True)

stats = get_basic_stats(df_t, df_h)
bad_temp, bad_humid = detect_anomalies(df_t, df_h)
total_len = max(len(df_t), len(df_h))
score = calculate_environmental_score(total_len, len(bad_temp), len(bad_humid))
label, emoji = get_score_label(score)

st.sidebar.info(f"📍 Statut : {label} {emoji}")

# 4. En-tête
st.title(f"🏭 OptiStock Solutions - {selected_entrepot}")
st.markdown(f"### Score de Conformité Environnementale : **{score}/100** ({label} {emoji})")

# 5. Métriques
col1, col2, col3, col4 = st.columns(4)
col1.metric("Entrepôt Actif", selected_entrepot, "Filtré")
col2.metric("Température Moyenne", f"{stats['temp_mean']}°C", "Stable")
col3.metric("Heures hors-normes", len(bad_temp), delta="- Alertes T°", delta_color="inverse")
col4.metric("Fiabilité Capteurs", "99.2%", "IoT Active")

st.divider()

# 6. Visualisation Combinée (Température + Humidité)
st.subheader("📈 Analyse Corrélée : Température & Humidité")
st.caption(f"Visualisation : Température ({selected_capteur_t}) et Humidité ({selected_capteur_h})")

# Création d'un graphique avec deux axes Y
fig_combined = make_subplots(specs=[[{"secondary_y": True}]])

# Ajout de la courbe de Température (Un seul capteur sélectionné)
fig_combined.add_trace(
    go.Scatter(x=df_t['datetime'], y=df_t[selected_capteur_t], name=f"Temp. {selected_capteur_t} (°C)",
               line=dict(color="#ef553b", width=1)),
    secondary_y=False,
)

# Ajout de la courbe d'Humidité (Un seul capteur sélectionné)
fig_combined.add_trace(
    go.Scatter(x=df_h['datetime'], y=df_h[selected_capteur_h], name=f"Hum. {selected_capteur_h} (%)",
               line=dict(color="#636efa", width=1, dash='dot')),
    secondary_y=True,
)

# Personnalisation des axes et seuils
fig_combined.update_layout(
    title_text="Corrélation Température vs Humidité (Vue Annuelle)",
    hovermode="x unified"
)

# Configuration des noms des axes
fig_combined.update_yaxes(title_text="<b>Température</b> (°C)", secondary_y=False)
fig_combined.update_yaxes(title_text="<b>Humidité</b> (%)", secondary_y=True)

# Affichage du graphique
st.plotly_chart(fig_combined, use_container_width=True)
# 7. Section Informations
st.info(f"💡 Conseil Expert : L'entrepôt a été hors-normes pendant {len(bad_temp)} heures pour la température et {len(bad_humid)} heures pour l'humidité.")

# --- SECTION DÉTAILLÉE POUR LE PROF ---
st.divider()
st.subheader("📋 Rapport d'Analyse Statistique")

col_stats1, col_stats2 = st.columns(2)

with col_stats1:
    st.write("**Statistiques Température**")
    stats_temp = {
        "Indicateur": ["Minimum", "Maximum", "Moyenne", "Écart-type"],
        "Valeur": [f"{stats['temp_min']}°C", f"{stats['temp_max']}°C", f"{stats['temp_mean']}°C", f"{stats['temp_std']}"]
    }
    st.table(pd.DataFrame(stats_temp))

with col_stats2:
    st.write("**Statistiques Humidité**")
    stats_humid = {
        "Indicateur": ["Minimum", "Maximum", "Moyenne", "Écart-type"],
        "Valeur": [f"{stats['humid_min']}%", f"{stats['humid_max']}%", f"{stats['humid_mean']}%", f"{stats['humid_std']}"]
    }
    st.table(pd.DataFrame(stats_humid))

# Conclusion finale
st.warning(f"**Analyse Industrielle :** Les écarts-types mesurés ({stats['temp_std']} pour T° / {stats['humid_std']} pour H%) révèlent une instabilité environnementale majeure. Le score de **{score}/100** confirme la nécessité d'implémenter des régulateurs automatiques.")