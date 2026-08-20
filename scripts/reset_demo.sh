#!/bin/bash
# Reset processing records to a chosen depth. Run from fintech-ops/.
#
#   scripts/reset_demo.sh logs        # ① 只清运行日志：actions/events/queue/clusters
#   scripts/reset_demo.sh artifacts   # ② ① + agent 工件（卡/包/简报）——重录完整流程用
#   scripts/reset_demo.sh room        # ③ 清空 war room 聊天（删群重建，bot 不动）
#   scripts/reset_demo.sh all         # ①+②+③
#
# 永不自动删除（要删请手动，想清楚）：
#   out/enriched.jsonl / out/theme_mapping.json  — enrichment 缓存（重跑要花 API 钱，
#                                                  且缓存保证演示确定性）
#   feedback/corrections.jsonl                   — 纠错记录（eval before/after 的依据）
#   eval/*                                       — golden 与两份报告
set -euo pipefail
cd "$(dirname "$0")/.."
MODE="${1:-logs}"

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
