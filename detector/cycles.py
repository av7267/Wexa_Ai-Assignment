"""
Cycle detection logic.
"""

from detector.db import run_query
from detector.queries import CYCLE_DETECTION_QUERY


def detect_cycles():
    """
    Detect simple directed transaction cycles from 3 to 6 hops.

    Returns:
        list[dict]
    """

    results = run_query(CYCLE_DETECTION_QUERY)

    cycles = []

    for row in results:
        cycles.append(
            {
                "account_sequence": row["account_sequence"],
                "hop_count": row["hop_count"],
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
            f"{cycle['hop_count']}-hop: "
            + " -> ".join(accounts)
            + f" -> {accounts[0]}"
        )

    print()
    print(f"Total valid cycles: {len(cycles)}")