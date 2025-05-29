# Azure Deployment Guide for Bytestorm Product Discovery System

This guide provides instructions for deploying the AI-Powered Product Discovery and Checkout Pipeline to Microsoft Azure cloud services.

## Prerequisites

- An Azure account with active subscription
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed
- [Python 3.8+](https://www.python.org/downloads/) installed locally
- Basic knowledge of terminal/command line operations

## Deployment Options

### Option 1: Automated Deployment (Recommended)

We've created a deployment script that automates the entire process of setting up and deploying to Azure.

1. Make the deployment script executable:
   ```bash
   chmod +x deploy-to-azure.sh
   ```

2. Run the deployment script:
   ```bash
   ./deploy-to-azure.sh
   ```

3. Follow the prompts in the script. You will need to log in to your Azure account during the process.

4. After deployment is complete, set your Voyage API key:
   ```bash
   az webapp config appsettings set --name bytestorm-product-discovery --resource-group BytestormAppRG --settings VOYAGE_API_KEY=your_api_key_here
   ```

5. Access your application at the URL provided at the end of the deployment script.

### Option 2: Manual Deployment

If you prefer to deploy manually or need to customize the deployment:

1. **Create Azure Resources**:
   - Create a Resource Group
   - Create an App Service Plan (Linux, B1 or higher recommended)
   - Create a Web App with Python 3.10 runtime
   - Create an Azure Storage Account and Blob Container for uploads

2. **Configure App Settings**:
   - Set the following environment variables in your Web App:
     - `AZURE_STORAGE_CONNECTION_STRING`: Your storage account connection string
     - `AZURE_STORAGE_CONTAINER_NAME`: Your blob container name (default: appain-uploads)
     - `VOYAGE_API_KEY`: Your Voyage AI API key
     - `SECRET_KEY`: A secure random string for Flask sessions
     - `FLASK_ENV`: Set to "production"

3. **Deploy Your Code**:
   - Compress your project files (excluding `.git`, `__pycache__`, etc.)
   - Deploy using Azure CLI:
     ```bash
     az webapp deployment source config-zip --resource-group <YOUR_RESOURCE_GROUP> --name <YOUR_WEBAPP_NAME> --src ./deployment.zip
     ```

## Application Architecture in Azure

The application uses the following Azure services:

- **Azure App Service**: Hosts the Flask web application
- **Azure Blob Storage**: Stores uploaded images and provides content delivery
- **Azure Monitor**: Provides logging and monitoring capabilities

## Monitoring and Maintenance

- **View Logs**: 
  ```bash
  az webapp log tail --name bytestorm-product-discovery --resource-group BytestormAppRG
  ```

- **Restart App Service**:
  ```bash
  az webapp restart --name bytestorm-product-discovery --resource-group BytestormAppRG
  ```

## Scaling Considerations

For production workloads:

1. **Upgrade App Service Plan**: Consider upgrading to a P1v2 or higher tier for better performance
2. **Configure Auto-scaling**: Set up rules based on CPU usage or request count
3. **Database Migration**: For large product databases, consider migrating to Azure SQL or Cosmos DB
4. **AI Processing**: For intensive AI workloads, consider using Azure Machine Learning or Azure Cognitive Services

## Troubleshooting

If you encounter issues:

1. Check application logs in the Azure portal
2. Verify all environment variables are set correctly
3. Ensure your Voyage API key is valid and has sufficient quota
4. Check network connectivity to dependent services

## Cost Management

The resources created by the deployment script are minimal but will incur charges:
- App Service (B1): ~$13/month
- Storage Account: Pay-as-you-go based on usage (~$0.02/GB)

For development and testing, consider stopping the App Service when not in use.

## Security Notes

- The default deployment uses HTTP. For production, enable HTTPS and configure SSL
- For user data and payment processing, implement proper encryption and security practices
- Consider implementing Azure Key Vault for sensitive configuration values

For additional assistance, contact the project maintainers. 