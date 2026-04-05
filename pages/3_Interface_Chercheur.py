import streamlit as st
import pandas as pd
import numpy as np

from core.logistique import (
    haversine, calculer_score_mixte, analyser_demandes_et_localiser,
    analyser_multi_entrepots, clustering_clients_pour_recommandation,
    calculer_taux_conformite_iot, compatibilite_type_stockage,
    score_distance, score_conformite_temperature, score_conformite_humidite,
    SEUILS_CONFORMITE
)
from core.carte import afficher_carte_barycentre, afficher_carte_recommandation_multi

@st.cache_data
def load_csv(file):
    """Charge un fichier CSV en mémoire cache."""
    return pd.read_csv(file)

@st.cache_data
def run_analyse(df):
    return analyser_demandes_et_localiser(df)

@st.cache_data
def run_multi_analyse(df_json, n):
    df = pd.read_json(df_json)
    return analyser_multi_entrepots(df, n)

def handle_upload(label, required_columns, display_columns=None, example_row=None, col=st, key=None):
    """Gère l'upload, affiche un tableau d'exemples et valide le fichier."""
    uploaded_file = col.file_uploader(label, type="csv", key=key)
    
    if display_columns is None:
        display_columns = required_columns
    
    if example_row:
        html_table = f"""
        <div style="margin-bottom: 10px; border-radius: 5px; overflow: hidden; border: 1px solid #e2e8f0;">
        <table style="font-size: 11.5px; width: 100%; border-collapse: collapse; font-family: sans-serif;">
            <thead>
                <tr style="background-color: #f1f5f9; border-bottom: 1px solid #cbd5e1; color: #334155;">
                    {''.join([f'<th style="padding: 6px; text-align: left; font-weight: 600;">{c}</th>' for c in display_columns])}
                </tr>
            </thead>
            <tbody>
                <tr style="background-color: transparent; color: #64748b;">
                    {''.join([f'<td style="padding: 6px; border-right: 1px dashed #e2e8f0;">{v}</td>' for v in example_row])}
                </tr>
            </tbody>
        </table>
        </div>
        """
        col.markdown(html_table, unsafe_allow_html=True)
    else:
        col.caption(f"Colonnes requises : {', '.join(required_columns)}")
    
    if uploaded_file is not None:
        try:
            df = load_csv(uploaded_file)
            if set(required_columns).issubset(df.columns):
                col.success(f"✅ Fichier importé — {len(df)} lignes.")
                return df
            else:
                missing = set(required_columns) - set(df.columns)
                col.error(f"Échec : Colonnes manquantes ({', '.join(missing)}).")
                return None
        except Exception as e:
            col.error(f"Échec de l'import : {str(e)}")
            return None
    return None

# ═══════════════════════════════════════════════════════════════════
#  EN-TÊTE
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<div style="display: flex; align-items: center; margin-bottom: 20px;">
    <svg width="45" height="45" viewBox="0 0 45 45" xmlns="http://www.w3.org/2000/svg" style="margin-right: 15px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
        <rect width="45" height="45" fill="#2563EB"/>
        <path d="M12 22L22.5 12L33 22" stroke="white" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M22.5 12V32" stroke="white" stroke-width="3.5" stroke-linecap="round"/>
        <circle cx="22.5" cy="22.5" r="4" fill="#2563EB" stroke="white" stroke-width="2.5"/>
        <circle cx="12" cy="22" r="3" fill="white"/>
        <circle cx="33" cy="22" r="3" fill="white"/>
    </svg>
    <div>
        <h1 style="color: #1E293B; margin: 0; font-family: sans-serif; font-weight: 800; font-size: 30px; letter-spacing: -0.5px;">OptiStock Analytics</h1>
        <p style="color: #64748B; margin: 0; font-size: 14px; font-weight: 500;">Espace Chercheur & Data Analyst</p>
    </div>
</div>
<hr style="border: 0; height: 1px; background: #E2E8F0; margin-bottom: 25px;">
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Module 1 : Recommandation Intelligente", "Module 2 : Optimisation de l'Emplacement"])

