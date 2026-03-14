import folium
from streamlit_folium import st_folium
import math

def afficher_carte_barycentre(df_demandes, coord_optimales):
    """
    Génère et affiche une carte Folium interactive dans Streamlit.
    Les noms des villes sont affichés sous forme d'étiquettes (badges) propres.
    """
    lat_centre, lon_centre = coord_optimales

    # 1. Initialiser la carte
    carte = folium.Map(location=[lat_centre, lon_centre], zoom_start=6, tiles="CartoDB positron")

    # 2. Placer le marqueur de l'entrepôt (Barycentre)
    folium.Marker(
        location=[lat_centre, lon_centre],
        popup=folium.Popup(f"<b>Entrepôt Optimal</b><br>Lat: {lat_centre:.4f}<br>Lon: {lon_centre:.4f}", max_width=200),
        tooltip="📍 Emplacement recommandé",
        icon=folium.Icon(color="red", icon="star", prefix='fa')
    ).add_to(carte)

    max_demande = df_demandes['demande'].max()

    # 3. Placer les points de demande (villes/clients)
    for index, row in df_demandes.iterrows():
        demande = row['demande']
        
        # Définir la couleur en fonction du volume
        ratio = demande / max_demande
        if ratio < 0.33:
            couleur_cercle = "#28a745" # Vert
        elif ratio < 0.66:
            couleur_cercle = "#fd7e14" # Orange
        else:
            couleur_cercle = "#dc3545" # Rouge

        # Calcul de la taille du cercle
        rayon_calcule = math.sqrt(demande) * 0.5 
        rayon_affichage = max(4, rayon_calcule) 
        
        # Dessiner le cercle
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=rayon_affichage, 
            popup=f"<b>{row['ville']}</b><br>Demande: {demande}<br>Dist: {row['distance_au_centre_km']:.1f} km",
            tooltip=row['ville'],
            color=couleur_cercle,
            fill=True,
            fill_color=couleur_cercle,
            fill_opacity=0.6
        ).add_to(carte)

        # --- CORRECTION DE L'AFFICHAGE DU NOM ---
        # Création d'un style CSS "Badge" propre et centré
        style_etiquette = (
            "font-family: Arial, sans-serif; "
            "font-size: 10px; "
            "font-weight: bold; "
            "color: #2c3e50; "
            "background-color: rgba(255, 255, 255, 0.85); " # Fond blanc presque opaque
            "border: 1px solid rgba(0,0,0,0.15); " # Légère bordure grise
            "border-radius: 4px; " # Coins arrondis
            "padding: 2px 6px; " # Espace autour du texte
            "white-space: nowrap; "
            "position: absolute; "
            "transform: translate(-50%, 14px); " # Centre le badge horizontalement et le descend sous le point
            "box-shadow: 0px 1px 3px rgba(0,0,0,0.2);" # Petite ombre sous la boîte
        )

        folium.Marker(
            location=[row['lat'], row['lon']],
            icon=folium.DivIcon(
                html=f'<div style="{style_etiquette}">{row["ville"]}</div>'
            )
        ).add_to(carte)

    # 4. Afficher la carte dans l'interface Streamlit
    st_folium(carte, width=800, height=500, returned_objects=[])