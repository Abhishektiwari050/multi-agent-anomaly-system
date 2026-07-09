import os

import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class AnomalyDetector:
    def __init__(self, contamination: float = 0.05, seed: int = 42):
        self.contamination = contamination
        self.seed = seed
        self.scaler = StandardScaler()
        self.model = IsolationForest(
            n_estimators=200, contamination=self.contamination, random_state=self.seed, n_jobs=-1
        )
        # Load severity thresholds from environment
        self.high_threshold = float(os.getenv("HIGH_SEVERITY_THRESHOLD", "-0.15"))
        self.medium_threshold = float(os.getenv("MEDIUM_SEVERITY_THRESHOLD", "-0.08"))

    def train_and_predict(self, df: pd.DataFrame):
        feature_cols = [
            "heart_rate",
            "systolic_bp",
            "diastolic_bp",
            "temperature",
            "oxygen_saturation",
            "respiratory_rate",
            "glucose_level",
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
