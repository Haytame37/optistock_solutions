import sys
import os
import argparse

# Ajouter le dossier racine du projet au PYTHONPATH pour pouvoir importer 'core' et 'utils'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.auth import create_user
except ImportError:
    print("❌ Erreur : Impossible d'importer 'core.auth'. Assurez-vous d'exécuter ce script depuis la racine du projet.")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="🛡️ OptiStock Solutions - Gestionnaire de Comptes Administrateurs")
    
    # Arguments
    parser.add_argument("--email", required=True, help="Email de l'administrateur")
    parser.add_argument("--prenom", required=True, help="Prénom")
    parser.add_argument("--nom", required=True, help="Nom")
    parser.add_argument("--password", required=True, help="Mot de passe (Min 8 caractères)")

    args = parser.parse_args()

    print(f"⏳ Tentative de création du compte admin pour : {args.email}...")

    # Appel de la fonction de création d'utilisateur avec le rôle 'admin'
    success, message = create_user(
        role="admin",
        first_name=args.prenom,
        last_name=args.nom,
        email=args.email,
        password=args.password
    )
    
    if success:
        print(f"✅ Succès ! Le compte administrateur '{args.email}' a été créé avec succès.")
        print("🚀 Vous pouvez maintenant vous connecter sur l'interface OptiStock.")
    else:
        print(f"❌ Échec de la création : {message}")

if __name__ == "__main__":
    main()
