# INTRODUCTION GÉNÉRALE

## 1. Contexte de l’étude
L’évolution fulgurante des technologies de l'information et la mondialisation des échanges ont profondément transformé le secteur de la logistique industrielle. Aujourd’hui, la performance d'une chaîne logistique ne dépend plus seulement de sa capacité de stockage, mais de son agilité à intégrer des outils de décision intelligents. La gestion des entrepôts, particulièrement pour les denrées sensibles soumises aux normes HACCP et à la chaîne du froid, exige une précision rigoureuse tant sur le plan géographique qu'environnemental. C’est dans cette dynamique de modernisation, souvent qualifiée de "Logistique 4.0", que s’inscrit le projet **OptiStock Solutions**. Développé au sein de l’École Nationale des Sciences Appliquées (ENSA) de Béni Mellal, ce travail propose une réponse technologique aux défis complexes de la gestion du foncier industriel et de la conformité réglementaire.

## 2. Intérêt de l’étude
Cette étude présente un intérêt stratégique majeur à plusieurs niveaux. Sur le plan économique, elle permet une optimisation substantielle des coûts opérationnels et de transport par l'identification scientifique du site le plus performant. Sur le plan technologique, elle explore la convergence entre l'Internet des Objets (IoT) et les algorithmes d'Intelligence Artificielle pour transformer des données brutes en indicateurs de décision fiables. Enfin, sur le plan environnemental, le projet contribue à la réduction de l'empreinte carbone en optimisant les trajets logistiques et en assurant une surveillance énergétique proactive des sites de stockage.

## 3. Problématique
La sélection d'un emplacement logistique est une décision critique qui repose encore trop souvent sur des analyses partielles ou subjectives, entraînant des inefficacités à long terme. Parallèlement, le suivi des conditions environnementales au sein des entrepôts se heurte à la réalité technique des capteurs IoT, souvent sujets au bruit électronique ou aux pannes. Ces lacunes posent une question fondamentale : comment garantir une évaluation objective et sécurisée des sites logistiques en intégrant de manière cohérente des critères géospatiaux et des flux de données IoT ?

Pour répondre à cette problématique, plusieurs interrogations guident notre réflexion :
*   Quels modèles mathématiques permettent de déterminer avec précision le centre de gravité idéal d'un réseau de distribution ?
*   Comment fiabiliser et reconstruire les données issus de capteurs IoT pour garantir un audit environnemental conforme aux normes sanitaires ?
*   De quelle manière peut-on agréger des variables hétérogènes pour produire un score de décision universel ?
*   Comment sécuriser les processus transactionnels pour assurer l'intégrité des données en environnement concurrentiel ?

## 4. Objectif de l’étude
L’objectif central de ce projet est de concevoir et réaliser la plateforme **OptiStock Solutions**, un Système d’Aide à la Décision (SAD) multicritère. Ce système doit permettre de géolocaliser les sites les plus pertinents par rapport aux centres de consommation, d'auditer dynamiquement la conformité thermique des entrepôts et de classer ces derniers selon une méthode de scoring rigoureuse. L'intégration d'un assistant intelligent vient compléter ce dispositif pour offrir une expérience utilisateur assistée et performante.

## 5. Méthodologie
La réalisation de ce projet repose sur une démarche méthodologique structurée en plusieurs étapes clés. La phase initiale a consisté en une étude approfondie des modèles de localisation (Weber, Haversine) et des méthodes de scoring (SAW). S'en est suivie une phase de conception architecturale privilégiant le découplage des services et la robustesse des données sous SQLite. Le développement technique a été porté par le framework Streamlit, tandis que le moteur d'analyse IoT a nécessité l'implémentation d'algorithmes de traitement du signal (lissage, interpolation, consensus multi-capteurs). Enfin, une phase de sécurisation a permis d'intégrer des mécanismes de verrouillage pessimiste pour garantir la fiabilité des transactions finales.

## 6. Annonce de plan
Le présent rapport s’articule autour de quatre chapitres principaux. Le premier chapitre expose l’état de l’art et l’analyse des besoins fonctionnels du système. Le deuxième chapitre détaille la conception technique et les modèles mathématiques qui régissent l'intelligence de la plateforme. Le troisième chapitre est consacré à l'implémentation logicielle, incluant le développement des modules de calcul et de l'interface utilisateur. Enfin, le quatrième chapitre présente les résultats obtenus et les tests de validation effectués pour démontrer l’efficacité de la solution OptiStock.
