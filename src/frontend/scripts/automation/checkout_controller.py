"""
Checkout Automation Controller

This module provides the API routes and controller logic for the AI-powered
checkout automation system. It interfaces between the Flask web application
and the Node.js automation script that uses Puppeteer and Google Gemini.
"""

import os
import json
import time
import uuid
import subprocess
import threading
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, current_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("checkout_automation")

# Create Blueprint for automation routes
router = Blueprint('checkout_automation', __name__)

# Dictionary to store job status information
automation_jobs = {}

def get_automation_script_path():
    """Return the path to the checkout automation script"""
    # Get the directory where this controller lives
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # The checkout_automation.js file should be in the same directory
    return os.path.join(current_dir, 'checkout_automation.js')

def run_automation(job_id, checkout_url, product_info):
    """
    Run the checkout automation script as a subprocess
    
    Args:
        job_id (str): Unique identifier for this automation job
        checkout_url (str): URL of the checkout page to automate
        product_info (dict): Information about the product being purchased
    """
    try:
        # Update job status
        automation_jobs[job_id]['status'] = 'running'
        automation_jobs[job_id]['progress'] = 5
        automation_jobs[job_id]['logs'].append('Starting checkout automation...')
        
        # Get the path to the automation script
        script_path = get_automation_script_path()
        
        # Ensure the screenshots directory exists
        screenshots_dir = os.path.join(os.path.dirname(script_path), 'screenshots')
        os.makedirs(screenshots_dir, exist_ok=True)
        
        # Create a temporary file with the job configuration
        config_file = os.path.join(os.path.dirname(script_path), f'job_{job_id}.json')
        with open(config_file, 'w') as f:
            json.dump({
                'job_id': job_id,
                'checkout_url': checkout_url,
                'product_info': product_info,
                'timestamp': datetime.now().isoformat()
            }, f)
        
        # Log the command we're about to run
        cmd = [
            'node', 
            script_path, 
            '--checkout-url', checkout_url,
            '--job-id', job_id
        ]
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # For demo purposes, we'll simulate the automation steps
        # In a real implementation, we would run the node script:
        # process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Simulate automation steps
        simulate_automation_steps(job_id)
        
        # Clean up the config file
        if os.path.exists(config_file):
            os.remove(config_file)
            
    except Exception as e:
        logger.error(f"Error running automation: {str(e)}")
        automation_jobs[job_id]['status'] = 'error'
        automation_jobs[job_id]['error'] = str(e)
        automation_jobs[job_id]['logs'].append(f'Error: {str(e)}')

def simulate_automation_steps(job_id):
    """
    Simulate the automation steps for demo purposes
    In a real implementation, this would be handled by the Node.js script
    """
    def update_progress():
        try:
            # Step 1: Analyzing the checkout page
            automation_jobs[job_id]['progress'] = 10
            automation_jobs[job_id]['logs'].append('Analyzing checkout page...')
            time.sleep(2)
            
            # Step 2: Filling out shipping information
            automation_jobs[job_id]['progress'] = 30
            automation_jobs[job_id]['logs'].append('Filling out shipping information...')
            time.sleep(2)
            
            # Step 3: Filling out payment information
            automation_jobs[job_id]['progress'] = 60
            automation_jobs[job_id]['logs'].append('Entering payment details...')
            time.sleep(2)
            
            # Step 4: Confirming order
            automation_jobs[job_id]['progress'] = 85
            automation_jobs[job_id]['logs'].append('Confirming order...')
            time.sleep(2)
            
            # Step 5: Order completed
            automation_jobs[job_id]['progress'] = 100
            automation_jobs[job_id]['status'] = 'completed'
            automation_jobs[job_id]['logs'].append('Order completed successfully!')
            
            # Generate fake order number
            order_number = f"AI-{uuid.uuid4().hex[:8].upper()}"
            automation_jobs[job_id]['order_number'] = order_number
            automation_jobs[job_id]['logs'].append(f'Order number: {order_number}')
            
            logger.info(f"Automation job {job_id} completed successfully")
        except Exception as e:
            logger.error(f"Error in simulation thread: {str(e)}")
            automation_jobs[job_id]['status'] = 'error'
            automation_jobs[job_id]['error'] = str(e)
    
    # Run the simulation in a separate thread
    thread = threading.Thread(target=update_progress)
    thread.daemon = True
    thread.start()

