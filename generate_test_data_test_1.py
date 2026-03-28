# -*- coding: utf-8 -*-
"""
=============================================================================
  OPTISTOCK SOLUTIONS — Générateur de Données de Test (1000 lignes)
  Contexte : Maroc — Villes, coordonnées et logistique réalistes
  Fichier : generate_test_data_test_1.py
=============================================================================
"""

import pandas as pd
import numpy as np
import os
import random

# ── Seed pour la reproductibilité ──
np.random.seed(2026)
random.seed(2026)

# ── Répertoire de sortie ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "samples")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
#  RÉFÉRENTIELS DU MAROC
# ══════════════════════════════════════════════════════════════════════════════

# 50 villes marocaines avec coordonnées réalistes
VILLES_MAROC = [
    {"ville": "Casablanca",      "lat": 33.5731, "lon": -7.5898},
    {"ville": "Rabat",           "lat": 34.0209, "lon": -6.8416},
    {"ville": "Marrakech",       "lat": 31.6295, "lon": -7.9811},
    {"ville": "Fès",             "lat": 34.0333, "lon": -4.9998},
    {"ville": "Tanger",          "lat": 35.7595, "lon": -5.8340},
    {"ville": "Agadir",          "lat": 30.4202, "lon": -9.5982},
    {"ville": "Meknès",          "lat": 33.8935, "lon": -5.5547},
    {"ville": "Oujda",           "lat": 34.6867, "lon": -1.9114},
    {"ville": "Kénitra",         "lat": 34.2610, "lon": -6.5802},
    {"ville": "Tétouan",         "lat": 35.5785, "lon": -5.3684},
    {"ville": "Safi",            "lat": 32.2994, "lon": -9.2372},
    {"ville": "El Jadida",       "lat": 33.2549, "lon": -8.5000},
    {"ville": "Nador",           "lat": 35.1681, "lon": -2.9287},
    {"ville": "Béni Mellal",     "lat": 32.3394, "lon": -6.3498},
    {"ville": "Taza",            "lat": 34.2100, "lon": -4.0100},
    {"ville": "Khémisset",       "lat": 33.8242, "lon": -6.0664},
    {"ville": "Settat",          "lat": 33.0016, "lon": -7.6166},
    {"ville": "Khouribga",       "lat": 32.8811, "lon": -6.9063},
    {"ville": "Berrechid",       "lat": 33.2651, "lon": -7.5875},
    {"ville": "Mohammedia",      "lat": 33.6861, "lon": -7.3828},
    {"ville": "Larache",         "lat": 35.1932, "lon": -6.1563},
    {"ville": "Guelmim",         "lat": 28.9870, "lon": -10.0574},
    {"ville": "Errachidia",      "lat": 31.9314, "lon": -4.4260},
    {"ville": "Ouarzazate",      "lat": 30.9189, "lon": -6.8936},
    {"ville": "Tan-Tan",         "lat": 28.4380, "lon": -11.1032},
    {"ville": "Al Hoceima",      "lat": 35.2517, "lon": -3.9372},
    {"ville": "Essaouira",       "lat": 31.5085, "lon": -9.7595},
    {"ville": "Ifrane",          "lat": 33.5228, "lon": -5.1109},
    {"ville": "Chefchaouen",     "lat": 35.1688, "lon": -5.2636},
    {"ville": "Midelt",          "lat": 32.6802, "lon": -4.7340},
    {"ville": "Azrou",           "lat": 33.4344, "lon": -5.2218},
    {"ville": "Tiznit",          "lat": 29.6974, "lon": -9.8022},
    {"ville": "Taroudant",       "lat": 30.4727, "lon": -8.8748},
    {"ville": "Sidi Kacem",      "lat": 34.2260, "lon": -5.7136},
    {"ville": "Sidi Slimane",    "lat": 34.2622, "lon": -5.9298},
    {"ville": "Youssoufia",      "lat": 32.2499, "lon": -8.5298},
    {"ville": "Benguerir",       "lat": 32.2328, "lon": -7.9534},
    {"ville": "Skhirat",         "lat": 33.8533, "lon": -7.0328},
    {"ville": "Témara",          "lat": 33.9288, "lon": -6.9122},
    {"ville": "Salé",            "lat": 34.0531, "lon": -6.7986},
    {"ville": "Inezgane",        "lat": 30.3553, "lon": -9.5370},
    {"ville": "Aït Melloul",     "lat": 30.3340, "lon": -9.4970},
    {"ville": "Dakhla",          "lat": 23.7148, "lon": -15.9570},
    {"ville": "Laâyoune",        "lat": 27.1253, "lon": -13.1625},
    {"ville": "Fnideq",          "lat": 35.8504, "lon": -5.3578},
    {"ville": "Berkane",         "lat": 34.9200, "lon": -2.3200},
    {"ville": "Taourirt",        "lat": 34.4100, "lon": -2.8900},
    {"ville": "Bouarfa",         "lat": 32.5300, "lon": -1.9500},
    {"ville": "Figuig",          "lat": 32.1141, "lon": -1.2296},
    {"ville": "Zagora",          "lat": 30.3280, "lon": -5.8383},
]

