# Import required modules
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
import sys
from pathlib import Path
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from content_understanding_client import AzureContentUnderstandingClient
from pathlib import Path
from azure.storage.filedatalake import DataLakeServiceClient
from datetime import datetime, timedelta
from openai import AzureOpenAI
import re
import time
import struct
import pyodbc
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

key_vault_name = "kv_to-be-replaced"
managed_identity_client_id = "mici_to-be-replaced"

file_system_client_name = "data"
directory_name = "videodata"


def get_secrets_from_kv(kv_name, secret_name):

    # Set the name of the Azure Key Vault
    key_vault_name = kv_name
    credential = DefaultAzureCredential(
        managed_identity_client_id=managed_identity_client_id
    )

    # Create a secret client object using the credential and Key Vault name
    secret_client = SecretClient(
        vault_url=f"https://{key_vault_name}.vault.azure.net/", credential=credential
    )

    # Retrieve the secret value
    return secret_client.get_secret(secret_name).value


# Add the parent directory to the path to use shared modules
parent_dir = Path(Path.cwd()).parent
sys.path.append(str(parent_dir))

AZURE_AI_ENDPOINT = get_secrets_from_kv(key_vault_name, "AZURE-OPENAI-CU-ENDPOINT")
AZURE_OPENAI_CU_KEY = get_secrets_from_kv(key_vault_name, "AZURE-OPENAI-CU-KEY")
AZURE_AI_API_VERSION = "2024-12-01-preview"

search_endpoint = get_secrets_from_kv(key_vault_name, "AZURE-SEARCH-ENDPOINT")
search_key = get_secrets_from_kv(key_vault_name, "AZURE-SEARCH-KEY")

openai_api_key = get_secrets_from_kv(key_vault_name, "AZURE-OPENAI-KEY")
openai_api_base = get_secrets_from_kv(key_vault_name, "AZURE-OPENAI-ENDPOINT")
openai_api_version = get_secrets_from_kv(
    key_vault_name, "AZURE-OPENAI-PREVIEW-API-VERSION"
)
deployment = get_secrets_from_kv(key_vault_name, "AZURE-OPEN-AI-DEPLOYMENT-MODEL")

credential = DefaultAzureCredential(
    managed_identity_client_id=managed_identity_client_id
)
token_provider = get_bearer_token_provider(
    credential, "https://cognitiveservices.azure.com/.default"
)
client = AzureContentUnderstandingClient(
    endpoint=AZURE_AI_ENDPOINT,
    api_version=AZURE_AI_API_VERSION,
    subscription_key=AZURE_OPENAI_CU_KEY,
    token_provider=token_provider,
)

ANALYZER_ID = "ckm-video"
ANALYZER_TEMPLATE_FILE = "ckm-analyzer_config_video.json"

# Create analyzer
response = client.begin_create_analyzer(
    ANALYZER_ID, analyzer_template_path=ANALYZER_TEMPLATE_FILE
)
result = client.poll_result(response)


account_name = get_secrets_from_kv(key_vault_name, "ADLS-ACCOUNT-NAME")
account_url = f"https://{account_name}.dfs.core.windows.net"

service_client = DataLakeServiceClient(
    account_url, credential=credential, api_version="2023-01-03"
)




# Function: Get Embeddings
def get_embeddings(text, openai_api_base, openai_api_version, openai_api_key):
    model_id = "text-embedding-ada-002"
    client = AzureOpenAI(
        api_version=openai_api_version,
        azure_endpoint=openai_api_base,
        api_key=openai_api_key,
    )

    embedding = client.embeddings.create(input=text, model=model_id).data[0].embedding

    return embedding


# Function: Clean Spaces with Regex -
def clean_spaces_with_regex(text):
    # Use a regular expression to replace multiple spaces with a single space
    cleaned_text = re.sub(r"\s+", " ", text)
    # Use a regular expression to replace consecutive dots with a single dot
    cleaned_text = re.sub(r"\.{2,}", ".", cleaned_text)
    return cleaned_text


