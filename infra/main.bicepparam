using './main.bicep'

param environmentName = readEnvironmentVariable('ENVIRONMENT_NAME', 'env_name')
param contentUnderstandingLocation = readEnvironmentVariable('CONTENT_UNDERSTANDING_LOCATION', 'swedencentral')
param secondaryLocation = readEnvironmentVariable('SECONDARY_LOCATION', 'eastus2')
param deploymentType = readEnvironmentVariable('AZURE_OPEN_AI_MODEL_DEPLOYMENT_TYPE', 'GlobalStandard')
param gptModelName = readEnvironmentVariable('AZURE_OPEN_AI_DEPLOYMENT_MODEL', 'gpt-4o-mini')
param gptDeploymentCapacity = int(readEnvironmentVariable('AZURE_OPEN_AI_DEPLOYMENT_MODEL_CAPACITY', '30'))
param embeddingModel = readEnvironmentVariable('AZURE_OPENAI_EMBEDDING_MODEL', 'text-embedding-ada-002')
param embeddingDeploymentCapacity = int(readEnvironmentVariable('AZURE_OPENAI_EMBEDDING_MODEL_CAPACITY', '80'))
