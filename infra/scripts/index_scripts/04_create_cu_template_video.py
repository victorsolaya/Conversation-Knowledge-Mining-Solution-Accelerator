# Import required modules
from azure.keyvault.secrets import SecretClient  
from azure.identity import DefaultAzureCredential
import sys
from pathlib import Path
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from content_understanding_client import AzureContentUnderstandingClient
from pathlib import Path

key_vault_name = 'kv_to-be-replaced'
managed_identity_client_id = 'mici_to-be-replaced'

VIDEO_LOCATION = Path("../data/FlightSimulator.mp4")

def get_secrets_from_kv(kv_name, secret_name):

    # Set the name of the Azure Key Vault  
    key_vault_name = kv_name 
    credential = DefaultAzureCredential(managed_identity_client_id=managed_identity_client_id)

    # Create a secret client object using the credential and Key Vault name  
    secret_client = SecretClient(vault_url=f"https://{key_vault_name}.vault.azure.net/", credential=credential)  

    # Retrieve the secret value  
    return secret_client.get_secret(secret_name).value


# Add the parent directory to the path to use shared modules
parent_dir = Path(Path.cwd()).parent
sys.path.append(str(parent_dir))

AZURE_AI_ENDPOINT = get_secrets_from_kv(key_vault_name,"AZURE-OPENAI-CU-ENDPOINT")
AZURE_OPENAI_CU_KEY = get_secrets_from_kv(key_vault_name,"AZURE-OPENAI-CU-KEY")
AZURE_AI_API_VERSION = "2024-12-01-preview" 


credential = DefaultAzureCredential(managed_identity_client_id=managed_identity_client_id)
token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
client = AzureContentUnderstandingClient(
    endpoint=AZURE_AI_ENDPOINT,
    api_version=AZURE_AI_API_VERSION,
    subscription_key=AZURE_OPENAI_CU_KEY,
    token_provider=token_provider
)

ANALYZER_ID = "ckm-video"
ANALYZER_TEMPLATE_FILE = 'ckm-analyzer_config_video.json'

# Create analyzer
response = client.begin_create_analyzer(ANALYZER_ID, analyzer_template_path=ANALYZER_TEMPLATE_FILE)
result = client.poll_result(response)

# Submit the video for content analysis
response = client.begin_analyze(ANALYZER_ID, file_location=VIDEO_LOCATION)

# Wait for the analysis to complete and get the content analysis result
video_cu_result = client.poll_result(response, timeout_seconds=3600)  # 1 hour timeout

# Print the content analysis result
print("Video Content Understanding result: ", video_cu_result)

# Delete the analyzer if it is no longer needed
client.delete_analyzer(ANALYZER_ID)