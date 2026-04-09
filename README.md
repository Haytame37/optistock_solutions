# 🏭 OptiStock Solutions (Phases 3 & 4)

> **Système IA et IoT d'Aide à la Décision (SAD) pour la Logistique d'Entrepôts.**

Projet réalisé dans le cadre du module **Apprentissage Par Projet**  
Filière : **Transformation Digitale Industrielle (TDI)**  
Université Sultan Moulay Slimane — ENSA Béni Mellal | Année 2025/2026  
Encadré par : **Pr. Hamza Touil**

---

## 👥 Équipe

| Nom               | Rôle                        |
| ----------------- | --------------------------- |
| **Rafiki Najat**      |  |
| **Atmane Salah**      |  |
| **ElAtraoui Haytame** |  |

---

## 📌 Description du Projet

OptiStock Solutions est une plateforme avancée destinée aux acteurs de la chaîne de distribution logistique (Supply Chain) et aux propriétaires de foncier industriel. 
Le but du système est d'évaluer de façon **rigoureuse et mathématique** la viabilité d'un site logistique pour des marchandises sous normes (Normes HACCP, Chaîne du Froid).

L’application propose une approche holistique (Macro et Micro) assistée par ordinateur afin de :
1. **Géolocaliser** l'entrepôt le plus pertinent vis-à-vis d'un centre de gravité client.
2. **Auditer thermiquement** le stockage via un traitement du signal IoT complexe (multi-capteurs).
3. **Scorer & Classer** les entrepôts à travers une fonction d'utilité (Méthode SAW).
4. **Verrouiller de façon concurrente** (Pessimistic Lock) la transaction financière.

---

## ⚙️ Implémentations et Modèles Mathématiques

L'application suit une architecture scientifique en 3 couches de décision :

### 1. Axe Logistique & Géospatial (Macro-localisation)
- Application de la **théorie de Weber / Centre de Gravité** pour localiser théoriquement une implantation idéale.
- Calcul matriciel des **Distances de Haversine** pour tous les points de livraison.

### 2. Axiome Environnemental IoT & Traitement du Signal (Micro-Gestion)
- **Interpolation Linéaire** : reconstruction des données (`NaN`) suite aux pannes matérielles.
- **Filtre de Lissage (Moyenne Mobile)** : atténuation du bruit électronique ou des variations brusques sur une fenêtre de 3 heures.
- **Redondance Multi-capteurs** : Agrégation de la moyenne de 3 capteurs pour obtenir un consensus "fiable".
- **Segmentation Saisonnière** : L'algorithme classifie la conformité (✅ Conforme, ⚠️ Vigilance, 🔴 Hors-norme) mois par mois en l'adaptant aux normes thermodynamiques des saisons.

### 3. Le Moteur de Scoring SAW (Simple Additive Weighting)
Afin de ne pas mélanger des bananes et des kilomètres, le système applique un filtre de conversion :
1. **Normalisation ciblée :** La distance est injectée via son inverse ($1 / d$), ainsi une proximité géographique forte garantit un score élevé (entre $0.0$ et $1.0$).
2. **Pondération 60 / 40 :**
   $$Score = (0.60 \times Logistique) + (0.40 \times Environnement)$$
   La logistique pèse 60% car un site mal placé détruit le bilan carbone, tandis qu'un environnement sous-noté (40%) est contournable par des investissements (climatisation, aménagement).
3. **Moteur IA :** Le résultat final n'est pas un nombre muet. Le système génère automatiquement un diagnostic textuel et lève des **alertes environnementales saisonnières**.

### 4. Transactions et Sécurité : System_Pre_Lock
Afin d'éviter tout conflit de réservation, une fois le contrat en cours de montage sur l'application, OptiStock exécute un `System_Pre_Lock`.
- Placement temporaire de l'entrepôt à un statut **LOCK**.
- **Timelock de 15 minutes** (Verrouillage pessimiste en mémoire). 
- **Lazy Cleanup** : Expiration en arrière-plan sans perturber le main thread du serveur.

---

## 🛠️ Stack Technique

| Composant             | Technologie     | Modélisation / Rôle                 |
| --------------------- | --------------- | ----------------------------------- |
| Interface / Frond-End | **Streamlit**       | Application Web réactive Mono-Page  |
| Data Science Core     | **Python / Pandas** / Numpy | Algorithmes, Interpolation, SAW |
| Graphiques Dynamiques | **Plotly**          | Cadrage zones d'alertes HACCP       |
| Cartographie          | **Folium**          | Isométries & Clusters (Weiszfeld)   |
| Base de données       | **SQLite**          | Stockage relationnel et dictionnaire|

---

## 📁 Structure Synthétique (Refactoring V4)

```
optistock_solutions/
├── app.py                          # Point d'entrée & Routeur Streamlit
├── TECHNICAL_DOC.md                # Justifications algorithmiques (Pr. Touil)
├── README.md                       # Présentation globale
│
├── core/                           # Intelligence du système (SAD)
│   ├── logistique.py               # Gravité géospatiale & Haversine
│   ├── iot_analysis.py             # Traitement signal, multi-capteurs, anomalies
│   └── scoring.py                  # SAW, Min-Max (1/d), IA Textuelle
│
├── models/                         # Structures de données applicatives
│   └── reservation.py              # Logique d'état System_Pre_Lock
│
├── utils/                          # Composants transverses
│   ├── constants.py                # Variables de pondérations mondiales
│   └── db.py                       # Accesseurs SQLite
│
└── data/                           # Datalake IoT brut et propre
    ├── cleaned/                    # Export DataFrame finalisés
    └── samples/                    # CSV Démo
```

---

## 🚀 Installation & Déploiement

### 1. Clonage
```bash
git clone https://github.com/Haytame37/optistock_solutions.git
cd optistock_solutions
```

### 2. Environnement Virtuel
```bash
python -m venv venv
# Windows :
venv\Scripts\activate
```

### 3. Dépendances
```bash
pip install -r requirements.txt
```

### 4. Lancer l'application
Le projet repose désormais sur un dashboard principal gérant de bout en bout l'expérience (Routeur interne).
```bash
streamlit run app.py
```
> Le serveur local Streamlit se lancera généralement sur `http://localhost:8501`.

---

## 📊 Format des Datasets IoT

Pour assurer le bon fonctionnement du **consensus Multi-Capteurs**, les historiques CSV doivent contenir la variable temporelle et au minimum les flux de 3 capteurs distincts (tolérance aux NaN).

**Exemple de structure recommandée (`temperature_ENT001.csv`) :**
```csv
datetime,capteur1,capteur2,capteur3
2024-01-01 08:00:00,18.5,18.6,18.4
2024-01-01 09:00:00,19.1,NaN,19.0
```

---

## 📝 Licence

Projet académique PFA — ENSA Béni Mellal © 2025/2026.  
Tous droits réservés. Destiné à des fins de jury académique et d'audit.
