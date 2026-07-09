from agents.agent_b.ml.data_generator import generate_patient_vitals
from agents.agent_b.ml.isolation_forest import AnomalyDetector
from agents.agent_b.ml.report_builder import build_report


def test_anomaly_detector_training():
    df, anomaly_indices = generate_patient_vitals(N=1000, contamination=0.05, seed=42)

    detector = AnomalyDetector(contamination=0.05, seed=42)
    predictions, scores = detector.train_and_predict(df)

    assert len(predictions) == 1000
    assert len(scores) == 1000

    # IsolationForest outputs 1 for normal, -1 for anomaly
    unique_labels = set(predictions)
    assert -1 in unique_labels or 1 in unique_labels


def test_anomaly_detector_recall():
    df, anomaly_indices = generate_patient_vitals(N=1000, contamination=0.05, seed=42)

    detector = AnomalyDetector(contamination=0.05, seed=42)
    predictions, scores = detector.train_and_predict(df)

    # Calculate how many of the injected anomalies were flagged by model (-1)
    detected_anomalies = [idx for idx in anomaly_indices if predictions[idx] == -1]
    recall = len(detected_anomalies) / len(anomaly_indices)

    # Model must detect at least 80% of injected anomalies
    assert recall >= 0.80


def test_classify_severity():
    detector = AnomalyDetector(contamination=0.05, seed=42)

    # Test threshold borders (HIGH < -0.15 <= MEDIUM < -0.08 <= LOW)
    assert detector.classify_severity(-0.20) == "HIGH"
    assert detector.classify_severity(-0.10) == "MEDIUM"
    assert detector.classify_severity(0.0) == "LOW"


def test_report_builder():
    df, anomaly_indices = generate_patient_vitals(N=100, contamination=0.05, seed=42)
    detector = AnomalyDetector(contamination=0.05, seed=42)
    predictions, scores = detector.train_and_predict(df)

    report = build_report("task-123", df, predictions, scores, detector)

    assert report["task_id"] == "task-123"
    assert report["total_records"] == 100
    assert "anomalies_detected" in report
    assert "high_severity" in report
    assert "top_anomalous_records" in report
    assert len(report["top_anomalous_records"]) <= 5
