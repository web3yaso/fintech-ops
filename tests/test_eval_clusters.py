"""Cluster-membership hit rate for the eval (spec §6): golden tickets carry
cluster labels (INC-DECLINES / INC-WIRES / TRD-FX); grade them against the
detected clusters by majority mapping. Contract: eval.run_eval.cluster_hit_rate."""
from eval.run_eval import cluster_hit_rate

GOLDEN = [
    {"ticket_id": "A1", "cluster": "INC-DECLINES"},
    {"ticket_id": "A2", "cluster": "INC-DECLINES"},
    {"ticket_id": "W1", "cluster": "INC-WIRES"},
    {"ticket_id": "W2", "cluster": "INC-WIRES"},
    {"ticket_id": "F1", "cluster": "TRD-FX"},
    {"ticket_id": "N1", "cluster": None},   # must NOT be in any cluster
]


def test_perfect_detection_scores_full():
    detected = {"incidents": [{"cluster_id": "INC-001", "member_ids": ["A1", "A2", "x9"]},
                              {"cluster_id": "INC-002", "member_ids": ["W1", "W2"]}],
                "trends": [{"cluster_id": "TRD-001", "member_ids": ["F1"]}]}
    hits, total = cluster_hit_rate(GOLDEN, detected)
    assert (hits, total) == (6, 6)


def test_misses_split_cluster_and_false_inclusion():
    detected = {"incidents": [{"cluster_id": "INC-001", "member_ids": ["A1", "N1"]},
                              {"cluster_id": "INC-002", "member_ids": ["A2"]},   # split
                              {"cluster_id": "INC-003", "member_ids": ["W1", "W2"]}],
                "trends": []}
    hits, total = cluster_hit_rate(GOLDEN, detected)
    # A1 ok (majority cluster for INC-DECLINES is INC-001), A2 split off -> miss,
    # W1/W2 ok, F1 not detected -> miss, N1 wrongly clustered -> miss
    assert (hits, total) == (3, 6)
