from detector.db import verify_connection, run_query, close_driver


def main():

    print("=" * 60)
    print("NEO4J CONNECTION TEST")
    print("=" * 60)

    try:

        # Test authentication/connectivity
        verify_connection()

        # Test Cypher query
        query = """
        RETURN
            1 AS test,
            "Neo4j connection works" AS message
        """

        results = run_query(query)

        print()
        print("Query result:")
        print(results)

        print()
        print("SUCCESS")

    except Exception as e:

        print()
        print("CONNECTION FAILED")
        print(type(e).__name__)
        print(e)

    finally:

        close_driver()


if __name__ == "__main__":
    main()