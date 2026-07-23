#!/bin/bash
set -e

IMAGE=$1
if [ -z "$IMAGE" ]; then
    echo "Error: Image argument is required (e.g. qrregistry.azurecr.io/ecommerce-app:latest)"
    exit 1
fi

RESOURCE_GROUP=${RESOURCE_GROUP:-"qr-payment-rg"}
ACI_GROUP_NAME=${ACI_GROUP_NAME:-"qr-payment-test-group"}
LOCATION=${LOCATION:-"eastus"}
YAML_FILE=${YAML_FILE:-"./deploy-aci.yaml"}

echo "--------------------------------------------------"
echo "Deploying Container Group to Azure Container Instances"
echo "Resource Group: $RESOURCE_GROUP"
echo "Container Group: $ACI_GROUP_NAME"
echo "Target Ecommerce Image: $IMAGE"
echo "--------------------------------------------------"

# 1. Ensure Resource Group exists
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output table

# 2. Update the image tag inside a temporary copy of deploy-aci.yaml
TEMP_YAML=$(mktemp)
sed "s|qrregistry.azurecr.io/ecommerce-app:latest|$IMAGE|g" "$YAML_FILE" > "$TEMP_YAML"

# 3. Deploy/Update the Container Group using the updated YAML file
echo "Applying container group definition..."
az container create \
    --resource-group "$RESOURCE_GROUP" \
    --file "$TEMP_YAML"

# 4. Clean up temporary file
rm -f "$TEMP_YAML"

echo "✅ ACI Deployment complete for $ACI_GROUP_NAME!"