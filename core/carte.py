import folium
from streamlit_folium import st_folium
import math

# Palette de couleurs pour les zones (jusqu'à 5 zones)
ZONE_COLORS = ['#2563EB', '#DC2626', '#059669', '#D97706', '#7C3AED']
ZONE_FILL_COLORS = ['#93C5FD', '#FCA5A5', '#6EE7B7', '#FCD34D', '#C4B5FD']
ZONE_NAMES = ['Zone A', 'Zone B', 'Zone C', 'Zone D', 'Zone E']


def afficher_carte_barycentre(df_demandes, coord_optimales, zones=None):
    """
    Carte Folium pour le module d'implantation.
    Supporte 1 ou N entrepôts optimaux (multi-zones).
    """
    # Déterminer le centre de la carte
    if isinstance(coord_optimales, list):
        # Multi-entrepôts : centrer sur la moyenne
        lat_c = sum(c[0] for c in coord_optimales) / len(coord_optimales)
        lon_c = sum(c[1] for c in coord_optimales) / len(coord_optimales)
    else:
        lat_c, lon_c = coord_optimales

    carte = folium.Map(location=[lat_c, lon_c], zoom_start=6, tiles="CartoDB positron")

    max_demande = df_demandes['demande'].max() if not df_demandes.empty else 1

    # Placer les points de demande
    for _, row in df_demandes.iterrows():
        demande = row['demande']
        zone = int(row.get('zone', 1)) - 1 if 'zone' in row else 0

        # Couleur par zone
        couleur = ZONE_COLORS[zone % len(ZONE_COLORS)]

        # Rayon proportionnel à la demande (plafonné)
        rayon = max(4, min(math.sqrt(demande) * 0.5, 20))

        popup_html = f"""
        <div style='font-family:sans-serif; min-width:120px'>
            <b>{row['ville']}</b><br>
            <span style='color:{couleur}'>Demande : {demande}</span><br>
            <span style='color:#64748b'>Dist : {row['distance_au_centre_km']:.1f} km</span>
            {'<br><span style="color:#334155">Zone : ' + str(zone+1) + '</span>' if 'zone' in row else ''}
        </div>
        """

        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=rayon,
            popup=folium.Popup(popup_html, max_width=200),
            tooltip=f"{row['ville']} — Demande: {demande}",
            color=couleur,
            fill=True,
            fill_color=couleur,
            fill_opacity=0.5,
            weight=1.5
        ).add_to(carte)

    # Placer le(s) marqueur(s) entrepôt(s) optimal(aux)
    if isinstance(coord_optimales, list):
        for i, (lat, lon) in enumerate(coord_optimales):
            color = ['red', 'blue', 'green', 'orange', 'purple'][i % 5]
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(
                    f"<b>Entrepôt Optimal — {ZONE_NAMES[i]}</b><br>"
                    f"Lat: {lat:.4f}<br>Lon: {lon:.4f}",
                    max_width=200
                ),
                tooltip=f"📍 {ZONE_NAMES[i]} — Emplacement optimal",
                icon=folium.Icon(color=color, icon="star", prefix='fa')
            ).add_to(carte)
    else:
        lat, lon = coord_optimales
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(f"<b>Entrepôt Optimal</b><br>Lat: {lat:.4f}<br>Lon: {lon:.4f}", max_width=200),
            tooltip="📍 Emplacement recommandé",
            icon=folium.Icon(color="red", icon="star", prefix='fa')
        ).add_to(carte)

    st_folium(carte, width=800, height=500, returned_objects=[])


def afficher_carte_recommandation_multi(df_trajets_zones, recommendations_par_zone, df_entrepots):
    """
    Carte pour le module de recommandation multi-zones.
    Affiche les clients colorés par zone et les entrepôts recommandés par zone.
    """
    # Centre de la carte
    lat_c = df_trajets_zones['lat'].mean()
    lon_c = df_trajets_zones['lon'].mean()
    carte = folium.Map(location=[lat_c, lon_c], zoom_start=6, tiles="CartoDB positron")

    # 1. Placer tous les clients, colorés par zone
    for _, row in df_trajets_zones.iterrows():
        zone = int(row['zone']) - 1
        couleur = ZONE_COLORS[zone % len(ZONE_COLORS)]

        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=4,
            popup=f"<b>{row['client_id']}</b><br>Type: {row['type_requis']}<br>Zone: {zone+1}",
            tooltip=f"{row['client_id']} — {ZONE_NAMES[zone]}",
            color=couleur,
            fill=True,
            fill_color=couleur,
            fill_opacity=0.6,
            weight=1
        ).add_to(carte)

    # 2. Placer les entrepôts recommandés (#1 de chaque zone)
    entrepots_places = set()
    for zone_id, recs in recommendations_par_zone.items():
        if not recs:
            continue
        zone_idx = zone_id - 1
        best = recs[0]  # Meilleur entrepôt de la zone
        nom = best['Entrepôt']

        # Trouver les coordonnées de l'entrepôt
        ent_row = df_entrepots[df_entrepots['nom'] == nom]
        if ent_row.empty:
            continue

        lat, lon = ent_row.iloc[0]['lat'], ent_row.iloc[0]['lon']
        color = ['darkgreen', 'blue', 'orange', 'red', 'purple'][zone_idx % 5]
        icon = ['trophy', 'thumbs-up', 'flag', 'bookmark', 'star'][zone_idx % 5]

        popup_html = f"""
        <div style='font-family:sans-serif; min-width:150px'>
            <b style='font-size:13px'>🏆 {ZONE_NAMES[zone_idx]} — {nom}</b><br>
            <span style='color:#2563EB'>Score : {best['Score Global']}/100</span><br>
            <span style='color:#64748b'>Distance moy. : {best['Distance Moy (km)']} km</span>
        </div>
        """

        if nom not in entrepots_places:
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"🏆 {ZONE_NAMES[zone_idx]} — {nom} (Score: {best['Score Global']})",
                icon=folium.Icon(color=color, icon=icon, prefix='fa')
            ).add_to(carte)
            entrepots_places.add(nom)

    # 3. Entrepôts non recommandés (gris)
    for _, row in df_entrepots.iterrows():
        if row['nom'] not in entrepots_places:
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=5,
                popup=f"<b>{row['nom']}</b><br>Type: {row['type_stockage']}",
                tooltip=row['nom'],
                color="#9CA3AF",
                fill=True,
                fill_color="#9CA3AF",
                fill_opacity=0.4,
                weight=1
            ).add_to(carte)

    st_folium(carte, width=800, height=500, returned_objects=[])