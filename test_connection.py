import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("COGNODB_URI")
USERNAME = os.getenv("COGNODB_USERNAME")
PASSWORD = os.getenv("COGNODB_PASSWORD")

driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD),
)

try:
    with driver.session() as session:
        result = session.run("RETURN 1 AS test")
        record = result.single()

        print("Got:", record["test"])

finally:
    driver.close()