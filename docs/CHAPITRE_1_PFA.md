# CHAPITRE 1 : ÉTUDE PRÉLIMINAIRE ET ANALYSE DES BESOINS

Ce premier chapitre pose les bases de la conception du système OptiStock Solutions. Il s'agit d'identifier les acteurs impliqués, de définir précisément les attentes du système et de comparer notre solution aux outils existants afin d'en dégager la valeur ajoutée technique.

## 1.1. Identification des parties prenantes
La réussite d'un système d'aide à la décision repose sur une compréhension fine des besoins de ses utilisateurs. Pour OptiStock Solutions, nous avons identifié quatre groupes d'acteurs majeurs :
*   **Les Propriétaires de Foncier Industriel :** Ils utilisent la plateforme pour valoriser leurs actifs en démontrant la conformité technique et environnementale de leurs locaux.
*   **Les Logisticiens et Directeurs Supply Chain :** Principaux utilisateurs finaux, ils exploitent le système pour localiser stratégiquement leurs centres de distribution et auditer la viabilité des sites de stockage.
*   **Les Auditeurs de Conformité :** Ils s'appuient sur les rapports générés par le moteur d'analyse IoT pour valider le respect des normes sanitaires (HACCP) et de la chaîne du froid.
*   **L'Équipe Technique :** En charge du déploiement, de la maintenance des algorithmes et de l'intégration des flux de données provenant des capteurs.

## 1.2. Analyse des besoins fonctionnels
Les besoins fonctionnels décrivent les actions que le système doit être capable d'exécuter. OptiStock Solutions s'articule autour de cinq piliers fonctionnels :
1.  **Macro-localisation Géospatiale :** Le système doit permettre de calculer la position théorique idéale (centre de gravité) d'un entrepôt en fonction des coordonnées géographiques des points de livraison, en utilisant le modèle de Weber.
2.  **Moteur d'Audit IoT :** La plateforme doit ingérer des flux de données de température et d'humidité, traiter les anomalies (interpolation des données manquantes) et lisser le signal pour fournir un diagnostic de conformité fiable.
3.  **Système de Scoring SAW (Simple Additive Weighting) :** Un algorithme doit agréger les performances logistiques et environnementales pour produire un score final normalisé, permettant un classement objectif des sites.
4.  **Interface de Messagerie et Assistant Intelligent :** L'intégration d'un chatbot (OptiBot) doit permettre une interaction fluide en langage naturel pour interroger les données du système.
5.  **Gestion des Réservations Sécurisées :** Un mécanisme de verrouillage temporaire (Pre-Lock) doit être implémenté pour éviter tout conflit lors du choix d'un entrepôt par plusieurs utilisateurs simultanés.

## 1.3. Analyse des besoins non-fonctionnels
Au-delà des fonctionnalités, la plateforme doit répondre à des exigences de qualité logicielle :
*   **Performance et Réactivité :** Les calculs matriciels de distance et le traitement des séries temporelles IoT doivent être exécutés en un temps quasi réel pour ne pas dégrader l'expérience utilisateur.
*   **Sécurité des Données :** L'accès au système doit être protégé par une authentification robuste, et l'intégrité des transactions immobilières doit être garantie par un verrouillage pessimiste au niveau de la base de données.
*   **Maintenabilité et Modularité :** L'architecture doit permettre l'ajout futur de nouveaux types de capteurs ou de nouveaux modèles mathématiques sans restructuration majeure du code.
*   **Ergonomie :** L'interface développée sous Streamlit doit être intuitive, offrant des visualisations claires (cartes interactives, graphiques de température) pour faciliter la prise de décision.

## 1.4. Benchmarking et Analyse Comparative
Le benchmarking a permis de comparer OptiStock Solutions aux solutions logicielles classiques de gestion d'entrepôt (WMS) et aux outils de SIG (Système d'Information Géographique). Il en ressort que si les outils actuels excellent dans la gestion de stock ou la cartographie pure, rares sont ceux qui intègrent nativement le couplage entre la géolocalisation théorique (Weber) et l'audit environnemental en temps réel (IoT). OptiStock se distingue par sa capacité à transformer des contraintes thermodynamiques et géospatiales en un indicateur de décision unique et intelligible.

## 1.5. Cahier des charges simplifié
Le développement du projet s'appuie sur une pile technologique moderne et robuste. Le langage **Python** a été choisi comme pivot central pour ses capacités en Data Science. Le framework **Streamlit** assure le déploiement rapide d'une interface web interactive, tandis que **SQLite** offre une persistance légère et efficace. Sur le plan algorithmique, le cahier des charges impose le respect des normes de distance de Haversine pour les calculs géographiques et des seuils HACCP pour la validation environnementale.
