"""
utils/product_conditions.py
═══════════════════════════════════════════════════════════════════════════════
Dictionnaire centralisant les conditions de conservation des produits.
Inclus : Cible MIN/MAX, Marges de tolérance et Temps de résistance avant altération.
Les temps sont exprimés en heures pour faciliter les calculs avec les historiques.
═══════════════════════════════════════════════════════════════════════════════
"""

# Temps de résistance exprimés en heures. Longue durée = valeur élevée arbitraire (ex: 1000h)
PRODUCT_CONDITIONS = {
    "Tomates": {
        "temperature": {
            "min": 10.0,
            "max": 15.0,
            "marge_bas": -2.0,  # Seuil critique < 8.0
            "marge_haut": 3.0,  # Seuil critique > 18.0
            "temps_resistance_bas_h": 4.0,   # 2 à 4 heures
            "temps_resistance_haut_h": 24.0  # 12 à 24 heures
        },
        "humidite": {
            "min": 85.0,
            "max": 90.0,
            "marge_bas": -5.0,  # Seuil critique < 80.0
            "marge_haut": 5.0,  # Seuil critique > 95.0
            "temps_resistance_bas_h": 120.0, # 3 à 5 jours
            "temps_resistance_haut_h": 72.0  # 48 à 72 heures
        }
    },
    "Produits Laitiers": {
        "temperature": {
            "min": 2.0,
            "max": 6.0,
            "marge_bas": -1.0,  # Seuil critique < 1.0
            "marge_haut": 2.0,  # Seuil critique > 8.0
            "temps_resistance_bas_h": 2.0,   # 1 à 2 heures
            "temps_resistance_haut_h": 2.0   # 30 min à 2 heures
        },
        "humidite": {
            "min": 65.0,
            "max": 80.0,
            "marge_bas": -5.0,  # Seuil critique < 60.0
            "marge_haut": 5.0,  # Seuil critique > 85.0
            "temps_resistance_bas_h": 504.0, # Plusieurs semaines (3 semaines = 504h)
            "temps_resistance_haut_h": 168.0 # 5 à 7 jours (168h)
        }
    },
    "Parapharmacie": {
        "temperature": {
            "min": 15.0,
            "max": 25.0,
            "marge_bas": -10.0, # Seuil critique < 5.0
            "marge_haut": 2.0,  # Seuil critique > 27.0
            "temps_resistance_bas_h": 72.0,  # 2 à 3 jours (72h)
            "temps_resistance_haut_h": 48.0  # 24 à 48 heures
        },
        "humidite": {
            "min": 40.0,
            "max": 60.0,
            "marge_bas": -10.0, # Seuil critique < 30.0
            "marge_haut": 5.0,  # Seuil critique > 65.0
            "temps_resistance_bas_h": 1000.0,# Longue durée
            "temps_resistance_haut_h": 240.0 # 5 à 10 jours (240h)
        }
    },
    "Composants Électroniques": {
        "temperature": {
            "min": 15.0,
            "max": 30.0,
            "marge_bas": -10.0, # Seuil critique < 5.0
            "marge_haut": 10.0, # Seuil critique > 40.0
            "temps_resistance_bas_h": 1000.0,# Longue durée
            "temps_resistance_haut_h": 2000.0# Plusieurs mois
        },
        "humidite": {
            "min": 1.0,
            "max": 10.0,
            "marge_bas": -0.0,  # Seuil critique < 1.0
            "marge_haut": 0.0,  # Seuil critique > 10.0
            "temps_resistance_bas_h": 1000.0,# Longue durée (Parfaite conservation)
            "temps_resistance_haut_h": 24.0  # 12 à 24 heures (Nécessite passage au four)
        }
    }
}
