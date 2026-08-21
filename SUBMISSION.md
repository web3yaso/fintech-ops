# Submission — Ops Control Tower
**Loop take-home · Business Operations Associate · Sophie Huang**

> **Try it in 2 seconds:** open `reports/console-snapshot.html` (zero-install
> snapshot of a real run). · 📹 Video: _[link goes here]_ · Weekly brief:
> `reports/ops-brief-2026-W33.html` · Repo: this repository (private —
> reviewer invites issued with the submission email).

Five bullets, one per question asked.

## 1 · What problem I chose to solve

- **Problem.** Ops is the role that must integrate the most information from inside and outside the company — and today it runs the old way: specialist columns, handoffs, one ticket at a time. In the dataset that failure is visible: a 4-day card outage handled as 14 "separate" tickets under 14 subject lines, ≥$342k of wires stuck across 9 more, a three-week churn trend from 10 customers and an account-takeover signal hiding under "Quick question" — none of which ever reached the people who owned them. The problem I chose: ops doesn't need a faster version of the old way of working — it needs an AI-native one. Real agent leverage is structural, not conversational.

## 2 · Why I chose it

- **Why.** I built it as a working sample of the "transposed organization" (blog.sshh.io): the ops generalist becomes a **loop owner** — making decisions, not artifacts — while agents execute the chain. Ops is the best place in a company to start this transition: highest task volume, the most complex information surface, the costliest failure modes for a FINTRAC-registered payments company (undetected incidents, silent churn, buried fraud) — and every ticket generates a natural training signal, because staff corrections become few-shot examples and eval cases automatically.

## 3 · How my solution works

- **How.** The team shares one set of agents instead of each person prompting alone — that's why the prototype runs in OpenMausBot (open-source, MIT): four agent roles (Triage / Pattern Commander / Case Worker / Liaison) live in a shared war room pinned to one workspace, so the agents accumulate maximal context — every ticket, correction, playbook and cross-team brief. Underneath: one deterministic pipeline (LLM enrichment into a validated schema → burst + trend detectors with a precedence rule → an explainable priority score, formula shown in output) whose outputs the agents consume but never re-derive; a git-tracked knowledge folder moves findings to engineering, product and marketing; and every declared pattern carries a closure state machine through to *customers actually notified* — the weekly brief reports **time-to-close beside time-to-declare**, because found is not fixed. Every consequential step is human-gated (escalation, customer drafts, skill changes), and it's measured, not vibed: a 24-ticket eval on the production code path shows two staff corrections lifting segment accuracy **75% → 96%** — and catching a coaching side effect the same run; detection on the full dataset is wires 9/9, FX trend 11/11, declines 14/14 with zero false positives, the 14th member recovered by a human-ratified merge rule sourced from an agent's own journal.

## 4 · Key assumptions I made

- **Assumptions.** The core assumption is a team design: 4 agent roles with defined responsibilities, and 3 human roles — the **loop owner** who runs the queue and makes judgment calls; the **platform specialist** who encodes expertise into playbooks and skills; the **loop manager** who reviews corrections and approves anything outbound. In this single-operator demo one person wears all three hats — the roster's role gates (`correct_labels`, `approve_drafts`, `approve_escalations`, `approve_skill_changes`) are exactly the seams where they split at scale. Plus: ticket text as the only system of record, monthly revenue as the impact proxy, and synthetic data, so no privacy concern in LLM calls.

## 5 · What I would improve with more time

- **With more time.** A live dashboard monitoring agent throughput, accuracy and backlog in real time (the console snapshot becoming a continuously-updated hosted view); systematic skill optimization driven by the eval and correction history (the proposal channel already collects the raw material); closing the loop inside the helpdesk — agents drafting outbound customer replies, gated by human approval before anything leaves the building; and swapping the mock helpdesk for a production adapter — the two-method seam exists, what remains is the unglamorous part (OAuth, webhooks, rate limits, idempotent write-backs).
