"""--watch mode core (spec §4): consume arriving tickets one at a time,
enrich only unseen ids, re-run the deterministic detectors over the full
enriched set on every tick (cheap at this scale), and emit events the moment
a threshold trips. The card-decline incident must be DECLARED on the third
arriving ticket, not diagnosed after the fact."""
from src.clustering import cluster
from src.pipeline import SECURITY_FLAGS


def process_stream(records_iter, sink, enrich_fn=None, seed=()):
    """records_iter: iterable of clustering records (make_record contract),
    optionally carrying risk_flags. sink: callable(event_dict). enrich_fn:
    optional callable(record) -> enrichment fields, called once per unseen id.
    seed: pre-cursor history — loaded silently (no events), counts toward
    clusters; clusters fully satisfied by history alone are marked declared
    so the stream only announces genuinely new patterns."""
    seen = {rec["ticket_id"]: dict(rec) for rec in seed}
    declared = set()  # (kind, theme)
    if seen:
        baseline = cluster(list(seen.values()))
        declared |= {("incident", c["theme"]) for c in baseline.incidents}
        declared |= {("trend", c["theme"]) for c in baseline.trends}
    for rec in records_iter:
        tid = rec["ticket_id"]
        if tid in seen:
            continue  # append-only cache semantics: never re-enrich, never re-announce
        rec = dict(rec)
        if enrich_fn is not None:
            rec.update(enrich_fn(rec) or {})
        seen[tid] = rec

        sink({"event": "TICKET_ARRIVED", "ticket_id": tid,
              "theme": rec.get("theme"), "created_at": str(rec["created_at"])})

        if SECURITY_FLAGS & set(rec.get("risk_flags", ())):
            sink({"event": "RISK_PINNED", "ticket_id": tid,
                  "risk_flags": list(rec["risk_flags"])})

        result = cluster(list(seen.values()))
        for c in result.incidents:
            key = ("incident", c["theme"])
            if key not in declared:
                declared.add(key)
                sink({"event": "INCIDENT_DECLARED", "cluster_id": c["cluster_id"],
                      "theme": c["theme"], "member_ids": c["member_ids"],
                      "trigger_ticket": tid})
        for c in result.trends:
            key = ("trend", c["theme"])
            if key not in declared:
                declared.add(key)
                sink({"event": "TREND_DECLARED", "cluster_id": c["cluster_id"],
                      "theme": c["theme"], "member_ids": c["member_ids"],
                      "trigger_ticket": tid})
    return seen
