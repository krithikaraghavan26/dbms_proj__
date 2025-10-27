# db_connector.py
import cx_Oracle
import os
from dotenv import load_dotenv

load_dotenv()

# Get credentials from the .env file
ORACLE_USER = os.getenv('ORACLE_USER')
ORACLE_PASSWORD = os.getenv('ORACLE_PASSWORD')
ORACLE_CONNECT_STRING = os.getenv('ORACLE_CONNECT_STRING')

def get_db_connection():
    """Returns a new connection from the pool."""
    try:
        # For a small project, a simple connection is fine, but a pool is better practice:
        conn = cx_Oracle.connect(ORACLE_USER, ORACLE_PASSWORD, ORACLE_CONNECT_STRING)
        return conn
    except cx_Oracle.Error as e:
        error, = e.args
        print(f"Database connection error: {error.code} - {error.message}")
        return None

def fetch_all_as_dict(cursor):
    """Fetches all rows from a cursor and returns them as a list of dictionaries."""
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]