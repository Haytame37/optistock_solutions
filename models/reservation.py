"""
models/reservation.py
═══════════════════════════════════════════════════════════════════════════════
Modèle de données pour les réservations d'entrepôts OptiStock.

System_Pre_Lock — Mécanisme de verrouillage applicatif :
    Avant de finaliser un contrat, une fenêtre de négociation de 15 minutes
    est ouverte pendant laquelle l'entrepôt est placé en statut 'LOCK'.
    Cela évite les réservations CONCURRENTES sur le même espace (pessimistic lock).

    Cycle de vie d'une réservation :
        DISPONIBLE → (négociation) → LOCK → CONFIRME
                                          ↘ EXPIRE (timeout)
                                          ↘ ANNULE  (libération manuelle)

Architecture :
    • Registre en mémoire (_verrous_actifs) : dict[entrepot_id → verrou]
    • Compatible multi-sessions Streamlit (état partagé via ClassVar)
    • Timer auto-expiration : vérifié à chaque accès (lazy evaluation)
═══════════════════════════════════════════════════════════════════════════════
"""

from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import ClassVar, Optional


# ─────────────────────────────────────────────────────────────────────────────
#  CONSTANTES SYSTÈME
# ─────────────────────────────────────────────────────────────────────────────

# Durée du verrouillage en minutes (phase de négociation — configurable)
DUREE_VERROU_MINUTES: int = 15

# Statuts possibles d'une réservation (machine d'états finis)
STATUT_DISPONIBLE = "DISPONIBLE"
STATUT_LOCK       = "LOCK"       # ← Verrou applicatif actif (négociation)
STATUT_CONFIRME   = "CONFIRME"   # Réservation finalisée par le client
STATUT_ANNULE     = "ANNULE"     # Réservation annulée manuellement
STATUT_EXPIRE     = "EXPIRE"     # Verrou expiré automatiquement (timeout)


