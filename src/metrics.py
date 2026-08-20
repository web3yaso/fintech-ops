"""Weekly ops brief (spec §4): ops-first ordering — money and risk on the
first screen, support hygiene second. Pure compute functions + a fully
self-contained HTML renderer (inline CSS/SVG, no external requests).

    python -m src.metrics [--out reports]
"""
import argparse
import json
import statistics
from datetime import datetime
from pathlib import Path

from src.closure import closure_state, time_to_close_hours, volume_subsided
from src.pipeline import SECURITY_FLAGS

# ---------------------------------------------------------------- compute --

def stuck_funds(enriched, by_id):
    """Unresolved payment investigations with a stated amount; follow-ups
    about the same wire (same customer, same amount) counted once."""
    seen, total = set(), 0.0
    for tid, e in enriched.items():
        t = by_id[tid]
        if (e["ops_workflow"] == "payment_investigation" and t["status"] != "resolved"
                and e["amount_usd"]):
            key = (t["customer_name"], e["amount_usd"])
            if key not in seen:
                seen.add(key)
                total += e["amount_usd"]
    return total


def risk_exposure(enriched, by_id):
    """MRR of distinct customers with an unresolved security-flagged ticket."""
    customers = {}
    for tid, e in enriched.items():
        t = by_id[tid]
        if t["status"] != "resolved" and SECURITY_FLAGS & set(e["risk_flags"]):
            customers[t["customer_name"]] = t["monthly_revenue_usd"]
    return sum(customers.values())


def open_security_tickets(enriched, by_id):
    return [tid for tid, e in enriched.items()
            if by_id[tid]["status"] != "resolved" and SECURITY_FLAGS & set(e["risk_flags"])]


def oldest_open_investigation_hours(enriched, by_id, now):
    """Age of the oldest unresolved payment investigation — the number an ops
    lead actually chases."""
    ages = [(now - by_id[tid]["created_at"]).total_seconds() / 3600
            for tid, e in enriched.items()
            if e["ops_workflow"] == "payment_investigation"
            and by_id[tid]["status"] != "resolved"]
    return round(max(ages), 1) if ages else None


def detection_lag_hours(cluster, by_id):
    """First report → burst threshold (3rd ticket): how long the pattern was
    live before the tool would have declared it."""
    times = sorted(by_id[tid]["created_at"] for tid in cluster["member_ids"]
                   if tid in by_id)
    if len(times) < 3:
        return None
    return round((times[2] - times[0]).total_seconds() / 3600, 1)


def segment_health(enriched, by_id):
    rows = {}
    for tid, e in enriched.items():
        t = by_id[tid]
        r = rows.setdefault(e["segment"], {"segment": e["segment"], "n": 0,
                                           "_res": [], "_csat": []})
        r["n"] += 1
        if t["resolution_time_hours"] is not None:
            r["_res"].append(t["resolution_time_hours"])
        if t["csat_score"] is not None:
            r["_csat"].append(t["csat_score"])
    out = []
    for r in sorted(rows.values(), key=lambda r: -r["n"]):
        out.append({"segment": r["segment"], "n": r["n"],
                    "avg_resolution_h": round(sum(r["_res"]) / len(r["_res"]), 1) if r["_res"] else None,
                    "avg_csat": round(sum(r["_csat"]) / len(r["_csat"]), 1) if r["_csat"] else None})
    return out


def deflection_candidates(enriched, by_id, top_n=10):
    themes = {}
    for tid, e in enriched.items():
        if e["segment"] != "faq":
            continue
        t = by_id[tid]
        g = themes.setdefault(e["theme"], {"theme": e["theme"], "count": 0,
                                           "customers": set(), "_res": []})
        g["count"] += 1
        g["customers"].add(t["customer_name"])
        if t["resolution_time_hours"] is not None:
            g["_res"].append(t["resolution_time_hours"])
    out = []
    for g in sorted(themes.values(), key=lambda g: -g["count"])[:top_n]:
        med = statistics.median(g["_res"]) if g["_res"] else 0.0
        out.append({"theme": g["theme"], "count": g["count"],
                    "customers": len(g["customers"]),
                    "median_h": round(med, 1),
                    "hours_saved": round(g["count"] * med, 1)})
    return out


