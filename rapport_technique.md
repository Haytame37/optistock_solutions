# Rapport Technique — OptiStock Solutions
## Système d'Aide à la Décision Logistique

---

## 1. Introduction

OptiStock Solutions est une plateforme d'aide à la décision logistique développée pour optimiser le réseau
de distribution au Maroc. L'application combine des modèles mathématiques classiques de la Recherche Opérationnelle
avec des données IoT temps réel pour fournir des recommandations quantitatives sur :
- **L'affectation optimale** des clients aux entrepôts existants (Module 1)
- **L'implantation optimale** de nouveaux entrepôts (Module 2)

---

## 2. Formules Mathématiques

### 2.1 Distance Haversine

La distance entre deux points sur la surface terrestre est calculée via la formule de Haversine,
qui tient compte de la courbure de la Terre.

**Formule :**

```
a = sin²(Δφ/2) + cos(φ₁) × cos(φ₂) × sin²(Δλ/2)

c = 2 × atan2(√a, √(1−a))

d = R × c
```

Où :
- `φ₁, φ₂` : latitudes des deux points (en radians)
- `λ₁, λ₂` : longitudes des deux points (en radians)
- `Δφ = φ₂ − φ₁`, `Δλ = λ₂ − λ₁`
- `R = 6 371 km` (rayon moyen de la Terre)
- `d` : distance en kilomètres

**Référence :** Sinnott, R.W. (1984). *Virtues of the Haversine*. Sky and Telescope, 68(2), 158.

---

### 2.2 Modèle de Gravité Itératif (Weber-Weiszfeld)

L'emplacement optimal d'un entrepôt est calculé en minimisant le coût total de transport
pondéré via l'algorithme itératif de Weiszfeld (1937), solution du problème de Weber (1909).

**Fonction objectif :**

```
min CT = Σᵢ (tᵢ × dᵢ × dist(P, Pᵢ))
```

Où :
- `CT` : coût total de transport (en Dhs)
- `tᵢ` : tarif de transport du point i (Dhs/unité/km)
- `dᵢ` : volume de demande du point i
- `P` : coordonnées (lat, lon) du point cherché
- `Pᵢ` : coordonnées du point de demande i

**Mise à jour itérative (Weiszfeld) :**

```
         Σᵢ (wᵢ × xᵢ / distᵢ)
x(n+1) = ─────────────────────────
           Σᵢ (wᵢ / distᵢ)
```

Avec : `wᵢ = tᵢ × dᵢ` (poids combiné tarif × demande)

**Relaxation :** Pour stabiliser la convergence :
```
x(n+1) = α × x_new + (1 − α) × x(n)    avec α = 0.8
```

**Critère d'arrêt :** `|x(n+1) − x(n)| < 10⁻⁶` ou `max_iter = 200`

**Références :**
- Weber, A. (1909). *Über den Standort der Industrien*. Tübingen.
- Weiszfeld, E. (1937). *Sur le point pour lequel la somme des distances de n points donnés est minimum*.
  Tohoku Mathematical Journal, 43, 355-386.
- Kuhn, H.W. & Kuenne, R.E. (1962). *An efficient algorithm for the numerical solution of the generalized
  Weber problem in spatial economics*. Journal of Regional Science, 4(2), 21-33.

---

### 2.3 Clustering K-Means Géographique

Pour l'implantation multiple (N entrepôts), les clients sont partitionnés en N zones
via un K-Means géographique pondéré.

**Algorithme :**
1. **Initialisation (K-Means++)** : Sélectionner le premier centre aléatoirement, puis chaque centre suivant
   avec probabilité proportionnelle à `dist² × demande`.
2. **Affectation** : Chaque client est affecté au centre le plus proche (distance Haversine).
3. **Mise à jour** : Chaque centre est recalculé comme le barycentre pondéré de son cluster.
4. **Convergence** : Répéter 2-3 jusqu'à stabilisation des affectations.

