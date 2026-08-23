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
// ============================================================
// 3-hop cycles
// ============================================================

MATCH (a:Account)-[:TRANSFERRED]->(b:Account)
      -[:TRANSFERRED]->(c:Account)
      -[:TRANSFERRED]->(a)

WHERE a.id < b.id
  AND a.id < c.id
  AND b.id <> c.id

RETURN [a.id, b.id, c.id] AS account_sequence,
       3 AS hop_count

UNION

// ============================================================
// 4-hop cycles
// ============================================================

MATCH (a:Account)-[:TRANSFERRED]->(b:Account)
      -[:TRANSFERRED]->(c:Account)
      -[:TRANSFERRED]->(d:Account)
      -[:TRANSFERRED]->(a)

WHERE a.id < b.id
  AND a.id < c.id
  AND a.id < d.id
  AND b.id <> c.id
  AND b.id <> d.id
  AND c.id <> d.id

RETURN [a.id, b.id, c.id, d.id] AS account_sequence,
       4 AS hop_count

UNION

// ============================================================
// 5-hop cycles
// ============================================================

MATCH (a:Account)-[:TRANSFERRED]->(b:Account)
      -[:TRANSFERRED]->(c:Account)
      -[:TRANSFERRED]->(d:Account)
      -[:TRANSFERRED]->(e:Account)
      -[:TRANSFERRED]->(a)

WHERE a.id < b.id
  AND a.id < c.id
  AND a.id < d.id
  AND a.id < e.id
  AND b.id <> c.id
  AND b.id <> d.id
  AND b.id <> e.id
  AND c.id <> d.id
  AND c.id <> e.id
  AND d.id <> e.id

RETURN [a.id, b.id, c.id, d.id, e.id] AS account_sequence,
       5 AS hop_count

UNION

// ============================================================
// 6-hop cycles
// ============================================================

MATCH (a:Account)-[:TRANSFERRED]->(b:Account)
      -[:TRANSFERRED]->(c:Account)
      -[:TRANSFERRED]->(d:Account)
      -[:TRANSFERRED]->(e:Account)
      -[:TRANSFERRED]->(f:Account)
      -[:TRANSFERRED]->(a)

WHERE a.id < b.id
  AND a.id < c.id
  AND a.id < d.id
  AND a.id < e.id
  AND a.id < f.id
  AND b.id <> c.id
  AND b.id <> d.id
  AND b.id <> e.id
  AND b.id <> f.id
  AND c.id <> d.id
  AND c.id <> e.id
  AND c.id <> f.id
  AND d.id <> e.id
  AND d.id <> f.id
  AND e.id <> f.id

RETURN [a.id, b.id, c.id, d.id, e.id, f.id] AS account_sequence,
       6 AS hop_count

ORDER BY hop_count, account_sequence
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


# ============================================================
# ACCOUNT QUERIES
# ============================================================

ACCOUNT_LIST_QUERY = """
MATCH (a:Account)

OPTIONAL MATCH (a)-[out:TRANSFERRED]->()
WITH a, count(out) AS outgoing_count

OPTIONAL MATCH ()-[inc:TRANSFERRED]->(a)
WITH
    a,
    outgoing_count,
    count(inc) AS incoming_count

RETURN
    a.id AS id,
    a.name AS name,
    a.account_type AS account_type,
    a.created_at AS created_at,
    outgoing_count + incoming_count AS transaction_count

ORDER BY a.id
"""

ACCOUNT_DETAIL_QUERY = """
MATCH (a:Account {id: $account_id})
RETURN
    a.id AS id,
    a.name AS name,
    a.account_type AS account_type,
    a.created_at AS created_at
"""


ACCOUNT_NEIGHBORHOOD_QUERY = """
MATCH (a:Account {id: $account_id})

OPTIONAL MATCH (a)-[out:TRANSFERRED]->(to:Account)
OPTIONAL MATCH (from:Account)-[inc:TRANSFERRED]->(a)

RETURN
    collect(DISTINCT {
        account_id: to.id,
        account_name: to.name,
        transaction_id: out.transaction_id,
        amount: out.amount,
        timestamp: out.timestamp
    }) AS outgoing,

    collect(DISTINCT {
        account_id: from.id,
        account_name: from.name,
        transaction_id: inc.transaction_id,
        amount: inc.amount,
        timestamp: inc.timestamp
    }) AS incoming
"""