"""Loop-closure state machine (spec §3.5): every declared pattern advances
detected → escalated → owner_acked → fix_confirmed → customers_notified →
closed. First two states derive from logs that already exist; `closed` is
earned — theme volume must be back to baseline. Contract: src/closure.py."""
from datetime import datetime

from src.closure import (closure_state, time_to_close_hours, volume_subsided)

EVENTS = [
    {"event": "INCIDENT_DECLARED", "cluster_id": "INC-001",
     "theme": "cards_online_declines", "created_at": "2026-08-04 15:43:00"},
]
ACTIONS = [
    {"ts": "2026-08-19T10:00:00", "actor": "liaison", "action": "brief_filed",
     "tickets": ["TKT-2059"], "artifact": "knowledge/outbound/eng/INC-001-brief.md"},
    {"ts": "2026-08-19T11:00:00", "actor": "liaison", "action": "owner_acked",
     "tickets": ["TKT-2059"], "artifact": "INC-001", "note": "Alex acked in room"},
    {"ts": "2026-08-19T12:00:00", "actor": "sophie", "action": "fix_confirmed",
     "tickets": ["TKT-2059"], "artifact": "INC-001"},
]


def test_state_derives_from_existing_logs_plus_new_actions():
    state, timeline = closure_state("INC-001", ACTIONS, EVENTS)
    assert state == "fix_confirmed"
    assert [t[0] for t in timeline] == ["detected", "escalated", "owner_acked",
                                        "fix_confirmed"]


def test_detected_only_when_no_actions():
    state, timeline = closure_state("INC-001", [], EVENTS)
    assert state == "detected" and len(timeline) == 1


def test_volume_subsided_needs_quiet_trailing_window():
    created = [datetime(2026, 8, 4, 8, 30), datetime(2026, 8, 7, 0, 27)]
    end = datetime(2026, 8, 13, 15, 40)
    assert volume_subsided(created, end, quiet_hours=72) is True     # 6.6d quiet
    created_late = created + [datetime(2026, 8, 12, 9, 0)]
    assert volume_subsided(created_late, end, quiet_hours=72) is False  # 1.3d quiet


def test_closed_is_earned_not_declared():
    acts = ACTIONS + [
        {"ts": "2026-08-19T13:00:00", "actor": "sophie",
         "action": "customers_notified", "tickets": ["TKT-2059"], "artifact": "INC-001"},
        {"ts": "2026-08-19T14:00:00", "actor": "sophie",
         "action": "loop_closed", "tickets": ["TKT-2059"], "artifact": "INC-001"},
    ]
    # subsided=False → loop_closed action present but NOT counted
    state, _ = closure_state("INC-001", acts, EVENTS, subsided=False)
    assert state == "customers_notified"
    state, _ = closure_state("INC-001", acts, EVENTS, subsided=True)
    assert state == "closed"


def test_time_to_close_from_first_ticket_to_notification():
    first_ticket = datetime(2026, 8, 4, 8, 30)
    acts = ACTIONS + [{"ts": "2026-08-06T08:30:00", "actor": "sophie",
                       "action": "customers_notified", "tickets": ["TKT-2059"],
                       "artifact": "INC-001"}]
    assert time_to_close_hours("INC-001", acts, first_ticket) == 48.0
    assert time_to_close_hours("INC-001", ACTIONS, first_ticket) is None
