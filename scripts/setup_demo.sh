#!/bin/bash
# setup_demo.sh — verified setup of the full war-room demo on a reviewer's Mac.
# Written to be READ before it is run (never pipe from the network):
#   * downloads the PINNED official OpenMausBot release and verifies SHA-256,
#     code signature (codesign --verify --deep --strict) and notarization
#     (spctl -a) — aborts on any mismatch; the app binary is never redistributed
#   * no sudo; writes only to ~/Applications and inside this repo
#   * prints its full plan and asks for confirmation; --dry-run touches nothing
#   * without OPENAI_API_KEY it runs --offline: the committed out/ cache renders
#     the queue, cards, work packages and brief at zero API cost
#   * agent autoApprove stays OFF on reviewer machines unless --with-approvals
set -euo pipefail
cd "$(dirname "$0")/.."

VERSION="0.1.24"
DMG_SHA="b8efdf13581b149450fb6aaf72276e28559312e93b0a7f19f96f328a04d677cd"
DMG_URL="https://github.com/milind-soni/openmausbot-releases/releases/download/v${VERSION}/OpenMausBot-${VERSION}.dmg"
TEAM_ID="993D98NH4J"
DRY=0; OFFLINE=0; WITH_APPROVALS=0
for a in "$@"; do case "$a" in
  --dry-run) DRY=1;; --offline) OFFLINE=1;; --with-approvals) WITH_APPROVALS=1;;
  *) echo "usage: $0 [--dry-run] [--offline] [--with-approvals]"; exit 1;;
esac; done

[[ "$(uname -s)/$(uname -m)" == "Darwin/arm64" ]] || {
  echo "This demo setup targets Apple-silicon macOS. Zero-install fallbacks:";
  echo "  open reports/console-snapshot.html   (the run, no setup at all)";
  echo "  open reports/ops-brief-2026-W33.html"; exit 0; }
[[ -n "${OPENAI_API_KEY:-}" ]] || OFFLINE=1

plan() {
cat <<EOF
PLAN (nothing has run yet):
 1. python venv + pip install -r requirements.txt fastapi httpx uvicorn
 2. pytest (68 tests must pass)
 3. download OpenMausBot ${VERSION} dmg → verify SHA-256=${DMG_SHA:0:12}…,
    codesign --deep --strict, spctl notarization, Team ID ${TEAM_ID}
 4. install to ~/Applications (no sudo), launch
 5. seed bots + rooms + routines via the app's LOCAL API (seed_openmausbot.py)
    · autoApprove: $( [[ $WITH_APPROVALS == 1 ]] && echo ON — you asked || echo OFF — approval cards on every command )
 6. mode: $( [[ $OFFLINE == 1 ]] && echo OFFLINE — committed out/ cache, zero API cost || echo LIVE — OPENAI_API_KEY found )
Uninstall: scripts/reset_demo.sh all + drag ~/Applications/OpenMausBot.app to Trash.
EOF
}
plan
[[ $DRY == 1 ]] && { echo "(dry run — exiting)"; exit 0; }
read -r -p "Proceed? [y/N] " yn; [[ "$yn" == y* || "$yn" == Y* ]] || exit 0

python3 -m venv .venv && .venv/bin/pip -q install -r requirements.txt fastapi httpx uvicorn
.venv/bin/python -m pytest -q || { echo "tests failed — aborting"; exit 1; }

TMP="$(mktemp -d)"; DMG="$TMP/OpenMausBot.dmg"
curl -sL -o "$DMG" "$DMG_URL"
echo "${DMG_SHA}  ${DMG}" | shasum -a 256 -c - || { echo "SHA-256 MISMATCH — aborting"; exit 1; }
MNT="$(hdiutil attach -nobrowse "$DMG" | awk -F'\t' 'END{print $NF}')"
APP="$MNT/OpenMausBot.app"
codesign --verify --deep --strict "$APP" || { hdiutil detach "$MNT"; echo "codesign FAILED"; exit 1; }
codesign -dv "$APP" 2>&1 | grep -q "$TEAM_ID" || { hdiutil detach "$MNT"; echo "unexpected Team ID"; exit 1; }
spctl -a -vv "$APP" 2>&1 | grep -q "Notarized" || { hdiutil detach "$MNT"; echo "not notarized"; exit 1; }
mkdir -p ~/Applications && cp -R "$APP" ~/Applications/ && hdiutil detach -quiet "$MNT"
open ~/Applications/OpenMausBot.app && sleep 8

.venv/bin/python scripts/seed_openmausbot.py
if [[ $WITH_APPROVALS == 0 ]]; then
  .venv/bin/python - <<'PY'
import json, urllib.request
def api(m, p, b=None):
    r = urllib.request.Request(f"http://127.0.0.1:8799{p}", method=m,
        data=json.dumps(b).encode() if b else None,
        headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=10).read() or "{}")
for bot in api("GET", "/api/bots")["bots"]:
    if not bot.get("hidden"):
        api("PATCH", f"/api/bots/{bot['id']}", {"autoApprove": False})
print("reviewer default: approval cards ON for every member")
PY
fi
echo "Done. Open the app → Ops War Room → try: @Triage process today's tickets"
[[ $OFFLINE == 1 ]] && echo "(offline mode: bots read the committed out/ cache — no API key used)"
