#!/usr/bin/env python
"""
Run script for the frontend Flask application.
"""
import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.frontend.app import create_app

if __name__ == "__main__":
    app = create_app()
    print(f"Starting Appain Product Finder on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000) 