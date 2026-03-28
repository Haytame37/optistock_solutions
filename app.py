import streamlit as st
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="OptiStock Solutions", layout="wide")



st.title("🏭 OptiStock Solutions")
st.sidebar.success("Sélectionnez un module ci-dessus.")

st.write("""
### Bienvenue dans le système d'aide à la décision logistique.
Cette application est en cours de développement. 
""")

# Test rapide de composant
col1, col2, col3 = st.columns(3)
col1.metric("Entrepôts", "12", "+2")
col2.metric("Température Moyenne", "21°C", "0.5°C")
col3.metric("Conformité IoT", "98%", "Stable")

st.info("Le squelette du projet est opérationnel. Prêt pour l'intégration des modules !")