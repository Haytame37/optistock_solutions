import pandas as pd
import numpy as np
import logging
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer
from sklearn.ensemble import RandomForestRegressor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def replace_faulty_with_median(df: pd.DataFrame, columns: list, window_size: int = 5,
                               temp_min_absolute: float = -50.0, temp_max_absolute: float = 100.0,
                               humid_min_absolute: float = 0.0, humid_max_absolute: float = 100.0) -> pd.DataFrame:
    """
    Détecte les valeurs 'fausses' (aberrantes physiquement ou pics anormaux) et les remplace par la médiane mobile.
    """
    df_clean = df.copy()
    
    for col in columns:
        if "temp" in col.lower() or col.startswith("capteur"):
            min_val, max_val = temp_min_absolute, temp_max_absolute
            is_temp = True
        elif "hum" in col.lower() or col.startswith("capteur"):
            min_val, max_val = humid_min_absolute, humid_max_absolute
            is_temp = False
        else:
            continue
            
        # 1. Remplacer les valeurs hors limites absolues par NaN (temporairement)
        mask_out_of_bounds = (df_clean[col] < min_val) | (df_clean[col] > max_val)
        df_clean.loc[mask_out_of_bounds, col] = np.nan
        
        # 2. Remplacer les pics anormaux (Z-score modifié avec la médiane)
        # On calcule la médiane mobile
        rolling_median = df_clean[col].rolling(window=window_size, min_periods=1, center=True).median()
        
        # Calcul du MAD (Median Absolute Deviation) pour détecter les pics
        deviation = np.abs(df_clean[col] - rolling_median)
        mad = deviation.rolling(window=window_size, min_periods=1, center=True).median()
        
        # Seuil de tolérance: 3 * MAD (ajustable)
        # Si la variation est très faible, on force un MAD minimum pour ne pas flagger tout
        min_mad = 2.0 if is_temp else 5.0
        mad = mad.clip(lower=min_mad)
        
        mask_spike = deviation > (3 * mad)
        df_clean.loc[mask_spike, col] = np.nan
        
        # 3. Remplacer les NaN (qui étaient des valeurs fausses) par la médiane locale
        df_clean[col] = df_clean[col].fillna(rolling_median)

    return df_clean

def impute_missing_with_missforest(df: pd.DataFrame, columns_to_impute: list) -> pd.DataFrame:
    """
    Utilise l'algorithme MissForest (RandomForest via IterativeImputer) pour imputer les valeurs manquantes réelles.
    """
    df_imputed = df.copy()
    
    # Isoler les données numériques à imputer
    data_to_impute = df_imputed[columns_to_impute]
    
    if data_to_impute.isnull().sum().sum() == 0:
        return df_imputed # Rien à imputer
    
    logger.info(f"MissForest: Imputation de {data_to_impute.isnull().sum().sum()} valeurs manquantes.")
    
    # Configuration du MissForest
    rf_estimator = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
    imputer = IterativeImputer(estimator=rf_estimator, max_iter=10, random_state=42, initial_strategy='mean')
    
    try:
        imputed_array = imputer.fit_transform(data_to_impute)
        df_imputed[columns_to_impute] = imputed_array
        logger.info("MissForest: Imputation réussie.")
    except Exception as e:
        logger.error(f"Erreur lors de l'imputation MissForest: {e}")
        # Fallback sur une méthode plus simple si MissForest échoue
        df_imputed[columns_to_impute] = df_imputed[columns_to_impute].interpolate(method='linear').bfill().ffill()
        
    return df_imputed

def clean_iot_data_pipeline(df: pd.DataFrame, sensor_columns: list) -> pd.DataFrame:
    """
    Pipeline complet de nettoyage des données IoT:
    1. Traitement des valeurs fausses par la médiane.
    2. Traitement des valeurs manquantes par MissForest.
    """
    # 1. Remplacer les valeurs fausses par la médiane
    df_cleaned = replace_faulty_with_median(df, columns=sensor_columns)
    
    # 2. Imputer les valeurs manquantes (NaNs) avec MissForest
    df_final = impute_missing_with_missforest(df_cleaned, columns_to_impute=sensor_columns)
    
    return df_final
