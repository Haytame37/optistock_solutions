import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import sys
import os

# Ajout du chemin racine pour éviter le ModuleNotFoundError
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importations propres depuis le module core
from core.logistique import calculer_centre_gravite

st.title("📍 Module 2 : Optimisation d'Implantation")

# 1. Entrée des données : Importation CSV des clients
st.subheader("1. Importation des points de livraison")
file_clients = st.file_uploader("Fichier des clients (CSV)", type="csv")

if file_clients:
    df_clients = pd.read_csv(file_clients)
    
    # 2. Calcul du point idéal
    # On transforme le DataFrame en liste de dictionnaires pour notre fonction
    points = df_clients.to_dict('records')
    lat_opt, lon_opt = calculer_centre_gravite(points)
    
    if lat_opt:
        st.success(f"Point optimal identifié : {lat_opt}, {lon_opt}")
        
        # 3. Création de la Carte Interactive
        m = folium.Map(location=[lat_opt, lon_opt], zoom_start=6)
        
        # Ajouter les clients sur la carte
        for _, row in df_clients.iterrows():
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=row['volume']/100, # La taille du cercle dépend du volume
                color='blue',
                fill=True,
                popup=f"{row['ville']} (Vol: {row['volume']})"
            ).add_to(m)
            
        # Ajouter le point IDÉAL (L'étoile rouge)
        folium.Marker(
            [lat_opt, lon_opt],
            popup="POINT OPTIMAL D'IMPLANTATION",
            icon=folium.Icon(color='red', icon='star')
        ).add_to(m)
        
        # Affichage
        st_folium(m, width=700, height=500)
        
        st.info("💡 L'étoile rouge représente le barycentre logistique. C'est ici que les coûts de transport globaux sont minimisés.")