param existingAIProjectName string
param existingAIServiceSubscription string
param existingAIServiceResourceGroup string
param aiSearchName string
param aiSearchResourceId string
param aiSearchLocation string
param solutionName string

resource existingAiProject 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' existing = {
  name: existingAIProjectName
  scope: resourceGroup()
}

resource connection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = {
  name: 'myVectorStoreProjectConnectionName-${solutionName}'
  parent: existingAiProject
  properties: {
    category: 'CognitiveSearch'
    target: 'https://${aiSearchName}.search.windows.net'
    authType: 'AAD'
    isSharedToAll: true
    metadata: {
      ApiType: 'Azure'
      ResourceId: aiSearchResourceId
      location: aiSearchLocation
    }
  }
}

output existingAIServiceSubscription string = existingAIServiceSubscription
output existingAIServiceResourceGroup string = existingAIServiceResourceGroup
output existingAiProjectId string = existingAiProject.id
output existingAiProjectName string = existingAiProject.name
