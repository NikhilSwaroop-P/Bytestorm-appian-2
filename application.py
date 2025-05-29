#!/usr/bin/env python
"""
Azure App Service entry point for the Product Recommendation System.
"""
import os
import sys

# Add the root directory to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from src.frontend.app import create_app

# Create the Flask application
app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 