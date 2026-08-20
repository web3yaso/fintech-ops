## Eval: 24 golden tickets (overrides OFF, few-shot ON)

| field | accuracy |
|---|---|
| segment | 18/24 = 75% |
| ops_workflow | 21/24 = 88% |
| severity | 24/24 = 100% |
| risk_flags | 23/24 = 96% |
| amount_usd | 24/24 = 100% |

Misses:
- TKT-2059.segment: got 'workflow', want 'incident_candidate'
- TKT-2083.segment: got 'workflow', want 'incident_candidate'
- TKT-2071.segment: got 'workflow', want 'incident_candidate'
- TKT-2072.segment: got 'workflow', want 'incident_candidate'
- TKT-2085.segment: got 'workflow', want 'incident_candidate'
- TKT-2074.segment: got 'workflow', want 'incident_candidate'
- TKT-2079.ops_workflow: got 'account_admin', want 'fraud_ato'
- TKT-2079.risk_flags: got ['access_control'], want ['ato', 'access_control']
- TKT-2090.ops_workflow: got 'payment_investigation', want 'account_admin'
- TKT-2092.ops_workflow: got 'payment_investigation', want 'card_ops'

Boundary: classification only; draft quality is assessed manually (spec §6).
