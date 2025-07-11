#Requires -Version 7.2

<#
.SYNOPSIS
    Creates a SQL user and assigns the user account to one or more roles.

.DESCRIPTION
    This script connects to an Azure SQL Database using a managed identity and creates a user from an external identity.
    It assigns the user to the specified database role if not already assigned.

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

# SQL Script to create user and assign role
$sql = @"
IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = N'$DisplayName')
BEGIN
    CREATE USER [$DisplayName] FROM EXTERNAL PROVIDER;
END
EXEC sp_addrolemember '$DatabaseRole', [$DisplayName];
"@

Write-Output "`nExecuting SQL:`n$sql`n"

# Connect to Azure using Managed Identity
Connect-AzAccount -Identity -AccountId $ManagedIdentityClientId
$token = (Get-AzAccessToken -ResourceUrl 'https://database.windows.net/').Token

# Execute SQL
Invoke-Sqlcmd -ServerInstance $SqlServerName -Database $SqlDatabaseName -AccessToken $token -Query $sql -ErrorAction Stop