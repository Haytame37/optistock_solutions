import streamlit as st
import time
from datetime import timedelta
from utils.db import load_sql_to_dataframe
from core.data_cleaning import clean_iot_data_pipeline
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from utils.product_conditions import PRODUCT_CONDITIONS

st.set_page_config(page_title="Suivi Temps Réel IoT", page_icon="⏱️", layout="wide")

st.title("⏱️ Suivi Temps Réel IoT")
st.caption("Simulation d'un flux de données temps réel (1 relevé = 15 minutes).")

# Sélecteur de contexte
col_ctx1, col_ctx2 = st.columns(2)
with col_ctx1:
    produit = st.selectbox("Produit suivi", list(PRODUCT_CONDITIONS.keys()))
with col_ctx2:
    df_wh = load_sql_to_dataframe("SELECT DISTINCT warehouse_id FROM iot_readings")
    entrepot_list = df_wh["warehouse_id"].tolist() if not df_wh.empty else ["ENT_001"]
    entrepot = st.selectbox("Entrepôt", entrepot_list)

cond = PRODUCT_CONDITIONS[produit]
t_min, t_max = cond["temperature"]["min"], cond["temperature"]["max"]
h_min, h_max = cond["humidite"]["min"], cond["humidite"]["max"]

st.markdown(f"**Conditions optimales pour {produit}** : T° [{t_min}°C - {t_max}°C] | H% [{h_min}% - {h_max}%]")
st.divider()

# Initialisation de la simulation dans la session
if "rt_index" not in st.session_state:
    st.session_state.rt_index = 0
if "rt_running" not in st.session_state:
    st.session_state.rt_running = False

# Boutons de contrôle
col_btn1, col_btn2, col_btn3 = st.columns([1,1,4])
with col_btn1:
    if st.button("▶️ Démarrer" if not st.session_state.rt_running else "⏸️ Pause"):
        st.session_state.rt_running = not st.session_state.rt_running
        st.rerun()
with col_btn2:
    if st.button("⏩ Avancer (15m)"):
        st.session_state.rt_index += 1
        st.rerun()

# Chargement des données pour la simulation
query = f"SELECT recorded_at as datetime, temp_sensor_1, temp_sensor_2, temp_sensor_3, hum_sensor_1, hum_sensor_2, hum_sensor_3 FROM iot_readings WHERE warehouse_id = '{entrepot}' ORDER BY recorded_at"
df_rt = load_sql_to_dataframe(query)

if df_rt.empty:
    st.error("Pas de données pour cet entrepôt.")
    st.stop()

# Nettoyage et aggrégation
cols_t = ["temp_sensor_1", "temp_sensor_2", "temp_sensor_3"]
cols_h = ["hum_sensor_1", "hum_sensor_2", "hum_sensor_3"]

df_rt = clean_iot_data_pipeline(df_rt, cols_t + cols_h)
df_rt["T"] = df_rt[cols_t].median(axis=1)
df_rt["H"] = df_rt[cols_h].median(axis=1)

max_idx = len(df_rt) - 1
idx = min(st.session_state.rt_index, max_idx)

current_data = df_rt.iloc[idx]

# Affichage des KPIs
st.subheader(f"📡 Relevé du {current_data['datetime']}")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

current_t = current_data["T"]
current_h = current_data["H"]

delta_t = 0
statut_t = "Optimal"
color_t = "#27ae60"
if current_t < t_min:
    delta_t = current_t - t_min
    statut_t = "Critique Bas" if current_t < (t_min + cond["temperature"]["marge_bas"]) else "Alerte Basse"
    color_t = "#e74c3c" if "Critique" in statut_t else "#f39c12"
elif current_t > t_max:
    delta_t = current_t - t_max
    statut_t = "Critique Haut" if current_t > (t_max + cond["temperature"]["marge_haut"]) else "Alerte Haute"
    color_t = "#e74c3c" if "Critique" in statut_t else "#f39c12"
    
