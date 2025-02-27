## Add Azure Function Users to Database
    
    This script automates the process of adding Azure Function identities as users in a database and assigning them appropriate roles.
    ## Prerequisites

    Before running the script, ensure you have:

    - **[Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli#install)** installed.
    - **[Python 3]( https://www.python.org/downloads/)** installed.
    - **[Microsoft ODBC Driver 17 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server?view=sql-server-ver16#version-17)** installed.
    ## Usage

    1. Clone the repository:

        ```sh
        git clone https://github.com/microsoft/Conversation-Knowledge-Mining-Solution-Accelerator.git
    
    2. Navigate to script directory
        ```sh
        cd infra\scripts\add_user_scripts

    3. Run the script
        ```sh
        chmod +x ./add_user.sh
        ./add_user.sh <resourcegroupname> <solution_prefix>