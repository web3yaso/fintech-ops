"""Seed the OpenMausBot war room through the app's own local API — no code
fork, no store poking, the signed binary stays untouched.

Run with the app open:  .venv/bin/python scripts/seed_openmausbot.py

Idempotent: bots/room are matched by name and patched, never duplicated.
Verified against OpenMausBot 0.1.24 (POST /api/bots · PATCH /api/bots/:id
accepts name/title/description/modelSelection/cwd/composio/computer ·
POST /api/groups · PATCH /api/groups/:id accepts memberIds/defaultResponder/
cwd/bulletin — cwd only before the room's first turn)."""
import json
import sys
import urllib.request
from pathlib import Path

REPO = str(Path(__file__).resolve().parent.parent)
MODEL = {"instanceId": "claude", "model": "claude-sonnet-5"}
ROOM = "Ops War Room"
STANDUP_ROOM = "Ops Standup"
STANDUP_MEMBERS = ["Triage", "Pattern Commander", "Case Worker"]  # ops-internal only
STANDUP_BULLETIN = (
    "Ops team meeting room — weekly review, chaired by sophie (incident "
    "manager). Not for live incidents (that's the War Room). Open the meeting "
    "with: @Triage run the weekly review. Agenda it drives: exposure & risk → "
    "segment health → deflection candidates → open cases → coaching rules.")
BOTS = [
    ("Triage", "Ops dispatcher",
     "Follow .claude/skills/ticket-triage/SKILL.md exactly: run the pipeline, "
     "present the queue, pin risk tickets, record staff corrections into "
     "feedback/corrections.jsonl."),
    ("Pattern Commander", "Incidents & trends",
     "Follow .claude/skills/pattern-commander/SKILL.md exactly: verify clusters, "
     "write incidents/INC-xxx.md and trends/TRD-xxx.md, hand off to Liaison."),
    ("Case Worker", "Ticket deep-dives",
     "Follow .claude/skills/case-worker/SKILL.md exactly: playbook-driven work "
     "packages in workpackages/, customer drafts always last."),
    ("Liaison", "Cross-team handoff",
     "Follow .claude/skills/liaison/SKILL.md exactly: translate confirmed "
     "patterns into knowledge/outbound briefs and file mock-Jira issues."),
]

# Simulated human colleagues (team/roster.json personas). The desktop shell is
# single-operator, so cross-team staff appear as clearly-labeled persona bots:
# visible in the room, answering as humans would — never doing agent work.
PERSONA_RULES = (
    "You are role-playing {name}, a HUMAN colleague on the {team} team — a "
    "clearly-labeled simulation for this demo (team/roster.json). Stay in "
    "character: reply in 1-3 short sentences, like a busy person on chat. "
    "You may read files under knowledge/ to react to briefs addressed to you. "
    "In group rooms never open with a self-introduction — respond directly to the matter at hand. You NEVER run pipelines, write ops artifacts, or act as an AI agent — if "
    "asked to do agent work, redirect to Triage. You cannot author label "
    "corrections: your roster role doesn't include correct_labels{extra}")
# Short names on purpose: the app triggers a teammate only on an exact
# "@Full Name" match in reply text, so names must be typable. The SIMULATED
# disclosure lives in the title, description, and the personas' own replies.
PERSONAS = [
    ("Alex", "SIMULATED persona — engineering on-call",
     PERSONA_RULES.format(name="Alex Osei", team="engineering",
                          extra=". You own incoming incident briefs: acknowledge, ask one "
                                "sharp question, and say what you'll check.")),
    ("Mei", "SIMULATED persona — product, FX pricing owner",
     PERSONA_RULES.format(name="Mei Tanaka", team="product",
                          extra=". You own trend briefs: react to churn evidence and say "
                                "what decision you'd take away.")),
    ("Raj", "SIMULATED persona — compliance",
     PERSONA_RULES.format(name="Raj Patel", team="compliance",
                          extra=", but you DO have coach_agents: you may ask an agent to add "
                                "a NOTES.md rule (e.g. CC compliance on escalations).")),
]
OLD_PERSONA_NAMES = {"Alex · Eng (simulated)": "Alex",
                     "Mei · Product (simulated)": "Mei",
                     "Raj · Compliance (simulated)": "Raj"}


def api(port, method, path, body=None):
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}", method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read() or "{}")


def find_port():
    for port in [8799] + list(range(8790, 8811)):
        try:
            h = api(port, "GET", "/api/health")
            if h.get("app") == "openmausbot":
                return port
        except Exception:
            continue
    sys.exit("OpenMausBot server not found — is the app running?")


