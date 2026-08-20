"""Theme canonicalization (batch): independent enrichment calls fragment
theme slugs (9 wire tickets -> 7 slugs in the first real run), so clustering
needs a merge pass. Contract: src/theme_registry.py
  canonicalize(theme_counts, client) -> {variant: canonical}
  apply_theme_mapping(enriched, mapping) -> new enriched dict
Guarantees: every input theme is a key; every canonical is one of the input
themes; on invalid client output fall back to identity (fail open)."""
import json

from src.theme_registry import apply_theme_mapping, canonicalize


def test_merges_variants_to_most_common(counting=None):
    counts = {"incoming_wire_delay": 3, "funds_transfer_missing": 1, "payments_missing": 1,
              "cards_online_declines": 5}
    mapping = canonicalize(counts, client=lambda p: json.dumps({
        "incoming_wire_delay": "incoming_wire_delay",
        "funds_transfer_missing": "incoming_wire_delay",
        "payments_missing": "incoming_wire_delay",
        "cards_online_declines": "cards_online_declines",
    }))
    assert mapping["funds_transfer_missing"] == "incoming_wire_delay"
    assert mapping["cards_online_declines"] == "cards_online_declines"


def test_invalid_canonical_falls_back_to_identity():
    counts = {"a_theme": 2, "b_theme": 1}
    # client maps to a slug that is not among the inputs -> reject, identity
    mapping = canonicalize(counts, client=lambda p: json.dumps(
        {"a_theme": "made_up_new_theme", "b_theme": "a_theme"}))
    assert mapping == {"a_theme": "a_theme", "b_theme": "b_theme"}


def test_missing_key_falls_back_to_identity():
    counts = {"a_theme": 2, "b_theme": 1}
    mapping = canonicalize(counts, client=lambda p: json.dumps({"a_theme": "a_theme"}))
    assert mapping == {"a_theme": "a_theme", "b_theme": "b_theme"}


def test_single_theme_skips_llm_call():
    calls = []
    mapping = canonicalize({"only_theme": 4}, client=lambda p: calls.append(p))
    assert mapping == {"only_theme": "only_theme"} and calls == []


def test_examples_are_included_in_merge_prompt():
    seen = []

    def client(prompt):
        seen.append(prompt)
        return json.dumps({"missing_wire": "missing_wire", "incoming_wire_delay": "incoming_wire_delay"})

    canonicalize({"missing_wire": 1, "incoming_wire_delay": 3}, client,
                 examples={"missing_wire": "A $64k incoming USD wire has been missing since Friday",
                           "incoming_wire_delay": "Customer's USD wire sent but not arrived"})
    assert "missing since Friday" in seen[0]


def test_apply_theme_mapping_rewrites_without_mutating():
    enriched = {"T1": {"ticket_id": "T1", "theme": "payments_missing"},
                "T2": {"ticket_id": "T2", "theme": "cards_online_declines"}}
    out = apply_theme_mapping(enriched, {"payments_missing": "incoming_wire_delay",
                                         "cards_online_declines": "cards_online_declines"})
    assert out["T1"]["theme"] == "incoming_wire_delay"
    assert enriched["T1"]["theme"] == "payments_missing"  # input untouched
