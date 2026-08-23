import os

from dotenv import load_dotenv
from neo4j import GraphDatabase


# Load environment variables
load_dotenv()


COGNODB_URI = os.getenv("COGNODB_URI")
COGNODB_USERNAME = os.getenv("COGNODB_USERNAME")
COGNODB_PASSWORD = os.getenv("COGNODB_PASSWORD")


# Validate configuration
if not COGNODB_URI:
    raise RuntimeError("COGNODB_URI is missing from .env")

if not COGNODB_USERNAME:
    raise RuntimeError("COGNODB_USERNAME is missing from .env")

if not COGNODB_PASSWORD:
    raise RuntimeError("COGNODB_PASSWORD is missing from .env")


# Connect to CognoDB using the official Neo4j driver.
driver = GraphDatabase.driver(
    COGNODB_URI,
    auth=(COGNODB_USERNAME, COGNODB_PASSWORD),
)


def verify_connection():
    """
    Verify that the application can connect to CognoDB.
    """

    driver.verify_connectivity()

    print("CognoDB connection successful.")


def run_query(query, parameters=None):
    """
    Execute an openCypher query against CognoDB.

    Parameters are passed separately from the Cypher query,
    preventing string-concatenated queries.
    """

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

    driver.close()