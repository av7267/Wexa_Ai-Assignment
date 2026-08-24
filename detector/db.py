import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

_driver = None


def get_driver():
    """
    Lazily initialize and return the CognoDB Neo4j driver.
    """
    global _driver

    if _driver is None:
        uri = os.getenv("COGNODB_URI")
        username = os.getenv("COGNODB_USERNAME")
        password = os.getenv("COGNODB_PASSWORD")

        if not uri:
            raise RuntimeError("COGNODB_URI is missing from .env")
        if not username:
            raise RuntimeError("COGNODB_USERNAME is missing from .env")
        if not password:
            raise RuntimeError("COGNODB_PASSWORD is missing from .env")

        _driver = GraphDatabase.driver(
            uri,
            auth=(username, password),
        )

    return _driver


def verify_connection():
    """
    Verify that the application can connect to CognoDB.
    """
    driver = get_driver()
    driver.verify_connectivity()
    print("CognoDB connection successful.")


def run_query(query, parameters=None):
    """
    Execute an openCypher query against CognoDB.

    Parameters are passed separately from the Cypher query,
    preventing string-concatenated queries.
    """
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            query,
            parameters or {},
        )
        return [record.data() for record in result]


def close_driver():
    """
    Close the database driver.
    """
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None