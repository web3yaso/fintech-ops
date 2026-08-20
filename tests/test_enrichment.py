"""Enrichment wrapper logic (spec §4) — LLM-free via injected client.
Contract: src/enrichment.py
  enrich_ticket(ticket, client, few_shot=()) -> dict (validated enrichment,
      or needs_human=True fallback after 1 retry)
  build_prompt(ticket, few_shot) -> str
client contract: callable(prompt: str) -> str (raw model text)."""
import json

import pytest

VALID = {
    "ticket_id": "TKT-2001", "segment": "faq", "ops_workflow": "faq_selfserve",
    "theme": "faq_user_permissions", "severity": 1, "risk_flags": [],
    "amount_usd": None, "summary": "How-to: view-only bookkeeper access",
    "suggested_action": "Send help-center link",
}

from src.enrichment import build_prompt, enrich_ticket


@pytest.fixture()
def ticket(by_id):
    return by_id["TKT-2001"]


def test_valid_response_parsed(ticket):
    out = enrich_ticket(ticket, client=lambda p: json.dumps(VALID))
    assert out["segment"] == "faq"
    assert out["theme"] == "faq_user_permissions"
    assert out["needs_human"] is False


def test_invalid_then_valid_retries_once(ticket):
    calls = []

    def client(prompt):
        calls.append(prompt)
        return "not json at all" if len(calls) == 1 else json.dumps(VALID)

    out = enrich_ticket(ticket, client=client)
    assert len(calls) == 2
    assert out["needs_human"] is False
    assert out["ops_workflow"] == "faq_selfserve"


def test_twice_invalid_falls_back_to_needs_human(ticket):
    bad = dict(VALID, severity=9)  # out of 1-4 range: schema must reject
    out = enrich_ticket(ticket, client=lambda p: json.dumps(bad))
    assert out["needs_human"] is True
    assert out["ticket_id"] == "TKT-2001"


def test_known_themes_offered_for_reuse_in_prompt(ticket):
    # live mode: the registry of already-coined themes is injected so a new
    # ticket about a known symptom reuses the slug instead of coining a variant
    prompt = build_prompt(ticket, known_themes=["cards_online_declines",
                                                "inbound_usd_wire_delay"])
    assert "inbound_usd_wire_delay" in prompt
    assert build_prompt(ticket) != prompt


def test_own_correction_excluded_from_own_prompt(by_id):
    # leave-one-out: when classifying TKT-2092, a correction ABOUT TKT-2092
    # must not appear in the prompt — otherwise before/after eval "generalization"
    # is just reading the answer key.
    shot = {"ticket_id": "TKT-2092", "field": "ops_workflow",
            "was": "card_ops", "should_be": "payment_investigation",
            "note": "n", "author": "s", "date": "2026-08-19"}
    own = build_prompt(by_id["TKT-2092"], few_shot=[shot])
    other = build_prompt(by_id["TKT-2001"], few_shot=[shot])
    assert "TKT-2092:" not in own.split("Ticket:")[0]   # no correction line
    assert "TKT-2092:" in other.split("Ticket:")[0]


def test_few_shot_corrections_appear_in_prompt(ticket):
    shot = {"ticket_id": "TKT-2092", "field": "ops_workflow",
            "was": "card_ops", "should_be": "payment_investigation",
            "note": "refund trace runs on the payment rail", "author": "s", "date": "2026-08-19"}
    prompt = build_prompt(ticket, few_shot=[shot])
    assert "payment_investigation" in prompt and "TKT-2092" in prompt
    assert build_prompt(ticket, few_shot=[]) != prompt