def chunk_data(text):
    tokens_per_chunk = 1024
    text = clean_spaces_with_regex(text)

    sentences = text.split(". ")  # Split text into sentences
    chunks = []
    current_chunk = ""
    current_chunk_token_count = 0

    # Iterate through each sentence
    for sentence in sentences:
        # Split sentence into tokens
        tokens = sentence.split()

        # Check if adding the current sentence exceeds tokens_per_chunk
        if current_chunk_token_count + len(tokens) <= tokens_per_chunk:
            # Add the sentence to the current chunk
            if current_chunk:
                current_chunk += ". " + sentence
            else:
                current_chunk += sentence
            current_chunk_token_count += len(tokens)
        else:
            # Add current chunk to chunks list and start a new chunk
            chunks.append(current_chunk)
            current_chunk = sentence
            current_chunk_token_count = len(tokens)

    # Add the last chunk
    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def prepare_search_doc(content, document_id):
    chunks = chunk_data(content)
    chunk_num = 0
    for chunk in chunks:
        chunk_num += 1
        chunk_id = document_id + "_" + str(chunk_num).zfill(2)

        try:
            v_contentVector = get_embeddings(
                str(chunk), openai_api_base, openai_api_version, openai_api_key
            )
        except Exception:
            time.sleep(30)
            try:
                v_contentVector = get_embeddings(
                    str(chunk), openai_api_base, openai_api_version, openai_api_key
                )
            except Exception:
                v_contentVector = []
        result = {
            "id": chunk_id,
            "chunk_id": chunk_id,
            "content": chunk,
            "sourceurl": path.name.split("/")[-1],
            "contentVector": v_contentVector,
        }
    return result


index_name = "video_index"

search_credential = AzureKeyCredential(search_key)

search_client = SearchClient(search_endpoint, index_name, search_credential)

driver = "{ODBC Driver 18 for SQL Server}"
server = get_secrets_from_kv(key_vault_name, "SQLDB-SERVER")
database = get_secrets_from_kv(key_vault_name, "SQLDB-DATABASE")

token_bytes = credential.get_token(
    "https://database.windows.net/.default"
).token.encode("utf-16-LE")
token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
SQL_COPT_SS_ACCESS_TOKEN = 1256

# Set up the connection
connection_string = f"DRIVER={driver};SERVER={server};DATABASE={database};"
conn = pyodbc.connect(
    connection_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct}
)

# conn = pymssql.connect(server, username, password, database)
cursor = conn.cursor()
print("Connected to the database")
cursor.execute("DROP TABLE IF EXISTS processed_data")
conn.commit()

file_system_client = service_client.get_file_system_client(file_system_client_name)
paths = file_system_client.get_paths(path=directory_name)

conversationIds = []
docs = []
counter = 0
# process and upload audio files to search index
for path in paths:
    file_client = file_system_client.get_file_client(path.name)
    data_file = file_client.download_file()
    data = data_file.readall()
    try:
        # # Analyzer file
        response = client.begin_analyze(ANALYZER_ID, file_location="", file_data=data)
        result = client.poll_result(response)

        file_name = path.name.split("/")[-1]
        start_time = file_name.replace(".wav", "")[-19:]

        timestamp_format = "%Y-%m-%d %H_%M_%S"  # Adjust format if necessary
        start_timestamp = datetime.strptime(start_time, timestamp_format)

        conversation_id = file_name.split("convo_", 1)[1].split("_")[0]
        conversationIds.append(conversation_id)

        duration = int(
            result["result"]["contents"][0]["fields"]["Duration"]["valueString"]
        )
        end_timestamp = str(start_timestamp + timedelta(seconds=duration))
        end_timestamp = end_timestamp.split(".")[0]

        summary = result["result"]["contents"][0]["fields"]["summary"]["valueString"]
        satisfied = result["result"]["contents"][0]["fields"]["satisfied"][
            "valueString"
        ]
        sentiment = result["result"]["contents"][0]["fields"]["sentiment"][
            "valueString"
        ]
        topic = result["result"]["contents"][0]["fields"]["topic"]["valueString"]
        key_phrases = result["result"]["contents"][0]["fields"]["keyPhrases"][
            "valueString"
        ]
        complaint = result["result"]["contents"][0]["fields"]["complaint"][
            "valueString"
        ]
        content = result["result"]["contents"][0]["fields"]["content"]["valueString"]
        # print(topic)
        cursor.execute(
            f"INSERT INTO processed_data (ConversationId, EndTime, StartTime, Content, summary, satisfied, sentiment, topic, key_phrases, complaint) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                conversation_id,
                end_timestamp,
                start_timestamp,
                content,
                summary,
                satisfied,
                sentiment,
                topic,
                key_phrases,
                complaint,
            ),
        )
        conn.commit()

        keyPhrases = key_phrases.split(",")
        for keyPhrase in keyPhrases:
            cursor.execute(
                f"INSERT INTO processed_data_key_phrases (ConversationId, key_phrase, sentiment) VALUES (?,?,?)",
                (conversation_id, keyPhrase, sentiment),
            )

        document_id = conversation_id

        result = prepare_search_doc(content, document_id)
        docs.append(result)
        counter += 1
    except Exception:
        pass

    if docs != [] and counter % 10 == 0:
        result = search_client.upload_documents(documents=docs)
        docs = []


# upload the last batch
if docs != []:
    search_client.upload_documents(documents=docs)

conn.commit()
cursor.close()
conn.close()
