# OpenMausBot war-room setup (the tool's UI)

## Installed & verified (done)
- **Version pinned: 0.1.24** (arm64 dmg from `milind-soni/openmausbot-releases`)
- SHA-256: `b8efdf13581b149450fb6aaf72276e28559312e93b0a7f19f96f328a04d677cd`
- Code signature: `Developer ID Application: Milind Soni (993D98NH4J)`,
  notarized, Gatekeeper-accepted (`spctl: source=Notarized Developer ID`)
- Installed at `/Applications/OpenMausBot.app`; local data in `~/.openmausbot`
- We use it ONLY as the chat shell: bots are real `claude` CLI processes.
  Composio app integrations stay OFF — the solution has no Composio dependency.

## Bots & room are seeded by script (done — no manual UI setup)

The app's window is a local web UI over an HTTP API on 127.0.0.1; the seed
script drives that same API — **no code fork** (the signed binary stays
untouched), no poking at private storage files:

```bash
# app must be running; idempotent — matches bots by name, patches, never duplicates
.venv/bin/python scripts/seed_openmausbot.py
```

It creates/updates **7 room members**:

- the **4 agents** — backing CLI **claude** (claude-sonnet-5), **cwd = this
  repo** (shared cwd is what lets all four discover the same
  `.claude/skills/`, queue files, and NOTES.md, zero fork), **Composio off,
  computer off**;
- **3 simulated human colleagues** — "Alex", "Mei", "Raj" — persona bots for
  the cross-team humans in `team/roster.json`. They make the multi-team room
  VISIBLE: they acknowledge briefs addressed to them and react in 1–3 human
  sentences, but never run pipelines or author corrections (their roster
  roles don't include `correct_labels`; the pipeline enforces that gate
  regardless of what any bot says). Names are deliberately short — **the app
  triggers a teammate only on an exact `@Full Name` mention**, so
  "@Alex" must be typable; the SIMULATED disclosure lives in each persona's
  title, description, intro page, and their own replies (and gets said out
  loud in the video).

Plus **two rooms**, both cwd = repo, responder = mentions:

- **"Ops War Room"** (all 7 members) — live incident handling and cross-team
  escalation; personas present because that's where other teams get pulled in.
- **"Ops Standup"** (Triage, Pattern Commander, Case Worker only) — the ops
  team's meeting room, chaired by sophie. Open the meeting with
  `@Triage run the weekly review`: Triage regenerates the brief and presents
  ops-first (exposure → segment health → deflection pick-of-the-week →
  coaching status), **shares one incident + one learning of its own**, then
  hands to PC and CW who do the same with their status recaps. The chair
  shares last; decisions stay with the chair; anything needing escalation
  goes back to the War Room. No Liaison, no personas — internal meetings
  don't ping other teams.

**Self-evolution (three loops, seeded as app routines):** every agent keeps
a `KNOWLEDGE.md` next to its SKILL.md — facts and lessons only, never rules
(that separation is the firewall: chat content can teach facts, it cannot
rewrite behavior). Loop 1: nightly-journal routines at 21:30 daily. Loop 2:
learn-on-correction, always on, same turn as the correction. Loop 3:
weekly-digest routines Sunday 18:00 (transcripts + corrections + actions +
`git log`). All 8 routines are created idempotently by the seed script —
see them under the app's Routines UI; runs only fire while the app is open.
**Agents commit their own KNOWLEDGE.md changes** (path-scoped, agent-named
author, no push): `git log --author=<agent>` is that agent's learning
history; `git revert` undoes a bad lesson. Human coaching and agent
self-learning share one audit story.

**Skill evolution — humans decide, in chat:** agents may file exact old→new
proposals (`python -m src.skill_proposals propose ...`, max 1/agent/day);
Triage's 21:45 daily routine digests pending ones for sophie. She decides
**without leaving the chat**: reply `approve SCP-xxx` or
`reject SCP-xxx: reason`, and Triage executes via the CLI — which can only
apply the diff frozen at proposal time (drift → refused), so execution can't
smuggle content past the decision. Commit lands with sophie as author;
`skill_change_applied` is logged with her instruction quoted. Same trust
model as `@Liaison go ahead`: identity = chat signature in the
single-operator demo, the platform directory in production.

Ops handles (sophie, marcus) are voiced by you, the operator.

**Handoff mechanics (the thing that makes the room talk):** a bot's reply
only triggers a teammate when it contains a whitespace-preceded, exact
`@Full Name` — `@Pattern Commander INC-001 …`, `@Liaison TRD-001 …`,
`@Alex ops filed OPS-101 …`. The agents' SKILL.md files spell out these
exact mention strings; kebab-case skill names (`pattern-commander`) do NOT
match and were the original cause of a silent room.

**Room etiquette:** every member carries a "no self-introductions in the
room" rule — first-turn-in-a-fresh-thread intros are an LLM reflex, and a
freshly reset room triggers it; the rule sends them straight to the work.
Their proper intros live in each profile thread (`scripts/intro_bots.py`).

