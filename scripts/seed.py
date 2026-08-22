import os
import sys
import random
import uuid
import json
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from detector.db import run_query


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

random.seed(42)

NUM_ACCOUNTS = 100
NUM_NORMAL_TX = 300

BASE_TIME = datetime(2026, 1, 1)
DAYS_RANGE = 180


# ---------------------------------------------------------
# Synthetic account data
# ---------------------------------------------------------

FIRST_NAMES = [
    "Alex",
    "Sam",
    "Jordan",
    "Taylor",
    "Morgan",
    "Riley",
    "Casey",
    "Priya",
    "Wei",
    "Fatima",
    "Diego",
    "Elena",
    "Noah",
    "Mia",
]

LAST_NAMES = [
    "Sharma",
    "Kim",
    "Garcia",
    "Chen",
    "Patel",
    "Rossi",
    "Muller",
    "Nguyen",
    "Silva",
    "Khan",
    "Cohen",
    "Novak",
]

BUSINESS_NAMES = [
    "QuickMart",
    "BluePeak Traders",
    "Nimbus Logistics",
    "Sunrise Retail",
    "Harbor Foods",
    "Vertex Consulting",
]

ACCOUNT_TYPES = [
    "personal",
    "business",
]


# ---------------------------------------------------------
# In-memory dataset
# ---------------------------------------------------------

accounts = []

transactions = []

# Bookkeeping only.
# NEVER written to CognoDB.
# NEVER used by detection queries.
planted_patterns = {}


# ---------------------------------------------------------
# Account generation
# ---------------------------------------------------------

def make_account(account_id, account_type=None, name=None):
    account_type = account_type or random.choice(ACCOUNT_TYPES)

    if name is None:
        if account_type == "business":
            name = random.choice(BUSINESS_NAMES) + f" {account_id[-2:]}"
        else:
            name = (
                f"{random.choice(FIRST_NAMES)} "
                f"{random.choice(LAST_NAMES)}"
            )

    created_at = (
        BASE_TIME
        - timedelta(days=random.uniform(30, 730))
    )

    return {
        "id": account_id,
        "name": name,
        "account_type": account_type,
        "created_at": created_at,
    }


# ---------------------------------------------------------
# Timestamp generation
# ---------------------------------------------------------

def random_timestamp(days_range=DAYS_RANGE):
    """
    Generate a random datetime within the seed window.
    """

    total_seconds = days_range * 24 * 60 * 60

    offset = timedelta(
        seconds=random.uniform(
            0,
            total_seconds,
        )
    )

    return BASE_TIME + offset


# ---------------------------------------------------------
# Transaction creation
# ---------------------------------------------------------

def new_tx(from_acc, to_acc, amount, timestamp):
    tx = {
        "transaction_id": str(uuid.uuid4()),
        "from": from_acc,
        "to": to_acc,
        "amount": round(amount, 2),

        # Keep this as a Python datetime.
        # The Neo4j driver will send it as a temporal value.
        "timestamp": timestamp,
    }

    transactions.append(tx)

    return tx


# ---------------------------------------------------------
# Normal transaction noise
# ---------------------------------------------------------

def generate_normal_transactions(n):
    account_ids = [
        account["id"]
        for account in accounts
    ]

    for _ in range(n):
        from_acc, to_acc = random.sample(
            account_ids,
            2,
        )

        new_tx(
            from_acc,
            to_acc,
            random.uniform(10, 5000),
            random_timestamp(),
        )


# ---------------------------------------------------------
# Ring pattern
# ---------------------------------------------------------

def plant_ring(pattern_id, length):
    """
    Create:

        A -> B -> C -> ... -> A

    Transactions occur close together in time.
    """

    account_ids = [
        account["id"]
        for account in accounts
    ]

    ring_accounts = random.sample(
        account_ids,
        length,
    )

    start_time = random_timestamp()

    for i in range(length):
        from_acc = ring_accounts[i]

        to_acc = ring_accounts[
            (i + 1) % length
        ]

        timestamp = (
            start_time
            + timedelta(
                minutes=random.uniform(5, 90) * i
            )
        )

        new_tx(
            from_acc,
            to_acc,
            random.uniform(500, 3000),
            timestamp,
        )

    planted_patterns[pattern_id] = ring_accounts


# ---------------------------------------------------------
# Fan-out pattern
# ---------------------------------------------------------

def plant_fanout(
    pattern_id,
    num_recipients=5,
):
    """
    Create:

        Source
        / | \
       A  B  C
       |  |  |
       ...

    One account sends money to several
    different accounts within a short period.
    """

    account_ids = [
        account["id"]
        for account in accounts
    ]

    source = random.choice(
        account_ids
    )

    recipients = random.sample(
        [
            account
            for account in account_ids
            if account != source
        ],
        num_recipients,
    )

    start_time = random_timestamp()

    for recipient in recipients:

        timestamp = (
            start_time
            + timedelta(
                minutes=random.uniform(1, 30)
            )
        )

        new_tx(
            source,
            recipient,
            random.uniform(200, 1500),
            timestamp,
        )

    planted_patterns[pattern_id] = {
        "source": source,
        "recipients": recipients,
    }


# ---------------------------------------------------------
# Fan-out + convergence pattern
# ---------------------------------------------------------

