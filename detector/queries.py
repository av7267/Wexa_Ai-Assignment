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
# Detect simple directed cycles from 3 to 6 hops.
#
# Example:
#
# A -> B -> C -> A
#
# Valid.
#
# A -> B -> C -> B -> A
#
# Invalid because B appears twice.
#
# The query:
#
# 1. Finds directed paths of 3-6 transfers.
# 2. Ensures the starting account is the smallest ID.
# 3. Ensures every account in the cycle is unique.
# 4. Returns one canonical representation of each cycle.
#
# ============================================================
CYCLE_DETECTION_QUERY = """
MATCH p = (start:Account)-[:TRANSFERRED*3..6]->(start)

WITH
    start,
    nodes(p)[0..-1] AS cycle_nodes,
    length(p) AS hop_count

WHERE
    // Only 3-6 hop cycles.
    hop_count >= 3
    AND hop_count <= 6

    // Canonical cycle:
    // smallest account ID must be the starting account.
    AND start.id = reduce(
        smallest = start.id,
        node IN cycle_nodes |
        CASE
            WHEN node.id < smallest
            THEN node.id
            ELSE smallest
        END
    )

UNWIND cycle_nodes AS node

WITH
    start,
    cycle_nodes,
    hop_count,
    collect(DISTINCT node.id) AS distinct_ids

// Reject cycles where an account occurs more than once.
WHERE size(cycle_nodes) = size(distinct_ids)

WITH
    [node IN cycle_nodes | node.id] AS account_sequence,
    hop_count

RETURN DISTINCT
    account_sequence,
    hop_count

ORDER BY hop_count, account_sequence
"""

# ============================================================
# THREE-HOP CYCLE DETECTION
# ============================================================

THREE_HOP_CYCLE_QUERY = """
MATCH (a:Account)-[:TRANSFERRED]->(b:Account)
      -[:TRANSFERRED]->(c:Account)
      -[:TRANSFERRED]->(a)

WHERE
    a <> b
    AND a <> c
    AND b <> c
    AND a.id < b.id
    AND a.id < c.id

RETURN DISTINCT
    [a.id, b.id, c.id] AS account_sequence,
    3 AS hop_count

ORDER BY account_sequence
"""


# ============================================================
# FAN-OUT DETECTION
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

FANOUT_CONVERGENCE_QUERY = """
MATCH (source:Account)-[tx1:TRANSFERRED]->(recipient:Account)
      -[tx2:TRANSFERRED]->(collector:Account)

WHERE source <> collector

RETURN DISTINCT
    source.id AS source_account,
    collector.id AS collector_account,
    recipient.id AS recipient_account,
    tx1.timestamp AS first_hop_timestamp,
    tx2.timestamp AS second_hop_timestamp

ORDER BY source_account, collector_account
"""


# ============================================================
# ACCOUNT TRANSACTION HISTORY
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