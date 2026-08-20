"""Zero-install console snapshot (spec §7 Day-3 ②): one self-contained HTML
built from a real run's out/ artifacts. Contract: scripts/export_console.py
::build_console(...) -> html string."""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from export_console import build_console


def test_console_is_selfcontained_and_complete(tmp_path):
    queue = [{"ticket_id": "TKT-2081", "customer_name": "Maple Ridge Imports",
              "segment": "workflow", "ops_workflow": "account_admin",
              "theme": "account_restriction", "severity": 4,
              "risk_flags": ["compliance_hold"], "status": "pending",
              "pinned": True, "priority": 130.2,
              "explain": "8 (sev 4) x 4.65 (MRR $4,500) x 2.15 (open 201h) + 50 (risk)",
              "summary": "restricted before payroll", "suggested_action": "verify",
              "needs_human": False}]
    clusters = {"incidents": [{"cluster_id": "INC-001", "kind": "incident",
                               "theme": "cards_online_declines",
                               "member_ids": ["TKT-2081"], "customers": ["X"],
                               "avg_csat": 1.6, "first_seen": "2026-08-04 08:30",
                               "last_seen": "2026-08-07 00:27"}], "trends": []}
    actions = [{"ts": "2026-08-19T10:00:00", "actor": "liaison",
                "action": "brief_filed", "tickets": ["TKT-2081"],
                "artifact": "knowledge/outbound/eng/INC-001-brief.md"}]
    artifacts = {"incidents/INC-001.md": "# INC-001\nblast radius…"}
    by_id = {"TKT-2081": {"ticket_id": "TKT-2081", "created_at": datetime(2026, 8, 11, 5, 0),
                          "customer_name": "Maple Ridge Imports",
                          "monthly_revenue_usd": 4500.0, "status": "pending",
                          "resolution_time_hours": None, "csat_score": None}}

    html = build_console(queue, clusters, actions, artifacts, by_id,
                         generated="2026-08-20 09:00")
    for needle in ["snapshot of a real run", "export_console.py",   # honesty header
                   "TKT-2081", "130.2", "8 (sev 4)",                # queue + explain
                   "INC-001", "closure:",                            # cards + state
                   "brief_filed",                                    # audit tail
                   "prefers-color-scheme"]:                          # dark mode
        assert needle in html, needle
    assert "http://" not in html and "https://" not in html         # zero external
    assert "/Users/" not in html                                     # no home paths