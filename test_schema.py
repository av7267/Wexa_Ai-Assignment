from detector.db import run_query


def main():

    print("=" * 60)
    print("NEO4J DATABASE INSPECTION")
    print("=" * 60)

    print("\n--- NODE LABELS ---")

    labels = run_query("""
        CALL db.labels()
        YIELD label
        RETURN label
        ORDER BY label
    """)

    for row in labels:
        print(row)

    print("\n--- RELATIONSHIP TYPES ---")

    relationships = run_query("""
        CALL db.relationshipTypes()
        YIELD relationshipType
        RETURN relationshipType
        ORDER BY relationshipType
    """)

    for row in relationships:
        print(row)

    print("\n--- NODE COUNT ---")

    node_count = run_query("""
        MATCH (n)
        RETURN count(n) AS count
    """)

    print(node_count)

    print("\n--- RELATIONSHIP COUNT ---")

    relationship_count = run_query("""
        MATCH ()-[r]->()
        RETURN count(r) AS count
    """)

    print(relationship_count)

    print("\n--- SAMPLE NODES ---")

    nodes = run_query("""
        MATCH (n)
        RETURN
            labels(n) AS labels,
            properties(n) AS properties
        LIMIT 10
    """)

    for row in nodes:
        print(row)

    print("\n--- SAMPLE RELATIONSHIPS ---")

    relationships = run_query("""
        MATCH (a)-[r]->(b)
        RETURN
            labels(a) AS from_labels,
            properties(a) AS from_properties,
            type(r) AS relationship_type,
            properties(r) AS relationship_properties,
            labels(b) AS to_labels,
            properties(b) AS to_properties
        LIMIT 10
    """)

    for row in relationships:
        print(row)


if __name__ == "__main__":
    main()