# Noms d'entrepôts réalistes pour le Maroc
NOMS_ENTREPOTS = [
    "Hub Casablanca Nord",     "Hub Casablanca Sud",     "Zone Ain Sebaa",
    "Plateforme Tanger Med",   "Entrepôt Tanger Free Zone", "Zone Tanger Automotive",
    "Hub Rabat Technopolis",   "Entrepôt Rabat Salé",    "Zone Kénitra Atlantic",
    "Plateforme Marrakech",    "Entrepôt Marrakech Tassiltante", "Zone Safi Industrielle",
    "Hub Fès Saïss",           "Entrepôt Meknès Agropolis", "Zone Oujda Technopole",
    "Plateforme Agadir Haliopolis", "Entrepôt Agadir Souss", "Zone Agadir Ait Melloul",
    "Hub Béni Mellal",         "Entrepôt El Jadida Jorf", "Zone Nador West Med",
    "Plateforme Settat",       "Entrepôt Berrechid",      "Zone Mohammedia",
    "Hub Khouribga",           "Entrepôt Laâyoune",       "Zone Dakhla Pêche",
    "Plateforme Ouarzazate Solar", "Entrepôt Errachidia",  "Zone Guelmim",
    "Hub Tétouan",             "Entrepôt Larache",        "Zone Sidi Kacem",
    "Plateforme Essaouira",    "Entrepôt Midelt",         "Zone Ifrane Logistique",
    "Hub Taza",                "Entrepôt Taroudant",      "Zone Tiznit",
    "Plateforme Benguerir UM6P", "Entrepôt Youssoufia",
]

TYPES_STOCKAGE = ["froid", "sec", "mixte"]

# ══════════════════════════════════════════════════════════════════════════════
#  1. DEMANDES CLIENTS — 1000 lignes
#     Colonnes : ville, lat, lon, demande, tarif_transport
# ══════════════════════════════════════════════════════════════════════════════

print("📦 Génération de demandes_clients_test_1.csv ...")

rows_demandes = []
for i in range(1000):
    ville_info = random.choice(VILLES_MAROC)
    # Ajouter un léger bruit aux coordonnées pour simuler différents points
    lat = round(ville_info["lat"] + np.random.uniform(-0.08, 0.08), 4)
    lon = round(ville_info["lon"] + np.random.uniform(-0.08, 0.08), 4)
    # Demande réaliste entre 50 et 5000 unités
    demande = int(np.random.lognormal(mean=6.5, sigma=0.8))
    demande = min(max(demande, 50), 8000)
    # Tarif transport en MAD/km (entre 0.8 et 3.5)
    tarif = round(np.random.uniform(0.8, 3.5), 2)
    rows_demandes.append({
        "ville": ville_info["ville"],
        "lat": lat,
        "lon": lon,
        "demande": demande,
        "tarif_transport": tarif,
    })