# ----------------------------------------------------------------- render --

_CSS = """
:root { color-scheme: light;
  --surface:#fcfcfb; --card:#f4f3f0; --line:#e3e2de;
  --ink-1:#0b0b0b; --ink-2:#52514e; --ink-3:#8b8a85;
  --bar:#2a78d6; --critical:#d03b3b; --serious:#ec835a; --good:#0ca30c; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  color-scheme: dark;
  --surface:#1a1a19; --card:#242422; --line:#383835;
  --ink-1:#ffffff; --ink-2:#c3c2b7; --ink-3:#8b8a85;
  --bar:#3987e5; --critical:#e66767; --serious:#ec835a; --good:#0ca30c; } }
:root[data-theme="dark"] { color-scheme: dark;
  --surface:#1a1a19; --card:#242422; --line:#383835;
  --ink-1:#ffffff; --ink-2:#c3c2b7; --ink-3:#8b8a85;
  --bar:#3987e5; --critical:#e66767; --serious:#ec835a; --good:#0ca30c; }
* { box-sizing:border-box; margin:0; }
body { background:var(--surface); color:var(--ink-1);
  font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; padding:32px 20px; }
main { max-width:960px; margin:0 auto; }
h1 { font-size:22px; } h2 { font-size:15px; color:var(--ink-2);
  text-transform:uppercase; letter-spacing:.06em; margin:36px 0 12px; }
.sub { color:var(--ink-3); font-size:13px; margin-top:4px; }
.tiles { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
  gap:12px; margin-top:16px; }
.tile { background:var(--card); border-radius:10px; padding:16px 18px; }
.tile .v { font-size:26px; font-weight:650; letter-spacing:-.01em; }
.tile .l { font-size:12.5px; color:var(--ink-2); margin-top:2px; }
.card { background:var(--card); border-radius:10px; padding:16px 18px; margin:10px 0; }
.badge { display:inline-block; font-size:11.5px; font-weight:700; padding:2px 8px;
  border-radius:99px; letter-spacing:.04em; }
.badge.inc { background:var(--critical); color:#fff; }
.badge.trd { background:var(--serious); color:#1a1a19; }
.meta { color:var(--ink-2); font-size:13px; margin-top:6px; }
.charts { display:flex; gap:16px; flex-wrap:wrap; }
.chart { flex:1 1 320px; background:var(--card); border-radius:10px; padding:14px 16px; }
.chart h3 { font-size:13.5px; color:var(--ink-2); font-weight:600; margin-bottom:8px; }
svg text { font:12px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
table { border-collapse:collapse; width:100%; font-size:13.5px; }
th { text-align:left; color:var(--ink-2); font-weight:600; }
th,td { padding:7px 10px; border-bottom:1px solid var(--line); }
td.num, th.num { text-align:right; font-variant-numeric:tabular-nums; }
#tip { position:fixed; pointer-events:none; background:var(--ink-1); color:var(--surface);
  font-size:12px; padding:4px 8px; border-radius:6px; opacity:0; transition:opacity .1s; }
footer { color:var(--ink-3); font-size:12px; margin-top:40px; }
"""

_TIP_JS = """
const tip = document.getElementById('tip');
document.querySelectorAll('[data-tip]').forEach(el => {
  el.addEventListener('mousemove', e => { tip.textContent = el.dataset.tip;
    tip.style.left = (e.clientX + 12) + 'px'; tip.style.top = (e.clientY - 10) + 'px';
    tip.style.opacity = 1; });
  el.addEventListener('mouseleave', () => tip.style.opacity = 0);
});
"""


def _fmt_money(v):
    return f"${v / 1000:,.1f}k" if v >= 1000 else f"${v:,.0f}"


