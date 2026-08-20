"""Day-2 scope: mock helpdesk replay + write-back round trip (spec §2).
Contract: src/mock_helpdesk.py FastAPI app; src/adapters/mock_adapter.py.
RED until Day 2 — do not implement on Day 1."""
import pytest

pytestmark = pytest.mark.day2

from fastapi.testclient import TestClient

from conftest import CURSOR, TICKETS_AFTER_CURSOR
from src.mock_helpdesk import create_app


@pytest.fixture()
def client():
    app = create_app(csv_path="data/tickets.csv", cursor="2026-08-03T00:00", speed=0)
    return TestClient(app)


def test_history_and_stream_split_at_cursor(client):
    history = client.get("/tickets").json()
    assert len(history) == 100 - TICKETS_AFTER_CURSOR  # 56 pre-cursor tickets


def test_replay_order_is_deterministic(client):
    a = [t["ticket_id"] for t in client.get("/tickets", params={"since": "2026-08-03T00:00", "peek": "all"}).json()]
    b = [t["ticket_id"] for t in client.get("/tickets", params={"since": "2026-08-03T00:00", "peek": "all"}).json()]
    assert a == b and len(a) == TICKETS_AFTER_CURSOR


def test_writeback_round_trip(client):
    resp = client.post("/tickets/TKT-2072/labels",
                       json={"segment": "incident_candidate", "priority": 97.5,
                             "incident": "INC-001"})
    assert resp.status_code == 200
    got = client.get("/tickets/TKT-2072").json()
    assert got["labels"]["incident"] == "INC-001"


def test_mock_tracker_returns_issue_keys(client):
    resp = client.post("/issues", json={"project": "OPS", "title": "Online card declines",
                                        "body": "...", "links": ["incidents/INC-001.md"]})
    assert resp.json()["key"] == "OPS-101"
    resp2 = client.post("/issues", json={"project": "OPS", "title": "t2", "body": "", "links": []})
    assert resp2.json()["key"] == "OPS-102"
