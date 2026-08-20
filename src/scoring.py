"""Explainable priority score (spec §4). Shown in the UI, never a black box:

    priority = severity_weight[1,2,4,8]
               x (1 + log10(1 + MRR))
               x age_factor(hours_open)
               + 50 if risk_flags
"""
import math

SEVERITY_WEIGHT = {1: 1, 2: 2, 3: 4, 4: 8}
RISK_OFFSET = 50


def age_factor(hours_open):
    """Gentle, monotonic: 1.0 at zero age, ~+0.5 after 24h, ~+1.0 after ~2 weeks."""
    return 1 + math.log10(1 + max(hours_open, 0)) / 2


def priority_score(severity, mrr, hours_open, has_risk_flags=False):
    base = SEVERITY_WEIGHT[severity] * (1 + math.log10(1 + mrr)) * age_factor(hours_open)
    return base + (RISK_OFFSET if has_risk_flags else 0)


def explain(severity, mrr, hours_open, has_risk_flags=False):
    """One-line breakdown for the queue table."""
    return (f"{SEVERITY_WEIGHT[severity]} (sev {severity}) "
            f"x {1 + math.log10(1 + mrr):.2f} (MRR ${mrr:,.0f}) "
            f"x {age_factor(hours_open):.2f} (open {hours_open:.0f}h)"
            + (f" + {RISK_OFFSET} (risk)" if has_risk_flags else ""))