**Then give every member a proper landing page** (each bot's default thread
otherwise shows the app's generic onboarding):

```bash
.venv/bin/python scripts/intro_bots.py     # idempotent; ~30-60s per member
```

Each member posts a pinned-style intro — Role / What I do / How to work with me —
generated from its own SKILL.md or persona. This doubles as the end-to-end
smoke test: if an intro comes back, that bot's CLI, skills, and cwd all work.
(Run 2026-08-19: 7/7 ok.)

Deeper smoke-test per agent with one working message:

| bot | first message to test |
|---|---|
| **Triage** | `process today's tickets` |
| **Pattern Commander** | `write up INC-001 from out/clusters.json` |
| **Case Worker** | `work TKT-2072` |
| **Liaison** | `brief engineering on INC-001` |

Skill routing is automatic: any claude process with the repo as cwd loads the
four skills; the skill descriptions map these phrases to the right workflow.

## War-room scene (group room "Ops War Room")

Pre-flight: mock helpdesk running
(`.venv/bin/python -m src.mock_helpdesk --cursor 2026-08-03T00:00 --speed 3600`).

**Your identity: you are sophie — the incident manager** (roster role
`approve_escalations`). Bots address you by name when a declared pattern
needs an escalation decision; only you green-light Liaison. Sign corrections
`— sophie`; voice marcus only when demonstrating a second ops member.

**Chain rule (app-enforced, `MAX_GROUP_HOPS = 1`):** one human message buys at
most TWO bot generations — you → botA → whoever botA @-mentions — then the
cascade stops, and each bot speaks at most once per cascade. This maps
exactly onto the incident-manager role: the chain halts right where the
escalation decision is yours — kickoff ② IS the approval. Say so on camera.

1. **Kickoff ① — you:** `@Triage watch the queue` (or `process today's
   tickets`) → Triage narrates + hands off → **Pattern Commander
   auto-fires**: verifies, writes the INC/TRD cards, logs to actions.jsonl,
   ends with @Liaison (which by rule does NOT auto-fire — expected)
2. **Kickoff ② — the escalation decision (you, as incident manager):**
   Triage/PC will have addressed you by name; once the card is up, reply
   `@Liaison go ahead` → Liaison writes the brief ("For: Alex Osei"), files
   OPS-xxx, logs → **Alex auto-fires**: human-voice ack + one sharp question
3. **Kickoff ③ — feedback beat, you → Triage:**
   `correction: TKT-2071 segment should be incident_candidate — expected
   inbound wires that haven't arrived look platform-side. — sophie`
   → Triage appends to `feedback/corrections.jsonl`, logs, confirms
4. **Governance beat (optional):** same correction signed `— alex` → Triage
   records it as audit trail but says the pipeline ignores it until an ops
   role co-signs. Role-gated coaching, live.
5. **Optional ④:** `@Raj weigh in on TKT-2081` → compliance voice; he may ask
   an agent to add a NOTES.md rule (raj holds `coach_agents`)

Diagnosis: silence after Triage = its last line lacked an exact
`@Pattern Commander`; Liaison idle after PC = normal (hop cap — kickoff ②);
personas silent = the mention wasn't exactly `@Alex` / `@Mei` / `@Raj`.

> Cross-team humans are SIMULATED personas from `team/roster.json`, visible
> as clearly-suffixed persona bots; ops handles (sophie, marcus) are voiced
> by the operator. On Slack/Lark the roster maps to the real directory.
> Mechanism real, people staged — say so in the video.

## Verification checklist
- [ ] All 4 bots respond and can read `out/ops_queue.json`
- [ ] Triage's correction line lands in `feedback/corrections.jsonl` with author+date
- [ ] Liaison's issue key comes from the real mock tracker (check `GET /issues`)
- [ ] A NOTES.md rule added in chat shows up in `git diff`
- [ ] Screen-record the room for Scene 2 footage

## Command approvals
The app surfaces every claude tool call as an approval card by default. The
seed script sets **autoApprove=true for the 4 agents** (their SKILL.md and
file contracts are the guardrail; nothing leaves the repo without a human
copying it out) and **leaves approvals ON for the persona bots** — they should
never run commands, so a card popping on a persona IS the alarm. If a card is
already pending when you re-seed, answer it once in the UI; new turns won't
ask again. In production you'd flip this: auto-approve reads, card on writes.

## Known constraints
- The seed script targets the local API shapes verified on **0.1.24**
  (`POST /api/bots`, `PATCH /api/bots/:id`, `POST /api/groups`,
  `PATCH /api/groups/:id`; groups list rides along on `GET /api/bots`) —
  re-verify before bumping the pinned version
- A room's cwd is fixed after its first turn (server enforces this); re-seed
  before chatting if the room cwd is wrong
- If the room misbehaves during recording, `docs/demo.md` Scene 2 has the
  plain-Claude-Code fallback; the UI integration itself remains part of the
  deliverable either way
