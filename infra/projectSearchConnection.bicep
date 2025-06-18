param existingAIProjectName string
// param existingAIServicesName string
param existingAIServiceSubscription string
param existingAIServiceResourceGroup string
// param aiSearchName string
// param aiSearchResourceId string
// param aiSearchLocation string
// param solutionName string

// resource existingAIServices 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing =  {
//   name: existingAIServicesName
//   scope: resourceGroup()
// }

resource existingAiProject 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' existing = {
  name: existingAIProjectName
  scope: resourceGroup(existingAIServiceSubscription, existingAIServiceResourceGroup)
}

// resource connection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = {
//   name: 'myVectorStoreProjectConnectionName-${solutionName}'
//   parent: existingAiProject
//   properties: {
//     category: 'CognitiveSearch'
//     target: 'https://${aiSearchName}.search.windows.net'
//     authType: 'AAD'
//     isSharedToAll: true
//     metadata: {
//       ApiType: 'Azure'
//       ResourceId: aiSearchResourceId
//       location: aiSearchLocation
//     }
//   }
// }

output existingAIServiceSubscription string = existingAIServiceSubscription
output existingAIServiceResourceGroup string = existingAIServiceResourceGroup
// output resourcegroupNames string = resourceGroup().name
// output existingAiProjectid string = !empty(existingAiProject) ? existingAiProject.id : ''
// output existingAiProjectName string = !empty(existingAiProject) ? existingAiProject.name : ''
output existingAiProjectName string = existingAiProject.name
// output existingAiProjectLocation string = !empty(existingAiProject) ? existingAiProject.location : ''
