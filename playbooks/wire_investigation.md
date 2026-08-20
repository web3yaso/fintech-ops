# Playbook: wire_investigation (payment_investigation)

For inbound/outbound wires that have not arrived or posted.

## Facts to extract (from ticket text only — never infer)
| fact | notes |
|---|---|
| amount + currency | as stated ("$118k USD") |
| direction | inbound / outbound |
| expected date | when the sender says it was sent/delivered |
| counterparty | sender/receiver name if given |
| business impact | what the customer says is blocked (payroll, supplier, inventory) |
| sender confirmation | has the sender's bank confirmed dispatch? |

## Investigation checklist (in order)
- [ ] Check the partner-bank portal for an unmatched inbound credit near the
      amount/date (fat-finger window: ±1 day, ±2% amount)
- [ ] Ask the customer for the sender's payment reference / IMAD or UETR if
      not already provided
- [ ] Trace the reference with the partner bank: was it received and queued,
      or never received?
- [ ] Determine which case this is:
      **(a) intermediary delay** — funds en route between correspondent banks;
      **(b) posting-queue delay** — partner bank has funds, not yet posted to
      the client's virtual account;
      **(c) recall/return** — sender error, funds bounced
- [ ] If ≥2 similar tickets exist in the same window, notify triage — this may
      be an incident, not a case
- [ ] Log findings in the work package before drafting the customer update

## Partner-bank inquiry draft must include
Reference (if known), amount, currency, expected value date, beneficiary
account, and ONE precise question (received? queued? returned?).

## Customer update rules
State what is confirmed, what is being checked, and the next checkpoint time.
No fake ETA — if we don't know, say what we'll know by when. Never speculate
about the sender's bank.
