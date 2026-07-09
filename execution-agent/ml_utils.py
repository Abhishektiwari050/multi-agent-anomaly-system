import os
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Data Sim Simulation Logic
def generate_patient_vitals(N: int = 1000, contamination: float = 0.05, seed: int = 42) -> Tuple[pd.DataFrame, List[int]]:
    np.random.seed(seed)
    
    # Generate normal vital bases
    heart_rate = np.random.normal(loc=80, scale=10, size=N)
    systolic_bp = np.random.normal(loc=110, scale=10, size=N)
    diastolic_bp = np.random.normal(loc=72, scale=6, size=N)
    temperature = np.random.normal(loc=36.6, scale=0.3, size=N)
    oxygen_saturation = np.random.normal(loc=98.5, scale=0.8, size=N)
    respiratory_rate = np.random.normal(loc=15, scale=2, size=N)
    glucose_level = np.random.normal(loc=90, scale=10, size=N)
    
    # Clip to medical bounds
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
    
    # Inject multivariate anomalies
    n_anomalies = int(N * contamination)
    if n_anomalies > 0:
        anomaly_indices = list(np.random.choice(N, n_anomalies, replace=False))
        
        # Shift values high/low to simulate clinical emergency
        df.loc[anomaly_indices, "heart_rate"] += np.random.uniform(50, 80, size=n_anomalies)
        df.loc[anomaly_indices, "oxygen_saturation"] -= np.random.uniform(10, 20, size=n_anomalies)
        df.loc[anomaly_indices, "temperature"] += np.random.uniform(2, 4, size=n_anomalies)
        
        # Clip limits
        df["heart_rate"] = np.clip(df["heart_rate"], 30, 220)
        df["oxygen_saturation"] = np.clip(df["oxygen_saturation"], 50.0, 100.0)
        df["temperature"] = np.clip(df["temperature"], 33.0, 43.0)
    else:
        anomaly_indices = []
        
    return df, sorted(anomaly_indices)

# Isolation Forest ML Engine
class AnomalyDetector:
    def __init__(self, contamination: float = 0.05, seed: int = 42):
        self.contamination = contamination
        self.seed = seed
        self.scaler = StandardScaler()
        self.model = IsolationForest(
            n_estimators=200,
            contamination=self.contamination,
            random_state=self.seed,
            n_jobs=-1
        )
        # Severity thresholds
        self.high_threshold = float(os.getenv("HIGH_SEVERITY_THRESHOLD", "-0.15"))
        self.medium_threshold = float(os.getenv("MEDIUM_SEVERITY_THRESHOLD", "-0.08"))
        
    def train_and_predict(self, df: pd.DataFrame) -> Tuple[List[int], List[float]]:
        feature_cols = [
            "heart_rate", "systolic_bp", "diastolic_bp", 
            "temperature", "oxygen_saturation", "respiratory_rate", "glucose_level"
        ]
        X = df[feature_cols].values
        X_scaled = self.scaler.fit_transform(X)
        
        self.model.fit(X_scaled)
        predictions = self.model.predict(X_scaled)
        scores = self.model.decision_function(X_scaled)
        
        return list(predictions), list(scores)
        
    def classify_severity(self, score: float) -> str:
        if score < self.high_threshold:
            return "HIGH"
        elif score < self.medium_threshold:
            return "MEDIUM"
        else:
            return "LOW"

# Telemetry Report Formatting
def build_report(
    task_id: str,
    df: pd.DataFrame,
    predictions: List[int],
    scores: List[float],
    detector: AnomalyDetector
) -> Dict[str, Any]:
    N = len(df)
    
    anomalies_idx = [i for i, pred in enumerate(predictions) if pred == -1]
    anomalies_scores = [scores[i] for i in anomalies_idx]
    
    high_count = 0
    medium_count = 0
    low_count = 0
    
    for s in scores:
        sev = detector.classify_severity(s)
        if sev == "HIGH":
            high_count += 1
        elif sev == "MEDIUM":
            medium_count += 1
        else:
            low_count += 1
            
    avg_score = float(sum(anomalies_scores) / len(anomalies_scores)) if anomalies_scores else 0.0
    
    # Top 5 most anomalous records (lowest scores)
    anomalies_with_scores = [(idx, scores[idx]) for idx in anomalies_idx]
    sorted_anomalies = sorted(anomalies_with_scores, key=lambda x: x[1])
    top_5 = sorted_anomalies[:5]
    
    top_records = []
    for idx, score in top_5:
        vitals_row = df.iloc[idx].to_dict()
        top_records.append({
            "record_id": int(idx),
            "score": float(score),
            "severity": detector.classify_severity(score),
            "vitals": vitals_row
        })
        
    return {
        "task_id": task_id,
        "total_records": N,
        "anomalies_detected": len(anomalies_idx),
        "high_severity": high_count,
        "medium_severity": medium_count,
        "low_severity": low_count,
        "avg_anomaly_score": avg_score,
        "top_anomalous_records": top_records
    }
