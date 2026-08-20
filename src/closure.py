"""Loop-closure state machine (spec §3.5). Zero new infrastructure:
`detected` = the pattern's DECLARED event, `escalated` = Liaison's existing
brief_filed/tracker_issue action; the last four states are ordinary
action_log entries (owner_acked, fix_confirmed, customers_notified,
loop_closed) whose `artifact` names the cluster id.

`closed` is earned, not declared: a loop_closed entry only counts once the
theme's ticket volume is back to baseline (quiet trailing window)."""
from datetime import datetime

STATES = ["detected", "escalated", "owner_acked", "fix_confirmed",
          "customers_notified", "closed"]
_ESCALATION_ACTIONS = {"brief_filed", "tracker_issue"}
_STATE_ACTIONS = {"owner_acked": "owner_acked", "fix_confirmed": "fix_confirmed",
                  "customers_notified": "customers_notified", "loop_closed": "closed"}


def _mentions(entry, cluster_id):
    return cluster_id in (entry.get("artifact") or "") or cluster_id in (entry.get("note") or "")


def closure_state(cluster_id, actions, events, subsided=True):
    """Returns (current_state, timeline) where timeline is [(state, ts), ...]
    in machine order. The furthest reached state wins; loop_closed requires
    subsided=True (metrics computes that from enriched data)."""
    timeline = []
    for e in events:
        if e.get("cluster_id") == cluster_id and e.get("event", "").endswith("_DECLARED"):
            timeline.append(("detected", e.get("created_at") or e.get("ts")))
            break
    for a in actions:
        if a["action"] in _ESCALATION_ACTIONS and _mentions(a, cluster_id):
            timeline.append(("escalated", a["ts"]))
            break
    for action, state in _STATE_ACTIONS.items():
        for a in actions:
            if a["action"] == action and _mentions(a, cluster_id):
                if state == "closed" and not subsided:
                    continue  # not earned yet
                timeline.append((state, a["ts"]))
                break
    timeline.sort(key=lambda t: STATES.index(t[0]))
    current = timeline[-1][0] if timeline else None
    return current, timeline


def volume_subsided(created_ats, dataset_end, quiet_hours=72):
    """Theme volume is back to baseline when no new ticket arrived in the
    trailing quiet window before dataset_end."""
    if not created_ats:
        return True
    quiet = (dataset_end - max(created_ats)).total_seconds() / 3600
    return quiet >= quiet_hours


def time_to_close_hours(cluster_id, actions, first_ticket_at):
    """First report → customers actually notified. None until that state."""
    for a in actions:
        if a["action"] == "customers_notified" and _mentions(a, cluster_id):
            ts = datetime.fromisoformat(a["ts"])
            return round((ts - first_ticket_at).total_seconds() / 3600, 1)
    return None
