"""Batch pipeline assembly (spec §4): cache-aware enrichment fan-out,
corrections application, queue building. `triage.py` is the CLI over this."""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src.corrections import apply_corrections
from src.enrichment import enrich_ticket
from src.scoring import explain, priority_score

# Only security-class flags pin a ticket and earn the +50 offset. churn_risk
# is surfaced through the trend escalation, not per-ticket pinning — otherwise
# a pricing-complaint cluster floods the top of the queue.
SECURITY_FLAGS = {"ato", "fraud", "compliance_hold", "access_control"}


def _load_cache(cache_path):
    p = Path(cache_path)
    if not p.exists():
        return {}
    with open(p) as f:
        entries = [json.loads(line) for line in f if line.strip()]
    return {e["ticket_id"]: e for e in entries}


def enrich_all(tickets, client, cache_path, corrections=(), eval_mode=False,
               few_shot=(), max_workers=8):
    """Enrich only unseen ticket_ids; append results to the cache file.
    Corrections: hard overrides applied unless eval_mode (spec §6)."""
    cache = _load_cache(cache_path)
    todo = [t for t in tickets if t["ticket_id"] not in cache]
    if todo:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            results = list(pool.map(lambda t: enrich_ticket(t, client, few_shot), todo))
        Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "a") as f:
            for r in results:
                f.write(json.dumps(r, default=str) + "\n")
                cache[r["ticket_id"]] = r
    wanted = {t["ticket_id"] for t in tickets}
    enriched = {tid: e for tid, e in cache.items() if tid in wanted}
    return apply_corrections(enriched, list(corrections), enabled=not eval_mode)


def _hours_open(ticket, now):
    if ticket["resolution_time_hours"] is not None:
        return ticket["resolution_time_hours"]
    return max((now - ticket["created_at"]).total_seconds() / 3600, 0)


def build_queue(enriched, by_id, now):
    """Priority queue entries, risk tickets pinned above everything else."""
    entries = []
    for tid, e in enriched.items():
        t = by_id[tid]
        hours = _hours_open(t, now)
        pinned = bool(SECURITY_FLAGS & set(e["risk_flags"]))
        entries.append({
            "ticket_id": tid,
            "customer_name": t["customer_name"],
            "segment": e["segment"],
            "ops_workflow": e["ops_workflow"],
            "theme": e["theme"],
            "severity": e["severity"],
            "risk_flags": e["risk_flags"],
            "status": t["status"],
            "pinned": pinned,
            "priority": round(priority_score(e["severity"], t["monthly_revenue_usd"],
                                             hours, pinned), 1),
            "explain": explain(e["severity"], t["monthly_revenue_usd"], hours, pinned),
            "summary": e["summary"],
            "suggested_action": e["suggested_action"],
            "needs_human": e.get("needs_human", False),
        })
    entries.sort(key=lambda q: (not q["pinned"], -q["priority"]))
    return entries
