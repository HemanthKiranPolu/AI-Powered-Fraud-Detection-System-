from worker.scoring import load_rules, score_features


def test_score_features():
    rules = load_rules("config/rules.yaml")
    feats = {
        "face_similarity": 90,
        "textract_conf_avg": 95,
        "mrz_valid": True,
        "expiry_valid": True,
        "template_geom_score": 0.7,
        "blur_score": 0.1,
        "velocity_count_24h": 0,
        "device_hash_dup": False,
        "glare_score": 0.05,
    }
    score, reasons, decision = score_features(feats, rules)
    assert 0.0 <= score <= 1.0
    assert decision in ("REJECT", "APPROVE", "REVIEW")

