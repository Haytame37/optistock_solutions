"""
app.py — OptiStock Solutions
═══════════════════════════════════════════════════════════════════════════════
Application Streamlit principale.

Pages disponibles :
    1. Recherche Entrepôts      → score IoT + analyse capteurs
    2. Analyse Environnementale → séries temporelles + score conformité (UI Dynamique)
    3. Décision Finale (Phase 4)→ fusion 60/40, jauge, tableau + recommandation intelligente
═══════════════════════════════════════════════════════════════════════════════
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from core.iot_analysis      import generer_rapport_iot, load_and_preprocess
from core.scoring           import (
    calculate_environmental_score,
    get_score_label,
    calculer_decision_finale,
    POIDS_LOGISTIQUE,
    POIDS_ENVIRONNEMENT,
    NORMES_SAISONNIERES
)
from core.warehouse_search  import search_entrepots
from utils.db               import load_sql_to_dataframe
from models.reservation     import Reservation, DUREE_VERROU_MINUTES


# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURATION GLOBALE
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="OptiStock Solutions",
    layout="wide",
    page_icon="🏭",
    initial_sidebar_state="expanded"
)

# Custom CSS pour peaufiner l'esthétique
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


# ═════════════════════════════════════════════════════════════════════════════
#  PAGE 1 — RECHERCHE ENTREPÔTS
# ═════════════════════════════════════════════════════════════════════════════

def render_search_page() -> None:
    st.title("🏭 Recherche d'Entrepôts & Audit IoT")
    st.caption("Recherche d'entrepôts basée sur l'historique capteurs.")

    with st.expander("Voir le processus de calcul logistique", expanded=False):
        st.markdown(
            """
            **Logique générale**
            L'algorithme suit une logique de fiabilité industrielle :
            1. Traduire un signal horaire robuste (multi-capteurs).
            2. Pénaliser les incohérences et pannes matérielles.
            3. Ajuster par rapport au type de stockage requis.
            Le score final est borné [0, 100].
            """
        )

    col1, col2 = st.columns([1, 3])
    with col1:
        type_recherche = st.selectbox(
            "Besoin de stockage",
            ["STANDARD", "FROID", "SEC", "CLIMATISE"],
            index=0,
        )
        if st.button("Rechercher 🔍", type="primary", use_container_width=True):
            st.session_state["do_search"] = True

    if st.session_state.get("do_search", False):
        data_dir = Path(__file__).parent / "data" / "cleaned"
        results = search_entrepots(type_recherche, data_dir)

        if not results:
            st.warning("Aucun entrepôt trouvé avec les critères actuels.")
            return

        st.markdown(f"### {len(results)} entrepôt(s) analysé(s) pour `{type_recherche}`")

        for entrepot in results:
            reject_line = ""
            if not entrepot["eligible"] and entrepot["motif_rejet"]:
                reject_line = f"<br><span style='color:#e74c3c'><strong>Motif rejet :</strong> {entrepot['motif_rejet']}</span>"

            card_html = f"""
            <div style="border: 1px solid #e0e0e0; padding: 20px; margin-bottom: 15px; border-radius: 8px; display: flex; align-items: center; background: white; box-shadow: 0 4px 8px rgba(0,0,0,0.06);">
                <div style="font-size: 2.5em; font-weight: bold; color: {entrepot['couleur']}; min-width: 100px; text-align: center;">
                    {entrepot['score']}
                </div>
                <div style="flex-grow: 1; padding-left: 20px;">
                    <div style="font-weight: bold; font-size: 1.3em; color: #34495e;">
                        {entrepot['id_entrepot']}
                        <span style="padding: 4px 12px; border-radius: 20px; color: white; display: inline-block; margin-left: 10px; font-size: 0.7em; background-color: {entrepot['couleur']};">
                            {entrepot['label']}
                        </span>
                    </div>
                    <div style="color: #7f8c8d; font-size: 0.95em; line-height: 1.6; margin-top: 5px;">
                        <strong>Temp:</strong> {entrepot['temp_moyenne']}°C | <strong>Hum:</strong> {entrepot['hum_moyenne']}%<br>
                        <strong>Incidents remontés:</strong> {entrepot['nb_incidents']}
                        {reject_line}
                    </div>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
