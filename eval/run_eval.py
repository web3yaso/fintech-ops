"""Eval harness (spec §6). Same production enrichment function, temperature 0.
HARD OVERRIDES DISABLED (few-shot stays on): before/after-corrections measures
generalization, not the override switch.

    python -m eval.run_eval [--golden eval/golden.json] [--cache eval/cache.jsonl]
"""
import argparse
import json
from pathlib import Path

from src.adapters.csv_adapter import CsvAdapter
from src.corrections import (authorize_corrections, build_few_shot,
                             load_corrections, load_roster, merge_into_golden)
from src.enrichment import make_openai_client
from src.pipeline import enrich_all
from src.triage import load_dotenv

GRADED_FIELDS = ["segment", "ops_workflow", "severity", "risk_flags", "amount_usd"]


def cluster_hit_rate(golden, detected):
    """Membership hit rate (spec §6): map each golden cluster label to its
    majority detected cluster, then grade every labeled golden ticket —
    including cluster: null tickets, which must NOT appear in any cluster."""
    from collections import Counter
    labeled = [g for g in golden if "cluster" in g]
    membership = {}
    for c in detected.get("incidents", []) + detected.get("trends", []):
        for tid in c["member_ids"]:
            membership[tid] = c["cluster_id"]
    label_map = {}
    for label in {g["cluster"] for g in labeled if g["cluster"]}:
        votes = Counter(membership.get(g["ticket_id"])
                        for g in labeled if g["cluster"] == label)
        votes.pop(None, None)
        label_map[label] = votes.most_common(1)[0][0] if votes else None
    hits = 0
    for g in labeled:
        got = membership.get(g["ticket_id"])
        if g["cluster"] is None:
            hits += got is None
        else:
            hits += got is not None and got == label_map.get(g["cluster"])
    return hits, len(labeled)


def grade(field, got, want):
    if field == "severity":
        return abs(got - want) <= 1
    if field == "risk_flags":
        return set(got) == set(want)
    return got == want


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", default="eval/golden.json")
    ap.add_argument("--data", default="data/tickets.csv")
    ap.add_argument("--cache", default="eval/cache.jsonl")
    ap.add_argument("--corrections", default="feedback/corrections.jsonl")
    args = ap.parse_args(argv)

    load_dotenv()
    golden = json.loads(Path(args.golden).read_text())["tickets"]
    corrections, _ = authorize_corrections(load_corrections(args.corrections),
                                           load_roster())
    # Channel-1 effect 3: corrections grow the golden set (in-memory merge;
    # entries for new tickets carry only the corrected fields)
    golden = merge_into_golden(golden, corrections)
    wanted = {g["ticket_id"] for g in golden}
    tickets = [t for t in CsvAdapter(args.data).fetch_tickets() if t["ticket_id"] in wanted]

    enriched = enrich_all(
        tickets, make_openai_client(), cache_path=args.cache,
        corrections=corrections, eval_mode=True,           # overrides OFF
        few_shot=build_few_shot(corrections),              # few-shot ON
    )

    hits = {f: 0 for f in GRADED_FIELDS}
    seen = {f: 0 for f in GRADED_FIELDS}
    errors = []
    for g in golden:
        e = enriched[g["ticket_id"]]
        for f in GRADED_FIELDS:
            if f not in g:      # correction-grown entries carry partial fields
                continue
            seen[f] += 1
            if grade(f, e[f], g[f]):
                hits[f] += 1
            else:
                errors.append(f"{g['ticket_id']}.{f}: got {e[f]!r}, want {g[f]!r}")

    print(f"## Eval: {len(golden)} golden tickets, "
          f"{len(corrections)} corrections merged (overrides OFF, few-shot ON, leave-one-out)\n")
    print("| field | accuracy |")
    print("|---|---|")
    for f in GRADED_FIELDS:
        print(f"| {f} | {hits[f]}/{seen[f]} = {hits[f]/seen[f]:.0%} |")
    clusters_path = Path("out/clusters.json")
    if clusters_path.exists():
        ch, ct = cluster_hit_rate(golden, json.loads(clusters_path.read_text()))
        print(f"| cluster membership | {ch}/{ct} = {ch/ct:.0%} |")
    else:
        print("| cluster membership | (run src.triage --all first) |")
    if errors:
        print("\nMisses:")
        for line in errors:
            print(f"- {line}")
    print("\nBoundary: classification only; draft quality is assessed manually (spec §6).")


if __name__ == "__main__":
    main()
