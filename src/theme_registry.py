"""Theme canonicalization. Independent per-ticket enrichment calls cannot
converge on slug names (the model never sees what slug another call coined),
so batch mode runs one merge pass over the distinct slugs. Fail open: any
invalid mapping from the model degrades to identity, never breaks the run."""
import json

MERGE_PROMPT = """You are normalizing symptom theme slugs from a support-ticket
classifier. Different tickets about the SAME operational symptom often received
different slugs because each was classified independently — your job is to
merge those. Ask: would an ops person file these under one queue? If yes, merge.
Example: missing_usd_transfer, incoming_wire_not_received, wire_delay and
missing_payment all describe "an expected incoming payment has not arrived" —
one symptom, one slug. Keep genuinely different symptoms separate (a card
decline is not a missing wire).

Respond with ONLY a JSON object mapping EVERY input slug to its canonical slug.
The canonical slug MUST be one of the input slugs (prefer the most frequent
variant). Be aggressive about merging paraphrases; be conservative about
merging different symptoms.

Input slugs (count + one sample ticket summary each):
"""


def canonicalize(theme_counts, client, examples=None, distinctions=(),
                 equivalences=()):
    """distinctions: ratified human knowledge — [{a, b, note?}] pairs that are
    DISTINCT symptoms and must never share a canonical slug. equivalences: the
    mirror — pairs a human confirmed are the SAME symptom, merged regardless
    of the model's output. Both are told to the model up front and enforced
    afterwards; enforcement beats trust in both directions."""
    themes = set(theme_counts)
    identity = {t: t for t in themes}
    if len(themes) < 2:
        return identity
    examples = examples or {}
    lines = [f"- {t} (x{n}): {examples.get(t, '')}".rstrip()
             for t, n in sorted(theme_counts.items(), key=lambda kv: -kv[1])]
    prompt = MERGE_PROMPT + "\n".join(lines)
    active = [d for d in distinctions if d["a"] in themes and d["b"] in themes]
    if active:
        prompt += ("\n\nRatified distinctions (NEVER merge these pairs):\n" +
                   "\n".join(f"- {d['a']} ≠ {d['b']}" +
                             (f" — {d['note']}" if d.get("note") else "")
                             for d in active))
    try:
        raw = client(prompt)
        start, end = raw.index("{"), raw.rindex("}") + 1
        mapping = json.loads(raw[start:end])
    except (ValueError, AttributeError, TypeError):
        return identity
    if set(mapping) != themes or not all(v in themes for v in mapping.values()):
        return identity
    for d in active:  # enforcement beats trust
        if mapping.get(d["a"]) == mapping.get(d["b"]):
            mapping[d["a"]], mapping[d["b"]] = d["a"], d["b"]
    for e in equivalences:
        if e["a"] in themes and e["b"] in themes:
            mapping[e["a"]] = mapping.get(e["b"], e["b"])
    return mapping


def apply_theme_mapping(enriched, mapping):
    out = {tid: dict(e) for tid, e in enriched.items()}
    for e in out.values():
        e["theme"] = mapping.get(e["theme"], e["theme"])
    return out