# ═══════════════════════════════════════════════════════════════════
#  MODULE 1 : RECOMMANDATION INTELLIGENTE (Multi-clients, Multi-entrepôts)
# ═══════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 10px; margin-top: 15px;">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 10px;">
            <path d="M9 21C9 21.5523 9.44772 22 10 22H14C14.5523 22 15 21.5523 15 21V20H9V21ZM12 2C7.58172 2 4 5.58172 4 10C4 12.8711 5.52125 15.3934 7.82843 16.7324L8 16.8321V19H16V16.8321L16.1716 16.7324C18.4788 15.3934 20 12.8711 20 10C20 5.58172 16.4183 2 12 2Z" fill="#2563EB"/>
            <path d="M12 4.5L12 11M9 8H15" stroke="#2563EB" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <h2 style="color: #1E293B; margin: 0; font-family: sans-serif; font-size: 22px; font-weight: 600;">Recommandation Intelligente d'Entrepôt</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("Analysez **tous les clients** et trouvez les meilleurs entrepôts du catalogue pour chaque zone géographique.")
    
    # --- SECTION 1 : IMPORTATION ---
    st.subheader("1. Importation des fichiers")
    col1, col2, col3 = st.columns(3)
    
    df_entrepots = handle_upload(
        "Catalogue des Entrepôts (CSV)", 
        ['id_entrepot', 'id_proprietaire', 'nom', 'latitude', 'longitude', 'type_stockage', 'volume'],
        ['id_entrepot', 'id_proprietaire', 'nom', 'latitude', 'longitude', 'type_stockage', 'volume (m³)'],
        ['ENT001', 'OWN001', 'Hub_Casa', '33.61', '-7.55', 'froid', '12000'],
        col=col1
    )
    df_temp = handle_upload(
        "Historique Température IoT (CSV)", 
        ['id', 'id_entrepot', 'datetime', 'capteur1', 'capteur2', 'capteur3'],
        ['id', 'id_entrepot', 'datetime', 'T_C1', 'T_C2', 'T_C3'],
        ['TMP-ENT001-001', 'ENT001', '2025-01-01 08:00', '4.2', '4.5', '4.1'],
        col=col2
    )
    df_humid = handle_upload(
        "Historique Humidité IoT (CSV)", 
        ['id', 'id_entrepot', 'id_proprietaire', 'datetime', 'capteur1', 'capteur2', 'capteur3'],
        ['id', 'id_entrepot', 'id_proprietaire', 'datetime', 'H_C1', 'H_C2', 'H_C3'],
        ['HUM-ENT001-001', 'ENT001', 'OWN001', '2025-01-01 08:00', '72.5', '71.5', '73.0'],
        col=col3
    )
    df_trajets = handle_upload(
        "Trajets logistiques de tous les clients (CSV)", 
        ['client_id', 'lat', 'lon', 'type_requis'],
        ['client_id', 'lat', 'lon', 'type_requis'],
        ['C0001', '33.58', '-7.62', 'froid'],
    )
    
    # --- SECTION 2 : PARAMÉTRAGE ---
    st.subheader("2. Paramétrage")
    
    col_p1, col_p2 = st.columns([1, 1])
    with col_p1:
        n_entrepots_reco = st.number_input(
            "Combien d'entrepôts recherchez-vous ?", 
            min_value=1, max_value=5, value=2, step=1,
            help="Le système répartira les clients en N zones et recommandera les 3 meilleurs entrepôts par zone."
        )
    
    with col_p2:
        st.caption("**Pondération des critères :**")
    
    w_dist = st.slider("Importance de la Proximité (%)", 0, 100, 50, step=5)
    w_temp = st.slider("Importance Stabilité Température (%)", 0, 100, 30, step=5)
    w_hum = st.slider("Importance Contrôle Humidité (%)", 0, 100, 20, step=5)
    
    somme = w_dist + w_temp + w_hum
    if somme == 0:
        st.warning("⚠️ Veuillez accorder de l'importance à au moins un critère.")
        poids = {'dist': 0.5, 'temp': 0.3, 'hum': 0.2}
    else:
        poids = {'dist': w_dist / somme, 'temp': w_temp / somme, 'hum': w_hum / somme}
        if somme != 100:
            st.caption(f"*(ℹ️ Normalisation auto : {somme}% → 100%)*")
    
    # --- SECTION 3 : ANALYSE ---
    if st.button("🚀 Lancer l'Analyse Complète", type="primary"):
        if df_entrepots is not None and df_temp is not None and df_humid is not None and df_trajets is not None:
            with st.spinner('Analyse en cours sur tous les clients...'):
                
                # ── Pré-calcul IoT ──
                type_map = dict(zip(df_entrepots['id_entrepot'], df_entrepots['type_stockage']))
                stats_iot = {}
                
                temp_grouped = dict(tuple(df_temp.groupby('id_entrepot')))
                humid_grouped = dict(tuple(df_humid.groupby('id_entrepot')))
                entrepots_avec_iot = set(temp_grouped.keys()).intersection(set(humid_grouped.keys()))
                
                for id_ent in entrepots_avec_iot:
                    group_temp = temp_grouped[id_ent]
                    group_humid = humid_grouped[id_ent]
                    type_stock = type_map.get(id_ent, "mixte")
                    stats_iot[id_ent] = calculer_taux_conformite_iot(group_temp, group_humid, type_stock)
                
                PENALITE_SANS_IOT = 0.85
                
                # ── Clustering des clients en N zones ──
                df_trajets_z, center_lats, center_lons = clustering_clients_pour_recommandation(
                    df_trajets, n_entrepots_reco
                )
                
                # ── Analyse par zone : scorer CHAQUE entrepôt pour CHAQUE client ──
                recommendations_par_zone = {}
                entrepots_sans_iot = set()
                
                for zone_id in range(1, n_entrepots_reco + 1):
                    df_zone = df_trajets_z[df_trajets_z['zone'] == zone_id]
                    
                    if len(df_zone) == 0:
                        recommendations_par_zone[zone_id] = []
                        continue
                    
                    # Score moyen de chaque entrepôt pour cette zone
                    scores_entrepots = {}
                    
                    for _, ent in df_entrepots.iterrows():
                        scores_clients = []
                        
                        for _, client in df_zone.iterrows():
                            coeff = compatibilite_type_stockage(ent['type_stockage'], client['type_requis'])
                            if coeff == 0:
                                continue
                            
                            d = haversine(client['lat'], client['lon'], ent['latitude'], ent['longitude'])
                            
                            val_ent = ent['id_entrepot']
                            if val_ent in stats_iot:
                                iot = stats_iot[val_ent]
                                s_t = iot['score_temp']
                                s_h = iot['score_hum']
                                has_iot = True
                            else:
                                seuils = SEUILS_CONFORMITE.get(ent['type_stockage'], SEUILS_CONFORMITE["mixte"])
                                s_t = score_conformite_temperature(seuils['temp_ideale'], ent['type_stockage'])
                                s_h = score_conformite_humidite(seuils['hum_ideale'], ent['type_stockage'])
                                has_iot = False
                                entrepots_sans_iot.add(val_ent)
                            
                            s = calculer_score_mixte(d, s_t, s_h, poids)
                            s = round(s * coeff, 2)
                            if not has_iot:
                                s = round(s * PENALITE_SANS_IOT, 2)
                            
                            scores_clients.append({'score': s, 'dist': d})
                        
                        if scores_clients:
                            avg_score = round(np.mean([x['score'] for x in scores_clients]), 2)
                            avg_dist = round(np.mean([x['dist'] for x in scores_clients]), 1)
                            nb_compat = len(scores_clients)
                            
                            val_ent = ent['id_entrepot']
                            scores_entrepots[val_ent] = {
                                'Score Global': avg_score,
                                'Distance Moy (km)': avg_dist,
                                'ID_Entrepôt': val_ent,
                                'Nom_Entrepôt': ent['nom'],
                                'Type': ent['type_stockage'],
                                'Capacité (m³)': ent['volume'],
                                'Clients Compatibles': f"{nb_compat}/{len(df_zone)}",
                                'IoT': "✅" if val_ent in stats_iot else "⚠️ Estimé",
                            }
                    
                    # Trier et prendre le Top 3
                    top3 = sorted(scores_entrepots.values(), key=lambda x: x['Score Global'], reverse=True)[:3]
                    recommendations_par_zone[zone_id] = top3
                
                # ═══════════ AFFICHAGE DES RÉSULTATS ═══════════
                st.success(f"✅ Analyse terminée — {len(df_trajets)} clients répartis en {n_entrepots_reco} zone(s)")
                
                # Résumé IoT manquant
                if entrepots_sans_iot:
                    with st.expander(f"ℹ️ {len(entrepots_sans_iot)} entrepôt(s) sans IoT — Pénalité de {int((1-PENALITE_SANS_IOT)*100)}%"):
                        st.caption(", ".join(sorted(entrepots_sans_iot)))
                
                # ── Affichage par zone ──
                for zone_id in range(1, n_entrepots_reco + 1):
                    zone_names = ['A', 'B', 'C', 'D', 'E']
                    zone_label = zone_names[zone_id - 1] if zone_id <= 5 else str(zone_id)
                    nb_clients_zone = len(df_trajets_z[df_trajets_z['zone'] == zone_id])
                    
                    st.divider()
                    st.subheader(f"📍 Entrepôt Zone {zone_label} — {nb_clients_zone} clients")
                    
                    top3 = recommendations_par_zone.get(zone_id, [])
                    
                    if not top3:
                        st.warning("Aucun entrepôt compatible trouvé dans le catalogue pour cette zone.")
                        continue
                    
                    # Podium Top 3
                    cols = st.columns(min(3, len(top3)))
                    medals = ["🥇 1er Choix", "🥈 2ème", "🥉 3ème"]
                    
                    for i, rec in enumerate(top3):
                        with cols[i]:
                            st.metric(
                                label=f"{medals[i]} : {rec['Entrepôt']}", 
                                value=f"{rec['Score Global']}/100",
                                delta=f"{rec['Distance Moy (km)']} km moy.",
                                delta_color="inverse"
                            )
                    
                    # Tableau détaillé
                    df_top3 = pd.DataFrame(top3)
                    df_top3.index = range(1, len(df_top3) + 1)
                    st.dataframe(df_top3, use_container_width=True)
                
                # ── Carte globale ──
                st.divider()
                st.subheader("🗺️ Visualisation Cartographique")
                afficher_carte_recommandation_multi(df_trajets_z, recommendations_par_zone, df_entrepots)
                
        else:
            st.error("Veuillez importer les 3 fichiers requis.")