delta_h = 0
statut_h = "Optimal"
color_h = "#27ae60"
if current_h < h_min:
    delta_h = current_h - h_min
    statut_h = "Critique Bas" if current_h < (h_min + cond["humidite"]["marge_bas"]) else "Alerte Basse"
    color_h = "#e74c3c" if "Critique" in statut_h else "#f39c12"
elif current_h > h_max:
    delta_h = current_h - h_max
    statut_h = "Critique Haut" if current_h > (h_max + cond["humidite"]["marge_haut"]) else "Alerte Haute"
    color_h = "#e74c3c" if "Critique" in statut_h else "#f39c12"
    
# Calcul simple du "Score de stabilité" instantané
stability_score = 100
if statut_t != "Optimal": stability_score -= 25 if "Critique" in statut_t else 10
if statut_h != "Optimal": stability_score -= 25 if "Critique" in statut_h else 10

# Styles CSS personnalisés pour les KPIs
st.markdown("""
<style>
.metric-box {
    background-color: #f8f9fa;
    border-radius: 8px;
    padding: 15px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    border-left: 4px solid #3498db;
}
.metric-title { color: #7f8c8d; font-size: 0.9em; font-weight: bold; }
.metric-value { color: #2c3e50; font-size: 1.8em; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

with kpi1:
    st.markdown(f"<div class='metric-box' style='border-left-color:{color_t};'><div class='metric-title'>🌡️ Température</div><div class='metric-value'>{current_t:.1f} °C</div><div style='color:{color_t};font-size:0.8em;'>{statut_t} (Δ {delta_t:+.1f})</div></div>", unsafe_allow_html=True)
with kpi2:
    st.markdown(f"<div class='metric-box' style='border-left-color:{color_h};'><div class='metric-title'>💧 Humidité</div><div class='metric-value'>{current_h:.1f} %</div><div style='color:{color_h};font-size:0.8em;'>{statut_h} (Δ {delta_h:+.1f})</div></div>", unsafe_allow_html=True)
with kpi3:
    # Résistance temporelle (simplifiée pour le dashboard)
    res_t = "OK"
    if "Basse" in statut_t: res_t = f"{cond['temperature']['temps_resistance_bas_h']}h max"
    elif "Haute" in statut_t: res_t = f"{cond['temperature']['temps_resistance_haut_h']}h max"
    st.markdown(f"<div class='metric-box'><div class='metric-title'>⏳ Tolérance T°</div><div class='metric-value' style='font-size:1.2em;margin-top:10px;'>{res_t}</div></div>", unsafe_allow_html=True)
with kpi4:
    st.markdown(f"<div class='metric-box'><div class='metric-title'>🎯 Indice Stabilité</div><div class='metric-value'>{stability_score}/100</div></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Graphique dynamique (historique récent + 1 point futur)
window = 24 # 24 derniers points (6 heures)
start_idx = max(0, idx - window)
df_window = df_rt.iloc[start_idx:idx+1].copy()

fig = make_subplots(specs=[[{"secondary_y": True}]])

fig.add_trace(go.Scatter(x=df_window["datetime"], y=df_window["T"], name="Température (°C)", line=dict(color="#e74c3c", width=3)), secondary_y=False)
fig.add_trace(go.Scatter(x=df_window["datetime"], y=df_window["H"], name="Humidité (%)", line=dict(color="#3498db", dash="dash")), secondary_y=True)

# Zones optimales
fig.add_hrect(y0=t_min, y1=t_max, fillcolor="green", opacity=0.1, line_width=0, secondary_y=False)

fig.update_layout(title="Dynamique Temps Réel (Fenêtre glissante)", height=400, margin=dict(l=0, r=0, t=40, b=0), plot_bgcolor="white")
st.plotly_chart(fig, use_container_width=True)

# Auto-refresh mechanism
if st.session_state.rt_running:
    time.sleep(2) # Attendre 2 secondes (simulation de l'écoulement du temps)
    st.session_state.rt_index += 1
    st.rerun()
