"""Mock helpdesk + mock tracker (spec §2): a single-file FastAPI server
seeded from the provided CSV, with a replay clock that releases post-cursor
tickets in created_at order on an accelerated clock. The seams are real; the
server behind them is a stand-in.

    python -m src.mock_helpdesk --cursor 2026-08-03T00:00 --speed 3600

Endpoints:
  GET  /tickets                       tickets visible at current sim time
  GET  /tickets?since=<iso>           visible tickets after cursor
  GET  /tickets?since=<iso>&peek=all  ALL tickets after cursor (clock ignored;
                                      deterministic — used by tests and demos)
  GET  /tickets/{id}                  one ticket + its labels/notes
  POST /tickets/{id}/labels           write-back: merge label dict
  POST /tickets/{id}/notes            write-back: append internal note
  POST /issues                        mock Jira: returns OPS-101, OPS-102, ...
"""
import argparse
import time
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException

from src.adapters.csv_adapter import CsvAdapter


def _iso(s):
    return datetime.fromisoformat(s)


def create_app(csv_path="data/tickets.csv", cursor="2026-08-03T00:00", speed=0.0):
    app = FastAPI(title="mock-helpdesk")
    tickets = CsvAdapter(csv_path).fetch_tickets()   # sorted by created_at
    store = {t["ticket_id"]: {**t, "labels": {}, "notes": []} for t in tickets}
    t0_sim = _iso(cursor)
    t0_wall = time.monotonic()
    issues = []

    def sim_now():
        if speed <= 0:
            return t0_sim
        return t0_sim + timedelta(seconds=(time.monotonic() - t0_wall) * speed)

    def visible(t):
        return t["created_at"] <= sim_now()

    @app.get("/tickets")
    def list_tickets(since: str | None = None, peek: str | None = None):
        rows = tickets
        if since is not None:
            s = _iso(since)
            rows = [t for t in rows if t["created_at"] > s]
        if peek != "all":
            rows = [t for t in rows if visible(t)]
        return [_serialize(store[t["ticket_id"]]) for t in rows]

    @app.get("/tickets/{ticket_id}")
    def get_ticket(ticket_id: str):
        if ticket_id not in store:
            raise HTTPException(404, "no such ticket")
        return _serialize(store[ticket_id])

    @app.post("/tickets/{ticket_id}/labels")
    def write_labels(ticket_id: str, labels: dict):
        if ticket_id not in store:
            raise HTTPException(404, "no such ticket")
        store[ticket_id]["labels"].update(labels)
        return {"ok": True, "labels": store[ticket_id]["labels"]}

    @app.post("/tickets/{ticket_id}/notes")
    def write_note(ticket_id: str, note: dict):
        if ticket_id not in store:
            raise HTTPException(404, "no such ticket")
        store[ticket_id]["notes"].append(note.get("text", ""))
        return {"ok": True, "notes": store[ticket_id]["notes"]}

    @app.post("/issues")
    def create_issue(issue: dict):
        key = f"{issue.get('project', 'OPS')}-{101 + len(issues)}"
        issues.append({**issue, "key": key})
        return {"key": key}

    @app.get("/issues")
    def list_issues():
        return issues

    return app


def _serialize(t):
    out = dict(t)
    out["created_at"] = t["created_at"].isoformat()
    return out


def main():
    import uvicorn
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="data/tickets.csv")
    ap.add_argument("--cursor", default="2026-08-03T00:00")
    ap.add_argument("--speed", type=float, default=3600.0,
                    help="sim seconds per wall second (3600 = 1h/s)")
    ap.add_argument("--port", type=int, default=8900)
    args = ap.parse_args()
    total_h = 254  # Aug 3 00:00 -> Aug 13 15:40 ≈ 254 sim-hours in the dataset
    eta = f"{total_h / args.speed * 3600 / 60:.1f} min" if args.speed > 0 else "frozen"
    print(f"mock helpdesk on http://127.0.0.1:{args.port}")
    print(f"replay clock STARTED NOW: cursor {args.cursor}, speed {args.speed:g}x "
          f"({args.speed / 3600:g} sim-hour/s) — full stream ≈ {eta}")
    print("watch with:  python -m src.triage --watch "
          f"--from {args.cursor} --server http://127.0.0.1:{args.port}")
    uvicorn.run(create_app(args.csv, args.cursor, args.speed),
                host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