def _bar_chart(title, rows, value_key, fmt, tip_fmt):
    """Horizontal single-hue bars: thin marks, data-end rounded 4px, direct
    value labels in ink (never series color), recessive baseline."""
    rows = [r for r in rows if r[value_key] is not None]
    if not rows:
        return ""
    vmax = max(r[value_key] for r in rows) or 1
    bar_h, gap, label_w, chart_w = 18, 10, 150, 560
    height = len(rows) * (bar_h + gap) + 6
    parts = [f'<div class="chart"><h3>{title}</h3>',
             f'<svg viewBox="0 0 {chart_w} {height}" role="img" aria-label="{title}">']
    for i, r in enumerate(rows):
        y = i * (bar_h + gap)
        w = max((r[value_key] / vmax) * (chart_w - label_w - 70), 3)
        path = (f"M{label_w},{y} h{w - 4:.1f} q4,0 4,4 v{bar_h - 8} q0,4 -4,4 "
                f"h-{w - 4:.1f} z")
        parts.append(
            f'<text x="{label_w - 8}" y="{y + bar_h / 2 + 4}" text-anchor="end" '
            f'fill="var(--ink-2)">{r["segment"]}</text>'
            f'<path d="{path}" fill="var(--bar)" data-tip="{tip_fmt(r)}"></path>'
            f'<text x="{label_w + w + 8:.1f}" y="{y + bar_h / 2 + 4}" '
            f'fill="var(--ink-1)">{fmt(r[value_key])}</text>')
    parts.append(f'<line x1="{label_w}" y1="0" x2="{label_w}" y2="{height - 4}" '
                 f'stroke="var(--line)" stroke-width="1"/></svg></div>')
    return "".join(parts)


def _closure_line(c, by_id, actions, events):
    """spec §3.5: current closure state + time-to-close beside time-to-declare.
    `closed` is earned — the theme must have gone quiet before it counts."""
    if not actions and not events:
        return ""
    member_times = [by_id[t]["created_at"] for t in c["member_ids"] if t in by_id]
    dataset_end = max(t["created_at"] for t in by_id.values())
    subsided = volume_subsided(member_times, dataset_end)
    state, _ = closure_state(c["cluster_id"], actions, events, subsided=subsided)
    if state is None:
        return ""
    ttc = time_to_close_hours(c["cluster_id"], actions, min(member_times))
    ttc_txt = f" · time-to-close {ttc:.0f}h" if ttc is not None else ""
    quiet_txt = "" if subsided else " (theme still active — cannot close)"
    return f' · closure: <strong>{state}</strong>{ttc_txt}{quiet_txt}'


def _pattern_card(c, kind_label, badge_cls, icon, lag_h=None, closure=""):
    window = f'{str(c["first_seen"])[:16]} → {str(c["last_seen"])[:16]}'
    lag = (f' · declared on the 3rd ticket, {lag_h}h after first report'
           if lag_h is not None else '')
    return (f'<div class="card"><span class="badge {badge_cls}">{icon} {kind_label}</span> '
            f'<strong>{c["cluster_id"]}</strong> · {c["theme"]}'
            f'<div class="meta">{len(c["member_ids"])} tickets · '
            f'{len(c["customers"])} customers · avg CSAT {c["avg_csat"]} · {window}{lag}{closure}</div></div>')


