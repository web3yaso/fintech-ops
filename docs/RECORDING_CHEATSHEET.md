# Recording cheat sheet — every operator action, in order

Keep this page open on a second screen. You type/click exactly what's below;
everything else happens by itself.

## Phase 0 · Pre-flight (terminal, BEFORE recording — ~10 min)

```bash
caffeinate -dis                          # 1. spare terminal — leave running
curl -s localhost:8799/api/health        # 2. app backend alive? (restart app if not)
scripts/reset_demo.sh all                # 3. wipe logs+artifacts+rooms+DM threads
.venv/bin/python scripts/intro_bots.py   # 4. regenerate landing pages (~5 min)
.venv/bin/python -m pytest               # 5. 71 passed
```
Font ≥14pt · notifications off · browser tab on `reports/ops-brief-2026-W33.html`.

## Phase 1 · Scene 1 — live catch (terminal, ~60s)

```bash
# 6. start the world (clock starts NOW — do this on camera)
.venv/bin/python -m src.mock_helpdesk --cursor 2026-08-03T00:00 --speed 3600 &
# 7. start the watcher; narrate INCIDENT_DECLARED / TREND_DECLARED / RISK_PINNED
.venv/bin/python -m src.triage --watch --from 2026-08-03T00:00 --poll 0.5
# 8. the round trip
curl -s localhost:8900/tickets/TKT-2072 | python3 -m json.tool | grep -A3 labels
```

## Phase 2 · Scene 2 — war room (chat, ~90s). You send FOUR messages:

```
9.  @Triage process today's tickets
        → Triage posts queue, hands off; Pattern Commander auto-writes cards,
          addresses you by name. (Chain stops at you — say: "the chain halts
          exactly where the decision is mine.")

10. @Liaison go ahead — file INC-001, INC-002 and TRD-001 to their owners.
        → briefs + OPS-xxx + @Alex/@Mei fire; Alex acks in human voice.

11. @Case Worker sophie here — two decisions on TKT-2088: (1) agreed, treat it
    as needing a fresh look; log my decision. (2) the customer draft stays
    UNRELEASED until you have the return reason code — log that hold too.
        → say: "the door sometimes says no — that's why it exists."

12. correction: TKT-2090 ops_workflow should be account_admin — statement
    reconciliation, not a payment trace. — sophie   (send to @Triage)
        → Triage records it; mention TKT-2088 replacing TKT-2090 in the queue
          proves last week's correction already re-routed the work.
```

## Phase 3 · Closure beat (terminal, ~15s — say "send button is never the AI's")

```bash
# 13. four human state advances + refresh (copy-paste block from setup doc §2b)
python -m src.action_log --actor liaison --action owner_acked --tickets TKT-2059 --artifact INC-001 --note "Alex acked the brief in the war room"
python -m src.action_log --actor sophie --action draft_approved --tickets TKT-2059 --artifact incidents/INC-001.md --note "canonical customer update released"
python -m src.action_log --actor sophie --action fix_confirmed --tickets TKT-2059 --artifact INC-001 --note "eng confirmed the CNP config rollback"
python -m src.action_log --actor sophie --action customers_notified --tickets TKT-2059 --artifact INC-001 --note "canonical update sent to the 12 affected customers"
.venv/bin/python -m src.metrics    # INC-001 closure cell fills; INC-002 still "cannot close"
```

## Phase 4 · Evolution beats (optional Act 2, ~90s — cut from the bottom)

```bash
# 14. (KEEP) the agent's own learning history + the 13/14→14/14 story
git log --author=ticket-triage --oneline
cat .claude/skills/ticket-triage/KNOWLEDGE.md
# 15. eval before/after side by side
open eval/baseline_report.md eval/after_corrections_report.md
```
```
16. (optional, chat) @Raj should escalation notes CC compliance? If yes, ask
    the right agent to make it a rule.
17. (optional, chat+UI) ask any agent to "file a skill proposal", run the
    digest routine from the Routines UI, reply: approve SCP-001
```

## Phase 5 · Close the video (~10s)

18. Switch to the browser tab: the weekly brief — "$191.5k stuck, who's
    exposed, time-to-close beside time-to-declare. Real agent leverage is
    structural, not conversational."

## Phase 6 · After recording (terminal)

```bash
# 19. re-export deliverables so the repo matches the camera
.venv/bin/python scripts/export_console.py
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless \
  --no-pdf-header-footer --print-to-pdf="$PWD/reports/console-snapshot.pdf" \
  "file://$PWD/reports/console-snapshot.html"
git add -A && git commit -m "post-recording snapshot" && git push
```
20. Paste the video link into `README.md` + `SUBMISSION.md` placeholders → push.
21. Email: body = SUBMISSION.md bullets · attach console-snapshot.html +
    ops-brief HTML · repo invite for reviewers.

**Total: ~13 required actions (7 commands, 4 chat messages, 2 edits) + 4 optional.**
If anything misbehaves mid-take: `scripts/reset_demo.sh all` + restart from
Phase 1 — every take is deterministic.
