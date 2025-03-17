import struct
from common.config.config import Config
import logging
from azure.identity import DefaultAzureCredential
import pyodbc

def get_db_connection():
    """Get a connection to the SQL database"""
    config = Config()

    server = config.sqldb_server
    database = config.sqldb_database
    username = config.sqldb_username
    password = config.sqldb_database
    driver = config.driver
    mid_id = config.mid_id

    try:
        credential = DefaultAzureCredential(managed_identity_client_id=mid_id)

        token_bytes = credential.get_token(
            "https://database.windows.net/.default"
        ).token.encode("utf-16-LE")
        token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
        SQL_COPT_SS_ACCESS_TOKEN = (
            1256  # This connection option is defined by microsoft in msodbcsql.h
        )

        # Set up the connection
        connection_string = f"DRIVER={driver};SERVER={server};DATABASE={database};"
        conn = pyodbc.connect(
            connection_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct}
        )

        logging.info("Connected using Default Azure Credential")

        return conn
    except pyodbc.Error as e:
        logging.error(f"Failed with Default Credential: {str(e)}")
        conn = pyodbc.connect(
            f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}",
            timeout=5
        )
        
        logging.info("Connected using Username & Password")
        return conn