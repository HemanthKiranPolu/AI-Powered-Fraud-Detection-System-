#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score


def load_features_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def main():
    ap = argparse.ArgumentParser(description="Evaluate fraud detection performance")
    ap.add_argument("--features-csv", required=True, help="CSV with features + label column 'is_fraud' (0/1)")
    ap.add_argument("--score-column", default="fraud_score", help="Column for model score if precomputed")
    ap.add_argument("--threshold", type=float, default=0.6, help="Decision threshold for reject")
    args = ap.parse_args()

    df = load_features_csv(Path(args.features_csv))
    if args.score_column in df.columns:
        scores = df[args.score_column].astype(float).values
    else:
        # Compute a naive score: face_similarity and mrz_valid
        fs = df.get("face_similarity", pd.Series(np.zeros(len(df))))
        mrz = df.get("mrz_valid", pd.Series(np.zeros(len(df))))
        scores = 0.6 * (fs / 100.0) + 0.4 * mrz
    y_true = df["is_fraud"].astype(int).values
    y_pred = (scores >= args.threshold).astype(int)

    print("Confusion Matrix:")
    print(confusion_matrix(y_true, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_true, y_pred, digits=3))
    try:
        auc = roc_auc_score(y_true, scores)
        print(f"ROC-AUC: {auc:.3f}")
    except Exception:
        pass


if __name__ == "__main__":
    main()