def generate_html(enriched, by_id, clusters, week, actions=(), events=()):
    sf = stuck_funds(enriched, by_id)
    exposure = risk_exposure(enriched, by_id)
    sec_open = open_security_tickets(enriched, by_id)
    health = segment_health(enriched, by_id)
    defl = deflection_candidates(enriched, by_id)
    incidents, trends = clusters["incidents"], clusters["trends"]

    latest = max(t["created_at"] for t in by_id.values())
    oldest_case = oldest_open_investigation_hours(enriched, by_id, now=latest)
    tiles = "".join(
        f'<div class="tile"><div class="v">{v}</div><div class="l">{l}</div></div>'
        for v, l in [
            (_fmt_money(sf), "Stuck inbound funds (unresolved, stated in tickets)"),
            (_fmt_money(exposure), "MRR exposed to open security risk"),
            (len(sec_open), "Open security-flagged tickets"),
            (f"{oldest_case:.0f}h" if oldest_case else "—",
             "Oldest open payment investigation"),
            (f"{len(incidents)} + {len(trends)}", "Active incidents + trends"),
        ])

    cards = "".join(_pattern_card(c, "INCIDENT", "inc", "&#9650;",
                                  detection_lag_hours(c, by_id),
                                  _closure_line(c, by_id, list(actions), list(events)))
                    for c in incidents)
    cards += "".join(_pattern_card(c, "TREND", "trd", "&#9888;", None,
                                   _closure_line(c, by_id, list(actions), list(events)))
                     for c in trends)

    charts = ('<div class="charts">'
              + _bar_chart("Avg resolution by segment (hours, resolved tickets)",
                           health, "avg_resolution_h", lambda v: f"{v:.0f}h",
                           lambda r: f'{r["segment"]}: {r["avg_resolution_h"]}h over {r["n"]} tickets')
              + _bar_chart("Avg CSAT by segment (scored tickets)",
                           health, "avg_csat", lambda v: f"{v:.1f}",
                           lambda r: f'{r["segment"]}: CSAT {r["avg_csat"]}, n={r["n"]}')
              + "</div>")

    health_rows = "".join(
        f'<tr><td>{r["segment"]}</td><td class="num">{r["n"]}</td>'
        f'<td class="num">{r["avg_resolution_h"] if r["avg_resolution_h"] is not None else "—"}</td>'
        f'<td class="num">{r["avg_csat"] if r["avg_csat"] is not None else "—"}</td></tr>'
        for r in health)
    defl_rows = "".join(
        f'<tr><td>{d["theme"]}</td><td class="num">{d["count"]}</td>'
        f'<td class="num">{d["customers"]}</td><td class="num">{d["median_h"]}</td>'
        f'<td class="num">{d["hours_saved"]}</td></tr>'
        for d in defl)

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ops Brief {week}</title><style>{_CSS}</style></head><body><main>
<h1>Ops Weekly Brief — {week}</h1>
<div class="sub">Money and risk first; support hygiene second. Generated by metrics.py.</div>

<h2>Exposure</h2>
<div class="tiles">{tiles}</div>
{cards}

<h2>Support health</h2>
{charts}
<div class="card"><table>
<tr><th>segment</th><th class="num">tickets</th><th class="num">avg res (h)</th><th class="num">avg CSAT</th></tr>
{health_rows}</table></div>

<h2>Deflection candidates (top repeat FAQs)</h2>
<div class="card"><table>
<tr><th>theme</th><th class="num">tickets</th><th class="num">customers</th>
<th class="num">median h</th><th class="num">hours saved if deflected</th></tr>
{defl_rows}</table></div>

<footer>Self-contained brief · no external requests · dark mode follows your system.</footer>
</main><div id="tip"></div><script>{_TIP_JS}</script></body></html>"""


# -------------------------------------------------------------------- cli --

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--enriched", default="out/enriched.jsonl")
    ap.add_argument("--clusters", default="out/clusters.json")
    ap.add_argument("--data", default="data/tickets.csv")
    ap.add_argument("--mapping", default="out/theme_mapping.json")
    ap.add_argument("--out", default="reports")
    args = ap.parse_args(argv)

    from src.adapters.csv_adapter import CsvAdapter
    from src.theme_registry import apply_theme_mapping

    by_id = {t["ticket_id"]: t for t in CsvAdapter(args.data).fetch_tickets()}
    enriched = {}
    with open(args.enriched) as f:
        for line in f:
            e = json.loads(line)
            enriched[e["ticket_id"]] = e
    mp = Path(args.mapping)
    if mp.exists():
        enriched = apply_theme_mapping(enriched, json.loads(mp.read_text()))
    clusters = json.loads(Path(args.clusters).read_text())

    def _jsonl(p):
        f = Path(p)
        return [json.loads(l) for l in f.read_text().splitlines() if l.strip()] if f.exists() else []
    actions = _jsonl("out/actions.jsonl")
    events = [dict(e, created_at=e.get("created_at") or e.get("ts"))
              for e in _jsonl("out/events.jsonl")]

    latest = max(t["created_at"] for t in by_id.values())
    week = f"{latest.isocalendar().year}-W{latest.isocalendar().week:02d}"
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"ops-brief-{week}.html"
    path.write_text(generate_html(enriched, by_id, clusters, week,
                                  actions=actions, events=events))
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
