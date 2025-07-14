#Requires -Version 7.4

<#
.SYNOPSIS
    Creates a SQL user and assigns the user account to a role using managed identity authentication.

.DESCRIPTION
    - Connects to Azure using a user-assigned managed identity.
    - Creates a SQL user from an external identity if not exists.
    - Assigns the user to a database role if not already assigned.

.PARAMETER SqlServerName
    Azure SQL Server FQDN (e.g., myserver.database.windows.net)

.PARAMETER SqlDatabaseName
    The name of the SQL database

.PARAMETER DisplayName
    The display name (user name) for SQL user creation

.PARAMETER ManagedIdentityClientId
    The client ID of the user-assigned managed identity used to authenticate

.PARAMETER DatabaseRole
    The role to assign (e.g., db_datareader)
#>

param(
    [string] $SqlServerName,
    [string] $SqlDatabaseName,
    [string] $DisplayName,
    [string] $ManagedIdentityClientId,
    [string] $DatabaseRole
)

###---------------------------------------------------
### Function: Resolve-Module
###---------------------------------------------------
function Resolve-Module {
    param (
        [Parameter(Mandatory = $true)]
        [string]$ModuleName
    )

    try {
        if (Get-Module -Name $ModuleName -ListAvailable | Where-Object { $_.Name -eq $ModuleName }) {
            if (-not (Get-Module -Name $ModuleName)) {
                Import-Module $ModuleName -Force
            }
        } else {
            $found = Find-Module -Name $ModuleName -ErrorAction SilentlyContinue
            if ($found) {
                Install-Module -Name $ModuleName -Force -Scope CurrentUser
                Import-Module $ModuleName -Force
            } else {
                throw "Module '$ModuleName' not found in repository."
            }
        }
    } catch {
        Write-Error "Resolve-Module failed: $($_.Exception.Message)"
        exit 1
    }
}

###---------------------------------------------------
### Resolve Required Modules
###---------------------------------------------------
Resolve-Module -moduleName Az.Resources
Resolve-Module -moduleName SqlServer

###---------------------------------------------------
### Authenticate with Managed Identity
###---------------------------------------------------
try {
    Connect-AzAccount -Identity -AccountId $ManagedIdentityClientId -ErrorAction Stop
    $token = (Get-AzAccessToken -ResourceUrl 'https://database.windows.net/').Token
} catch {
    Write-Error "Azure login or token retrieval failed: $($_.Exception.Message)"
    exit 1
}

###---------------------------------------------------
### Prepare SQL Script
###---------------------------------------------------
$sql = @"
IF NOT EXISTS (
    SELECT 1 FROM sys.database_principals WHERE name = N'$DisplayName'
)
BEGIN
    CREATE USER [$DisplayName] FROM EXTERNAL PROVIDER;
    PRINT 'User created.';
END
ELSE
BEGIN
    PRINT 'User already exists.';
END

IF NOT EXISTS (
    SELECT 1
    FROM sys.database_role_members rm
    JOIN sys.database_principals r ON rm.role_principal_id = r.principal_id
    JOIN sys.database_principals u ON rm.member_principal_id = u.principal_id
    WHERE r.name = N'$DatabaseRole' AND u.name = N'$DisplayName'
)
BEGIN
    EXEC sp_addrolemember N'$DatabaseRole', N'$DisplayName';
    PRINT 'Role assigned.';
END
ELSE
BEGIN
    PRINT 'User already in role.';
END
"@

Write-Output "`nSQL to Execute:`n$sql`n"

###---------------------------------------------------
### Execute SQL
###---------------------------------------------------
try {
    Invoke-Sqlcmd -ServerInstance $SqlServerName -Database $SqlDatabaseName -AccessToken $token -Query $sql -ErrorAction Stop
    exit 0
} catch {
    Write-Error "SQL execution failed: $($_.Exception.Message)"
    exit 1
}
