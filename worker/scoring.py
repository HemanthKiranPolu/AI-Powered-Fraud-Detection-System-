from __future__ import annotations

from typing import Any, Dict, List, Tuple

import yaml


class RulesConfig:
    def __init__(self, cfg: Dict[str, Any]):
        self.weights: Dict[str, float] = cfg.get("weights", {})
        self.thresholds = cfg.get("thresholds", {"approve": 0.25, "review": "0.25-0.6", "reject": 0.6})
        self.explanations: List[Dict[str, str]] = cfg.get("explanations", [])


def load_rules(path: str) -> RulesConfig:
    with open(path, "r") as f:
        cfg = yaml.safe_load(f)
    return RulesConfig(cfg)


def score_features(features: Dict[str, Any], rules: RulesConfig) -> Tuple[float, List[str], str]:
    # Weighted sum; normalize missing features to 0
    score = 0.0
    total_w = 0.0
    for k, w in rules.weights.items():
        total_w += float(w)
        v = features.get(k)
        if isinstance(v, bool):
            v = 1.0 if v else 0.0
        try:
            v = float(v)
        except Exception:
            v = 0.0
        # Normalize common percentage-based features
        if k in ("face_similarity", "textract_conf_avg"):
            v = v / 100.0
        # Normalize velocity counts (cap at 5 -> 1.0)
        if k == "velocity_count_24h":
            v = min(v / 5.0, 1.0)
        score += float(w) * float(v)
    fraud_score = score / total_w if total_w > 0 else 0.0
    reasons = evaluate_reasons(features, rules)
    decision = decide(fraud_score, rules)
    return fraud_score, reasons, decision


def evaluate_reasons(features: Dict[str, Any], rules: RulesConfig) -> List[str]:
    out: List[str] = []
    for rule in rules.explanations:
        expr = rule.get("when", "")
        if not expr:
            continue
        try:
            # Very restricted eval context
            ctx = {k: features.get(k) for k in features.keys()}
            # Normalize booleans for comparisons
            for k, v in ctx.items():
                if isinstance(v, bool):
                    ctx[k] = 1 if v else 0
            if safe_eval(expr, ctx):
                out.append(rule.get("reason", expr))
        except Exception:
            continue
    return out


def safe_eval(expr: str, ctx: Dict[str, Any]) -> bool:
    allowed_names = {k: ctx.get(k) for k in ctx.keys()}
    allowed_names.update({"True": True, "False": False, "None": None})
    code = compile(expr, "<expr>", "eval")
    for name in code.co_names:
        if name not in allowed_names:
            raise NameError(f"Use of name '{name}' not allowed")
    return bool(eval(code, {"__builtins__": {}}, allowed_names))


def decide(score: float, rules: RulesConfig) -> str:
    # thresholds: approve: 0.25, review: 0.25-0.6, reject: 0.6
    approve = float(rules.thresholds.get("approve", 0.25))
    reject = float(rules.thresholds.get("reject", 0.6))
    if score >= reject:
        return "REJECT"
    if score < approve:
        return "APPROVE"
    return "REVIEW"
