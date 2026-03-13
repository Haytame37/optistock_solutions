# 🏭 OptiStock Solutions

> Système IoT-Cloud d'aide à la décision pour la gestion optimale des centres de stockage logistique.

Projet réalisé dans le cadre du module **Apprentissage Par Projet**  
Filière : **Transformation Digitale Industrielle (TDI)**  
Université Sultan Moulay Slimane — ENSA Béni Mellal | Année 2025/2026  
Encadré par : **Pr. Hamza Touil**

---

## 👥 Équipe

| Nom               | Rôle                        |
| ----------------- | --------------------------- |
| Rafiki Najat      | Module 1&2 |
| Atmane Salah      | Module 1&2          |
| ElAtraoui Haytame | Module 1&2    |

---

## 📌 Description du Projet

OptiStock Solutions est une application web interactive qui aide les entreprises à :

- **Trouver l'entrepôt idéal** en fonction de leurs points de livraison (Macro-localisation)
- **Valider les conditions environnementales** d'un entrepôt via l'historique des capteurs IoT (température, humidité)
- **Scorer et comparer** les entrepôts disponibles grâce à un système de pondération personnalisable

L'application met en relation deux types d'utilisateurs :

- 🔍 **Clients Chercheurs** : entreprises à la recherche d'un entrepôt adapté
- 🏢 **Clients Propriétaires** : gestionnaires d'entrepôts souhaitant les proposer sur la plateforme

---

## ⚙️ Fonctionnalités principales

### Axe 1 — Macro-Localisation (Optimisation géographique)

- Calcul du **point optimal théorique** via l'algorithme du Centre de Gravité
- **Recommandation d'entrepôts existants** classés par score logistique pondéré
- Affichage sur **carte interactive** (Folium)

### Axe 2 — Micro-Gestion (Validation environnementale)

- **Analyse des données IoT** (température, humidité) sur les 6 derniers mois
- **Détection automatique d'anomalies** et périodes de non-conformité
- **Score environnemental** basé sur le taux de conformité aux exigences client

### Système de Scoring

- Formule : **S = Σ(Ci × Wi)** — somme pondérée des critères
- Curseurs interactifs pour que l'utilisateur ajuste les poids selon ses priorités
- Score final sur 100 combinant logistique + environnemental

---

## 🛠️ Stack Technique

| Composant             | Technologie     | Rôle                                |
| --------------------- | --------------- | ----------------------------------- |
| Interface (Dashboard) | Streamlit       | Front-end interactif                |
| Moteur de calcul      | Python + Pandas | Logique métier & algorithmes        |
| Base de données       | SQLite          | Stockage entrepôts & historique IoT |
| Cartographie          | Folium          | Cartes interactives                 |
| Graphiques            | Plotly          | Visualisation capteurs & scores     |
| Hashage mots de passe | bcrypt          | Sécurité authentification           |

---

## 📁 Structure du Projet

```
optistock_solutions/
├── app.py                          # Point d'entrée principal
├── requirements.txt                # Dépendances Python
├── .env                            # Variables d'environnement
├── README.md                       # Ce fichier
│
├── database/
│   ├── optistock.db                # Base SQLite (auto-générée)
│   ├── init_db.py                  # Création des tables
│   └── seed_data.py                # Données de démonstration
│
├── data/
│   ├── entrepots_catalogue.csv     # Catalogue initial entrepôts
│   └── samples/
│       └── capteurs_exemple.csv    # Modèle CSV IoT importable
│
├── core/                           # Moteur de décision (Back-end)
│   ├── logistique.py               # Centre de Gravité + distances
│   ├── iot_analysis.py             # Analyse capteurs + anomalies
│   ├── scoring.py                  # Calcul S = Σ(Ci × Wi)
│   └── auth.py                     # Authentification & rôles
│
├── models/                         # Accès base de données
│   ├── entrepot.py
│   ├── utilisateur.py
│   ├── capteur.py
│   └── reservation.py
│
├── pages/                          # Pages Streamlit
│   ├── 1_Login.py
│   ├── 2_Dashboard_Admin.py
│   ├── 3_Interface_Chercheur.py
│   └── 4_Interface_Proprietaire.py
│
├── components/                     # Composants UI réutilisables
│   ├── carte.py
│   ├── graphiques.py
│   ├── kpi_cards.py
│   └── sidebar.py
│
├── utils/
│   ├── validation.py
│   ├── notifications.py
│   └── helpers.py
│
└── tests/
    ├── test_logistique.py
    ├── test_scoring.py
    └── test_iot_analysis.py
```

---

## 🚀 Installation & Lancement

### 1. Cloner le projet

```bash
git clone https://github.com/votre-repo/optistock-solutions.git
cd optistock-solutions
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configurer les variables d'environnement

```bash
cp .env.example .env
# Éditer .env avec vos paramètres si nécessaire
```

### 5. Lancer l'application

```bash
streamlit run app.py
```

L'application s'ouvre automatiquement sur `http://localhost:8501`

---

---

## 📊 Format CSV capteurs IoT

Les propriétaires doivent importer un fichier CSV respectant ce format :

```csv
date,temperature,humidite
2024-01-01 08:00:00,18.5,55.2
2024-01-01 09:00:00,19.1,54.8
2024-01-01 10:00:00,20.3,56.1
```

> Un fichier exemple est disponible dans `data/samples/capteurs_exemple.csv`

---

## 🧮 Formule de Scoring

```
Score Global = (Score_Logistique × W_log) + (Score_Environnemental × W_env)

Score_Logistique     = f(distance, capacité, type_stockage)
Score_Environnemental = f(taux_conformité_température, taux_conformité_humidité)

W_log + W_env = 1.0   (ajustables via les curseurs de l'interface)
```

---

## 🗺️ Flux de navigation

```
[Login]
   ├── Admin       → Dashboard Admin (gestion utilisateurs & statistiques)
   ├── Chercheur   → Saisie besoins → Analyse → Carte + Scores → Réservation
   └── Propriétaire → Formulaire entrepôt → Import CSV IoT → Mise en ligne
```

---

## 📝 Licence

Projet académique — ENSA Béni Mellal © 2025/2026  
Tous droits réservés au Groupe OptiStockSolutions.
