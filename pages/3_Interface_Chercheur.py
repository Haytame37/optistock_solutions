import streamlit as st
import pandas as pd

from core.logistique import haversine, calculer_score_mixte, analyser_demandes_et_localiser
from core.carte import afficher_carte_barycentre

@st.cache_data
def load_csv(file):
    """Charge un fichier CSV en mémoire cache pour optimiser les performances."""
    return pd.read_csv(file)

@st.cache_data
def run_analyse(df):
    return analyser_demandes_et_localiser(df)

def handle_upload(label, required_columns, col=st, key=None):
    """Gère l'upload, affiche les colonnes requises et valide le fichier."""
    uploaded_file = col.file_uploader(label, type="csv", key=key)
    col.caption(f"Colonnes requises : {', '.join(required_columns)}")
    
    if uploaded_file is not None:
        try:
            df = load_csv(uploaded_file)
            if set(required_columns).issubset(df.columns):
                col.success("Fichier importé avec succès.")
                return df
            else:
                missing = set(required_columns) - set(df.columns)
                col.error(f"Échec : Colonnes manquantes ({', '.join(missing)}).")
                return None
        except Exception as e:
            col.error(f"Échec de l'import : {str(e)}")
            return None
    return None

# --- EN-TÊTE AVEC LOGO SVG ---
st.markdown("""
<div style="display: flex; align-items: center; margin-bottom: 20px;">
    <svg width="45" height="45" viewBox="0 0 45 45" xmlns="http://www.w3.org/2000/svg" style="margin-right: 15px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
        <!-- Fond de l'icône -->
        <rect width="45" height="45" fill="#2563EB"/>
        <!-- Géométrie abstraite Logistique/Data -->
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

with tab1:
    # Logo SVG pour l'Intelligence / Algorithme
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 10px; margin-top: 15px;">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 10px;">
            <path d="M9 21C9 21.5523 9.44772 22 10 22H14C14.5523 22 15 21.5523 15 21V20H9V21ZM12 2C7.58172 2 4 5.58172 4 10C4 12.8711 5.52125 15.3934 7.82843 16.7324L8 16.8321V19H16V16.8321L16.1716 16.7324C18.4788 15.3934 20 12.8711 20 10C20 5.58172 16.4183 2 12 2ZM17.4398 14.5204L16.2995 15.1834V17H7.70054V15.1834L6.56019 14.5204C4.60627 13.3835 3.31053 11.2338 3.31053 8.89474C3.31053 4.54228 6.84228 1.01053 11.1947 1.01053C15.5472 1.01053 19.0789 4.54228 19.0789 8.89474C19.0789 11.2338 17.7832 13.3835 15.8293 14.5204H17.4398Z" fill="#2563EB"/>
            <path d="M12 4.5L12 11M9 8H15" stroke="#2563EB" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <h2 style="color: #1E293B; margin: 0; font-family: sans-serif; font-size: 22px; font-weight: 600;">Recommandation Intelligente d'Entrepôt</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("Recommandez le meilleur entrepôt basé sur les distances et l'historique IoT des conditions de stockage.")
    
    # --- SECTION 1 : IMPORTATION DES DONNÉES ---
    st.subheader("1. Importation des fichiers (Entrées)")
    col1, col2 = st.columns(2)
    
    df_entrepots = handle_upload("Catalogue des Entrepôts (CSV)", ['nom', 'lat', 'lon', 'type_stockage'], col1)
    df_iot = handle_upload("Historique Capteurs IoT (CSV)", ['nom_entrepot', 'temperature', 'humidite'], col2)
    df_trajets = handle_upload("Trajets logistiques (CSV)", ['client_id', 'lat', 'lon', 'type_requis'], st)
    
    # --- SECTION 2 : BESOINS SPÉCIFIQUES ET POIDS ---
    st.subheader("2. Paramétrage des priorités (Contraintes)")
    w_dist = st.slider("Importance de la Proximité (Wi)", 0.0, 1.0, 0.5)
    w_temp = st.slider("Importance Stabilité Température (Wi)", 0.0, 1.0, 0.3)
    w_hum = st.slider("Importance Contrôle Humidité (Wi)", 0.0, 1.0, 0.2)
    
    poids = {'dist': w_dist, 'temp': w_temp, 'hum': w_hum}
    
    # --- SECTION 3 : TRAITEMENT ET SORTIE ---
    if st.button("Lancer l'Analyse"):
        # On vérifie que les 3 DataFrames sont bien chargés et valides (non None)
        if df_entrepots is not None and df_iot is not None and df_trajets is not None:
            with st.spinner('Analyse des scores en cours...'):
                
                # Calcul de conformité IoT simplifiée pour le test
                stats_iot = df_iot.groupby('nom_entrepot').agg({
                    'temperature': 'mean',
                    'humidite': 'mean'
                }).reset_index()
    
                resultats = []
                
                # On prend le premier trajet pour l'exemple
                # (Dans un vrai système, on bouclerait sur df_trajets)
                trajet = df_trajets.iloc[0] 
                
                for _, ent in df_entrepots.iterrows():
                    # Filtrage par type (Besoin spécifique)
                    if ent['type_stockage'] == trajet['type_requis']:
                        d = haversine(trajet['lat'], trajet['lon'], ent['lat'], ent['lon'])
                        
                        # Récupération données IoT
                        iot_row = stats_iot[stats_iot['nom_entrepot'] == ent['nom']]
                        
                        if iot_row.empty:
                            st.warning(f"Données IoT absentes pour l'entrepôt '{ent['nom']}'. Exclu de la sélection de sécurité.")
                            continue 
                        
                        t_val = iot_row['temperature'].values[0]
                        h_val = iot_row['humidite'].values[0]
    
                        # Calcul du score via la formule pondérée
                        s = calculer_score_mixte(d, t_val, h_val, poids)
                        
                        resultats.append({
                            "Entrepôt": ent['nom'],
                            "Score Global": s,
                            "Distance (km)": round(d, 2),
                            "Type": ent['type_stockage']
                        })
    
                if resultats:
                    df_final = pd.DataFrame(resultats).sort_values(by="Score Global", ascending=False)
                    st.success("Analyse terminée !")
                    st.write("### Classement des meilleures options logistiques")
                    st.dataframe(df_final, use_container_width=True)
                    
                    # Mise en avant du meilleur
                    meilleur = df_final.iloc[0]
                    st.info(f"Meilleur choix : {meilleur['Entrepôt']} (Score: {meilleur['Score Global']}/100)")
                else:
                    st.warning("Aucun entrepôt ne correspond au type de stockage requis.")
        else:
            st.error("Veuillez importer des fichiers valides pour les trois catégories afin de continuer.")

with tab2:
    # Logo SVG pour Géographie / Localisation
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 10px; margin-top: 15px;">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 10px;">
            <path d="M12 2C8.13 2 5 5.13 5 9C5 14.25 12 22 12 22C12 22 19 14.25 19 9C19 5.13 15.87 2 12 2ZM12 11.5C10.62 11.5 9.5 10.38 9.5 9C9.5 7.62 10.62 6.5 12 6.5C13.38 6.5 14.5 7.62 14.5 9C14.5 10.38 13.38 11.5 12 11.5Z" fill="#2563EB"/>
        </svg>
        <h2 style="color: #1E293B; margin: 0; font-family: sans-serif; font-size: 22px; font-weight: 600;">Optimisation de l'Emplacement de Stockage</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("Trouvez le centre de gravité logistique parfait pour un panel de clients.")
    
    df_demande = handle_upload("Fichier des points de demande", ['ville', 'lat', 'lon', 'demande'], st, key="upload_demande")

    if df_demande is not None:
        with st.spinner('Calcul du centre de gravité en cours...'):
            # Exécution du calcul métier (Back-end) avec cache
            resultats = run_analyse(df_demande)
            
            # Affichage des KPIs
            col1, col2 = st.columns(2)
            col1.metric("Latitude Optimale", f"{resultats['coordonnees_optimales'][0]:.5f}")
            col2.metric("Longitude Optimale", f"{resultats['coordonnees_optimales'][1]:.5f}")
            
            st.divider()
            
            # --- Affichage de la carte ---
            st.subheader("Visualisation Géographique")
            afficher_carte_barycentre(resultats['details_df'], resultats['coordonnees_optimales'])
            
            st.divider()

            # Affichage du tableau détaillé
            st.subheader("Détails par point de destination")
            st.dataframe(resultats['details_df'])