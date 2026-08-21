# Deck narration — spoken, ~2:50, 8 slides

Talk, don't read. Every line points at something visible on the slide.
Advance on **[→]**.

---

## 1 · Cover (~15s)

"Hi — I'm Sophie. This is my take-home. I call it Ops Control Tower.

One thing before we start — it's right there on the slide. This isn't a
chatbot that answers tickets. It catches the problems that hide *across*
tickets, and tracks them until they're actually fixed. One person owns every
problem; four agents do the legwork.

See this row of pills down here? That's a real state machine from the tool.
Keep an eye on the last one — 'earned, not declared'. It'll make sense in a
minute. **[→]**"

## 2 · The problem (~25s)

"So, a hundred tickets. Looks like a normal support queue. It isn't.

These four cards are what's hiding inside it.

This outage? Fourteen tickets, four days — and nobody ever said the word
'incident'. This one — three hundred forty grand stuck, payroll blocked.
This trend ran for three weeks. One angry ticket every two days — no single
day ever looked urgent. And my favorite — this ticket's subject line is
'Quick question'. It's probably an account takeover.

Answering tickets faster fixes none of these. That's the line at the
bottom. **[→]**"

## 3 · Why (~25s)

"Same story, as a picture.

Left side is today. Every box is a different person. Work bounces between
them. Now look at the dashed red boxes — engineering? Never told. Product?
Never reached. Eleven complaints, answered eleven times, and the pricing
owner never heard a word.

Right side is my version. The green boxes — that's one human. Me. Owning
each row start to finish. The blue boxes are agents doing everything in
between.

And look at the bottom-right corner. The FX signal actually lands on Mei's
desk this time. Honestly — that one cell is the whole pitch. **[→]**"

## 4 · The system (~25s)

"Under the hood. Four boxes, left to right.

Tickets stream in here — a mock helpdesk replaying the dataset in real
time. The second box is boring on purpose: plain deterministic Python.
Finds incidents, finds trends, scores every ticket — and shows you the
formula.

The interesting one is this box. Four agents living in an actual chat app —
OpenMausBot, open source, MIT. I didn't fork it. Every bot is a real Claude
process, and everything it knows is a file in the repo.

This dashed bar underneath? Whatever the team learns flows back into the
pipeline. And these three pills at the bottom — those are the doors only a
human can open. **[→]**"

## 5 · Caught live, tracked to closed (~25s)

"Here it is actually running.

First decline ticket — eight thirty in the morning. Third similar one lands
at quarter to four, and the tool declares an incident. Seven hours in. The
real team took three days.

But the part I actually care about is the right side. Because finding it
isn't fixing it.

Top row — INC-001 walked the whole way: acked, fix confirmed, customers
told. Four hundred and ten hours, and that number goes on the weekly
report. Bottom row — look at the red pill. It refuses to close. Customers
are still reporting it. The tool will not let anyone call a thing done when
it isn't. **[→]**"

## 6 · Learning (~25s)

"Do the agents get better? Yes — four ways, and each way has a different
boss.

Corrections — only ops can make those. Coaching — one rule at a time, hard
cap. The green card — agents teach themselves, journals every night. But
facts only. They cannot rewrite their own rules. Which is the fourth card:
changing an agent's job description takes a human. Full stop.

And these tiles are the receipts. Two corrections: seventy-five to
ninety-six percent. This red one? Same test caught a correction making
something *else* worse — the scale weighs both directions. And this green
one — every planted pattern in the dataset, found, zero false alarms.
**[→]**"

## 7 · Assumptions (~20s)

"So what am I actually assuming? Honestly — a team shape.

Four agent jobs on top. Three human jobs underneath: someone runs the
loops, someone writes the playbooks, someone signs off on what leaves the
building.

In this demo all three humans are me. But these four pills — they're
permission gates, in code. And they sit exactly where you'd cut this into
three real jobs when the team grows. **[→]**"

## 8 · Close (~15s)

"What's next: a live dashboard. Letting the eval history tune the skills.
And drafted customer replies — human-approved before anything goes out.
Always.

Which brings us back to this line. *Real agent leverage is structural, not
conversational.* All it means is what you just watched: the win was never a
smarter chat window. It's a workflow where nothing falls between people —
one person, four agents, every decision gated, every action on the record.

If you've only got two seconds — open the console snapshot in the repo.
It's a real run. Thanks for watching."

---

**Delivery notes:** point the cursor at what you're naming — the dashed
cells (s3), the red "cannot close" pill (s5), the red tile (s6). Pause a
beat after "It'll make sense in a minute" (s1) and "the whole pitch" (s3);
slow right down on the slogan gloss in s8 — it's the last thing they hear.
If pairing with war-room footage: slides 1–3 as intro, cut to the live
demo, come back for 6–8.
