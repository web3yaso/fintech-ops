"""Per-ticket audit trail: out/actions.jsonl, append-only. Every action an
agent or human takes on a ticket gets one line — who, what, when, which
tickets, which artifact. Agents call the CLI after writing any artifact:

    python -m src.action_log --actor case-worker --action workpackage_filed \
        --tickets TKT-2090 --artifact workpackages/TKT-2090.md --note "..."
    python -m src.action_log --history TKT-2090      # one ticket's trail
    python -m src.action_log --tail 20               # latest activity
"""
import argparse
import json
import re
from datetime import datetime
from pathlib import Path

DEFAULT_PATH = Path("out/actions.jsonl")
_ACTION_RE = re.compile(r"^[a-z][a-z0-9_]{2,40}$")
_TICKET_RE = re.compile(r"^TKT-\d{4}$")


def log_action(actor, action, tickets, artifact=None, note=None, path=DEFAULT_PATH):
    if not actor or not str(actor).strip():
        raise ValueError("actor required")
    if not _ACTION_RE.match(action or ""):
        raise ValueError("action must be snake_case (e.g. workpackage_filed)")
    tickets = list(tickets or [])
    if not tickets or any(not _TICKET_RE.match(t) for t in tickets):
        raise ValueError("tickets must be TKT-NNNN ids")
    rec = {"ts": datetime.now().isoformat(timespec="seconds"),
           "actor": actor, "action": action, "tickets": tickets}
    if artifact:
        rec["artifact"] = artifact
    if note:
        rec["note"] = note
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def _load(path=DEFAULT_PATH):
    p = Path(path)
    if not p.exists():
        return []
    with open(p) as f:
        return [json.loads(line) for line in f if line.strip()]


def history(ticket_id, path=DEFAULT_PATH):
    return [e for e in _load(path) if ticket_id in e.get("tickets", [])]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--actor")
    ap.add_argument("--action")
    ap.add_argument("--tickets", nargs="+")
    ap.add_argument("--artifact")
    ap.add_argument("--note")
    ap.add_argument("--history", metavar="TKT-NNNN")
    ap.add_argument("--tail", type=int)
    ap.add_argument("--path", default=str(DEFAULT_PATH))
    args = ap.parse_args(argv)

    if args.history:
        entries = history(args.history, path=args.path)
        if not entries:
            print(f"(no recorded actions for {args.history})")
        for e in entries:
            print(f"{e['ts']}  {e['actor']:16} {e['action']:22} "
                  f"{e.get('artifact', '')} {('— ' + e['note']) if e.get('note') else ''}")
        return
    if args.tail:
        for e in _load(args.path)[-args.tail:]:
            print(f"{e['ts']}  {e['actor']:16} {e['action']:22} {','.join(e['tickets'])}")
        return
    rec = log_action(args.actor, args.action, args.tickets,
                     args.artifact, args.note, path=args.path)
    print(f"logged: {rec['actor']} {rec['action']} {','.join(rec['tickets'])}")


if __name__ == "__main__":
    main()
