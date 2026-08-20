#!/bin/bash
# Reset processing records to a chosen depth. Run from fintech-ops/.
#
#   scripts/reset_demo.sh logs        # (1) run logs only: actions/events/queue/clusters
#   scripts/reset_demo.sh artifacts   # (2) = (1) + agent artifacts (cards/packages/briefs) — for re-recording a full run
#   scripts/reset_demo.sh room        # (3) clear war-room chat (delete + recreate the room; bots untouched)
#   scripts/reset_demo.sh all         # (1)+(2)+(3)
#
# NEVER deleted automatically (remove by hand only, deliberately):
#   out/enriched.jsonl / out/theme_mapping.json  — enrichment cache (re-running costs API money,
#                                                  and the cache keeps demos deterministic)
#   feedback/corrections.jsonl                   — corrections (the basis of the before/after eval)
#   eval/*                                       — golden set and both reports
set -euo pipefail
cd "$(dirname "$0")/.."
MODE="${1:-}"
[[ -n "$MODE" ]] || { echo "usage: $0 [logs|artifacts|room|all] — no default: deleting requires an explicit choice"; exit 1; }

clear_logs() {
  rm -f out/actions.jsonl out/events.jsonl out/ops_queue.json out/clusters.json out/watch_run.log
  echo "✓ logs cleared (actions/events/queue/clusters)"
}

clear_artifacts() {
  rm -f incidents/INC-*.md trends/TRD-*.md workpackages/TKT-*.md
  rm -f knowledge/outbound/eng/*.md knowledge/outbound/product/*.md
  echo "✓ agent artifacts cleared (cards / workpackages / briefs; help-center drafts kept)"
}

clear_room() {
  .venv/bin/python - << 'EOF'
import json, urllib.request

def api(method, path, body=None):
    req = urllib.request.Request(f"http://127.0.0.1:8799{path}", method=method,
        data=json.dumps(body).encode() if body else None,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read() or "{}")

try:
    d = api("GET", "/api/bots")
except Exception:
    raise SystemExit("✗ OpenMausBot not running — start the app, then re-run: scripts/reset_demo.sh room")
g = next((g for g in d.get("groups", []) if g["name"] == "Ops War Room"), None)
if g:
    api("DELETE", f"/api/groups/{g['id']}")
    print("✓ old war room deleted")
EOF
  .venv/bin/python scripts/seed_openmausbot.py > /dev/null
  echo "✓ war room recreated empty (7 members, bulletin, mentions routing)"
}

case "$MODE" in
  logs)      clear_logs ;;
  artifacts) clear_logs; clear_artifacts ;;
  room)      clear_room ;;
  all)       clear_logs; clear_artifacts; clear_room ;;
  *) echo "usage: $0 [logs|artifacts|room|all]"; exit 1 ;;
esac
echo "kept: enriched cache · theme mapping · corrections · eval reports · NOTES.md · roster"
