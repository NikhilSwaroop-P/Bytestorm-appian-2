#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting Azure deployment for Bytestorm-appian-2 project${NC}"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}Error: Azure CLI is not installed. Please install it first.${NC}"
    echo "Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Set variables
resourceGroup="BytestormAppRG"
location="eastus"
appServicePlan="BytestormPlan"
webAppName="bytestorm-product-discovery"
storageAccountName="bytestormstore"
storageContainerName="appain-uploads"

# Login to Azure
echo -e "${YELLOW}Logging in to Azure...${NC}"
az login

# Create resource group if it doesn't exist
echo -e "${YELLOW}Creating resource group if it doesn't exist...${NC}"
az group create --name $resourceGroup --location $location

# Create storage account if it doesn't exist
echo -e "${YELLOW}Creating storage account if it doesn't exist...${NC}"
az storage account create --name $storageAccountName --resource-group $resourceGroup --location $location --sku Standard_LRS --kind StorageV2

# Get storage connection string
echo -e "${YELLOW}Getting storage connection string...${NC}"
connectionString=$(az storage account show-connection-string --name $storageAccountName --resource-group $resourceGroup --output tsv)

# Create container if it doesn't exist
echo -e "${YELLOW}Creating storage container if it doesn't exist...${NC}"
az storage container create --name $storageContainerName --connection-string "$connectionString" --public-access blob

# Create App Service Plan if it doesn't exist
echo -e "${YELLOW}Creating App Service Plan if it doesn't exist...${NC}"
az appservice plan create --name $appServicePlan --resource-group $resourceGroup --is-linux --sku B1

# Create Web App if it doesn't exist
echo -e "${YELLOW}Creating Web App if it doesn't exist...${NC}"
az webapp create --name $webAppName --resource-group $resourceGroup --plan $appServicePlan --runtime "PYTHON|3.10"

# Configure Web App settings
echo -e "${YELLOW}Configuring Web App settings...${NC}"
az webapp config set --name $webAppName --resource-group $resourceGroup \
    --startup-file "startup.sh" \
    --python-version "3.10"

# Set environment variables
echo -e "${YELLOW}Setting environment variables...${NC}"
az webapp config appsettings set --name $webAppName --resource-group $resourceGroup \
    --settings \
    WEBSITE_RUN_FROM_PACKAGE="1" \
    AZURE_STORAGE_CONNECTION_STRING="$connectionString" \
    AZURE_STORAGE_CONTAINER_NAME="$storageContainerName" \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true" \
    FLASK_ENV="production" \
    SECRET_KEY="$(openssl rand -hex 24)"

# Deploy the application
echo -e "${YELLOW}Deploying application...${NC}"
echo -e "${YELLOW}Creating zip package...${NC}"
cd "$(dirname "$0")" # Navigate to script directory
zip -r ../deployment.zip . -x "*.git*" -x "*__pycache__*" -x "*.pyc"

echo -e "${YELLOW}Deploying to Azure...${NC}"
az webapp deployment source config-zip --resource-group $resourceGroup --name $webAppName --src ../deployment.zip

# Clean up
echo -e "${YELLOW}Cleaning up...${NC}"
rm -f ../deployment.zip

# Show the URL to access the webapp
url="https://$webAppName.azurewebsites.net"
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}Your application is now available at:${NC} $url"

# Add reminder to set Voyage API key
echo -e "${YELLOW}IMPORTANT: Remember to set your Voyage API key${NC}"
echo "You can set it using the command:"
echo "az webapp config appsettings set --name $webAppName --resource-group $resourceGroup --settings VOYAGE_API_KEY=your_api_key_here"

echo -e "${GREEN}Deployment process complete!${NC}" 