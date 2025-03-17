#!/bin/bash

# Parameters
IFS=',' read -r -a MODEL_NAMES <<< "$1"  # Split the comma-separated model names into an array
CAPACITY="$2"
USER_REGION="$3"

if [ ${#MODEL_NAMES[@]} -ne 2 ] || [ -z "$CAPACITY" ]; then
    echo "❌ ERROR: Exactly two model names and capacity must be provided as arguments."
    exit 1
fi

echo "🔄 Using Models: ${MODEL_NAMES[0]} and ${MODEL_NAMES[1]} with Minimum Capacity: $CAPACITY"

# Authenticate using Managed Identity
echo "Authentication using Managed Identity..."
if ! az login --use-device-code; then
   echo "❌ Error: Failed to login using Managed Identity."
   exit 1
fi

# Fetch the default subscription ID dynamically
SUBSCRIPTION_ID=$(az account show --query "id" -o tsv)

# Set Azure subscription
echo "🔄 Setting Azure subscription..."
if ! az account set --subscription "$SUBSCRIPTION_ID"; then
    echo "❌ ERROR: Invalid subscription ID or insufficient permissions."
    exit 1
fi
echo "✅ Azure subscription set successfully."

# List of regions to check
DEFAULT_REGIONS=("eastus" "uksouth" "eastus2" "northcentralus" "swedencentral" "westus" "westus2" "southcentralus" "canadacentral")

# Prioritize user-provided region if given
if [ -n "$USER_REGION" ]; then
    # Ensure the user-provided region is checked first
    REGIONS=("$USER_REGION" "${DEFAULT_REGIONS[@]}")
else
    REGIONS=("${DEFAULT_REGIONS[@]}")
fi

echo "✅ Retrieved Azure regions. Checking availability..."

VALID_REGIONS=()
for REGION in "${REGIONS[@]}"; do
    echo "----------------------------------------"
    echo "🔍 Checking region: $REGION"

    # Fetch quota information for the region
    QUOTA_INFO=$(az cognitiveservices usage list --location "$REGION" --output json)
    if [ -z "$QUOTA_INFO" ]; then
        echo "⚠️ WARNING: Failed to retrieve quota for region $REGION. Skipping."
        continue
    fi

    # Initialize a flag to track if both models have sufficient quota in the region
    BOTH_MODELS_AVAILABLE=true

    for MODEL_NAME in "${MODEL_NAMES[@]}"; do
        echo "🔍 Checking model: $MODEL_NAME"

        # Extract model quota information
        MODEL_INFO=$(echo "$QUOTA_INFO" | awk -v model="\"value\": \"OpenAI.Standard.$MODEL_NAME\"" '
            BEGIN { RS="},"; FS="," }
            $0 ~ model { print $0 }
        ')

        if [ -z "$MODEL_INFO" ]; then
            echo "⚠️ WARNING: No quota information found for model: OpenAI.Standard.$MODEL_NAME in $REGION. Skipping."
            BOTH_MODELS_AVAILABLE=false
            break  # If any model is not available, no need to check further for this region
        fi

        CURRENT_VALUE=$(echo "$MODEL_INFO" | awk -F': ' '/"currentValue"/ {print $2}' | tr -d ',' | tr -d ' ')
        LIMIT=$(echo "$MODEL_INFO" | awk -F': ' '/"limit"/ {print $2}' | tr -d ',' | tr -d ' ')

        CURRENT_VALUE=${CURRENT_VALUE:-0}
        LIMIT=${LIMIT:-0}

        CURRENT_VALUE=$(echo "$CURRENT_VALUE" | cut -d'.' -f1)
        LIMIT=$(echo "$LIMIT" | cut -d'.' -f1)

        AVAILABLE=$((LIMIT - CURRENT_VALUE))

        echo "✅ Model: OpenAI.Standard.$MODEL_NAME | Used: $CURRENT_VALUE | Limit: $LIMIT | Available: $AVAILABLE"

        # Check if quota is sufficient
        if [ "$AVAILABLE" -lt "$CAPACITY" ]; then
            echo "❌ ERROR: 'OpenAI.Standard.$MODEL_NAME' in $REGION has insufficient quota. Required: $CAPACITY, Available: $AVAILABLE"
            BOTH_MODELS_AVAILABLE=false
            break
        fi
    done

    # If both models have sufficient quota, add region to valid regions
    if [ "$BOTH_MODELS_AVAILABLE" = true ]; then
        echo "✅ Both models have sufficient quota in $REGION."
        VALID_REGIONS+=("$REGION")
    fi
done

# Determine final result
if [ ${#VALID_REGIONS[@]} -eq 0 ]; then
    echo "❌ No region with sufficient quota found for both models. Blocking deployment."
    exit 0
else
    echo "✅ Suggested Regions: ${VALID_REGIONS[*]}"
    exit 0
fi