def plant_fanout_convergence(
    pattern_id,
    num_recipients=5,
    num_collectors=2,
):
    """
    Create:

        Source
        / | \
       R  R  R
       \\  | /
       Collector(s)

    This represents fan-out followed by convergence.
    """

    account_ids = [
        account["id"]
        for account in accounts
    ]

    source = random.choice(
        account_ids
    )

    remaining = [
        account
        for account in account_ids
        if account != source
    ]

    recipients = random.sample(
        remaining,
        num_recipients,
    )

    collectors = random.sample(
        [
            account
            for account in remaining
            if account not in recipients
        ],
        num_collectors,
    )

    start_time = random_timestamp()

    for recipient in recipients:

        first_timestamp = (
            start_time
            + timedelta(
                minutes=random.uniform(1, 20)
            )
        )

        new_tx(
            source,
            recipient,
            random.uniform(300, 1000),
            first_timestamp,
        )

        collector = random.choice(
            collectors
        )

        second_timestamp = (
            first_timestamp
            + timedelta(
                minutes=random.uniform(5, 60)
            )
        )

        new_tx(
            recipient,
            collector,
            random.uniform(250, 950),
            second_timestamp,
        )

    planted_patterns[pattern_id] = {
        "source": source,
        "recipients": recipients,
        "collectors": collectors,
    }


# ---------------------------------------------------------
# Legitimate high-volume account
# ---------------------------------------------------------

def plant_payroll_account():
    """
    Create a legitimate high-out-degree account.

    It sends money to many recipients, but the transactions
    are spread across the entire time window rather than
    being clustered together.

    This gives the detector a realistic false-positive case.
    """

    account_ids = [
        account["id"]
        for account in accounts
    ]

    source = random.choice(
        account_ids
    )

    recipients = random.sample(
        [
            account
            for account in account_ids
            if account != source
        ],
        15,
    )

    for recipient in recipients:

        new_tx(
            source,
            recipient,
            random.uniform(2000, 4000),
            random_timestamp(),
        )

    planted_patterns["payroll_legit"] = {
        "source": source,
        "recipients": recipients,
    }


# ---------------------------------------------------------
# Database reset
# ---------------------------------------------------------

def reset_db():
    """
    Delete all nodes and relationships.

    Only use this against the dedicated assignment database.
    """

    run_query(
        "MATCH (n) DETACH DELETE n"
    )


# ---------------------------------------------------------
# Database constraint
# ---------------------------------------------------------

def ensure_constraints():
    """
    Ensure every Account has a unique ID.
    """

    run_query(
        """
        CREATE CONSTRAINT account_id_unique IF NOT EXISTS
        FOR (a:Account)
        REQUIRE a.id IS UNIQUE
        """
    )


# ---------------------------------------------------------
# Write data to CognoDB
# ---------------------------------------------------------

def write_to_cognodb():

    # -----------------------------------------------------
    # Accounts
    # -----------------------------------------------------

    run_query(
        """
        UNWIND $accounts AS acc

        MERGE (a:Account {id: acc.id})

        SET
            a.name = acc.name,
            a.account_type = acc.account_type,
            a.created_at = acc.created_at
        """,
        {
            "accounts": accounts
        },
    )

    # -----------------------------------------------------
    # Transactions
    # -----------------------------------------------------

    batch_size = 200

    for i in range(
        0,
        len(transactions),
        batch_size,
    ):

        batch = transactions[
            i:i + batch_size
        ]

        run_query(
            """
            UNWIND $batch AS tx

            MATCH (from:Account {id: tx.from})
            MATCH (to:Account {id: tx.to})

            CREATE (from)-[:TRANSFERRED {
                transaction_id: tx.transaction_id,
                amount: tx.amount,
                timestamp: tx.timestamp
            }]->(to)
            """,
            {
                "batch": batch
            },
        )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    if "--reset" in sys.argv:
        reset_db()

    ensure_constraints()

    # -----------------------------------------------------
    # Create 100 accounts
    # -----------------------------------------------------

    for i in range(
        1,
        NUM_ACCOUNTS + 1,
    ):
        accounts.append(
            make_account(
                f"A{str(i).zfill(3)}"
            )
        )

    # -----------------------------------------------------
    # Generate normal transactions
    # -----------------------------------------------------

    generate_normal_transactions(
        NUM_NORMAL_TX
    )

    # -----------------------------------------------------
    # Plant 5 rings
    # -----------------------------------------------------

    for i in range(1, 6):

        plant_ring(
            f"ring_{i:03d}",
            length=random.randint(3, 6),
        )

    # -----------------------------------------------------
    # Plant 5 fan-outs
    # -----------------------------------------------------

    for i in range(1, 6):

        plant_fanout(
            f"fanout_{i:03d}",
            num_recipients=random.randint(4, 6),
        )

    # -----------------------------------------------------
    # Plant 3 fan-out + convergence patterns
    # -----------------------------------------------------

    for i in range(1, 4):

        plant_fanout_convergence(
            f"convergence_{i:03d}"
        )

    # -----------------------------------------------------
    # Plant legitimate payroll account
    # -----------------------------------------------------

    plant_payroll_account()

    # -----------------------------------------------------
    # Write everything to CognoDB
    # -----------------------------------------------------

    write_to_cognodb()

    # -----------------------------------------------------
    # Save planted patterns for verification
    # -----------------------------------------------------

    patterns_path = os.path.join(
        os.path.dirname(__file__),
        "planted_patterns.json",
    )

    with open(
        patterns_path,
        "w",
    ) as file:

        json.dump(
            planted_patterns,
            file,
            indent=2,
            default=str,
        )

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    print(
        f"Accounts: {len(accounts)}"
    )

    print(
        f"Transactions: {len(transactions)}"
    )

    print(
        "Planted patterns saved to "
        "scripts/planted_patterns.json "
        "(for verification only)"
    )


if __name__ == "__main__":
    main()