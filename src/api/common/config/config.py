import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        # Initialize Key Vault client
        key_vault_url = os.getenv("AZURE_KEY_VAULT_URL")
        credential = DefaultAzureCredential()
        self.secret_client = SecretClient(vault_url=key_vault_url, credential=credential)

        # SQL Database configuration
        self.sqldb_database = os.getenv("SQLDB_DATABASE")
        self.sqldb_server = os.getenv("SQLDB_SERVER")
        self.sqldb_username = os.getenv("SQLDB_USERNAME")
        self.driver = "{ODBC Driver 17 for SQL Server}"
        self.mid_id = os.getenv("SQLDB_USER_MID")

        # Azure OpenAI configuration
        self.azure_openai_endpoint = os.getenv("AZURE_OPEN_AI_ENDPOINT")
        self.azure_openai_deployment_model = os.getenv("AZURE_OPEN_AI_DEPLOYMENT_MODEL")
        self.azure_openai_api_key = self.get_secret("AZURE_OPENAI_API_KEY")
        self.azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        self.azure_openai_resource = os.getenv("AZURE_OPENAI_RESOURCE")

        # Azure AI Search configuration
        self.azure_ai_search_endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
        self.azure_ai_search_api_key = self.get_secret("AZURE_AI_SEARCH_API_KEY")
        self.azure_ai_search_index = os.getenv("AZURE_AI_SEARCH_INDEX")

        # AI Project Client configuration
        self.use_ai_project_client = os.getenv("USE_AI_PROJECT_CLIENT", "False").lower() == "true"
        self.azure_ai_project_conn_string = self.get_secret("AZURE_AI_PROJECT_CONN_STRING")

        # Chat history configuration
        self.use_chat_history_enabled = os.getenv("USE_CHAT_HISTORY_ENABLED", "false").strip().lower() == "true"
        self.azure_cosmosdb_database = os.getenv("AZURE_COSMOSDB_DATABASE")
        self.azure_cosmosdb_account = os.getenv("AZURE_COSMOSDB_ACCOUNT")
        self.azure_cosmosdb_conversations_container = os.getenv("AZURE_COSMOSDB_CONVERSATIONS_CONTAINER")
        self.azure_cosmosdb_enable_feedback = os.getenv("AZURE_COSMOSDB_ENABLE_FEEDBACK", "false").lower() == "true"

    def get_secret(self, secret_name):
        """Retrieve a secret value from Azure Key Vault."""
        secret_name_value = os.getenv(secret_name, "")
        try:
            secret = self.secret_client.get_secret(secret_name_value)
            return secret.value
        except Exception as e:
            print(f"Error retrieving secret '{secret_name_value}': {e}")
            return None
