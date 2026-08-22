"""
Fan-out + convergence detection logic.
"""

from datetime import timedelta
from collections import defaultdict

from detector.db import run_query
from detector.queries import FANOUT_CONVERGENCE_QUERY


def detect_convergence(window_hours=6):
    rows = run_query(FANOUT_CONVERGENCE_QUERY)

    by_source_collector = defaultdict(list)
    for r in rows:
        by_source_collector[(r["source_account"], r["collector_account"])].append({
            "recipient": r["recipient_account"],
            "first_ts": r["first_hop_timestamp"].to_native(),
            "second_ts": r["second_hop_timestamp"].to_native(),
        })

    flagged = []
    for (source, collector), hops in by_source_collector.items():
        recipients = {h["recipient"] for h in hops}
        if len(recipients) < 3:
            continue

        all_ts = [h["first_ts"] for h in hops] + [h["second_ts"] for h in hops]
        span = max(all_ts) - min(all_ts)

        if span <= timedelta(hours=window_hours):
            flagged.append({
                "source_account": source,
                "collector_account": collector,
                "recipients": sorted(recipients),
                "recipient_count": len(recipients),
                "span_hours": round(span.total_seconds() / 3600, 2),
            })

    return flagged

def print_convergence(flagged):
    if not flagged:
        print("No convergence patterns found.")
        return

    print("=" * 60)
    print("CONVERGENCE DETECTION")
    print("=" * 60)

    for f in flagged:
        print(
            f"{f['source_account']} -> {f['recipient_count']} recipients "
            f"-> {f['collector_account']}: {f['recipients']}"
        )

    print()
    print(f"Total flagged: {len(flagged)}")