def main():
    port = find_port()
    existing = {b["name"]: b for b in api(port, "GET", "/api/bots")["bots"]}
    for old, new in OLD_PERSONA_NAMES.items():   # migrate pre-rename personas
        if old in existing and new not in existing:
            existing[new] = existing.pop(old)
    ids = []
    agent_names = {n for n, _, _ in BOTS}
    for name, title, description in BOTS + PERSONAS:
        bot = existing.get(name) or api(port, "POST", "/api/bots")["bot"]
        patch = {"name": name, "title": title, "description": description,
                 "modelSelection": MODEL, "cwd": REPO,
                 "composio": False, "computer": "off",
                 # agents auto-approve (their SKILL.md + file contracts are the
                 # guardrail); personas keep approval cards ON — they should
                 # never run commands, so a card popping IS the alarm
                 "autoApprove": name in agent_names}
        api(port, "PATCH", f"/api/bots/{bot['id']}", patch)
        ids.append(bot["id"])
        print(f"bot ready: {name} ({bot['id'][:8]})")

    groups = api(port, "GET", "/api/bots").get("groups", [])  # groups ride along on /api/bots
    room = next((g for g in groups if g.get("name") == ROOM), None)
    if room is None:
        room = api(port, "POST", "/api/groups", {"name": ROOM, "memberIds": ids})["group"]
        print(f"room created: {ROOM} ({room['id'][:8]})")
    patch = {"memberIds": ids, "defaultResponder": {"kind": "mentions"},
             "bulletin": "AI ops team + simulated cross-team colleagues (Alex=eng, "
                         "Mei=product, Raj=compliance — staged personas, see "
                         "team/roster.json). Handoffs happen by exact @Full Name "
                         "mention: @Triage @Pattern Commander @Case Worker @Liaison "
                         "@Alex @Mei @Raj. Start with: @Triage process today's tickets."}
    if room.get("pinnedCwd") is None:
        patch["cwd"] = REPO
    api(port, "PATCH", f"/api/groups/{room['id']}", patch)
    print(f"room ready: {ROOM} · members={len(ids)} · responder=mentions")

    # ops-internal meeting room (weekly review) — agents only, no personas
    name_to_id = {}
    for b in api(port, "GET", "/api/bots")["bots"]:
        name_to_id.setdefault(b["name"], b["id"])
    standup_ids = [name_to_id[n] for n in STANDUP_MEMBERS if n in name_to_id]
    standup = next((g for g in api(port, "GET", "/api/bots").get("groups", [])
                    if g.get("name") == STANDUP_ROOM), None)
    if standup is None:
        standup = api(port, "POST", "/api/groups",
                      {"name": STANDUP_ROOM, "memberIds": standup_ids})["group"]
        print(f"room created: {STANDUP_ROOM} ({standup['id'][:8]})")
    spatch = {"memberIds": standup_ids, "defaultResponder": {"kind": "mentions"},
              "bulletin": STANDUP_BULLETIN}
    if standup.get("pinnedCwd") is None:
        spatch["cwd"] = REPO
    api(port, "PATCH", f"/api/groups/{standup['id']}", spatch)
    print(f"room ready: {STANDUP_ROOM} · members={len(standup_ids)} · responder=mentions")

    # self-evolution routines (Loops 1 & 3) — one nightly journal and one
    # weekly digest per agent; idempotent by routine name
    existing_routines = {r["name"] for r in api(port, "GET", "/api/routines")["routines"]}
    for name in agent_names:
        bid = name_to_id.get(name)
        if not bid:
            continue
        jname = f"{name} — nightly journal"
        if jname not in existing_routines:
            api(port, "POST", "/api/routines", {
                "name": jname, "botId": bid, "runOn": "maus", "enabled": True,
                "schedule": {"type": "daily", "time": "21:30",
                             "weekdays": [0, 1, 2, 3, 4, 5, 6]},
                "prompt": "Write your journal (Loop 1 in your SKILL.md's "
                          "self-evolution section): review today's actions, "
                          "corrections and room messages; update KNOWLEDGE.md; "
                          "log journal_written."})
            print(f"routine created: {jname} (daily 21:30)")
        if name == "Triage":
            pname = "Triage — daily skill-proposal digest for sophie"
            if pname not in existing_routines:
                api(port, "POST", "/api/routines", {
                    "name": pname, "botId": bid, "runOn": "maus", "enabled": True,
                    "schedule": {"type": "daily", "time": "21:45",
                                 "weekdays": [0, 1, 2, 3, 4, 5, 6]},
                    "prompt": "Run `python -m src.skill_proposals list`. If no "
                              "pending proposals, reply exactly 'No skill "
                              "proposals today.' Otherwise post a digest "
                              "addressed to sophie: for each proposal show id, "
                              "proposer, target skill, rationale, the old→new "
                              "diff, and the ready-to-copy decision commands "
                              "(`python -m src.skill_proposals apply --id SCP-xxx "
                              "--as sophie` / `... reject --id SCP-xxx --as sophie "
                              "--reason \"...\"`). Recommend approve or reject "
                              "for each with one honest sentence — sophie "
                              "decides, you only advise."})
                print(f"routine created: {pname} (daily 21:45)")
        dname = f"{name} — weekly knowledge digest"
        if dname not in existing_routines:
            api(port, "POST", "/api/routines", {
                "name": dname, "botId": bid, "runOn": "maus", "enabled": True,
                "schedule": {"type": "daily", "time": "18:00", "weekdays": [0]},
                "prompt": "Weekly knowledge digest (Loop 3 in your SKILL.md's "
                          "self-evolution section): scan the week's room "
                          "transcripts, corrections, actions and repo changes; "
                          "compress into KNOWLEDGE.md's Weekly digests; prune "
                          "stale entries; log knowledge_added."})
            print(f"routine created: {dname} (Sun 18:00)")

    print("\nVerify:")
    wanted = {n for n, _, _ in BOTS + PERSONAS}
    for b in api(port, "GET", "/api/bots")["bots"]:
        if b["name"] in wanted:
            print(f"  {b['name']:26} model={b['modelSelection']['model']} "
                  f"cwd={'OK' if b.get('cwd') == REPO else b.get('cwd')}")


if __name__ == "__main__":
    main()
