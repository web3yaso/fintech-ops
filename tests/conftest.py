"""Shared fixtures. Cluster memberships below were hand-verified against
data/tickets.csv (2026-08-19) — they are the ground truth the detectors
must reproduce, independent of any production code."""
import csv
from datetime import datetime
from pathlib import Path

import pytest

DATA = Path(__file__).parent.parent / "data" / "tickets.csv"

DECLINE_IDS = {
    "TKT-2059", "TKT-2060", "TKT-2061", "TKT-2062", "TKT-2063", "TKT-2064",
    "TKT-2065", "TKT-2066", "TKT-2067", "TKT-2068", "TKT-2069", "TKT-2070",
    "TKT-2083", "TKT-2084",
}  # 14 tickets, Aug 4-7
WIRE_IDS = {
    "TKT-2071", "TKT-2072", "TKT-2073", "TKT-2074", "TKT-2075", "TKT-2076",
    "TKT-2077", "TKT-2078", "TKT-2085",
}  # 9 tickets, Aug 8-11
FX_IDS = {
    "TKT-2049", "TKT-2050", "TKT-2051", "TKT-2052", "TKT-2053", "TKT-2054",
    "TKT-2055", "TKT-2056", "TKT-2057", "TKT-2058", "TKT-2086",
}  # 11 tickets, Jul 20 - Aug 7, 10 customers
VENDOR_PAYMENT_FAQ_IDS = {
    # verbatim "Can I schedule a supplier payment for next Friday?" x7,
    # 6 customers, Jul 4 - Aug 10, avg CSAT 3.14 — must NOT become a trend
    "TKT-2035", "TKT-2043", "TKT-2031",  # + 4 more resolved dynamically below
}
RISK_IDS = {"TKT-2079", "TKT-2080", "TKT-2081", "TKT-2082"}

THIRD_DECLINE_ID = "TKT-2060"  # 2026-08-04 15:43 — burst threshold trips here
CURSOR = datetime(2026, 8, 3, 0, 0)
TICKETS_AFTER_CURSOR = 44  # verified count with created_at > 2026-08-03 00:00


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


@pytest.fixture(scope="session")
def tickets():
    with open(DATA) as f:
        return [_parse(r) for r in csv.DictReader(f)]


@pytest.fixture(scope="session")
def by_id(tickets):
    return {t["ticket_id"]: t for t in tickets}


def make_record(ticket, theme, segment="workflow"):
    """Clustering-input contract: what triage.py hands the detectors after
    enrichment. Detectors are deterministic — they never see the LLM.
    `segment` matters: burst detection must skip faq records (two FAQ themes
    in the dataset bunch >=3 tickets inside 72h and must not become incidents)."""
    return {
        "ticket_id": ticket["ticket_id"],
        "created_at": ticket["created_at"],
        "customer_name": ticket["customer_name"],
        "product": ticket["product"],
        "theme": theme,
        "segment": segment,
        "csat_score": ticket["csat_score"],
    }


@pytest.fixture(scope="session")
def enriched_full(tickets):
    """Full dataset as clustering records with ground-truth themes, simulating
    a correct enrichment pass so detector tests are LLM-free."""
    vendor_faq = {t["ticket_id"] for t in tickets
                  if t["ticket_body"].startswith("Can I schedule a supplier payment")}
    stmt_faq = {t["ticket_id"] for t in tickets
                if t["ticket_body"].startswith("Where can I download last month's account statement")}
    records = []
    for t in tickets:
        tid = t["ticket_id"]
        if tid in DECLINE_IDS:
            theme, seg = "cards_online_declines", "incident_candidate"
        elif tid in WIRE_IDS:
            theme, seg = "inbound_usd_wire_delay", "incident_candidate"
        elif tid in FX_IDS:
            theme, seg = "fx_pricing_complaint", "trend_candidate"
        elif tid in vendor_faq:
            theme, seg = "faq_vendor_payment", "faq"
        elif tid in stmt_faq:
            # 4 of these 6 land inside one 72h window — the burst-FAQ trap
            theme, seg = "faq_statement_download", "faq"
        else:
            theme, seg = f"other_{tid}", "workflow"  # unique theme: never clusters
        records.append(make_record(t, theme, seg))
    return records