@dataclass
class Reservation:
    """
    Représente une réservation d'entrepôt avec gestion du cycle de vie complet.

    Attributs
    ---------
    id_reservation  : Identifiant unique (UUID tronqué)
    entrepot_id     : Identifiant de l'entrepôt concerné (ex: 'ENT_001')
    client_id       : Identifiant du client demandeur
    score_global    : Score SAW Phase 4 au moment de la réservation
    statut          : Statut courant (voir STATUT_* constants)
    date_creation   : Horodatage de création
    date_expiration : Horodatage d'expiration du verrou (None si pas de verrou)
    motif           : Commentaire libre (annulation, etc.)

    Registre de classe (_verrous_actifs) :
        Simule une table de verrous en base de données.
        dict[entrepot_id → dict(reservation_id, client_id, creation, expiration)]
    """
    id_reservation:  str
    entrepot_id:     str
    client_id:       str
    score_global:    float            = 0.0
    statut:          str              = STATUT_DISPONIBLE
    date_creation:   datetime         = field(default_factory=datetime.now)
    date_expiration: Optional[datetime] = None
    motif:           str              = ""

    # ── Registre global des verrous (partagé entre toutes les instances) ─────
    _verrous_actifs: ClassVar[dict] = {}

    # ─────────────────────────────────────────────────────────────────────────
    #  System_Pre_Lock — Verrou applicatif principal
    # ─────────────────────────────────────────────────────────────────────────

    def appliquer_verrou(self, entrepot_id: str) -> dict:
        """
        System_Pre_Lock — Verrouille un entrepôt pour DUREE_VERROU_MINUTES minutes
        pendant la phase de négociation.

        Algorithme :
            1. Purger les verrous expirés du registre (lazy cleanup)
            2. Vérifier si un verrou actif non expiré existe déjà
               → Si OUI : retourner DEJA_VERROUILLE (pas de doublon)
            3. Créer le nouveau verrou et l'enregistrer dans _verrous_actifs
            4. Mettre à jour le statut de cet objet Reservation

        Paramètres
        ----------
        entrepot_id : str — Identifiant de l'entrepôt (ex: 'ENT_001')

        Retourne
        --------
        dict :
            'succes'         : bool  — True si verrou créé
            'statut'         : str   — 'LOCK' ou 'DEJA_VERROUILLE'
            'entrepot_id'    : str
            'expiration'     : datetime
            'duree_restante' : int   — minutes restantes
            'message'        : str   — message UI lisible
        """
        maintenant = datetime.now()

        # ── Étape 1 : Nettoyage paresseux des verrous expirés ─────────────────
        self._purger_verrous_expires()

        # ── Étape 2 : Vérification d'un verrou existant non expiré ───────────
        verrou_existant = Reservation._verrous_actifs.get(entrepot_id)
        if verrou_existant is not None:
            expiration = verrou_existant["expiration"]
            if expiration > maintenant:
                # Verrou actif appartenant à une autre session
                temps_restant = max(
                    1,
                    int((expiration - maintenant).total_seconds() / 60) + 1
                )
                return {
                    "succes":         False,
                    "statut":         "DEJA_VERROUILLE",
                    "entrepot_id":    entrepot_id,
                    "expiration":     expiration,
                    "duree_restante": temps_restant,
                    "message": (
                        f"⛔ L'entrepôt '{entrepot_id}' est déjà verrouillé "
                        f"(client: {verrou_existant['client_id']}). "
                        f"Expire dans {temps_restant} minute(s) "
                        f"à {expiration.strftime('%H:%M:%S')}."
                    ),
                }

        # ── Étape 3 : Création du nouveau verrou ──────────────────────────────
        expiration = maintenant + timedelta(minutes=DUREE_VERROU_MINUTES)

        # Mise à jour de l'objet courant
        self.entrepot_id     = entrepot_id
        self.statut          = STATUT_LOCK
        self.date_expiration = expiration

        # Enregistrement dans le registre global
        Reservation._verrous_actifs[entrepot_id] = {
            "reservation_id": self.id_reservation,
            "client_id":      self.client_id,
            "creation":       maintenant,
            "expiration":     expiration,
            "statut":         STATUT_LOCK,
            "score_global":   self.score_global,
        }

        return {
            "succes":         True,
            "statut":         STATUT_LOCK,
            "entrepot_id":    entrepot_id,
            "expiration":     expiration,
            "duree_restante": DUREE_VERROU_MINUTES,
            "message": (
                f"🔒 Entrepôt '{entrepot_id}' verrouillé pour "
                f"{DUREE_VERROU_MINUTES} minutes "
                f"(jusqu'à {expiration.strftime('%H:%M:%S')}). "
                f"Phase de négociation en cours — Score: {self.score_global}/100."
            ),
        }

    # ─────────────────────────────────────────────────────────────────────────
    #  Libération manuelle du verrou
    # ─────────────────────────────────────────────────────────────────────────

    def liberer_verrou(self, entrepot_id: str) -> dict:
        """
        Libère manuellement un verrou (ex: négociation échouée, client annule).

        Met le statut de la réservation à ANNULE et supprime du registre.

        Retourne
        --------
        dict : 'succes' (bool) + 'message' (str)
        """
        if entrepot_id in Reservation._verrous_actifs:
            del Reservation._verrous_actifs[entrepot_id]
            self.statut          = STATUT_ANNULE
            self.date_expiration = None
            return {
                "succes":  True,
                "message": (
                    f"🔓 Verrou sur '{entrepot_id}' libéré manuellement. "
                    f"Entrepôt de nouveau disponible."
                ),
            }
        return {
            "succes":  False,
            "message": f"ℹ️ Aucun verrou actif trouvé sur '{entrepot_id}'.",
        }

    # ─────────────────────────────────────────────────────────────────────────
    #  Confirmation de réservation (LOCK → CONFIRME)
    # ─────────────────────────────────────────────────────────────────────────

    def confirmer_reservation(self) -> dict:
        """
        Finalise la réservation (passage LOCK → CONFIRME).

        Précondition : statut == STATUT_LOCK
        Postcondition : suppression du verrou + statut CONFIRME

        Retourne
        --------
        dict : 'succes' (bool) + 'message' (str)
        """
        if self.statut != STATUT_LOCK:
            return {
                "succes":  False,
                "message": (
                    f"❌ Impossible de confirmer : statut actuel '{self.statut}' "
                    f"(doit être LOCK)."
                ),
            }
        self.statut = STATUT_CONFIRME
        # Libération du verrou après confirmation (l'entrepôt est définitivement réservé)
        Reservation._verrous_actifs.pop(self.entrepot_id, None)
        return {
            "succes":  True,
            "message": (
                f"✅ Réservation {self.id_reservation} CONFIRMÉE "
                f"pour '{self.entrepot_id}' "
                f"(client: {self.client_id}, score: {self.score_global}/100)."
            ),
        }

    # ─────────────────────────────────────────────────────────────────────────
    #  Méthodes de classe — Administration des verrous
    # ─────────────────────────────────────────────────────────────────────────

    @classmethod
    def get_verrous_actifs(cls) -> dict:
        """
        Retourne tous les verrous actifs non expirés (vue d'administration).
        Effectue un nettoyage paresseux au passage.
        """
        cls._purger_verrous_expires_cls()
        return dict(cls._verrous_actifs)   # copie défensive

    @classmethod
    def get_statut_entrepot(cls, entrepot_id: str) -> str:
        """
        Retourne le statut courant d'un entrepôt :
            'LOCK'       → verrou actif
            'EXPIRE'     → verrou expiré (auto-libéré)
            'DISPONIBLE' → libre
        """
        cls._purger_verrous_expires_cls()
        if entrepot_id in cls._verrous_actifs:
            return STATUT_LOCK
        return STATUT_DISPONIBLE

    @classmethod
    def _purger_verrous_expires_cls(cls) -> int:
        """
        Supprime du registre tous les verrous dont la date d'expiration est passée.
        Retourne le nombre de verrous purgés.

        Cette méthode est appelée automatiquement avant chaque consultation
        du registre (pattern "lazy cleanup").
        """
        maintenant = datetime.now()
        expires = [
            eid for eid, v in cls._verrous_actifs.items()
            if v["expiration"] <= maintenant
        ]
        for eid in expires:
            del cls._verrous_actifs[eid]
        return len(expires)

    def _purger_verrous_expires(self) -> int:
        """Wrapper d'instance vers la méthode de classe."""
        return Reservation._purger_verrous_expires_cls()

    # ─────────────────────────────────────────────────────────────────────────
    #  Représentation
    # ─────────────────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return (
            f"Reservation("
            f"id={self.id_reservation!r}, "
            f"entrepot={self.entrepot_id!r}, "
            f"client={self.client_id!r}, "
            f"statut={self.statut!r}, "
            f"score={self.score_global:.1f})"
        )
