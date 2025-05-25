/**
 * Checkout Controller
 * 
 * This script provides an Express.js controller to handle checkout automation requests.
 * It interfaces between the frontend UI and the Puppeteer automation backend.
 */

const express = require('express');
const router = express.Router();
const path = require('path');
const fs = require('fs');
const { automateCheckout } = require('./checkout_automation');

// Storage for tracking automation jobs
const automationJobs = new Map();

/**
 * Start a new checkout automation process
 * POST /api/automation/checkout
 */
router.post('/checkout', async (req, res) => {
  try {
    const { checkoutUrl, productInfo, customerProfile } = req.body;
    
    if (!checkoutUrl) {
      return res.status(400).json({
        success: false,
        error: 'Missing required parameter: checkoutUrl'
      });
    }
    
    // Generate a unique job ID
    const jobId = `job_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`;
    
    // Store job information
    automationJobs.set(jobId, {
      status: 'pending',
      checkoutUrl,
      productInfo: productInfo || {},
      customerProfile: customerProfile || 'default',
      createdAt: new Date(),
      logs: ['Job created. Waiting to start...']
    });
    
    // Start the automation process in the background
    startAutomationJob(jobId);
    
    // Return the job ID to the client
    return res.json({
      success: true,
      jobId,
      message: 'Checkout automation job created'
    });
    
  } catch (error) {
    console.error('Error creating automation job:', error);
    return res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * Get status of a checkout automation job
 * GET /api/automation/checkout/:jobId
 */
router.get('/checkout/:jobId', (req, res) => {
  const { jobId } = req.params;
  
  if (!automationJobs.has(jobId)) {
    return res.status(404).json({
      success: false,
      error: 'Job not found'
    });
  }
  
  const job = automationJobs.get(jobId);
  
  // If the job is completed, return the full result
  if (job.status === 'completed' || job.status === 'failed') {
    return res.json({
      success: true,
      job
    });
  }
  
  // For in-progress jobs, return the status and logs
  return res.json({
    success: true,
    status: job.status,
    logs: job.logs,
    progress: job.progress || 0
  });
});

/**
 * Cancel a running checkout automation job
 * DELETE /api/automation/checkout/:jobId
 */
router.delete('/checkout/:jobId', (req, res) => {
  const { jobId } = req.params;
  
  if (!automationJobs.has(jobId)) {
    return res.status(404).json({
      success: false,
      error: 'Job not found'
    });
  }
  
  const job = automationJobs.get(jobId);
  
  // If the job is already completed or failed, just return the status
  if (job.status === 'completed' || job.status === 'failed') {
    return res.json({
      success: true,
      message: `Job already ${job.status}`,
      job
    });
  }
  
  // Mark the job as cancelled
  job.status = 'cancelled';
  job.logs.push('Job cancelled by user');
  
  // Try to terminate the browser process if it exists
  if (job.browser) {
    try {
      job.browser.close().catch(() => {});
    } catch (error) {
      console.warn('Error closing browser:', error);
    }
  }
  
  return res.json({
    success: true,
    message: 'Job cancelled successfully'
  });
});

/**
 * Start an automation job in the background
 * @param {string} jobId - The ID of the job to start
 */
async function startAutomationJob(jobId) {
  const job = automationJobs.get(jobId);
  
  if (!job) {
    console.error(`Job ${jobId} not found`);
    return;
  }
  
  try {
    // Update job status
    job.status = 'running';
    job.logs.push('Starting checkout automation...');
    job.startedAt = new Date();
    
    // Run the automation
    const result = await automateCheckout(
      job.checkoutUrl,
      job.productInfo,
      job.customerProfile
    );
    
    // Update job with result
    job.status = result.success ? 'completed' : 'failed';
    job.logs.push(result.success 
      ? `Checkout completed successfully. Order number: ${result.orderNumber}` 
      : `Checkout failed: ${result.error}`);
    job.result = result;
    job.completedAt = new Date();
    
    // If screenshot was taken, save the path
    if (result.screenshots) {
      job.screenshots = result.screenshots;
    }
    
  } catch (error) {
    console.error(`Error in automation job ${jobId}:`, error);
    
    // Update job with error
    job.status = 'failed';
    job.logs.push(`Error: ${error.message}`);
    job.error = error.message;
    job.completedAt = new Date();
  }
  
  // Clean up older jobs (keep for 1 hour)
  cleanupOldJobs();
}

/**
 * Clean up completed jobs older than 1 hour
 */
function cleanupOldJobs() {
  const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
  
  for (const [jobId, job] of automationJobs.entries()) {
    if ((job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') &&
        job.completedAt && job.completedAt < oneHourAgo) {
      automationJobs.delete(jobId);
    }
  }
}

/**
 * Register additional routes for testing/demo purposes
 */
function registerTestRoutes(app) {
  // Serve screenshots
  app.get('/api/automation/screenshots/:filename', (req, res) => {
    const { filename } = req.params;
    const screenshotPath = path.join(process.cwd(), filename);
    
    if (fs.existsSync(screenshotPath)) {
      res.sendFile(screenshotPath);
    } else {
      res.status(404).send('Screenshot not found');
    }
  });
  
  // List all jobs (for debugging/admin)
  app.get('/api/automation/jobs', (req, res) => {
    const jobs = Array.from(automationJobs.entries()).map(([id, job]) => ({
      id,
      status: job.status,
      product: job.productInfo?.title || 'Unknown product',
      created: job.createdAt,
      completed: job.completedAt
    }));
    
    res.json({ jobs });
  });
}

module.exports = {
  router,
  registerTestRoutes,
  startAutomationJob
}; 