@router.route('/checkout', methods=['POST'])
def start_checkout_automation():
    """API endpoint to start the checkout automation process"""
    try:
        # Get the checkout URL and product info from the request
        data = request.json
        checkout_url = data.get('checkout_url')
        product_info = data.get('product_info', {})
        
        if not checkout_url:
            return jsonify({
                'success': False,
                'error': 'Checkout URL is required'
            }), 400
        
        # Generate a unique job ID
        job_id = str(uuid.uuid4())
        
        # Initialize job status
        automation_jobs[job_id] = {
            'id': job_id,
            'status': 'initializing',
            'progress': 0,
            'created_at': datetime.now().isoformat(),
            'checkout_url': checkout_url,
            'product_info': product_info,
            'logs': ['Initializing checkout automation...']
        }
        
        # Start the automation process in a separate thread
        thread = threading.Thread(
            target=run_automation, 
            args=(job_id, checkout_url, product_info)
        )
        thread.daemon = True
        thread.start()
        
        logger.info(f"Started automation job {job_id} for URL: {checkout_url}")
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Checkout automation started'
        })
        
    except Exception as e:
        logger.error(f"Error starting automation: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@router.route('/status/<job_id>', methods=['GET'])
def get_automation_status(job_id):
    """API endpoint to get the status of an automation job"""
    try:
        if job_id not in automation_jobs:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404
        
        job = automation_jobs[job_id]
        
        # Clean up logs, filter out None values
        logs = [log for log in job.get('logs', []) if log is not None]
        
        return jsonify({
            'success': True,
            'status': job.get('status', 'unknown'),
            'progress': job.get('progress', 0),
            'logs': logs,
            'error': job.get('error'),
            'order_number': job.get('order_number')
        })
        
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@router.route('/logs/<job_id>', methods=['GET'])
def get_automation_logs(job_id):
    """API endpoint to get the logs for an automation job"""
    try:
        if job_id not in automation_jobs:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404
        
        logs = automation_jobs[job_id].get('logs', [])
        # Clean up logs, filter out None values
        logs = [log for log in logs if log is not None]
        
        return jsonify({
            'success': True,
            'logs': logs
        })
        
    except Exception as e:
        logger.error(f"Error getting job logs: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def registerTestRoutes(app):
    """Register additional test routes for the automation system"""
    
    @app.route('/test-automation')
    def test_automation_page():
        """Test page to demonstrate the checkout automation"""
        return render_template('test_automation.html')
    
    @app.route('/api/automation/test', methods=['POST'])
    def test_automation():
        """API endpoint to test the automation system"""
        try:
            # Generate a unique job ID
            job_id = str(uuid.uuid4())
            
            # Initialize job status
            automation_jobs[job_id] = {
                'id': job_id,
                'status': 'initializing',
                'progress': 0,
                'created_at': datetime.now().isoformat(),
                'checkout_url': 'http://example.com/test-checkout',
                'product_info': {'title': 'Test Product', 'price': '₹499'},
                'logs': ['Initializing test automation...']
            }
            
            # Start the simulation in a separate thread
            thread = threading.Thread(target=simulate_automation_steps, args=(job_id,))
            thread.daemon = True
            thread.start()
            
            logger.info(f"Started test automation job {job_id}")
            
            return jsonify({
                'success': True,
                'job_id': job_id,
                'message': 'Test automation started'
            })
            
        except Exception as e:
            logger.error(f"Error starting test automation: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500 