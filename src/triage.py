"""Triage CLI (spec §4, batch mode). Day-2 adds --watch.

    python -m src.triage --all [--data data/tickets.csv] [--out out]
"""
import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from src.adapters.csv_adapter import CsvAdapter
from src.clustering import cluster
from src.corrections import authorize_corrections, build_few_shot, load_corrections, load_roster
from src.enrichment import make_openai_client
from src.pipeline import build_queue, enrich_all
from src.theme_registry import apply_theme_mapping, canonicalize


def load_dotenv(path=".env"):
    p = Path(path)
    if p.exists():
        for line in p.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="batch: process everything")
    ap.add_argument("--watch", action="store_true", help="live: poll the mock helpdesk")
    ap.add_argument("--from", dest="from_cursor", default="2026-08-03T00:00",
                    help="watch: history/stream split — MUST match the server cursor")
    ap.add_argument("--server", default="http://127.0.0.1:8900")
    ap.add_argument("--poll", type=float, default=1.0, help="watch poll interval (s)")
    ap.add_argument("--idle-ticks", type=int, default=8,
                    help="stop watch after N empty polls")
    ap.add_argument("--data", default="data/tickets.csv")
    ap.add_argument("--out", default="out")
    ap.add_argument("--corrections", default="feedback/corrections.jsonl")
    args = ap.parse_args(argv)

    load_dotenv()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.watch:
        return watch(args, out)

    tickets = CsvAdapter(args.data).fetch_tickets()
    by_id = {t["ticket_id"]: t for t in tickets}
    corrections, rejected = authorize_corrections(load_corrections(args.corrections),
                                                  load_roster())
    for c in rejected:
        print(f"⚠ correction ignored — author '{c.get('author')}' lacks the "
              f"correct_labels role ({c['ticket_id']}.{c['field']})")

    client = make_openai_client()
    enriched = enrich_all(
        tickets, client, cache_path=out / "enriched.jsonl",
        corrections=corrections, few_shot=build_few_shot(corrections),
    )

    # batch theme canonicalization: independent calls fragment slugs.
    # One call on a stronger model, with a sample summary per slug as evidence.
    counts, examples = {}, {}
    for e in enriched.values():
        counts[e["theme"]] = counts.get(e["theme"], 0) + 1
        examples.setdefault(e["theme"], e["summary"])
    merge_client = make_openai_client(model=os.environ.get("LLM_MODEL_MERGE", "gpt-4o"))
    mapping = canonicalize(counts, merge_client, examples=examples)
    (out / "theme_mapping.json").write_text(json.dumps(mapping, indent=2))
    enriched = apply_theme_mapping(enriched, mapping)

    records = [{
        "ticket_id": tid, "created_at": by_id[tid]["created_at"],
        "customer_name": by_id[tid]["customer_name"], "product": by_id[tid]["product"],
        "theme": e["theme"], "segment": e["segment"], "csat_score": by_id[tid]["csat_score"],
    } for tid, e in enriched.items()]
    result = cluster(records)
    (out / "clusters.json").write_text(json.dumps(
        {"incidents": result.incidents, "trends": result.trends}, indent=2, default=str))

    queue = build_queue(enriched, by_id, now=datetime.now())
    (out / "ops_queue.json").write_text(json.dumps(queue, indent=2, default=str))

    # GFM summary for the Triage skill to relay
    print(f"## Queue: {len(queue)} tickets · {len(result.incidents)} incidents · "
          f"{len(result.trends)} trends\n")
    print("| # | ticket | customer | segment | priority | why |")
    print("|---|---|---|---|---|---|")
    for i, q in enumerate(queue[:10], 1):
        pin = "📌 " if q["pinned"] else ""
        print(f"| {i} | {pin}{q['ticket_id']} | {q['customer_name']} | "
              f"{q['segment']} | {q['priority']} | {q['explain']} |")
    for c in result.incidents + result.trends:
        print(f"\n**{c['cluster_id']}** ({c['kind']}, {c['theme']}): "
              f"{len(c['member_ids'])} tickets, {len(c['customers'])} customers, "
              f"avg CSAT {c['avg_csat']}")


