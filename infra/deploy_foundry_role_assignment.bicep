param principalId string = ''
param roleDefinitionId string
param roleAssignmentName string = ''
param aiServicesName string
param aiProjectName string = ''
param aiLocation string=''
param aiKind string=''
param aiSkuName string=''
param enableSystemAssignedIdentity bool = true
param customSubDomainName string = ''
param publicNetworkAccess string = ''
param defaultNetworkAction string
param vnetRules array = []
param ipRules array = []

// AI Services with Identity (enabled only if flag is true)
resource aiServices 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = if (enableSystemAssignedIdentity) {
  name: aiServicesName
  location: aiLocation
  kind: aiKind
  sku: {
    name: aiSkuName
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    allowProjectManagement: true
    customSubDomainName: customSubDomainName 
    networkAcls: {
      defaultAction: defaultNetworkAction
      virtualNetworkRules: vnetRules
      ipRules: ipRules
    }
    publicNetworkAccess: publicNetworkAccess

  }
}

// AI Project with Identity (only if name provided and flag is true)
resource aiProject 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = if (!empty(aiProjectName) && enableSystemAssignedIdentity) {
  name: aiProjectName
  parent: aiServices
  location: aiLocation
  identity: {
    type: 'SystemAssigned'
  }
  properties: {}
}

// Role Assignment to AI Services
resource roleAssignmentToFoundry 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: roleAssignmentName
  scope: aiServices
  properties: {
    roleDefinitionId: roleDefinitionId
    principalId: principalId
  }
}

// Outputs
output aiServicesPrincipalId string = aiServices.identity.principalId
output aiProjectPrincipalId string = !empty(aiProjectName) ? aiProject.identity.principalId : ''
