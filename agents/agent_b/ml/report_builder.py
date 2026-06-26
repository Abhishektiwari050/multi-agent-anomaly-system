import pandas as pd
from typing import List, Dict, Any

def build_report(
    task_id: str,
    df: pd.DataFrame,
    predictions: List[int],
    scores: List[float],
    detector
) -> Dict[str, Any]:
    N = len(df)
    
    anomalies_idx = [i for i, pred in enumerate(predictions) if pred == -1]
    anomalies_scores = [scores[i] for i in anomalies_idx]
    
    high_count = 0
    medium_count = 0
    low_count = 0
    
    # Classify all scores to count severity categories
    for s in scores:
        sev = detector.classify_severity(s)
        if sev == "HIGH":
            high_count += 1
        elif sev == "MEDIUM":
            medium_count += 1
        else:
            low_count += 1
            
    avg_score = float(sum(anomalies_scores) / len(anomalies_scores)) if anomalies_scores else 0.0
    
    # Identify top 5 most anomalous records (lowest scores)
    anomalies_with_scores = [(idx, scores[idx]) for idx in anomalies_idx]
    sorted_anomalies = sorted(anomalies_with_scores, key=lambda x: x[1])  # most anomalous first
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
