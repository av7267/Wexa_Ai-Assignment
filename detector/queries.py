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
# IMPORTANT:
# We intentionally use separate queries for each cycle length.
#
# Do NOT use:
#
# MATCH p = (start)-[:TRANSFERRED*3..6]->(start)
#
# because that causes a massive variable-length path search.
#
# Each query below also requires the starting account to have
# the smallest ID in the cycle. This removes rotational
# duplicates.
#
# Example:
#
# A004 -> A006 -> A053 -> A004
#
# will be returned once, rather than once from A004, A006,
# and A053.
# ============================================================


CYCLE_DETECTION_QUERY = """

// ============================================================
// 3-HOP CYCLES
// ============================================================

MATCH (a:Account)-[:TRANSFERRED]->(b:Account)
      -[:TRANSFERRED]->(c:Account)
      -[:TRANSFERRED]->(a)

WHERE
    a.id < b.id
    AND a.id < c.id

RETURN
    [a.id, b.id, c.id] AS account_sequence,
    3 AS hop_count


UNION


// ============================================================
// 4-HOP CYCLES
// ============================================================

MATCH (a:Account)-[:TRANSFERRED]->(b:Account)
      -[:TRANSFERRED]->(c:Account)
      -[:TRANSFERRED]->(d:Account)
      -[:TRANSFERRED]->(a)

WHERE
    a.id < b.id
    AND a.id < c.id
    AND a.id < d.id

RETURN
    [a.id, b.id, c.id, d.id] AS account_sequence,
    4 AS hop_count


UNION


// ============================================================
// 5-HOP CYCLES
// ============================================================

MATCH (a:Account)-[:TRANSFERRED]->(b:Account)
      -[:TRANSFERRED]->(c:Account)
      -[:TRANSFERRED]->(d:Account)
      -[:TRANSFERRED]->(e:Account)
      -[:TRANSFERRED]->(a)

WHERE
    a.id < b.id
    AND a.id < c.id
    AND a.id < d.id
    AND a.id < e.id

RETURN
    [a.id, b.id, c.id, d.id, e.id] AS account_sequence,
    5 AS hop_count


UNION


// ============================================================
// 6-HOP CYCLES
// ============================================================

MATCH (a:Account)-[:TRANSFERRED]->(b:Account)
      -[:TRANSFERRED]->(c:Account)
      -[:TRANSFERRED]->(d:Account)
      -[:TRANSFERRED]->(e:Account)
      -[:TRANSFERRED]->(f:Account)
      -[:TRANSFERRED]->(a)

WHERE
    a.id < b.id
    AND a.id < c.id
    AND a.id < d.id
    AND a.id < e.id
    AND a.id < f.id

RETURN
    [a.id, b.id, c.id, d.id, e.id, f.id] AS account_sequence,
    6 AS hop_count
"""


# ============================================================
# THREE-HOP CYCLE DETECTION
# ============================================================

THREE_HOP_CYCLE_QUERY = """
MATCH (a:Account)-[:TRANSFERRED]->(b:Account)
      -[:TRANSFERRED]->(c:Account)
      -[:TRANSFERRED]->(a)

WHERE
    a.id < b.id
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
# EXECUTE CYCLE DETECTION
# ============================================================

def detect_cycles():
    """
    Execute the cycle detection query.

    Returns:
        list[dict]
    """

    from detector.db import run_query

    return run_query(CYCLE_DETECTION_QUERY)