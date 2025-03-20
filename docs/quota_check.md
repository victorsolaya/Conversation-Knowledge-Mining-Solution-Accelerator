This file will contain instructions for checking quota availability using two different scripts

## Check Quota Availability Before Deployment

Before deploying the accelerator, check the quota availability for the model to ensure sufficient capacity.

## **If using Azure Portal and Cloud Shell**

1. Navigate to the [Azure Portal](https://portal.azure.com).
2. Click on **Azure Cloud Shell** in the top right navigation menu.
3. Run the following commands:

    ```sh
    curl -L -o check_azure_quota_public.sh "https://raw.githubusercontent.com/microsoft/Conversation-Knowledge-Mining-Solution-Accelerator/main/infra/scripts/quota_check_params.sh"
    chmod +x quota_check_params.sh
    ./quota_check_params.sh <model_name:capacity> [<model_region>]
    ```
## **If using VS Code or Codespaces**

1. Run the script:

    ```sh
    ./quota_check_params.sh <model_name:capacity> [<model_region>]
    ```
     
   If you see this error:  _bash: az: command not found_

   ```sh
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   az login
   ```
Then, rerun the script.
   
**Parameters**
- `<model_name:capacity>`: The name and required capacity for each model, in the format model_name:capacity (**e.g., gpt-4o-mini:30,text-embedding-ada-002:20**).
- `[<model_region>] (optional)`: The Azure region to check first. If not provided, all supported regions will be checked (**e.g., eastus**).

If sufficient quota is available, proceed with the deployment.
