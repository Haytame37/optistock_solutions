# DOCUMENTATION TECHNIQUE — OPTISTOCK (Phases 3 & 4)

## 1. Contexte et Objectif
OptiStock est une plateforme d'aide à la décision (SAD - Système d'Aide à la Décision) dédiée à la logistique d'entrepôts. L'objectif de la Phase 3 et 4 est d'apporter **rigueur mathématique**, **robustesse des données** et **validation croisée** au prototype initial, répondant ainsi aux standards industriels stricts (HACCP, GDP).

Cette documentation résume l'architecture des composants mis en place pour garantir l'exhaustivité et la pertinence scientifique des scores finaux.

## 2. Architecture 3-Couches

L'architecture décisionnelle est scindée en 3 niveaux distincts afin de garantir modularité et maintenabilité.

### Couche 1 : Traitement du Signal (Acquisition & Fiabilisation)
Les données reçues des capteurs IoT sont par nature bruitées, incomplètes ou soumises à des pannes passagères.
*   **Consensus Multi-Capteurs :** L'algorithme ne s'appuie plus sur une seule source. Il établit la moyenne temporelle de 3 capteurs par environnement (`capteur1`, `capteur2`, `capteur3`).
*   **Imputation des valeurs manquantes (`NaN`) :** Application d'une **interpolation linéaire temporelle** centripète.
    *   *Référence : Moritz & Bartz-Beielstein (2017).*
*   **Atténuation du bruit (Lissage) :** Application d'un filtre de **moyenne mobile** (fenêtre de 3 heures) pour lisser la courbe et éliminer les faux-positifs liés à des micro-variations brusques d'origine électronique.

### Couche 2 : Normalisation Min-Max Dynamique
Pour fusionner des unités hétérogènes (distances en kilomètres vs pourcentages d'anomalies), une étape de normalisation est capitale. L'objectif est de projeter toutes les mesures sur un espace continu $[0, 1]$.

#### Le paradoxe géospatial
Un entrepôt très éloigné offre une *plus grande distance*, mais constitue une *moins bonne solution logistique*.
*   **Transformation Mathématique :** Avant normalisation, la transformation inverse $X' = \frac{1}{\text{Distance}}$ est appliquée.
*   **Normalisation :** $Score = \frac{X'}{\max(X')}$
Ainsi, l'entrepôt le **plus proche** obtient la valeur maximale ($1.0$), et aucun effet de biais ne pénalise la logique de pondération avale.

### Couche 3 : Fusion SAW (Simple Additive Weighting)
L'agrégation finale repose sur la méthode SAW, un standard de la recherche opérationnelle pour les MCDA (Multiple Criteria Decision Analysis).

$Score\_Global = (\omega_{log} \times Logistique) + (\omega_{env} \times Environnement)$

**Justification des poids ($\omega_{log} = 0.60$, $\omega_{env} = 0.40$) :**
*   L'axe Logistique ($60\%$) domine, car il capte simultanément le positionnement géographique (coût de transport, empreinte carbone) et la fiabilité connectique globale.
*   L'axe Environnement ($40\%$) est mesuré via la conformité thermique. Les variables, bien que critiques, peuvent en effet être corrigées via de nouveaux investissements (isolation, systèmes thermo-régulés artificiels).

*Référence : Triantaphyllou, E. (2000). Multi-Criteria Decision Making Methods.*

## 3. Segmentation Saisonnière (HACCP)

L'évaluation de la conformité IoT a été repensée pour ne plus être globale mais **mensuelle**. Un dépassement "critique" en juillet n'a pas la même signification thermodynamique qu'en décembre. 
*   **Intégration d'un dictionnaire normatif saisonnier** (`NORMES_SAISONNIERES`).
*   **Calcul mensuel des anomalies** permettant de localiser l'apparition des risques de gel (hiver) ou développement bactérien/fongique dû à un taux d'humidité excessif (printemps/été).

## 4. Sécurité Transactionnelle (Pessimistic Lock)

Un mécanisme de verrouillage applicatif (`System_Pre_Lock`) a été imposé au niveau des réservations des entrepôts :
*   Une fois verrouillé, l'entrepôt passe à l'état transitoire `LOCK` pour **15 minutes**.
*   **Unicité Concurrentielle :** Empêche le chevauchement de réservations pendant la phase de validation de contrat.
*   **Lazy Cleanup :** Le registre applicatif purge les verrous morts sans CRON ni background task, uniquement sur la base de sollicitations.

## 5. Moteur de Recommandation IA

Le résultat final pour l'opérateur ne se limite plus à un score numérique brut. Le système :
1.  **Dégage un statut** (Optimal, Acceptable, Critique).
2.  **Opère une analyse en composante** ("Quel est le maillot faible ? L'environnement ou la position logistique ?").
3.  **Appose une recommandation contextuelle et saisonnière** (ex: *"Alerte hivernale - mois 12 : vérifier l'isolation des quais"*).