def watch(args, out):
    """Live mode: seed detector state with pre-cursor history, then poll the
    replay stream; enrich each arrival once (append-only cache), write labels
    back to the helpdesk, and append events to out/events.jsonl."""
    import time as _time

    from src.adapters.mock_adapter import MockHelpdeskAdapter
    from src.enrichment import enrich_ticket
    from src.pipeline import _load_cache, SECURITY_FLAGS
    from src.scoring import priority_score
    from src.watch import process_stream

    adapter = MockHelpdeskAdapter(args.server)
    client = make_openai_client()
    corrections, _ = authorize_corrections(load_corrections(args.corrections),
                                           load_roster())
    few_shot = build_few_shot(corrections)
    cache_path = out / "enriched.jsonl"
    cache = _load_cache(cache_path)
    events_path = out / "events.jsonl"
    cursor = datetime.fromisoformat(args.from_cursor)

    # reuse the theme vocabulary the batch merge learned; live tickets about a
    # known symptom converge on the canonical slug instead of re-fragmenting
    mapping_path = out / "theme_mapping.json"
    mapping = json.loads(mapping_path.read_text()) if mapping_path.exists() else {}

    def theme_of(e):
        return mapping.get(e["theme"], e["theme"])

    def to_record(t, e):
        return {"ticket_id": t["ticket_id"], "created_at": t["created_at"],
                "customer_name": t["customer_name"], "product": t["product"],
                "theme": theme_of(e), "segment": e["segment"],
                "csat_score": t["csat_score"], "risk_flags": e["risk_flags"], "_t": t}

    def enrich(t):
        e = cache.get(t["ticket_id"])
        if e is None:
            known = sorted({theme_of(c) for c in cache.values()})
            e = enrich_ticket(t, client, few_shot, known_themes=known)
            cache[e["ticket_id"]] = e
            with open(cache_path, "a") as f:
                f.write(json.dumps(e, default=str) + "\n")
        return e

    # split history/stream at the CURSOR, never at "sim now" — startup latency
    # on a fast replay clock must not swallow the first live tickets
    everything = adapter.fetch_tickets(peek=True)
    history = [t for t in everything if t["created_at"] <= cursor]
    seed = [to_record(t, enrich(t)) for t in history]
    last_seen = cursor
    print(f"seeded {len(seed)} history tickets (≤ {cursor}); watching {args.server} ...")

    def stream():
        nonlocal last_seen
        idle = 0
        while idle < args.idle_ticks:
            new = adapter.fetch_tickets(since=last_seen)
            if not new:
                idle += 1
                _time.sleep(args.poll)
                continue
            idle = 0
            for t in new:
                last_seen = max(last_seen, t["created_at"]) if last_seen else t["created_at"]
                yield to_record(t, enrich(t))

    def sink(event):
        with open(events_path, "a") as f:
            f.write(json.dumps(event, default=str) + "\n")
        print(f"  [{event['event']}] {event.get('ticket_id') or event.get('cluster_id')}"
              f"{' · ' + event['theme'] if event.get('theme') else ''}")
        if event["event"] == "INCIDENT_DECLARED":
            for tid in event["member_ids"]:
                adapter.write_back(tid, labels={"incident": event["cluster_id"]})

    by_id = {t["ticket_id"]: t for t in everything}
    arrived = [t["ticket_id"] for t in history]

    def refresh_queue():
        live = {tid: cache[tid] for tid in arrived if tid in cache}
        queue = build_queue(live, by_id, now=datetime.now())
        (out / "ops_queue.json").write_text(json.dumps(queue, indent=2, default=str))

    def enrich_and_writeback(rec):
        e = cache[rec["ticket_id"]]
        t = rec["_t"]
        pinned = bool(SECURITY_FLAGS & set(e["risk_flags"]))
        adapter.write_back(t["ticket_id"],
                           labels={"segment": e["segment"]},
                           priority=round(priority_score(e["severity"],
                                          t["monthly_revenue_usd"], 0, pinned), 1),
                           internal_note=e["summary"])
        arrived.append(t["ticket_id"])
        refresh_queue()  # spec §4: --watch refreshes ops_queue.json as tickets land
        return {}

    refresh_queue()
    process_stream(stream(), sink, enrich_fn=enrich_and_writeback, seed=seed)
    refresh_queue()
    print(f"stream idle — events in {events_path}; queue refreshed in {out / 'ops_queue.json'}")


if __name__ == "__main__":
    main()
