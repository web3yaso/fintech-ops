"""HTTP implementations of the two seams (spec §2): HelpdeskAdapter against
the mock helpdesk server, TrackerAdapter against its /issues endpoints.
Swapping in real Zendesk/Intercom/Jira later means reimplementing these few
methods against a real API."""
from datetime import datetime

import httpx


def _parse(t):
    t = dict(t)
    t["created_at"] = datetime.fromisoformat(t["created_at"])
    return t


class MockHelpdeskAdapter:
    def __init__(self, base_url="http://127.0.0.1:8900", timeout=10.0):
        self.http = httpx.Client(base_url=base_url, timeout=timeout)

    def fetch_tickets(self, since=None, peek=False):
        params = {}
        if since is not None:
            params["since"] = since.isoformat()
        if peek:
            params["peek"] = "all"
        r = self.http.get("/tickets", params=params)
        r.raise_for_status()
        return [_parse(t) for t in r.json()]

    def write_back(self, ticket_id, labels=None, priority=None, internal_note=None):
        payload = dict(labels or {})
        if priority is not None:
            payload["priority"] = priority
        if payload:
            self.http.post(f"/tickets/{ticket_id}/labels", json=payload).raise_for_status()
        if internal_note:
            self.http.post(f"/tickets/{ticket_id}/notes",
                           json={"text": internal_note}).raise_for_status()


class MockTracker:
    def __init__(self, base_url="http://127.0.0.1:8900", timeout=10.0):
        self.http = httpx.Client(base_url=base_url, timeout=timeout)

    def create_issue(self, project, title, body, links=()):
        r = self.http.post("/issues", json={"project": project, "title": title,
                                            "body": body, "links": list(links)})
        r.raise_for_status()
        return r.json()["key"]
