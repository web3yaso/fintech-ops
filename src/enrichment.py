"""Per-ticket LLM enrichment (spec §4): temperature 0, pydantic-validated,
one retry on validation failure, then needs_human=True. The LLM client is
injected as callable(prompt) -> str so all wrapper logic is testable offline;
make_openai_client() provides the production client."""
import json
import os

from pydantic import ValidationError

from src.schemas import TicketEnrichment

MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")

SYSTEM = """You are the triage classifier for a cross-border fintech ops team.
Classify one support ticket into the exact JSON schema below. Rules:

Segment definitions (pick exactly one):
- faq: generic how-to a help-center article fully answers; nothing
  account-specific to investigate. If segment=faq, ops_workflow MUST be
  faq_selfserve.
- workflow: needs an ops action or investigation on THIS account — fraud
  check, access removal, KYB/verification, tracing or cancelling one payment,
  reconciling one statement.
- incident_candidate: symptom that looks platform-side and could plausibly hit
  multiple customers (cards suddenly declining online, expected incoming wires
  not arriving, dashboards down).
- trend_candidate: recurring dissatisfaction with pricing or product rather
  than a breakage (FX rate/spread complaints) — add churn_risk flag.

Risk cues OVERRIDE surface tone — a subject like "Quick question" can hide an
account takeover:
- unrecognized admin/user/login -> workflow, fraud_ato, severity 4, [ato, access_control]
- departed employee still has access -> workflow, account_admin, severity 4, [access_control]
- account restricted on a live, previously-working account -> workflow, severity 4, [compliance_hold]
- unrecognized charge -> workflow, fraud_ato, severity 4, [fraud]
- BUT routine KYB/onboarding verification delays are NOT compliance holds:
  workflow, kyb_onboarding, severity 3, no flags

Other rules:
- theme: short snake_case symptom slug; the SAME underlying symptom must get
  the SAME theme even when customers word it differently (e.g. every online
  card decline -> "cards_online_declines"). Distinct symptoms get distinct themes.
- severity rubric: 4 = security/fraud/regulatory exposure or >= $100k funds
  impact; 3 = money movement or account function actively blocked;
  2 = degraded experience or financial dissatisfaction; 1 = how-to.
- amount_usd: only a number explicitly present in the text; never infer.
Respond with ONLY the JSON object, no prose."""

SCHEMA_HINT = json.dumps({
    "ticket_id": "TKT-XXXX", "segment": "faq|workflow|incident_candidate|trend_candidate",
    "ops_workflow": "payment_investigation|card_ops|kyb_onboarding|fraud_ato|account_admin|fx_pricing|faq_selfserve",
    "theme": "snake_case_slug", "severity": "1-4", "risk_flags": ["..."],
    "amount_usd": "number or null", "summary": "one line", "suggested_action": "one line",
})


def build_prompt(ticket, few_shot=(), known_themes=()):
    # leave-one-out: a correction about THIS ticket never enters its own
    # prompt — eval generalization must not read the answer key
    few_shot = [c for c in few_shot if c["ticket_id"] != ticket["ticket_id"]]
    parts = [SYSTEM, "", "JSON schema:", SCHEMA_HINT]
    if known_themes:
        parts += ["", "Themes already in use — REUSE one of these if the symptom "
                  "matches; coin a new slug only for a genuinely new symptom:",
                  ", ".join(sorted(known_themes))]
    if few_shot:
        parts += ["", "Staff corrections to learn from (recent mistakes and the correct label):"]
        for c in few_shot:
            parts.append(f"- {c['ticket_id']}: {c['field']} was '{c['was']}', "
                         f"correct is '{c['should_be']}' — {c.get('note', '')}")
    parts += [
        "", "Ticket:",
        json.dumps({
            "ticket_id": ticket["ticket_id"],
            "product": ticket["product"],
            "subject": ticket["ticket_subject"],
            "body": ticket["ticket_body"],
            "status": ticket["status"],
        }),
    ]
    return "\n".join(parts)


def _fallback(ticket):
    return {
        "ticket_id": ticket["ticket_id"], "segment": "workflow",
        "ops_workflow": "account_admin", "theme": f"unclassified_{ticket['ticket_id'].lower().replace('-', '_')}",
        "severity": 2, "risk_flags": [], "amount_usd": None,
        "summary": "Enrichment failed validation twice — route to a human.",
        "suggested_action": "Manual triage", "needs_human": True,
    }


def enrich_ticket(ticket, client, few_shot=(), known_themes=()):
    prompt = build_prompt(ticket, few_shot, known_themes)
    for _ in range(2):  # first try + one retry
        raw = client(prompt)
        try:
            start, end = raw.index("{"), raw.rindex("}") + 1
            data = json.loads(raw[start:end])
            data["ticket_id"] = ticket["ticket_id"]
            out = TicketEnrichment(**data).model_dump()
            out["needs_human"] = False
            return out
        except (ValueError, ValidationError):
            continue
    return _fallback(ticket)


def make_openai_client(model=None):
    """Production client. Honors OPENAI_API_KEY, and OPENAI_BASE_URL for
    OpenAI-compatible endpoints; model via LLM_MODEL (default gpt-4o-mini)."""
    from openai import OpenAI
    api = OpenAI()  # reads OPENAI_API_KEY / OPENAI_BASE_URL from env

    def client(prompt):
        resp = api.chat.completions.create(
            model=model or MODEL, max_tokens=1024, temperature=0,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content

    return client
