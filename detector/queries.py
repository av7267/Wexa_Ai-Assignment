"""
Cypher queries used by the fraud detector.
"""


# ============================================================
# BASIC GRAPH STATISTICS
# ============================================================

ACCOUNT_COUNT_QUERY = """
MATCH (a:Account)
RETURN count(a) AS account_count
"""


TRANSACTION_COUNT_QUERY = """
MATCH ()-[tx:TRANSFERRED]->()
RETURN count(tx) AS transaction_count
"""


# ============================================================
# CYCLE DETECTION
# ============================================================
#
# Detect directed cycles between 3 and 6 hops.
#
# Example:
#
# A -> B -> C -> A
#
# We:
#
# 1. Require a directed path.
# 2. Require 3-6 transfers.
# 3. Require all intermediate accounts to be different.
# 4. Use the smallest account ID as the starting point.
#
# This prevents the same cycle from being returned once for every
# possible starting account.
#
# ============================================================

CYCLE_DETECTION_QUERY = """
MATCH p = (start:Account)-[:TRANSFERRED*3..6]->(start)

WITH
    [node IN nodes(p) | node.id] AS accounts,
    length(p) AS hop_count

WHERE
    ALL(
        i IN range(0, size(accounts) - 2)
        WHERE NOT accounts[i] IN accounts[i + 1..]
    )

    AND start.id = reduce(
        smallest = start.id,
        account_id IN accounts |
        CASE
            WHEN account_id < smallest THEN account_id
            ELSE smallest
        END
    )

RETURN DISTINCT
    accounts AS account_sequence,
    hop_count

ORDER BY hop_count, account_sequence
"""


# ============================================================
# THREE-HOP CYCLE DETECTION
# ============================================================
#
# Dedicated query for short cycles.
#
# 3-hop cycles are generally stronger signals than long random
# graph cycles, so we keep this query separately available.
#
# ============================================================

THREE_HOP_CYCLE_QUERY = """
MATCH (a:Account)-[:TRANSFERRED]->(b:Account)
      -[:TRANSFERRED]->(c:Account)
      -[:TRANSFERRED]->(a)

WHERE a.id < b.id
  AND a.id < c.id

RETURN DISTINCT
    [a.id, b.id, c.id] AS account_sequence,
    3 AS hop_count

ORDER BY account_sequence
"""


# ============================================================
# FAN-OUT DETECTION
# ============================================================
#
# Retrieve outgoing transfers for accounts that have multiple
# recipients.
#
# IMPORTANT:
#
# High number of recipients alone is NOT considered fraud.
#
# The Python detector will examine the timestamps and determine
# whether the transactions are clustered in a short time window.
#
# This is necessary because the seed contains a legitimate
# payroll account with many recipients spread over 180 days.
#
# ============================================================

FANOUT_QUERY = """
MATCH (source:Account)-[tx:TRANSFERRED]->(recipient:Account)

RETURN
    source.id AS source_account,
    source.name AS source_name,
    source.account_type AS account_type,
    recipient.id AS recipient_account,
    tx.amount AS amount,
    tx.timestamp AS timestamp

ORDER BY source.id, tx.timestamp
"""


# ============================================================
# CONVERGENCE DETECTION
# ============================================================
#
# Find accounts receiving transfers from multiple different
# accounts.
#
# Example:
#
# A ----\
# B -----+--> X
# C ----/
#
# We retrieve the raw transactions and let Python perform the
# structural/time-window analysis.
#
# ============================================================

CONVERGENCE_QUERY = """
MATCH (source:Account)-[tx:TRANSFERRED]->(collector:Account)

RETURN
    collector.id AS collector_account,
    collector.name AS collector_name,
    collector.account_type AS account_type,
    source.id AS source_account,
    tx.amount AS amount,
    tx.timestamp AS timestamp

ORDER BY collector.id, tx.timestamp
"""


# ============================================================
# FAN-OUT + CONVERGENCE
# ============================================================
#
# Detect the structure:
#
#              source
#             /  |  \
#            A   B   C
#             \  |  /
#              collector
#
# This is stronger than either fan-out or convergence by itself.
#
# ============================================================

FANOUT_CONVERGENCE_QUERY = """
MATCH (source:Account)-[:TRANSFERRED]->(recipient:Account)
      -[:TRANSFERRED]->(collector:Account)

WHERE source <> collector

RETURN DISTINCT
    source.id AS source_account,
    source.name AS source_name,
    collector.id AS collector_account,
    collector.name AS collector_name,
    recipient.id AS recipient_account

ORDER BY source_account, collector_account
"""


# ============================================================
# ACCOUNT TRANSACTION HISTORY
# ============================================================
#
# Useful later for risk scoring.
#
# ============================================================

ACCOUNT_TRANSACTION_HISTORY_QUERY = """
MATCH (a:Account)-[tx:TRANSFERRED]->(b:Account)

RETURN
    a.id AS from_account,
    b.id AS to_account,
    tx.transaction_id AS transaction_id,
    tx.amount AS amount,
    tx.timestamp AS timestamp

ORDER BY tx.timestamp
"""


# ============================================================
# DETECT CYCLES
# ============================================================

def detect_cycles():
    """
    Execute the cycle detection query.
    """

    from detector.db import run_query

    return run_query(CYCLE_DETECTION_QUERY)