#  PAGE 2 — ANALYSE ENVIRONNEMENTALE (Avec Graphiques Dynamiques)
# ═════════════════════════════════════════════════════════════════════════════

def render_environmental_page() -> None:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎛️ Paramètres d'Analyse")

    # Chargement robuste des données (via SQL avec fallback simulé)
    try:
        df_t_raw = load_sql_to_dataframe("SELECT * FROM temperature")
        df_h_raw = load_sql_to_dataframe("SELECT * FROM humidite")

        if df_t_raw.empty or df_h_raw.empty:
            raise ValueError("Tables IoT vides.")
            
        df_t_raw["datetime"] = pd.to_datetime(df_t_raw["datetime"])
        df_h_raw["datetime"] = pd.to_datetime(df_h_raw["datetime"])
    except Exception:
        # En cas d'erreur DB, on charge des datasets CSV si disponibles
        try:
            data_dir = Path(__file__).parent / "data" / "samples"
            df_t_raw = pd.read_csv(data_dir / "temperature.csv")
            df_h_raw = pd.read_csv(data_dir / "humidite.csv")
            df_t_raw["datetime"] = pd.to_datetime(df_t_raw["datetime"])
            df_h_raw["datetime"] = pd.to_datetime(df_h_raw["datetime"])
            st.toast("Mode Fallback : Fichiers CSV locaux utilisés.", icon="📂")
        except Exception as e:
            st.error("Impossible de charger les données IoT (ni DB, ni CSV).")
            return

    entrepot_list = df_t_raw["id_entrepot"].unique()
    selected_entrepot = st.sidebar.selectbox("Sélection de l'entrepôt :", entrepot_list)

    df_t = df_t_raw[df_t_raw["id_entrepot"] == selected_entrepot].copy()
    df_h = df_h_raw[df_h_raw["id_entrepot"] == selected_entrepot].copy()

    with st.spinner("Traitement du signal (Lissage & Interpolation)..."):
        # Nouveau pipeline : utilise generer_rapport_iot 
        # (Lissage du bruit des 3 capteurs et agrégation)
        rapport = generer_rapport_iot(df_t, df_h)
        stats = rapport["stats"]
        df_mensuel = rapport["df_mensuel"]

    score_env = calculate_environmental_score(
        rapport["total_releves"],
        rapport["n_anom_temp"],
        rapport["n_anom_humid"]
    )
    label, emoji = get_score_label(score_env)

    # ── En-tête ─────────────────────────────────────────────────────────────
    st.title(f"🌍 Analyse Environnementale • {selected_entrepot}")
    st.markdown(f"### Score de Conformité : **{score_env}/100** &nbsp; {emoji} {label}")
    
    st.divider()

    # ── Kpis ─────────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='metric-box'><div class='metric-title'>🌡️ Température Moyenne</div><div class='metric-value'>{stats['temp_mean']} °C</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-box' style='border-left-color:#2ecc71;'><div class='metric-title'>💧 Humidité Moyenne</div><div class='metric-value'>{stats['humid_mean']} %</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-box' style='border-left-color:#e74c3c;'><div class='metric-title'>🚨 Alertes T° détectées</div><div class='metric-value'>{rapport['n_anom_temp']}</div></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='metric-box' style='border-left-color:#f1c40f;'><div class='metric-title'>📊 Fiabilité Bruit</div><div class='metric-value'>Filtrée (Lissée)</div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Trace du Graphique avec seuils HACCP dynamiques ───────────────────────
    st.subheader("📈 Séries Temporelles Multi-Capteurs avec Normes Saisonnières")
    st.caption("Affiche la série après interpolation linéaire et lissage par moyenne mobile.")

    # Re-calcul simple des séries traitées pour le chart
    cols_t = [c for c in ["capteur1", "capteur2", "capteur3"] if c in df_t.columns]
    cols_h = [c for c in ["capteur1", "capteur2", "capteur3"] if c in df_h.columns]
    
    # Pour alléger plotly en web, on resample si dataset énorme
    df_t_chart = df_t.sort_values("datetime").iloc[::5, :] # 1 point sur 5
    df_h_chart = df_h.sort_values("datetime").iloc[::5, :]
    
    val_t_moy = df_t_chart[cols_t].mean(axis=1) if cols_t else df_t_chart.select_dtypes('number').mean(axis=1)
    val_h_moy = df_h_chart[cols_h].mean(axis=1) if cols_h else df_h_chart.select_dtypes('number').mean(axis=1)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Signal température
    fig.add_trace(go.Scatter(
        x=df_t_chart["datetime"], y=val_t_moy, 
        name="T° Moyenne Lissée", line=dict(color="#e74c3c", width=2)
    ), secondary_y=False)
    
    # Signal humidité
    fig.add_trace(go.Scatter(
        x=df_h_chart["datetime"], y=val_h_moy, 
        name="Humidité", line=dict(color="#3498db", dash="dot")
    ), secondary_y=True)

    # Zones de seuil HACCP (On trace un ruban rouge pour alerter visuellement)
    max_t, min_t = 25.0, 15.0 # Valeurs génériques pour la zone de danger visuelle
    fig.add_hrect(
        y0=max_t, y1=max_t+15, fillcolor="red", opacity=0.1, line_width=0, 
        secondary_y=False, annotation_text="Hors Norme (Chaud)", annotation_position="top left"
    )
    fig.add_hrect(
        y0=min_t-15, y1=min_t, fillcolor="blue", opacity=0.1, line_width=0, 
        secondary_y=False, annotation_text="Hors Norme (Froid)", annotation_position="bottom left"
    )

    fig.update_layout(
        title="Variation Thermodynamique vs Seuils",
        hovermode="x unified",
        height=500, margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor="white"
    )
    fig.update_yaxes(title_text="Température (°C)", secondary_y=False, gridcolor="#ecf0f1")
    fig.update_yaxes(title_text="Humidité (%)", secondary_y=True, showgrid=False)

    st.plotly_chart(fig, use_container_width=True)

    # ── Analyse Saisonnière (Mensuelle) ──────────────────────────────────────
    st.divider()
    st.subheader("📅 Segmentation Saisonnière (HACCP)")
    st.caption("Détection intelligente des anomalies par mois (ex: un pic de 25°C est toléré en été, mais bloque en hiver).")

    if df_mensuel.empty:
        st.info("Oups ! Pas de données suffisantes pour une analyse mensuelle.")
    else:
        # Pimp le dataframe
        def color_statut(val):
            if "Conforme" in val: return "color: #27ae60; font-weight:bold;"
            if "Vigilance" in val: return "color: #f39c12; font-weight:bold;"
            return "color: #e74c3c; font-weight:bold;"
        
        display_df = df_mensuel[['mois', 'saison', 'n_anom_temp', 'pct_anom_temp', 'norm_t_min', 'norm_t_max', 'statut_mois']].copy()
        display_df.columns = ["Mois", "Saison", "Nb Anomalies", "% Anomalies", "Cible Min", "Cible Max", "Avis Synthétique"]
        
        st.dataframe(display_df.style.applymap(color_statut, subset=["Avis Synthétique"]), use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
#  PAGE 3 — DÉCISION FINALE (Phase 4)
# ═════════════════════════════════════════════════════════════════════════════

def render_decision_finale_page() -> None:
    st.title("⚖️ Décision Finale — Phase 4 (SAW)")
    st.caption(
        f"Moteur de fusion pondérée selon Triantaphyllou : **{int(POIDS_LOGISTIQUE*100)}% Logistique** "
        f"+ **{int(POIDS_ENVIRONNEMENT*100)}% Environnement**"
    )

    st.divider()

    # ── SECTION 1 : Saisie des scores ────────────────────────────────────────
    st.subheader("📥 1. Analyse Algorithmique Globale")

    col_a, col_b = st.columns(2)
    with col_a:
        score_log_input = st.slider("🚚 Score Logistique (0-100)", 0.0, 100.0, 80.5, 0.5)
    with col_b:
        score_env_input = st.slider("🌡️ Score Environnemental (0-100)", 0.0, 100.0, 62.0, 0.5)

    # ── SECTION 2 : Décision Automatique ─────────────────────────────────────
    # Intégration du moteur intelligent mis à jour avec alertes
    decision = calculer_decision_finale(score_log_input, score_env_input)
    score_global = decision["score_global"]
    conseil = decision["conseil"]

    col_gauge, col_conseil = st.columns([1.2, 1])

    with col_gauge:
        # Gauge Chart modernisé
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score_global,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "<b>Score SAW Global</b><br><span style='font-size:0.8em;color:gray'>OptiStock Intelligence</span>"},
            delta={"reference": 75, "increasing": {"color": "#27ae60"}, "decreasing": {"color": "#e74c3c"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "darkblue"},
                "bar": {"color": conseil["couleur"], "thickness": 0.3},
                "bgcolor": "white",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 50], "color": "#fde8e8"},
                    {"range": [50, 75], "color": "#fef3e2"},
                    {"range": [75, 100], "color": "#e8f8f5"}
                ],
                "threshold": {"line": {"color": "black", "width": 4}, "thickness": 0.5, "value": 75}
            }
        ))
        fig.update_layout(height=350, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    with col_conseil:
        # Bloc Conseil Expert
        st.markdown(f"### {conseil['emoji']} Verdict : **{conseil['statut']}**")
        st.info(f"**Diagnostic :** {conseil['texte']}")
        
        # Alerte saisonnière dynamique !
        st.warning(f"**{conseil['alerte_saisonniere']}**")
        
        st.success(f"📌 **Action immédiate :** {conseil['action']}")

    st.divider()

    # ── SECTION 3 : Verrouillage Transactionnel (Pre_Lock) ───────────────────
    st.subheader("🔒 2. Transaction et Verrouillage (`System_Pre_Lock`)")
    st.write("Ce système prévient les conditions de course (pessimistic lock) pour une durée de **15 minutes** (modulable) lors de la finalisation.")
    
    c_lock1, c_lock2 = st.columns(2)
    with c_lock1:
        e_id = st.text_input("ID Entrepôt :", "ENT_001")
        btn_lock = st.button("Activer Verrou", type="primary")
        btn_unlock = st.button("Libérer")
    
    with c_lock2:
        st.markdown("**Monitoring des Verrous Actifs :**")
        verrous = Reservation.get_verrous_actifs()
        if verrous:
            for eid, v in verrous.items():
                st.code(f"[{v['statut']}] {eid} > Expire à {v['expiration'].strftime('%H:%M:%S')}")
        else:
            st.success("Aucun entrepôt n'est actuellement en phase de négociation exclusive.")

    # Logique boutons
    if btn_lock:
        resa = Reservation(id_reservation="RES001", entrepot_id=e_id, client_id="CLIENT_WEB", score_global=score_global)
        res = resa.appliquer_verrou(e_id)
        if res["succes"]: st.success(res["message"])
        else: st.error(res["message"])
        st.rerun()

    if btn_unlock:
        tmp = Reservation("TMP", e_id, "TMP")
        msg = tmp.liberer_verrou(e_id)
        st.toast(msg["message"])
        st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
#  ROUTAGE DU MENU
# ═════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3256/3256860.png", width=60)
    st.title("OptiStock")
    st.markdown("---")
    vue = st.radio("Navigation", ["🔍 Recherche IoT", "🌍 Analyse Environnementale", "⚖️ Décision (Phase 4)"])

if vue == "🔍 Recherche IoT":
    render_search_page()
elif vue == "🌍 Analyse Environnementale":
    render_environmental_page()
else:
    render_decision_finale_page()
