"""Deterministic cross-ticket detectors (spec §2, §4). No LLM in here:
input records already carry theme/segment from enrichment.

  burst:  per theme, chain tickets <=72h apart, >=3 tickets -> incident.
          faq records never burst (verbatim-repeat questions can bunch
          inside 72h; volume alone is not an incident, and a CSAT gate
          would break live detection — arriving tickets have no CSAT).
  trend:  per theme, >=5 distinct customers over >=14 days with
          avg CSAT (scored tickets only) <= 2.5 -> trend.
  precedence: a theme that qualifies as a trend absorbs all its tickets;
          no burst is emitted for it (the FX tail bunches 3-in-72h twice
          and must not misfire as a mini-incident).
"""
from dataclasses import dataclass, field
from datetime import timedelta

BURST_MIN_TICKETS = 3
BURST_MAX_GAP = timedelta(hours=72)
TREND_MIN_CUSTOMERS = 5
TREND_MIN_SPAN = timedelta(days=14)
TREND_MAX_AVG_CSAT = 2.5


@dataclass
class ClusterResult:
    incidents: list = field(default_factory=list)
    trends: list = field(default_factory=list)


def _cluster_dict(kind, theme, members):
    scored = [r["csat_score"] for r in members if r.get("csat_score") is not None]
    return {
        "kind": kind,
        "theme": theme,
        "member_ids": [r["ticket_id"] for r in members],
        "customers": sorted({r["customer_name"] for r in members}),
        "first_seen": members[0]["created_at"],
        "last_seen": members[-1]["created_at"],
        "avg_csat": round(sum(scored) / len(scored), 2) if scored else None,
    }


def _trend_qualifies(group):
    customers = {r["customer_name"] for r in group}
    span = group[-1]["created_at"] - group[0]["created_at"]
    scored = [r["csat_score"] for r in group if r.get("csat_score") is not None]
    avg = sum(scored) / len(scored) if scored else None
    return (len(customers) >= TREND_MIN_CUSTOMERS
            and span >= TREND_MIN_SPAN
            and avg is not None and avg <= TREND_MAX_AVG_CSAT)


def _burst_chains(group):
    chains, chain = [], []
    for r in group:
        if chain and r["created_at"] - chain[-1]["created_at"] > BURST_MAX_GAP:
            chains.append(chain)
            chain = []
        chain.append(r)
    chains.append(chain)
    return [c for c in chains if len(c) >= BURST_MIN_TICKETS]


def cluster(records):
    by_theme = {}
    for r in records:
        by_theme.setdefault(r["theme"], []).append(r)

    incidents, trends = [], []
    for theme, group in by_theme.items():
        group.sort(key=lambda r: r["created_at"])
        if _trend_qualifies(group):
            trends.append(_cluster_dict("trend", theme, group))
            continue  # precedence: trend absorbs; never also a burst
        eligible = [r for r in group if r.get("segment") != "faq"]
        for chain in _burst_chains(eligible):
            incidents.append(_cluster_dict("incident", theme, chain))

    incidents.sort(key=lambda c: c["first_seen"])
    trends.sort(key=lambda c: c["first_seen"])
    for i, c in enumerate(incidents, 1):
        c["cluster_id"] = f"INC-{i:03d}"
    for i, c in enumerate(trends, 1):
        c["cluster_id"] = f"TRD-{i:03d}"
    return ClusterResult(incidents=incidents, trends=trends)
