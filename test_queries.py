from detector.db import run_query


query = """
MATCH (a:Account)-[t:TRANSFERRED]->(b:Account)
RETURN
    a.id AS from_account,
    b.id AS to_account,
    t.amount AS amount,
    t.timestamp AS timestamp
LIMIT 5
"""


results = run_query(query)

for result in results:
    print(result)