df_demandes = pd.DataFrame(rows_demandes)
df_demandes.to_csv(os.path.join(OUTPUT_DIR, "demandes_clients_test_1.csv"), index=False, encoding="utf-8-sig")
print(f"   ✅ {len(df_demandes)} lignes générées.")


# ══════════════════════════════════════════════════════════════════════════════
#  2. CATALOGUE ENTREPÔTS — 1000 lignes
#     Colonnes : nom, lat, lon, type_stockage, volume
# ══════════════════════════════════════════════════════════════════════════════

print("🏭 Génération de entrepots_test_1.csv ...")

rows_entrepots = []
used_names = set()

for i in range(1000):
    ville_info = random.choice(VILLES_MAROC)
    # Créer un nom unique pour chaque entrepôt
    base_name = random.choice(NOMS_ENTREPOTS)
    unique_name = f"{base_name} #{i+1:04d}"
    
    lat = round(ville_info["lat"] + np.random.uniform(-0.05, 0.05), 4)
    lon = round(ville_info["lon"] + np.random.uniform(-0.05, 0.05), 4)
    type_stockage = random.choice(TYPES_STOCKAGE)
    # Volume en m³ (entre 500 et 50000)
    volume = int(np.random.lognormal(mean=8.5, sigma=0.7))
    volume = min(max(volume, 500), 60000)
    
    rows_entrepots.append({
        "nom": unique_name,
        "lat": lat,
        "lon": lon,
        "type_stockage": type_stockage,
        "volume": volume,
    })

df_entrepots = pd.DataFrame(rows_entrepots)
df_entrepots.to_csv(os.path.join(OUTPUT_DIR, "entrepots_test_1.csv"), index=False, encoding="utf-8-sig")
print(f"   ✅ {len(df_entrepots)} lignes générées.")


# ══════════════════════════════════════════════════════════════════════════════
#  3. HISTORIQUE IoT — ~50 000 lignes (50 relevés × 1000 entrepôts)
#     Colonnes : nom_entrepot, date, temperature, humidite
#     Chaque entrepôt du catalogue reçoit 50 mesures capteurs sur l'année 2025
# ══════════════════════════════════════════════════════════════════════════════

print("🌡️  Génération de historique_iot_test_1.csv ...")

# Générer des données IoT pour TOUS les entrepôts du catalogue
entrepots_iot = df_entrepots["nom"].unique()

rows_iot = []
dates_range = pd.date_range("2025-01-01", "2025-12-31 23:00:00", freq="6h")

for ent_nom in entrepots_iot:
    # Déterminer le type de cet entrepôt pour ajuster les températures
    ent_row = df_entrepots[df_entrepots["nom"] == ent_nom].iloc[0]
    type_stock = ent_row["type_stockage"]
    
    # Paramètres de température selon le type
    if type_stock == "froid":
        temp_base, temp_noise = 4.0, 1.2
        hum_base, hum_noise = 82.0, 4.0
    elif type_stock == "sec":
        temp_base, temp_noise = 22.0, 3.5
        hum_base, hum_noise = 45.0, 8.0
    else:  # mixte
        temp_base, temp_noise = 12.0, 3.0
        hum_base, hum_noise = 60.0, 6.0
    
    # 50 relevés par entrepôt
    sample_dates = np.random.choice(dates_range, size=50, replace=False)
    sample_dates = sorted(sample_dates)
    
    for dt in sample_dates:
        dt = pd.Timestamp(dt)
        # Effet saisonnier
        jour = dt.dayofyear
        saison = -np.cos(2 * np.pi * (jour - 20) / 365.25) * 2.5
        
        temp = round(temp_base + saison + np.random.normal(0, temp_noise), 2)
        hum = round(hum_base + np.random.normal(0, hum_noise), 2)
        hum = max(0, min(100, hum))
        
        # Injection rare d'anomalies (pannes)
        if random.random() < 0.005:
            temp += round(np.random.uniform(5, 12), 2)
        
        rows_iot.append({
            "nom_entrepot": ent_nom,
            "date": dt.strftime("%Y-%m-%d %H:%M:%S"),
            "temperature": temp,
            "humidite": hum,
        })

