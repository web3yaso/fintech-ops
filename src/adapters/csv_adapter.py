"""Offline HelpdeskAdapter: reads the provided CSV. Zero moving parts —
keeps every demo scene runnable without the mock server."""
import csv
from datetime import datetime
from pathlib import Path


def _parse(row):
    return {
        "ticket_id": row["ticket_id"],
        "created_at": datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M"),
        "customer_name": row["customer_name"],
        "customer_segment": row["customer_segment"],
        "monthly_revenue_usd": float(row["monthly_revenue_usd"]),
        "country": row["country"],
        "product": row["product"],
        "ticket_subject": row["ticket_subject"],
        "ticket_body": row["ticket_body"],
        "status": row["status"],
        "resolution_time_hours": float(row["resolution_time_hours"]) if row["resolution_time_hours"] else None,
        "csat_score": float(row["csat_score"]) if row["csat_score"] else None,
    }


class CsvAdapter:
    def __init__(self, path):
        self.path = Path(path)
        self._written = []  # write-back is recorded, not persisted, offline

    def fetch_tickets(self, since=None):
        with open(self.path) as f:
            tickets = [_parse(r) for r in csv.DictReader(f)]
        tickets.sort(key=lambda t: t["created_at"])
        if since is not None:
            tickets = [t for t in tickets if t["created_at"] > since]
        return tickets

    def write_back(self, ticket_id, labels=None, priority=None, internal_note=None):
        self._written.append({"ticket_id": ticket_id, "labels": labels or {},
                              "priority": priority, "internal_note": internal_note})