Après le clustering, un problème de Weber est résolu **indépendamment** dans chaque zone.

**Référence :** Arthur, D. & Vassilvitskii, S. (2007). *K-Means++: The Advantages of Careful Seeding*.
SODA '07: Proceedings of the 18th Annual ACM-SIAM Symposium on Discrete Algorithms, 1027-1035.

---

### 2.4 Score de Proximité (Distance)

Le score de distance suit une décroissance exponentielle douce :

```
S_dist = 100 × exp(−d / d_ref)
```

- `d` : distance en km entre le client et l'entrepôt
- `d_ref = 1500 km` (correspondant au corridor Tanger–Dakhla)
- `S_dist ∈ [0, 100]` : aucun entrepôt n'est brutalement éliminé

| Distance | Score |
|----------|-------|
| 0 km     | 100   |
| 100 km   | 93.6  |
| 500 km   | 71.7  |
| 1000 km  | 51.3  |
| 1500 km  | 36.8  |

---

### 2.5 Score de Conformité IoT (Température & Humidité)

Le score combine deux composantes :

```
S_IoT = 0.6 × Taux_Conformité + 0.4 × Score_Proximité_Idéale
```

**Taux de conformité :** Pourcentage de relevés dans la plage acceptable
```
Taux = (nb_relevés_dans_plage / nb_total_relevés) × 100
```

**Proximité à l'idéale :** Score proportionnel à l'écart avec la valeur idéale
```
Si dans [min, max] : S = 100 − (|val − idéale| / amplitude) × 50    → S ∈ [50, 100]
Si hors plage      : S = max(0, 50 − écart × K)                     → S ∈ [0, 50]
```

Avec K = 5 pour la température, K = 2 pour l'humidité.

**Seuils par type de stockage (Normes HACCP / GDP) :**

| Type   | Temp Min | Temp Max | Temp Idéale | Hum Min | Hum Max | Hum Idéale |
|--------|----------|----------|-------------|---------|---------|------------|
| Froid  | 2°C      | 8°C      | 4°C         | 65%     | 95%     | 80%        |
| Sec    | 15°C     | 30°C     | 22°C        | 30%     | 60%     | 45%        |
| Mixte  | 5°C      | 25°C     | 15°C        | 40%     | 80%     | 60%        |

**Référence :** European Commission. (2013). *Guidelines on Good Distribution Practice of Medicinal Products
for Human Use (2013/C 343/01)*. Official Journal of the European Union.

---

### 2.6 Score Global Pondéré

Le score final combine les trois dimensions avec normalisation :

```
S_global = w₁ × S_dist + w₂ × S_temp + w₃ × S_hum
```

Où : `Σwᵢ = 1` (normalisation automatique si la somme des curseurs ≠ 100%)

**Coefficient de compatibilité type :**
```
Si type_entrepôt == type_requis → × 1.0  (Exact)
Si type_entrepôt == "mixte"    → × 0.85 (Polyvalent, −15%)
Si type_requis == "mixte"      → × 0.90 (Sur-qualifié, −10%)
Sinon                          → × 0.0  (Incompatible)
```

---

## 3. Outils et Technologies

### 3.1 Stack Technique

| Composant        | Technologie      | Version  | Rôle                                      |
|------------------|------------------|----------|--------------------------------------------|
| **Frontend**     | Streamlit        | ≥ 1.30   | Interface web interactive                  |
| **Cartographie** | Folium           | ≥ 0.15   | Cartes Leaflet interactives                |
|                  | streamlit-folium | ≥ 0.15   | Intégration Folium ↔ Streamlit             |
| **Backend**      | Python           | ≥ 3.10   | Logique métier                             |
|                  | Pandas           | ≥ 2.0    | Manipulation de données tabulaires         |
|                  | NumPy            | ≥ 1.24   | Calcul vectorisé (Haversine, K-Means)      |
| **Base de données** | SQLite        | 3.x      | Stockage utilisateurs et sessions          |

