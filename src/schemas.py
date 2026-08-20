"""Enrichment output schema (spec §4). `theme` is the deterministic
clustering key the detectors group on — a short snake_case symptom slug,
stable across paraphrases of the same underlying issue."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class TicketEnrichment(BaseModel):
    ticket_id: str
    segment: Literal["faq", "workflow", "incident_candidate", "trend_candidate"]
    ops_workflow: Literal["payment_investigation", "card_ops", "kyb_onboarding",
                          "fraud_ato", "account_admin", "fx_pricing", "faq_selfserve"]
    theme: str = Field(pattern=r"^[a-z0-9_]{3,60}$")
    severity: int = Field(ge=1, le=4)
    risk_flags: list[Literal["ato", "fraud", "compliance_hold",
                             "access_control", "churn_risk"]] = []
    amount_usd: Optional[float] = None   # extracted, not inferred
    summary: str                          # one line, internal voice
    suggested_action: str
