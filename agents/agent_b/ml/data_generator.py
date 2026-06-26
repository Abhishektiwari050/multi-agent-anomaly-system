import pandas as pd
import numpy as np

def generate_patient_vitals(N: int = 1000, contamination: float = 0.05, seed: int = 42):
    np.random.seed(seed)
    
    # 1. Generate normal clinical base
    heart_rate = np.random.normal(loc=80, scale=10, size=N)
    systolic_bp = np.random.normal(loc=110, scale=10, size=N)
    diastolic_bp = np.random.normal(loc=72, scale=6, size=N)
    temperature = np.random.normal(loc=36.6, scale=0.3, size=N)
    oxygen_saturation = np.random.normal(loc=98.5, scale=0.8, size=N)
    respiratory_rate = np.random.normal(loc=15, scale=2, size=N)
    glucose_level = np.random.normal(loc=90, scale=10, size=N)
    
    # Clip normal values to clinical limits
    heart_rate = np.clip(heart_rate, 40, 120)
    systolic_bp = np.clip(systolic_bp, 80, 160)
    diastolic_bp = np.clip(diastolic_bp, 45, 100)
    temperature = np.clip(temperature, 35.0, 39.0)
    oxygen_saturation = np.clip(oxygen_saturation, 90.0, 100.0)
    respiratory_rate = np.clip(respiratory_rate, 8, 25)
    glucose_level = np.clip(glucose_level, 50, 180)
    
    df = pd.DataFrame({
        "heart_rate": heart_rate,
        "systolic_bp": systolic_bp,
        "diastolic_bp": diastolic_bp,
        "temperature": temperature,
        "oxygen_saturation": oxygen_saturation,
        "respiratory_rate": respiratory_rate,
        "glucose_level": glucose_level
    })
    
    # 2. Inject anomalies
    n_anomalies = int(N * contamination)
    if n_anomalies > 0:
        anomaly_indices = list(np.random.choice(N, n_anomalies, replace=False))
        
        # Shift values high/low to simulate clinical emergency
        df.loc[anomaly_indices, "heart_rate"] += np.random.uniform(50, 80, size=n_anomalies)
        df.loc[anomaly_indices, "oxygen_saturation"] -= np.random.uniform(10, 20, size=n_anomalies)
        df.loc[anomaly_indices, "temperature"] += np.random.uniform(2, 4, size=n_anomalies)
        
        # Enforce bounds even after anomaly shifts
        df["heart_rate"] = np.clip(df["heart_rate"], 30, 220)
        df["oxygen_saturation"] = np.clip(df["oxygen_saturation"], 50.0, 100.0)
        df["temperature"] = np.clip(df["temperature"], 33.0, 43.0)
    else:
        anomaly_indices = []
        
    return df, sorted(anomaly_indices)
