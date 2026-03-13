import streamlit as st
import pandas as pd
import sys
import os

# 1. FIX: ModuleNotFoundError
# On ajoute la racine du projet au chemin de recherche de Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from core.logistique import haversine, calculer_score_mixte
except ModuleNotFoundError:
    st.error("⚠️ Le module 'core' est introuvable. Vérifiez que vous avez bien un fichier __init__.py dans le dossier core.")

st.title("🚀 Module 1 : Recommandation Intelligente")

# --- SECTION 1 : IMPORTATION DES DONNÉES ---
st.subheader("1. Importation des fichiers (Entrées)")
col1, col2 = st.columns(2)

# FIX: On définit bien les variables AVANT de les utiliser dans le IF
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
            # Lecture des fichiers
            df_entrepots = pd.read_csv(file_entrepots)
            df_iot = pd.read_csv(file_iot)
            df_trajets = pd.read_csv(file_trajets)
            
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
                    t_val = iot_row['temperature'].values[0] if not iot_row.empty else 50
                    h_val = iot_row['humidite'].values[0] if not iot_row.empty else 50

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