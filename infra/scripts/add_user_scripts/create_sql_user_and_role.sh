#!/bin/bash

# Parameters
SqlServerName="$1"
SqlDatabaseName="$2"
ClientId="$3"
DisplayName="$4"
UserManagedIdentityClientId="$5"
DatabaseRole="$6"

# Function to check if a command exists or runs successfully
function check_command() {
    if ! eval "$1" &> /dev/null; then
        echo "Error: Command '$1' failed or is not installed."
        exit 1
    fi
}

# Ensure required commands are available
check_command "az --version"
check_command "sqlcmd '-?'"

# Authenticate with Azure
if az account show &> /dev/null; then
    echo "Already authenticated with Azure."
else
    if [ -n "$UserManagedIdentityClientId" ]; then
        echo "Authenticating with Managed Identity..."
        az login --identity --client-id ${UserManagedIdentityClientId}
    else
        echo "Authenticating with Azure CLI..."
        az login
    fi
fi

# Construct the SQL query
SQL_QUERY="
DECLARE @username nvarchar(max) = N'$DisplayName';
DECLARE @clientId uniqueidentifier = '$ClientId';
DECLARE @sid NVARCHAR(max) = CONVERT(VARCHAR(max), CONVERT(VARBINARY(16), @clientId), 1);
DECLARE @cmd NVARCHAR(max) = N'CREATE USER [' + @username + '] WITH SID = ' + @sid + ', TYPE = E;';
IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = @username)
BEGIN
    EXEC(@cmd)
END
DECLARE @roles NVARCHAR(max) = '$DatabaseRole';
DECLARE @role NVARCHAR(max);
WHILE LEN(@roles) > 0
BEGIN
    SET @role = LTRIM(RTRIM(LEFT(@roles, CHARINDEX(',', @roles + ',') - 1)));
    SET @roles = STUFF(@roles, 1, LEN(@role) + 1, '');
    EXEC sp_addrolemember @role, @username;
END
"

# Create heredoc for the SQL query
SQL_QUERY_FINAL=$(cat <<EOF
$SQL_QUERY
EOF
)

# Check if OS is Windows
OS=$(uname | tr '[:upper:]' '[:lower:]')

if [[ "$OS" == "mingw"* || "$OS" == "cygwin"* || "$OS" == "msys"* ]]; then
    echo "Running on Windows OS, will use interactive login"
    echo "Getting signed-in user email"
    UserEmail=$(az ad signed-in-user show --query mail -o tsv)
    if [[ -z "$UserEmail" ]]; then
        UserEmail=$(az ad signed-in-user show --query userPrincipalName -o tsv)
    fi
    echo "Executing SQL query..."
    sqlcmd -S "$SqlServerName.database.windows.net" -d "$SqlDatabaseName" -G -U "$UserEmail" -Q "$SQL_QUERY_FINAL" || {
        echo "Failed to execute SQL query."
        exit 1
    }
else
    echo "Running on Linux or macOS, will use access token"
    mkdir -p usersql
    # Get an access token for the Azure SQL Database
    echo "Retrieving access token..."
    az account get-access-token --resource https://database.windows.net --output tsv | cut -f 1 | tr -d '\n' | iconv -f ascii -t UTF-16LE > usersql/tokenFile
    if [ $? -ne 0 ]; then
        echo "Failed to retrieve access token."
        exit 1
    fi
    errorFlag=false
    # Execute the SQL query
    echo "Executing SQL query..."
    sqlcmd -S "$SqlServerName.database.windows.net" -d "$SqlDatabaseName" -G -P usersql/tokenFile -Q "$SQL_QUERY_FINAL" || {
        echo "Failed to execute SQL query."
        errorFlag=true
    }
    #delete the usersql directory
    rm -rf usersql
    if [ "$errorFlag" = true ]; then
        exit 1
    fi
fi

echo "SQL user and role assignment completed successfully."