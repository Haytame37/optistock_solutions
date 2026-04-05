# Seuils Environnementaux (Target)
TEMP_MIN = 15.0
TEMP_MAX = 25.0
HUMID_MIN = 30.0
HUMID_MAX = 60.0

# Paramètres de simulation
DAYS_IN_YEAR = 365
HOURS_PER_DAY = 24
TEMP_DATA_PATH = "data/samples/temperature.csv"
HUMID_DATA_PATH = "data/samples/humidite.csv"

# La Pondération,utilisé pour calcluer le score dans le dossier core/scoring.py
WEIGHT_TEMP = 0.7  # La température compte pour 70% de la note
WEIGHT_HUMID = 0.3 # L'humidité compte pour 30% de la note