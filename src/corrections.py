"""Feedback Channel 1 (spec §5): one corrections file, three effects —
hard override, few-shot exemplars, golden-set growth. Overrides are
switchable OFF for eval (spec §6): before/after must measure whether the
model generalized, not whether the override switch works."""
import json
from pathlib import Path


def load_corrections(path):
    p = Path(path)
    if not p.exists():
        return []
    with open(p) as f:
        return [json.loads(line) for line in f if line.strip()]


def load_roster(path="team/roster.json"):
    p = Path(path)
    return json.loads(p.read_text()) if p.exists() else None


def authorize_corrections(corrections, roster):
    """Coaching authority is role-based: only roster members carrying the
    `correct_labels` role may author corrections. Rejected entries stay in the
    file (audit trail) but never reach overrides, few-shot, or the eval.
    No roster configured → no gate (single-operator setups)."""
    if roster is None:
        return list(corrections), []
    allowed = {p["handle"] for p in roster.get("people", [])
               if "correct_labels" in p.get("roles", [])}
    accepted = [c for c in corrections if c.get("author") in allowed]
    rejected = [c for c in corrections if c.get("author") not in allowed]
    return accepted, rejected


def apply_corrections(enriched, corrections, enabled=True):
    """enriched: {ticket_id: enrichment dict}. Returns a new dict; never
    mutates input. With enabled=False (eval mode) returns entries unchanged."""
    out = {tid: dict(e) for tid, e in enriched.items()}
    if not enabled:
        return out
    for c in corrections:
        if c["ticket_id"] in out:
            out[c["ticket_id"]][c["field"]] = c["should_be"]
    return out


def build_few_shot(corrections, n=10):
    """Most recent N corrections, oldest-first, for prompt injection."""
    return sorted(corrections, key=lambda c: c["date"])[-n:]


def merge_into_golden(golden, corrections):
    """Fold corrections into the golden list: update the field in place for
    known tickets (other fields untouched), append a new entry otherwise.
    Never duplicates a ticket."""
    out = [dict(g) for g in golden]
    by_id = {g["ticket_id"]: g for g in out}
    for c in corrections:
        if c["ticket_id"] in by_id:
            by_id[c["ticket_id"]][c["field"]] = c["should_be"]
        else:
            entry = {"ticket_id": c["ticket_id"], c["field"]: c["should_be"]}
            out.append(entry)
            by_id[c["ticket_id"]] = entry
    return out
