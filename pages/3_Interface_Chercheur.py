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

st.title("🔬 Espace Chercheur & Analyste")
st.write("Bienvenue dans l'espace d'analyse logistique avancée. Choisissez un module ci-dessous :")

tab1, tab2 = st.tabs(["🚀 Module 1 : Recommandation Intelligente", "📦 Module 2 : Optimisation de l'Emplacement"])

with tab1:
    st.header("Recommandation Intelligente d'Entrepôt")
    st.write("Recommandez le meilleur entrepôt basé sur les distances et l'historique IoT des conditions de stockage.")
    
    # --- SECTION 1 : IMPORTATION DES DONNÉES ---
    st.subheader("1. Importation des fichiers (Entrées)")
    col1, col2 = st.columns(2)
    
    file_entrepots = col1.file_uploader("Catalogue des Entrepôts (CSV)", type="csv")
    file_iot = col2.file_uploader("Historique Capteurs IoT (CSV)", type="csv")
    file_trajets = st.file_uploader("Trajets logistiques (CSV)", type="csv")
    
    # --- SECTION 2 : BESOINS SPÉCIFIQUES ET POIDS ---
    st.subheader("2. Paramétrage des priorités (Contraintes)")
    w_dist = st.slider("Importance de la Proximité (Wi)", 0.0, 1.0, 0.5)
    w_temp = st.slider("Importance Stabilité Température (Wi)", 0.0, 1.0, 0.3)
    w_hum = st.slider("Importance Contrôle Humidité (Wi)", 0.0, 1.0, 0.2)
    
    poids = {'dist': w_dist, 'temp': w_temp, 'hum': w_hum}
    
    # --- SECTION 3 : TRAITEMENT ET SORTIE ---
    if st.button("Lancer l'Analyse"):
        if file_entrepots and file_iot and file_trajets:
            with st.spinner('Analyse des scores en cours...'):
                # Lecture des fichiers avec cache
                df_entrepots = load_csv(file_entrepots)
                df_iot = load_csv(file_iot)
                df_trajets = load_csv(file_trajets)
                
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
                            # FIX: Au lieu de mettre t_val=50, on prévient l'utilisateur et on ignore (compliance)
                            st.warning(f"⚠️ Données IoT absentes pour l'entrepôt '{ent['nom']}'. Exclu de la sélection de sécurité.")
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
                    st.info(f"🏆 Meilleur choix : **{meilleur['Entrepôt']}** (Score: {meilleur['Score Global']}/100)")
                else:
                    st.warning("Aucun entrepôt ne correspond au type de stockage requis.")
        else:
            st.error("Veuillez importer les trois fichiers CSV pour continuer.")

with tab2:
    st.header("Optimisation de l'Emplacement du Stockage")
    st.markdown("Trouvez le centre de gravité logistique parfait pour un panel de clients. Chargez un fichier CSV contenant les colonnes : `ville`, `lat`, `lon`, `demande`.")
    
    fichier_upload = st.file_uploader("Fichier des points de demande", type=["csv"], key="upload_demande")

    if fichier_upload is not None:
        try:
            df = load_csv(fichier_upload)
            colonnes_requises = {'ville', 'lat', 'lon', 'demande'} 
            
            if colonnes_requises.issubset(df.columns):
                st.success("Données chargées avec succès !")
                
                with st.spinner('Calcul du centre de gravité en cours...'):
                    # Exécution du calcul métier (Back-end) avec cache
                    resultats = run_analyse(df)
                    
                    # Affichage des KPIs
                    col1, col2 = st.columns(2)
                    col1.metric("📍 Latitude Optimale", f"{resultats['coordonnees_optimales'][0]:.5f}")
                    col2.metric("📍 Longitude Optimale", f"{resultats['coordonnees_optimales'][1]:.5f}")
                    #st.metric("Coût de transport global estimé (Unité x Km)", f"{resultats['cout_transport_global']:,.2f}")
                    
                    st.divider()
                    
                    # --- Affichage de la carte ---
                    st.subheader("🗺️ Visualisation Géographique")
                    afficher_carte_barycentre(resultats['details_df'], resultats['coordonnees_optimales'])
                    
                    st.divider()
    
                    # Affichage du tableau détaillé
                    st.subheader("📊 Détails par point de destination")
                    st.dataframe(resultats['details_df'])
                
            else:
                st.error(f"Format invalide. Colonnes manquantes. Attendu : {colonnes_requises}")
        except Exception as e:
            st.error(f"Une erreur s'est produite lors de l'analyse : {e}")