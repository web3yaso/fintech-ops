"""Skill-change proposals — the only path by which SKILL.md evolves.
Agents PROPOSE (exact old→new text + rationale); only a human holding
`approve_skill_changes` APPLIES or REJECTS, by running this CLI themselves.
Agents never edit skills, approved or not.

    # agent side (propose only)
    python -m src.skill_proposals propose --agent liaison --skill ticket-triage \
        --old "<exact current text>" --new "<replacement>" --rationale "<why>"
    python -m src.skill_proposals list

    # human side
    python -m src.skill_proposals apply  --id SCP-001 --as sophie
    python -m src.skill_proposals reject --id SCP-001 --as sophie --reason "<why>"
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

DEFAULT_PATH = Path("feedback/skill_proposals.jsonl")


def _skill_path(skill, root):
    return Path(root) / ".claude/skills" / skill / "SKILL.md"


def _load(path):
    p = Path(path)
    if not p.exists():
        return []
    with open(p) as f:
        return [json.loads(line) for line in f if line.strip()]


def _save(records, path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def propose(agent, skill, old, new, rationale, root=".", path=DEFAULT_PATH):
    f = _skill_path(skill, root)
    if not f.exists():
        raise ValueError(f"no such skill: {skill}")
    if not old or old not in f.read_text():
        raise ValueError("`old` must quote text that exists verbatim in the target SKILL.md")
    if not (new or "").strip() or not (rationale or "").strip():
        raise ValueError("proposal needs replacement text and a rationale")
    records = _load(path)
    rec = {"id": f"SCP-{len(records) + 1:03d}",
           "ts": datetime.now().isoformat(timespec="seconds"),
           "agent": agent, "skill": skill, "old": old, "new": new,
           "rationale": rationale, "status": "proposed"}
    records.append(rec)
    _save(records, path)
    return rec


def list_pending(path=DEFAULT_PATH):
    return [r for r in _load(path) if r["status"] == "proposed"]


def _authorize(handle, roster):
    people = (roster or {}).get("people", [])
    me = next((p for p in people if p.get("handle") == handle), None)
    if not me or "approve_skill_changes" not in me.get("roles", []):
        raise PermissionError(f"'{handle}' does not hold approve_skill_changes")


def apply_proposal(pid, approver, roster, root=".", path=DEFAULT_PATH):
    _authorize(approver, roster)
    records = _load(path)
    rec = next((r for r in records if r["id"] == pid), None)
    if not rec or rec["status"] != "proposed":
        raise ValueError(f"no pending proposal {pid}")
    f = _skill_path(rec["skill"], root)
    text = f.read_text()
    if rec["old"] not in text:
        raise ValueError(f"{pid}: target text has drifted since proposal — re-propose against current SKILL.md")
    f.write_text(text.replace(rec["old"], rec["new"], 1))
    rec.update(status="approved", approver=approver,
               decided_at=datetime.now().isoformat(timespec="seconds"))
    _save(records, path)
    return rec


def reject(pid, approver, roster, reason, path=DEFAULT_PATH):
    _authorize(approver, roster)
    records = _load(path)
    rec = next((r for r in records if r["id"] == pid), None)
    if not rec or rec["status"] != "proposed":
        raise ValueError(f"no pending proposal {pid}")
    rec.update(status="rejected", approver=approver, reason=reason,
               decided_at=datetime.now().isoformat(timespec="seconds"))
    _save(records, path)
    return rec


def main(argv=None):
    from src.corrections import load_roster
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    pp = sub.add_parser("propose")
    for a in ["--agent", "--skill", "--old", "--new", "--rationale"]:
        pp.add_argument(a, required=True)
    sub.add_parser("list")
    for name in ["apply", "reject"]:
        sp = sub.add_parser(name)
        sp.add_argument("--id", required=True)
        sp.add_argument("--as", dest="approver", required=True)
        if name == "reject":
            sp.add_argument("--reason", required=True)
    args = ap.parse_args(argv)

    if args.cmd == "propose":
        rec = propose(args.agent, args.skill, args.old, args.new, args.rationale)
        print(f"{rec['id']} proposed → awaiting a human with approve_skill_changes")
    elif args.cmd == "list":
        pending = list_pending()
        if not pending:
            print("(no pending skill proposals)")
        for r in pending:
            print(f"{r['id']} [{r['agent']} → {r['skill']}] {r['rationale']}\n"
                  f"  - {r['old'][:90]}\n  + {r['new'][:90]}")
    elif args.cmd == "apply":
        rec = apply_proposal(args.id, args.approver, load_roster())
        print(f"{rec['id']} APPLIED to {rec['skill']} by {rec['approver']} — "
              f"now commit: git add -A && git commit -m 'skill({rec['skill']}): {rec['id']} approved by {rec['approver']}'")
    else:
        rec = reject(args.id, args.approver, load_roster(), args.reason)
        print(f"{rec['id']} rejected by {rec['approver']}: {rec['reason']}")


if __name__ == "__main__":
    main()
