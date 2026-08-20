"""CsvAdapter: the offline HelpdeskAdapter implementation (spec §2).
Contract: src/adapters/csv_adapter.py::CsvAdapter(path).fetch_tickets(since=None)"""
from datetime import datetime
from pathlib import Path

from conftest import CURSOR, TICKETS_AFTER_CURSOR

from src.adapters.csv_adapter import CsvAdapter

DATA = Path(__file__).parent.parent / "data" / "tickets.csv"


def test_fetch_all_returns_100_sorted():
    got = CsvAdapter(DATA).fetch_tickets()
    assert len(got) == 100
    stamps = [t["created_at"] for t in got]
    assert stamps == sorted(stamps)


def test_field_types_parsed():
    t = {x["ticket_id"]: x for x in CsvAdapter(DATA).fetch_tickets()}
    assert isinstance(t["TKT-2001"]["created_at"], datetime)
    assert t["TKT-2001"]["monthly_revenue_usd"] == 10100.0
    assert t["TKT-2001"]["csat_score"] == 5.0
    assert t["TKT-2079"]["csat_score"] is None      # open ticket: empty CSAT
    assert t["TKT-2079"]["resolution_time_hours"] is None


def test_since_cursor_filters():
    got = CsvAdapter(DATA).fetch_tickets(since=CURSOR)
    assert len(got) == TICKETS_AFTER_CURSOR
    assert all(t["created_at"] > CURSOR for t in got)