# ═══════════════════════════════════════════════════════════════════
#  MODULE 2 : OPTIMISATION DE L'EMPLACEMENT (Multi-Entrepôts)
# ═══════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 10px; margin-top: 15px;">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 10px;">
            <path d="M12 2C8.13 2 5 5.13 5 9C5 14.25 12 22 12 22C12 22 19 14.25 19 9C19 5.13 15.87 2 12 2ZM12 11.5C10.62 11.5 9.5 10.38 9.5 9C9.5 7.62 10.62 6.5 12 6.5C13.38 6.5 14.5 7.62 14.5 9C14.5 10.38 13.38 11.5 12 11.5Z" fill="#2563EB"/>
        </svg>
        <h2 style="color: #1E293B; margin: 0; font-family: sans-serif; font-size: 22px; font-weight: 600;">Optimisation de l'Emplacement de Stockage</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("Trouvez **un ou plusieurs** centres de gravité logistiques optimaux pour vos clients.")
    
    df_demande = handle_upload(
        "Fichier des points de demande", 
        ['ville', 'lat', 'lon', 'demande', 'tarif_transport'], 
        ['ville', 'lat', 'lon', 'demande', 'tarif_transport (Dhs/km)'],
        ['Casablanca', '33.57', '-7.58', '1500', '1.2'],
        col=st, 
        key="upload_demande"
    )
    
    n_entrepots_loc = st.number_input(
        "Nombre d'entrepôts à implanter :", 
        min_value=1, max_value=5, value=1, step=1,
        help="Le système utilisera K-Means + Weber pour calculer N emplacements optimaux.",
        key="n_entrepots_loc"
    )

    if df_demande is not None:
        if st.button("🚀 Calculer les Emplacements Optimaux", type="primary", key="btn_loc"):
            with st.spinner(f'Calcul de {n_entrepots_loc} emplacement(s) optimal(aux)...'):
                
                if n_entrepots_loc == 1:
                    resultats = run_analyse(df_demande)
                    coord = resultats['coordonnees_optimales']
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Latitude Optimale", f"{coord[0]:.5f}")
                    col2.metric("Longitude Optimale", f"{coord[1]:.5f}")
                    col3.metric("Coût Total Transport", f"{resultats['cout_transport_global']:,.0f} Dhs")
                    
                    st.divider()
                    st.subheader("Visualisation Géographique")
                    afficher_carte_barycentre(resultats['details_df'], coord)
                    
                    st.divider()
                    st.subheader("Détails par point de destination")
                    st.dataframe(resultats['details_df'], use_container_width=True)
                    
                else:
                    # Multi-entrepôts
                    resultats = analyser_multi_entrepots(df_demande, n_entrepots_loc)
                    
                    st.success(f"✅ {resultats['n_entrepots']} emplacements calculés")
                    
                    # KPIs globaux
                    col_g1, col_g2, col_g3 = st.columns(3)
                    col_g1.metric("Entrepôts calculés", resultats['n_entrepots'])
                    col_g2.metric("Coût Total Transport", f"{resultats['cout_transport_global']:,.0f} Dhs")
                    col_g3.metric("Distance Moyenne", f"{resultats['distance_moyenne_km']:.0f} km")
                    
                    # KPIs par zone
                    st.divider()
                    zone_names = ['A', 'B', 'C', 'D', 'E']
                    
                    for zone in resultats['zones']:
                        zid = zone['zone_id']
                        zlabel = zone_names[zid - 1] if zid <= 5 else str(zid)
                        
                        with st.expander(f"📍 Zone {zlabel} — {zone['nb_clients']} clients — Coût: {zone['cout_transport']:,.0f} Dhs", expanded=True):
                            c1, c2, c3 = st.columns(3)
                            c1.metric("Latitude", f"{zone['coordonnees'][0]:.5f}")
                            c2.metric("Longitude", f"{zone['coordonnees'][1]:.5f}")
                            c3.metric("Distance Moyenne", f"{zone['distance_moy']:.1f} km")
                    
                    # Carte multi-entrepôts
                    st.divider()
                    st.subheader("Visualisation Géographique")
                    afficher_carte_barycentre(
                        resultats['details_df'], 
                        resultats['coordonnees_optimales']
                    )
                    
                    st.divider()
                    st.subheader("Détails par point de destination")
                    st.dataframe(resultats['details_df'], use_container_width=True)