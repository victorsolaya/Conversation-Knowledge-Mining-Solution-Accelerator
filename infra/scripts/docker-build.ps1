# Define script parameters
param (
    [string]$AZURE_SUBSCRIPTION_ID,
    [string]$ENV_NAME,
    [string]$AZURE_LOCATION,
    [string]$AZURE_RESOURCE_GROUP,
    [string]$USE_LOCAL_BUILD,
    [string]$ACR_NAME,
    [string]$ACR_IMAGE_TAG
)

# Convert USE_LOCAL_BUILD to Boolean
$USE_LOCAL_BUILD = if ($USE_LOCAL_BUILD -match "^(?i:true)$") { $true } else { $false }

# Validate required parameters
if (-not $AZURE_SUBSCRIPTION_ID -or -not $ENV_NAME -or -not $AZURE_LOCATION -or -not $AZURE_RESOURCE_GROUP -or -not $ACR_NAME) {
    Write-Error "Missing required arguments. Usage: docker-build.ps1 <AZURE_SUBSCRIPTION_ID> <ENV_NAME> <AZURE_LOCATION> <AZURE_RESOURCE_GROUP> <USE_LOCAL_BUILD> <ACR_NAME> [ACR_IMAGE_TAG]"
    exit 1
}

# Exit early if local build is not requested
if ($USE_LOCAL_BUILD -eq $false) {
    Write-Output "Local Build not enabled. Using prebuilt image."
    exit 0
}

Write-Output "Local Build enabled. Starting build process."

# STEP 1: Set Azure subscription
az account set --subscription "$AZURE_SUBSCRIPTION_ID"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to set Azure subscription."
    exit 1
}

# STEP 2: Login to Azure Container Registry
Write-Host "Logging into Azure Container Registry: $ACR_NAME"
az acr login -n $ACR_NAME
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to log in to ACR"
    exit 1
}

# STEP 3: Get current script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# STEP 4: Resolve full paths to Dockerfiles and build contexts
$WebAppDockerfilePath = Join-Path $ScriptDir "..\..\src\App\WebApp.Dockerfile" | Resolve-Path
$WebAppContextPath = Join-Path $ScriptDir "..\..\src\App" | Resolve-Path
$ApiAppDockerfilePath = Join-Path $ScriptDir "..\..\src\api\ApiApp.Dockerfile" | Resolve-Path
$ApiAppContextPath = Join-Path $ScriptDir "..\..\src\api" | Resolve-Path

# STEP 5: Define function to build and push Docker images
function Build-And-Push-Image {
    param (
        [string]$IMAGE_NAME,
        [string]$BUILD_PATH,
        [string]$BUILD_CONTEXT,
        [string]$TAG
    )

    $IMAGE_URI = "$ACR_NAME.azurecr.io/$($IMAGE_NAME):$TAG"

    Write-Host "`n--- Building Docker image: $IMAGE_URI ---"
    docker build --no-cache -f $BUILD_PATH -t $IMAGE_URI $BUILD_CONTEXT

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to build Docker image: $IMAGE_URI"
        exit 1
    }

    Write-Host "--- Pushing Docker image to ACR: $IMAGE_URI ---"
    docker push $IMAGE_URI
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to push Docker image: $IMAGE_URI"
        exit 1
    }

    Write-Host "--- Docker image pushed successfully: $IMAGE_URI ---`n"
}

# STEP 6: Build and push images with provided tag
Build-And-Push-Image "km-api" $ApiAppDockerfilePath $ApiAppContextPath $ACR_IMAGE_TAG
Build-And-Push-Image "km-app" $WebAppDockerfilePath $WebAppContextPath $ACR_IMAGE_TAG

Write-Host "`nAll Docker images built and pushed successfully with tag: $ACR_IMAGE_TAG"
