#!/usr/bin/env node
/**
 * Standalone Checkout Automation Script
 * 
 * This script can be run from the command line to automate the checkout process.
 * Usage: node run_checkout.js <checkout_url> [--profile=default]
 */

const { automateCheckout } = require('./checkout_automation');

// Parse command line arguments
const args = process.argv.slice(2);
const checkoutUrl = args[0];

// Extract named parameters
const namedArgs = {};
args.slice(1).forEach(arg => {
  if (arg.startsWith('--')) {
    const [key, value] = arg.substring(2).split('=');
    namedArgs[key] = value || true;
  }
});

// Check if we have the required checkout URL
if (!checkoutUrl) {
  console.error('Error: Checkout URL is required');
  console.log('Usage: node run_checkout.js <checkout_url> [--profile=default] [--debug]');
  process.exit(1);
}

// Set debug mode based on command line flag
if (namedArgs.debug) {
  process.env.DEBUG = 'puppeteer:*';
}

// Extract product information from URL if available
let productInfo = {};
try {
  const url = new URL(checkoutUrl);
  const productId = url.searchParams.get('product_id');
  const productTitle = url.searchParams.get('title') || 'Unknown Product';
  const productPrice = url.searchParams.get('price') || 'Unknown Price';
  
  productInfo = {
    id: productId,
    title: productTitle,
    price: productPrice
  };
  
} catch (error) {
  console.warn('Failed to extract product info from URL:', error.message);
  productInfo = { title: 'Unknown Product' };
}

// Run the automation
async function run() {
  console.log('================================');
  console.log('AI Checkout Automation');
  console.log('================================');
  console.log(`Checkout URL: ${checkoutUrl}`);
  console.log(`Product: ${productInfo.title}`);
  console.log(`Price: ${productInfo.price || 'Unknown'}`);
  console.log(`Customer Profile: ${namedArgs.profile || 'default'}`);
  console.log('================================');
  console.log('Starting automation...');
  
  try {
    const result = await automateCheckout(
      checkoutUrl,
      productInfo,
      namedArgs.profile || 'default'
    );
    
    if (result.success) {
      console.log('\n✅ Checkout completed successfully!');
      console.log(`Order Number: ${result.orderNumber}`);
      console.log(`Confirmation Screenshot: ${result.screenshot || 'N/A'}`);
    } else {
      console.error('\n❌ Checkout failed!');
      console.error(`Error: ${result.error}`);
      console.error(`Debug Screenshot: ${result.screenshot || 'N/A'}`);
      process.exit(1);
    }
  } catch (error) {
    console.error('\n❌ Automation error!');
    console.error(error);
    process.exit(1);
  }
}

// Run the automation
run().catch(error => {
  console.error('Unhandled error:', error);
  process.exit(1);
}); 