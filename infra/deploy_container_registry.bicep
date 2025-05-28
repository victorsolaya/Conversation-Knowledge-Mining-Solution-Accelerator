param solutionName string
param solutionLocation string

var abbrs = loadJsonContent('./abbreviations.json')
var containerRegistryName = '${abbrs.containers.containerRegistry}${solutionName}'
var containerRegistryNameCleaned = replace(containerRegistryName, '-', '')
 
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2021-09-01' = {
  name: containerRegistryName
  location: solutionLocation
  sku: {
    name: 'Premium'
  }
  properties: {
    adminUserEnabled: true
    dataEndpointEnabled: false
    networkRuleBypassOptions: 'AzureServices'
    networkRuleSet: {
      defaultAction: 'Deny'
    }
    policies: {
      quarantinePolicy: {
        status: 'disabled'
      }
      retentionPolicy: {
        status: 'enabled'
        days: 7
      }
      trustPolicy: {
        status: 'disabled'
        type: 'Notary'
      }
    }
    publicNetworkAccess: 'Enabled'
    zoneRedundancy: 'Disabled'
  }
}
 
output createdAcrName string = containerRegistryNameCleaned
output createdAcrId string = containerRegistry.id
 