"""
Fan-out detection logic.
"""

from datetime import timedelta
from collections import defaultdict

from detector.db import run_query
from detector.queries import FANOUT_QUERY


def detect_fanout(min_recipients=4, window_hours=6):
    """
    Detect accounts that sent money to several distinct recipients
    within a short time window. A high recipient count alone is not
    enough signal — payroll-style accounts have that too — so this
    also requires the transactions to be clustered in time.

    Returns:
        list[dict]
    """

    rows = run_query(FANOUT_QUERY)

    by_source = defaultdict(list)
    for r in rows:
        by_source[r["source_account"]].append({
            "recipient": r["recipient_account"],
            "timestamp": r["timestamp"].to_native(),
        })

    flagged = []

    for source, txs in by_source.items():
        txs.sort(key=lambda t: t["timestamp"])

        for i, anchor in enumerate(txs):
            window = [
                t for t in txs[i:]
                if t["timestamp"] - anchor["timestamp"] <= timedelta(hours=window_hours)
            ]
            recipients = {t["recipient"] for t in window}

            if len(recipients) >= min_recipients:
                flagged.append({
                    "source_account": source,
                    "window_start": anchor["timestamp"],
                    "recipients": sorted(recipients),
                    "recipient_count": len(recipients),
                })
                break  # one flag per source account is enough

    return flagged


def print_fanout(flagged):
    if not flagged:
        print("No fan-out patterns found.")
        return

    print("=" * 60)
    print("FAN-OUT DETECTION")
    print("=" * 60)

    for f in flagged:
        print(
            f"{f['source_account']} -> {f['recipient_count']} recipients "
            f"starting {f['window_start']}: {f['recipients']}"
        )

    print()
    print(f"Total flagged: {len(flagged)}")