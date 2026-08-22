"""
Cycle detection logic.
"""

from datetime import timedelta
from collections import defaultdict

from detector.db import run_query
from detector.queries import CYCLE_DETECTION_QUERY

EDGE_TIMESTAMPS_QUERY = """
MATCH (a:Account)-[tx:TRANSFERRED]->(b:Account)
RETURN a.id AS from_id, b.id AS to_id, tx.timestamp AS timestamp
"""


def detect_cycles(max_span_hours=6):
    results = run_query(CYCLE_DETECTION_QUERY)
    edges = run_query(EDGE_TIMESTAMPS_QUERY)

    by_pair = defaultdict(list)
    for e in edges:
        by_pair[(e["from_id"], e["to_id"])].append(e["timestamp"].to_native())

    cycles = []

    for row in results:
        seq = row["account_sequence"]
        edge_pairs = list(zip(seq, seq[1:] + [seq[0]]))

        timestamps = []
        has_all_edges = True
        for a, b in edge_pairs:
            candidates = by_pair.get((a, b))
            if not candidates:
                has_all_edges = False
                break
            timestamps.append(min(candidates))

        if not has_all_edges:
            continue

        span = max(timestamps) - min(timestamps)
        if span <= timedelta(hours=max_span_hours):
            cycles.append(
                {
                    "hop_count": row["hop_count"],
                    "account_sequence": seq,
                    "span_hours": round(span.total_seconds() / 3600, 2),
                }
            )

    return cycles


def print_cycles(cycles):
    """
    Print detected cycles in a readable format.
    """

    if not cycles:
        print("No cycles found.")
        return

    print("=" * 60)
    print("CYCLE DETECTION")
    print("=" * 60)

    for cycle in cycles:
        accounts = cycle["account_sequence"]

        print(
            f"{cycle['hop_count']}-hop ({cycle['span_hours']}h): "
            f"{' -> '.join(accounts)} -> {accounts[0]}"
        )

    print()
    print(f"Total valid cycles: {len(cycles)}")