df_iot = pd.DataFrame(rows_iot)
df_iot.to_csv(os.path.join(OUTPUT_DIR, "historique_iot_test_1.csv"), index=False, encoding="utf-8-sig")
print(f"   ✅ {len(df_iot)} lignes générées ({len(entrepots_iot)} entrepôts × 50 relevés).")


# ══════════════════════════════════════════════════════════════════════════════
#  4. TRAJETS CLIENTS — 1000 lignes
#     Colonnes : client_id, lat, lon, type_requis
# ══════════════════════════════════════════════════════════════════════════════

print("🚚 Génération de trajets_clients_test_1.csv ...")

rows_trajets = []
for i in range(1000):
    ville_info = random.choice(VILLES_MAROC)
    lat = round(ville_info["lat"] + np.random.uniform(-0.1, 0.1), 4)
    lon = round(ville_info["lon"] + np.random.uniform(-0.1, 0.1), 4)
    type_requis = random.choice(["froid", "sec", "mixte"])
    
    rows_trajets.append({
        "client_id": f"C{i+1:04d}",
        "lat": lat,
        "lon": lon,
        "type_requis": type_requis,
    })

df_trajets = pd.DataFrame(rows_trajets)
df_trajets.to_csv(os.path.join(OUTPUT_DIR, "trajets_clients_test_1.csv"), index=False, encoding="utf-8-sig")
print(f"   ✅ {len(df_trajets)} lignes générées.")


# ══════════════════════════════════════════════════════════════════════════════
#  5. CLIENTS MAROC (Centre de Gravité) — 1000 lignes
#     Colonnes : ville, lat, lon, volume
# ══════════════════════════════════════════════════════════════════════════════

print("📍 Génération de clients_maroc_test_1.csv ...")

rows_clients = []
for i in range(1000):
    ville_info = random.choice(VILLES_MAROC)
    lat = round(ville_info["lat"] + np.random.uniform(-0.06, 0.06), 4)
    lon = round(ville_info["lon"] + np.random.uniform(-0.06, 0.06), 4)
    volume = int(np.random.lognormal(mean=6.2, sigma=0.9))
    volume = min(max(volume, 20), 10000)
    
    rows_clients.append({
        "ville": ville_info["ville"],
        "lat": lat,
        "lon": lon,
        "volume": volume,
    })

df_clients = pd.DataFrame(rows_clients)
df_clients.to_csv(os.path.join(OUTPUT_DIR, "clients_maroc_test_1.csv"), index=False, encoding="utf-8-sig")
print(f"   ✅ {len(df_clients)} lignes générées.")


# ══════════════════════════════════════════════════════════════════════════════
#  RÉSUMÉ FINAL
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 65)
print("  ✅ GÉNÉRATION TERMINÉE — Tous les fichiers de test sont prêts !")
print("=" * 65)
print(f"\n  📂 Répertoire de sortie : {OUTPUT_DIR}\n")
print(f"  📄 demandes_clients_test_1.csv   → {len(df_demandes):>5} lignes")
print(f"  📄 entrepots_test_1.csv          → {len(df_entrepots):>5} lignes")
print(f"  📄 historique_iot_test_1.csv      → {len(df_iot):>5} lignes")
print(f"  📄 trajets_clients_test_1.csv    → {len(df_trajets):>5} lignes")
print(f"  📄 clients_maroc_test_1.csv      → {len(df_clients):>5} lignes")
print(f"\n  Total : {len(df_demandes) + len(df_entrepots) + len(df_iot) + len(df_trajets) + len(df_clients)} lignes de données")
print("=" * 65)
