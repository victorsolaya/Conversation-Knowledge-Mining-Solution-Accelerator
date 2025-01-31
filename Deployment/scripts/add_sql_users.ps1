param(
    [string] $resourceGroupName,
    [string] $serverName,
    [string] $databaseName,
    [string] $chartJsFuncAppName,  # Function App Name of Chart JS
    [string] $ragFuncAppName  # Function App Name of RAG
)

try {
    Write-Host "Installing modules"
    Import-Module -Name SqlServer

    # Import modules
    Import-Module SqlServer

    Write-Host "Modules imported successfully."

    # Authenticate using current logged in user
    az login
    $loggedInUser = (Get-AzADUser -SignedIn).UserPrincipalName

    Set-AzSqlServerActiveDirectoryAdministrator -ResourceGroupName $resourceGroupName `
                                            -ServerName $serverName `
                                            -DisplayName $loggedInUser
                                            
    Write-Host "Entra ID Admin set to: $loggedInUser"

    # Define connection details
    $connectionString = "Server=tcp:${serverName}.database.windows.net,1433;Initial Catalog=$databaseName;Authentication=Active Directory Integrated;"

    Write-Host "Database Connection String: $connectionString"

    # Define the T-SQL script to add a new user and grant permissions
    $queryChartJs = @"
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = '${chartJsFuncAppName}')
BEGIN
    CREATE USER [${chartJsFuncAppName}] FROM EXTERNAL PROVIDER;
    ALTER ROLE db_datareader ADD MEMBER [${chartJsFuncAppName}]; -- Grant SELECT on all user tables and views.
    ALTER ROLE db_datawriter ADD MEMBER [${chartJsFuncAppName}]; -- Grant INSERT, UPDATE, and DELETE on all user tables and views.
END
"@

# Define the T-SQL script to add a new user and grant permissions
    $queryRag = @"
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = '${ragFuncAppName}')
BEGIN
    CREATE USER [${ragFuncAppName}] FROM EXTERNAL PROVIDER;
    ALTER ROLE db_datareader ADD MEMBER [${ragFuncAppName}]; -- Grant SELECT on all user tables and views.
    ALTER ROLE db_datawriter ADD MEMBER [${ragFuncAppName}]; -- Grant INSERT, UPDATE, and DELETE on all user tables and views.
END
"@

# ALTER ROLE db_ddladmin ADD MEMBER [${principalName}]; -- Grants CREATE, ALTER, and DROP on tables, views, functions, procedures, etc.

    Write-Host "Executing SQL script for Chart JS Func..."
    Invoke-Sqlcmd -ConnectionString $connectionString -Query $queryChartJs
    Write-Host "SQL statement executed for Chart JS."

    Write-Host "Executing SQL script for RAG.."
    Invoke-Sqlcmd -ConnectionString $connectionString -Query $queryRag

    Write-Host "SQL statement executed for RAG."
} catch {
    # Print the detailed error message
    Write-Host "An error occurred while querying the database:"
    Write-Host "Error Message: $($_.Exception.Message)"
    Write-Host "Error Type: $($_.Exception.GetType())"
    Write-Host "Stack Trace: $($_.Exception.StackTrace)"
    if ($_.Exception.InnerException) {
        Write-Host "Inner Exception: $($_.Exception.InnerException.Message)"
    }
} 