from detector.db import run_query


def print_section(title):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


# ---------------------------------------------------------
# 1. Count accounts
# ---------------------------------------------------------

print_section("ACCOUNT COUNT")

result = run_query(
    """
    MATCH (a:Account)
    RETURN count(a) AS account_count
    """
)

print(
    "Accounts:",
    result[0]["account_count"]
)


# ---------------------------------------------------------
# 2. Count transactions
# ---------------------------------------------------------

print_section("TRANSACTION COUNT")

result = run_query(
    """
    MATCH ()-[t:TRANSFERRED]->()
    RETURN count(t) AS transaction_count
    """
)

print(
    "Transactions:",
    result[0]["transaction_count"]
)


# ---------------------------------------------------------
# 3. Check account properties
# ---------------------------------------------------------

print_section("SAMPLE ACCOUNTS")

result = run_query(
    """
    MATCH (a:Account)
    RETURN
        a.id AS id,
        a.name AS name,
        a.account_type AS account_type,
        a.created_at AS created_at
    ORDER BY a.id
    LIMIT 5
    """
)

for account in result:
    print(account)


# ---------------------------------------------------------
# 4. Check transaction properties
# ---------------------------------------------------------

print_section("SAMPLE TRANSACTIONS")

result = run_query(
    """
    MATCH (from:Account)-[t:TRANSFERRED]->(to:Account)

    RETURN
        from.id AS from_account,
        to.id AS to_account,
        t.transaction_id AS transaction_id,
        t.amount AS amount,
        t.timestamp AS timestamp

    LIMIT 5
    """
)

for transaction in result:
    print(transaction)


# ---------------------------------------------------------
# 5. Check relationship type
# ---------------------------------------------------------

print_section("RELATIONSHIP TYPES")

result = run_query(
    """
    MATCH ()-[t]->()
    RETURN type(t) AS relationship_type, count(t) AS count
    ORDER BY relationship_type
    """
)

for relationship in result:
    print(relationship)


# ---------------------------------------------------------
# 6. Find 3-hop cycles
# ---------------------------------------------------------

print_section("3-HOP CYCLES")

result = run_query(
    """
    MATCH
        (a:Account)-[:TRANSFERRED]->(b:Account)
            -[:TRANSFERRED]->(c:Account)
            -[:TRANSFERRED]->(a)

    WHERE
        a.id < b.id
        AND a.id < c.id

    RETURN
        a.id AS account_a,
        b.id AS account_b,
        c.id AS account_c
    ORDER BY account_a
    """
)

print(
    "3-hop cycles found:",
    len(result)
)

for cycle in result:
    print(
        f"{cycle['account_a']} -> "
        f"{cycle['account_b']} -> "
        f"{cycle['account_c']} -> "
        f"{cycle['account_a']}"
    )


print()
print("Graph verification complete.")