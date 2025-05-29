"""
Azure Storage helper for managing image uploads and retrieval.
"""
import os
from datetime import datetime, timedelta
import uuid
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas

def get_blob_service_client():
    """Get Azure Blob Service client from connection string."""
    connect_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    if not connect_str:
        raise ValueError("Azure Storage connection string not found in environment variables")
    return BlobServiceClient.from_connection_string(connect_str)

def upload_image(file_stream, filename=None):
    """
    Upload an image to Azure Blob Storage.
    
    Args:
        file_stream: The file-like object to upload
        filename: Optional filename, will generate UUID if not provided
        
    Returns:
        str: URL to access the blob
    """
    if not filename:
        filename = f"{uuid.uuid4()}.jpg"
    
    blob_service_client = get_blob_service_client()
    container_name = os.environ.get("AZURE_STORAGE_CONTAINER_NAME", "appain-uploads")
    
    # Get container client
    try:
        container_client = blob_service_client.get_container_client(container_name)
        # Check if container exists, create if not
        if not container_client.exists():
            container_client = blob_service_client.create_container(container_name)
    except Exception as e:
        print(f"Error accessing/creating container: {e}")
        raise
    
    # Upload the file
    blob_client = container_client.get_blob_client(filename)
    blob_client.upload_blob(file_stream, overwrite=True)
    
    # Generate URL with SAS token that expires in 1 hour
    sas_token = generate_blob_sas(
        account_name=blob_service_client.account_name,
        container_name=container_name,
        blob_name=filename,
        account_key=blob_service_client.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1)
    )
    
    # Return the full URL
    return f"{blob_client.url}?{sas_token}"

def delete_image(filename):
    """Delete an image from Azure Blob Storage."""
    blob_service_client = get_blob_service_client()
    container_name = os.environ.get("AZURE_STORAGE_CONTAINER_NAME", "appain-uploads")
    
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(filename)
    
    # Delete the blob if it exists
    if blob_client.exists():
        blob_client.delete_blob()
        return True
    return False 