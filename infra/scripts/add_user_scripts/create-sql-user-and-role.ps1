#Requires -Version 7.0

<#
.SYNOPSIS
    Creates a SQL user and assigns the user account to one or more roles.

.DESCRIPTION
    During an application deployment, the managed identity (and potentially the developer identity)
    must be added to the SQL database as a user and assigned to one or more roles. This script
    accomplishes this task using Azure AD authentication.

.PARAMETER SqlServerName
    The name of the Azure SQL Server resource.

.PARAMETER SqlDatabaseName
    The name of the Azure SQL Database where the user will be created.

.PARAMETER ClientId
    The Client (Principal) ID (GUID) of the identity to be added.

.PARAMETER DisplayName
    The Object (Principal) display name of the identity to be added.

.PARAMETER UseManagedIdentity
    Switch to indicate whether to use a Managed Identity for authentication (useful for automation).
    If not provided, it will use your currently logged-in Azure AD account.

.PARAMETER DatabaseRole
    A comma-separated list of database roles that should be assigned to the user (e.g., db_datareader, db_datawriter, db_owner).
#>

param (
    [string] $SqlServerName,
    [string] $SqlDatabaseName,
    [string] $ClientId,
    [string] $DisplayName,
    [switch] $UseManagedIdentity,
    [string] $DatabaseRole
)

function Resolve-Module($moduleName) {
    if (-not (Get-Module -ListAvailable -Name $moduleName)) {
        Install-Module -Name $moduleName -Scope CurrentUser -Force -AllowClobber
    }
    Import-Module -Name $moduleName -Force
}

### Load Required Modules
Resolve-Module -moduleName Az.Accounts
Resolve-Module -moduleName Az.Resources
Resolve-Module -moduleName SqlServer

### Authenticate and Get Access Token
if ($UseManagedIdentity) {
    Write-Host "[INFO] Logging in using Managed Identity..."
    Connect-AzAccount -Identity
} else {
    Write-Host "[INFO] Logging in using current user identity..."
    Connect-AzAccount
}

# Split the roles by comma and remove any extra spaces
$roles = $DatabaseRole -split "," | ForEach-Object { $_.Trim() }

foreach ($role in $roles) {
    Write-Output "Assigning Role: $role"
    
### Generate SQL Script
$sql = @"
DECLARE @username nvarchar(max) = N'$($DisplayName)';
DECLARE @clientId uniqueidentifier = '$($ClientId)';
DECLARE @sid NVARCHAR(max) = CONVERT(VARCHAR(max), CONVERT(VARBINARY(16), @clientId), 1);
DECLARE @cmd NVARCHAR(max) = N'CREATE USER [' + @username + '] WITH SID = ' + @sid + ', TYPE = E;';
IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = @username)
BEGIN
    EXEC(@cmd)
END
EXEC sp_addrolemember '$role', @username;
"@

Write-Output "`nSQL to be executed:`n$($sql)`n"

# Get the Azure SQL token for authentication
$token = (Get-AzAccessToken -ResourceUrl https://database.windows.net/).Token

### Execute the SQL Command
Write-Host "[INFO] Executing SQL against $SqlDatabaseName..."
Invoke-Sqlcmd -ServerInstance "$SqlServerName.database.windows.net" -Database $SqlDatabaseName -AccessToken $token -Query $sql -ErrorAction Stop
}

Write-Host "[SUCCESS] User and role assignment completed."
