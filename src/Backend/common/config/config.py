import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        self.sqldb_database = os.getenv("SQLDB_DATABASE")
        self.sqldb_password = os.getenv("SQLDB_PASSWORD")
        self.sqldb_server = os.getenv("SQLDB_SERVER")
        self.sqldb_username = os.getenv("SQLDB_USERNAME")
        self.driver = "{ODBC Driver 17 for SQL Server}"
        self.mid_id = os.environ.get("SQLDB_USER_MID")

        self.azure_openai_endpoint = os.getenv("AZURE_OPEN_AI_ENDPOINT")
        self.azure_openai_deployment_model = os.getenv("AZURE_OPEN_AI_DEPLOYMENT_MODEL")
        self.azure_openai_api_key = os.getenv("AZURE_OPEN_AI_API_KEY")
        self.azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")

        self.azure_ai_search_endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
        self.azure_ai_search_api_key = os.getenv("AZURE_AI_SEARCH_API_KEY")
        self.azure_ai_search_index = os.getenv("AZURE_AI_SEARCH_INDEX")

        self.use_ai_project_client = os.environ.get("USE_AI_PROJECT_CLIENT", "False").lower() == "true"
        self.azure_ai_project_conn_string = os.environ.get("AZURE_AI_PROJECT_CONN_STRING")
