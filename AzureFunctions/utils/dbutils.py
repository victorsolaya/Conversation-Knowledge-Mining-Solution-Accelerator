from azure.identity import DefaultAzureCredential
import logging
import os
import pyodbc
import struct

# get database connection
def get_db_connection():
    driver = "{ODBC Driver 17 for SQL Server}"
    server = os.environ.get("SQLDB_SERVER")
    database = os.environ.get("SQLDB_DATABASE")
    username = os.environ.get("SQLDB_USERNAME")
    password = os.environ.get("SQLDB_PASSWORD")

    # Attempt connection using Managed identity
    try:
        credential = DefaultAzureCredential()

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

        # Connect using Username & Password if it fails to connect using Default Credentials
        conn = pyodbc.connect(
            f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}",
            timeout=5
        )
        logging.info("Connected using Username & Password")
        return conn
