import os

from dotenv import load_dotenv
from neo4j import GraphDatabase


# Load .env
load_dotenv()


NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE")


# Validate configuration before creating the driver
if not NEO4J_URI:
    raise RuntimeError("NEO4J_URI is missing from .env")

if not NEO4J_USERNAME:
    raise RuntimeError("NEO4J_USERNAME is missing from .env")

if not NEO4J_PASSWORD:
    raise RuntimeError("NEO4J_PASSWORD is missing from .env")

if not NEO4J_DATABASE:
    raise RuntimeError("NEO4J_DATABASE is missing from .env")


# Create Neo4j driver
driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
)


def verify_connection():
    """
    Verify that the application can connect to Neo4j Aura.
    """

    driver.verify_connectivity()

    print("Neo4j connection successful.")


def run_query(query, parameters=None):
    """
    Execute a Cypher query and return the results as dictionaries.
    """

    with driver.session(database=NEO4J_DATABASE) as session:
        result = session.run(
            query,
            parameters or {},
        )

        return [record.data() for record in result]


def close_driver():
    """
    Close the Neo4j driver.
    """

    driver.close()