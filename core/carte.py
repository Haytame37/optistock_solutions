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

def afficher_carte_recommandation(trajet, df_entrepots, df_final):
    """
    Affiche la carte pour le système de recommandation.
    Met en évidence le client cible et le podium des 3 meilleurs entrepôts.
    """
    # 1. Centrer la carte sur le client (Trajet)
    carte = folium.Map(location=[trajet['lat'], trajet['lon']], zoom_start=6, tiles="CartoDB positron")

    # 2. Placer le point de livraison (Client)
    folium.Marker(
        location=[trajet['lat'], trajet['lon']],
        popup=f"<b>Client: {trajet.get('client_id', 'Inconnu')}</b><br>Besoin: {trajet.get('type_requis', 'Non spécifié')}",
        tooltip="📍 Point de Livraison Client",
        icon=folium.Icon(color="blue", icon="user", prefix='fa')
    ).add_to(carte)

    # 3. Podium avec couleurs sémantiques claires
    top3_names = df_final.head(3)['Entrepôt'].tolist()
    podium_icons = [
        {"color": "darkgreen", "icon": "trophy"},    # #1 Or
        {"color": "blue",      "icon": "thumbs-up"}, # #2 Argent
        {"color": "orange",    "icon": "flag"},      # #3 Bronze
    ]
    
    # 4. Placer tous les entrepôts
    for _, row in df_entrepots.iterrows():
        nom = row['nom']
        lat, lon = row['lat'], row['lon']
        
        # Vérifier si l'entrepôt est dans le top 3 des recommandations
        if nom in top3_names:
            rank = top3_names.index(nom)
            icon_cfg = podium_icons[rank]
            # Récupération du score
            score_row = df_final[df_final['Entrepôt'] == nom]
            score = score_row['Score Global'].values[0] if not score_row.empty else "N/A"
            dist = score_row['Distance (km)'].values[0] if not score_row.empty else "N/A"
            
            popup_html = f"""
            <div style='font-family:sans-serif; min-width:150px'>
                <b style='font-size:13px'>#{rank+1} {nom}</b><br>
                <span style='color:#2563EB'>Score : {score}/100</span><br>
                <span style='color:#64748b'>Distance : {dist} km</span>
            </div>
            """
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=200),
                tooltip=f"#{rank+1} {nom} — Score: {score}/100",
                icon=folium.Icon(color=icon_cfg["color"], icon=icon_cfg["icon"], prefix='fa')
            ).add_to(carte)
            
            # Ligne entre client et 1er choix
            if rank == 0:
                folium.PolyLine(
                    locations=[[trajet['lat'], trajet['lon']], [lat, lon]],
                    color="#16a34a", weight=2.5, opacity=0.7,
                    tooltip=f"Distance : {dist} km"
                ).add_to(carte)
        else:
            # Autres entrepôts de la base de données qui ne sont pas dans le Top 3 (ou incompatibles)
            folium.CircleMarker(
                location=[lat, lon],
                radius=4,
                popup=f"<b>{nom}</b><br>Non recommandé pour ce trajet",
                tooltip=nom,
                color="#6c757d", # Gris
                fill=True,
                fill_color="#6c757d",
                fill_opacity=0.6
            ).add_to(carte)
            
    # Affichage
    st_folium(carte, width=800, height=500, returned_objects=[])