### 3.2 Architecture de l'Application

```
optistock_solutions/
├── app.py                           # Point d'entrée Streamlit
├── .streamlit/config.toml           # Thème et configuration
├── core/
│   ├── logistique.py                # Algorithmes : Haversine, Weber, K-Means, Scoring
│   ├── carte.py                     # Visualisation Folium (cartes)
│   └── auth.py                      # Authentification et rôles
├── pages/
│   ├── 1_Login.py                   # Page de connexion
│   ├── 2_Dashboard_Admin.py         # Administration
│   ├── 3_Interface_Chercheur.py     # Module 1 + Module 2 (Chercheur)
│   └── 4_Interface_Proprietaire.py  # Vue Propriétaire
├── data/
│   └── samples/                     # Fichiers CSV de test
│       ├── entrepots_test_1.csv     # 15 entrepôts marocains
│       ├── trajets_clients_test_1.csv # 200 clients
│       ├── historique_iot_test_1.csv  # Relevés IoT (1350 lignes)
│       └── demandes_clients_test_1.csv # 200 points de demande
└── rapport_technique.md             # Ce document
```

### 3.3 Flux de Données

```
CSV Upload → Pandas DataFrame → Validation Colonnes
                                      ↓
                             Clustering K-Means
                                      ↓
                        ┌─── Zone 1 ──┴── Zone N ───┐
                        ↓                            ↓
                  Weber/Weiszfeld             Weber/Weiszfeld
                        ↓                            ↓
                  Scoring IoT                  Scoring IoT
                        ↓                            ↓
                  Recommandations             Recommandations
                        ↓                            ↓
                        └──── Folium Map ────────────┘
                                      ↓
                              Streamlit UI
```

---

## 4. Limites et Perspectives

### 4.1 Limites Actuelles
- **Distances** : La formule de Haversine calcule des distances "à vol d'oiseau". Les distances routières réelles
  sont en moyenne 20-40% supérieures.
- **K-Means** : L'algorithme peut converger vers un optimum local. L'initialisation K-Means++ réduit ce risque
  mais ne le supprime pas.
- **Données IoT** : L'analyse utilise la moyenne des relevés, ce qui lisse les écarts ponctuels critiques.

### 4.2 Améliorations Futures
- **Routing API** : Intégration OSRM ou Google Directions pour les distances routières réelles.
- **Contraintes de capacité** : Intégrer la capacité volumétrique des entrepôts comme contrainte dure.
- **Analyse temporelle IoT** : Exploitation de la dimension temporelle pour détecter les tendances de dérive.
- **Optimisation multi-objectif** : Algorithme NSGA-II pour optimiser simultanément coût, temps et conformité.

---

## 5. Références Bibliographiques

1. **Sinnott, R.W.** (1984). Virtues of the Haversine. *Sky and Telescope*, 68(2), 158.
2. **Weber, A.** (1909). *Über den Standort der Industrien*. Tübingen: J.C.B. Mohr.
3. **Weiszfeld, E.** (1937). Sur le point pour lequel la somme des distances de n points donnés est minimum.
   *Tohoku Mathematical Journal*, 43, 355-386.
4. **Kuhn, H.W. & Kuenne, R.E.** (1962). An efficient algorithm for the numerical solution of the generalized
   Weber problem in spatial economics. *Journal of Regional Science*, 4(2), 21-33.
5. **Arthur, D. & Vassilvitskii, S.** (2007). K-Means++: The Advantages of Careful Seeding. *SODA '07*.
6. **European Commission** (2013). Guidelines on Good Distribution Practice (2013/C 343/01).
7. **HACCP** — Hazard Analysis and Critical Control Points. Codex Alimentarius Commission (FAO/WHO).

---

*Document généré automatiquement par OptiStock Solutions — Mars 2025*
