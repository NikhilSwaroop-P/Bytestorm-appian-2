#!/usr/bin/env node
/**
 * Test Checkout Automation
 * 
 * This script helps test the AI-powered checkout automation with a sample checkout page.
 * It launches a test server with a mock checkout page and runs the automation against it.
 */

const express = require('express');
const path = require('path');
const { spawn } = require('child_process');
const open = require('open');
const { automateCheckout } = require('./checkout_automation');

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  magenta: '\x1b[35m'
};

// Configuration
const PORT = 3000;
const TEST_SERVER_URL = `http://localhost:${PORT}`;
const CHECKOUT_PATH = '/checkout';
const CHECKOUT_URL = `${TEST_SERVER_URL}${CHECKOUT_PATH}`;

// Parse command line arguments
const args = process.argv.slice(2);
const showHelp = args.includes('--help') || args.includes('-h');
const debug = args.includes('--debug');
const noAutoRun = args.includes('--no-autorun');

// Show help message
if (showHelp) {
  console.log(`
${colors.blue}AI Checkout Automation Test${colors.reset}

Usage: node test_automation.js [options]

Options:
  --help, -h     Show this help message
  --debug        Enable debug mode (verbose logging)
  --no-autorun   Start the test server but don't automatically run the automation

Description:
  This script starts a test server with a mock checkout page and runs the
  checkout automation against it. This allows you to test the automation
  functionality without having to use a real e-commerce site.

Example:
  node test_automation.js          Start server and run automation
  node test_automation.js --debug  Run with debug logging enabled
  `);
  process.exit(0);
}

// Create express app for the test server
const app = express();

// Serve static files
app.use(express.static(path.join(__dirname, 'test_assets')));

// Set view engine
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'test_assets'));

// Checkout page route
app.get(CHECKOUT_PATH, (req, res) => {
  const productId = req.query.product_id || 'TEST123';
  const productTitle = req.query.title || 'Test Product';
  const productPrice = req.query.price || '₹499';
  
  res.render('checkout', {
    product: {
      id: productId,
      title: productTitle,
      price: productPrice,
      image: '/test_product.jpg'
    }
  });
});

// Order confirmation page
app.post('/confirm-order', (req, res) => {
  const orderNumber = 'ORD-' + Math.random().toString(36).substring(2, 10).toUpperCase();
  
  res.render('confirmation', {
    order: {
      number: orderNumber,
      date: new Date().toLocaleDateString(),
      total: '₹499'
    }
  });
});

// Start the server
const server = app.listen(PORT, () => {
  console.log(`${colors.green}Test server started at ${colors.cyan}${TEST_SERVER_URL}${colors.reset}`);
  console.log(`${colors.green}Checkout page available at ${colors.cyan}${CHECKOUT_URL}${colors.reset}`);
  
  // Auto-run the checkout automation if not disabled
  if (!noAutoRun) {
    runAutomation();
  } else {
    console.log('\nAutomation not running automatically. To test manually:');
    console.log(`1. Open ${colors.cyan}${CHECKOUT_URL}${colors.reset} in your browser`);
    console.log(`2. Run in another terminal: ${colors.cyan}node run_checkout.js ${CHECKOUT_URL}${colors.reset}`);
    console.log('\nPress Ctrl+C to stop the server');
  }
});

// Run the checkout automation
async function runAutomation() {
  console.log(`\n${colors.blue}Starting checkout automation...${colors.reset}`);
  
  try {
    // Create command arguments
    const cmdArgs = [`${CHECKOUT_URL}?product_id=TEST123&title=Test%20Product&price=₹499`];
    if (debug) cmdArgs.push('--debug');
    
    // Run the automation script as a child process
    const child = spawn('node', ['run_checkout.js', ...cmdArgs], {
      stdio: 'inherit',
      cwd: __dirname
    });
    
    // Handle process exit
    child.on('close', (code) => {
      if (code === 0) {
        console.log(`\n${colors.green}Automation completed successfully!${colors.reset}`);
      } else {
        console.error(`\n${colors.red}Automation failed with code ${code}${colors.reset}`);
      }
      
      // Ask if user wants to try again
      console.log('\nOptions:');
      console.log(`1. Press ${colors.cyan}r${colors.reset} to run again`);
      console.log(`2. Press ${colors.cyan}o${colors.reset} to open checkout page in browser`);
      console.log(`3. Press ${colors.cyan}q${colors.reset} to quit`);
      
      // Listen for key press
      process.stdin.setRawMode(true);
      process.stdin.resume();
      process.stdin.on('data', (key) => {
        if (key.toString() === 'r') {
          process.stdin.setRawMode(false);
          process.stdin.pause();
          runAutomation();
        } else if (key.toString() === 'o') {
          open(CHECKOUT_URL);
        } else if (key.toString() === 'q' || key.toString() === '\u0003') { // q or Ctrl+C
          console.log('\nShutting down...');
          server.close();
          process.exit(0);
        }
      });
    });
    
  } catch (error) {
    console.error(`${colors.red}Error running automation: ${error.message}${colors.reset}`);
    server.close();
    process.exit(1);
  }
}

// Handle process termination
process.on('SIGINT', () => {
  console.log('\nShutting down...');
  server.close();
  process.exit(0);
}); 