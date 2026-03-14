import streamlit as st
import pandas as pd
from core.logistique import analyser_demandes_et_localiser
# Importation du nouveau composant visuel
from core.carte import afficher_carte_barycentre

def afficher_module_localisation():
    st.header("📦 Optimisation de l'Emplacement du Stockage")
    st.markdown("Chargez un fichier CSV contenant les colonnes : `ville`, `lat`, `lon`, `demande`.")

    fichier_upload = st.file_uploader("Fichier des points de demande", type=["csv"])

    if fichier_upload is not None:
        try:
            df = pd.read_csv(fichier_upload)
            colonnes_requises = {'ville', 'lat', 'lon', 'demande'} 
            
            if colonnes_requises.issubset(df.columns):
                st.success("Données chargées avec succès !")
                
                # Exécution du calcul métier (Back-end)
                resultats = analyser_demandes_et_localiser(df)
                
                # Affichage des KPIs
                col1, col2 = st.columns(2)
                col1.metric("📍 Latitude Optimale", f"{resultats['coordonnees_optimales'][0]:.5f}")
                col2.metric("📍 Longitude Optimale", f"{resultats['coordonnees_optimales'][1]:.5f}")
                st.metric("Coût de transport global estimé (Unité x Km)", f"{resultats['cout_transport_global']:,.2f}")
                
                st.divider()
                
                # --- NOUVEAU : Affichage de la carte ---
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

if __name__ == "__main__":
    afficher_module_localisation()