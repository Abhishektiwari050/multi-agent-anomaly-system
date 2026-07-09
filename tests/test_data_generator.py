import pandas as pd

from agents.agent_b.ml.data_generator import generate_patient_vitals


def test_generate_patient_vitals_shape():
    df, anomaly_indices = generate_patient_vitals(N=1000, contamination=0.05, seed=42)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1000
    assert len(anomaly_indices) == 50  # 5% of 1000

    expected_cols = [
        "heart_rate", "systolic_bp", "diastolic_bp",
        "temperature", "oxygen_saturation", "respiratory_rate", "glucose_level"
    ]
    for col in expected_cols:
        assert col in df.columns

def test_generate_patient_vitals_ranges():
    df, _ = generate_patient_vitals(N=100, contamination=0.0, seed=42)
    # Normals should be within reasonable clinical boundaries
    assert df["heart_rate"].min() >= 40
    assert df["heart_rate"].max() <= 120
    assert df["oxygen_saturation"].min() >= 90
    assert df["temperature"].min() >= 35.0

def test_generate_patient_vitals_anomalies():
    df, anomaly_indices = generate_patient_vitals(N=100, contamination=0.10, seed=42)
    assert len(anomaly_indices) == 10

    # Check that anomalies exhibit anomalous ranges (e.g., elevated heart rate, fever, etc.)
    anomaly_df = df.iloc[anomaly_indices]

    # Injected anomalies are shifted high or low
    # Specifically, heart rate offset is +50 to +80
    assert anomaly_df["heart_rate"].mean() > df["heart_rate"].mean()

def test_generate_patient_vitals_reproducibility():
    df1, idx1 = generate_patient_vitals(N=100, contamination=0.05, seed=10)
    df2, idx2 = generate_patient_vitals(N=100, contamination=0.05, seed=10)

    pd.testing.assert_frame_equal(df1, df2)
    assert idx1 == idx2
