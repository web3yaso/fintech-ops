# Deck narration script — ~3 minutes, 8 slides

Spoken English, one block per slide. Advance on the **[→]** marker.
Total ≈ 2:50 at a calm pace; cut the bracketed optional lines to hit 2:30.

---

## Slide 1 · Cover (~15s)

"This is Ops Control Tower — one human loop owner plus an AI execution
layer. The one-line thesis: real agent leverage is structural, not
conversational. That row of chips at the bottom is a real state machine
from the tool — notice the last state says *earned, not declared*. We'll
come back to that. **[→]**"

## Slide 2 · Q1 — Problem (~25s)

"First, the problem I chose. Ops integrates more information than any other
role, but it still works one ticket at a time. In this dataset, thirty-eight
of a hundred tickets aren't support work at all. A four-day card outage
lived as fourteen separate tickets under fourteen different subject lines.
Three hundred forty-two thousand dollars of wires sat stuck across nine
more. A three-week churn trend scored CSAT 1.67 eleven times in a row. And
a probable account takeover hid under the subject line 'Quick question.'
None of these ever reached the people who owned them. Ops doesn't need a
faster version of the old way of working — it needs an AI-native one. **[→]**"

## Slide 3 · Q2 — Why (~25s)

"Here's the same failure as a picture. On the left, the old shape: functions
own columns, problems travel by handoff — and look at the dashed cells:
engineering was never told, and the FX churn signal *never reached product
at all*. On the right, the transposed shape: one loop, one owner. Sophie —
the green cells — owns each problem end to end, and agents fill every cell
that used to be a handoff. Same grid, and this time the churn loop reaches
Mei in product. [Why start in ops? Highest volume, densest information —
and every ticket is a free training signal.] **[→]**"

## Slide 4 · Q3 — The system (~25s)

"How it works. The whole team shares one set of agents instead of everyone
prompting alone. Underneath is a deterministic pipeline — LLM enrichment
into a validated schema, burst and trend detectors, and a priority score
that shows its own formula. Agents only consume what the pipeline computed;
they never re-derive it. The four agents live in a war room built on
OpenMausBot — an open-source MIT desktop app where every bot is a real
Claude CLI process. I seeded it through its own local API: zero forking,
the signed binary untouched, and the shell carries no business logic — the
intelligence lives in version-controlled files. And note the human gates:
escalation, customer drafts, and skill changes all stop at a named person.
**[→]**"

## Slide 5 · Q3 — Caught live, tracked to closed (~25s)

"Detection is live: the card incident was declared on the third arriving
ticket, seven hours in — the real team worked those as separate cases for
three days. But found is not fixed. Every pattern carries a closure state
machine, and *closed* has to be earned: the theme's ticket volume must
actually return to baseline. That's why INC-001 shows a time-to-close,
while INC-002 refuses to close — its theme was still producing tickets.
This is state tracking, not fix verification — and the send button is
never the AI's. **[→]**"

## Slide 6 · Q3 — Four learning channels (~25s)

"The team learns on four channels, each with the right authority.
Corrections are role-gated in code, and one correction becomes an override,
a few-shot example, and an eval case in a single step. Coaching lands in
capped, git-audited notes. Agents self-learn into their own knowledge files
— facts only, never rules; that separation is the prompt-injection
firewall — and they commit under their own git author. And the skills
themselves evolve humans-only. The numbers underneath are the proof: two
staff corrections lifted segment accuracy from 75 to 96 percent — and the
same eval run caught a coaching side effect. Detection is now fourteen of
fourteen, nine of nine, eleven of eleven, zero false positives. **[→]**"

## Slide 7 · Q4 — Assumptions (~20s)

"My core assumption is a team design. Four agent roles doing execution,
and three human roles doing judgment: a loop owner, a platform specialist
who encodes expertise into playbooks, and a loop manager who approves
anything outbound. In this demo one operator wears all three hats — and
the roster's four role gates are exactly the seams where those hats split
at scale. **[→]**"

## Slide 8 · Q5 — Close (~15s)

"With more time: a live dashboard, eval-driven skill optimization, and
human-gated outbound replies. But the claim stands as built: real agent
leverage is structural, not conversational. You can verify that in two
seconds — the console snapshot in the repo is a real run, and everything
you just saw reproduces from one verified script. Thank you."

---

**Delivery notes:** slow down on "earned, not declared" (s1), "never
reached product" (s3), "zero forking, the signed binary untouched" (s4),
and the closing thesis (s8). If pairing with the live war-room footage,
this deck script plays as the intro (slides 1-3), then cut to the live
demo, then return for slides 6-8.
