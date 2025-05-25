/**
 * Demo Checkout Automation Script using Puppeteer
 * 
 * To run:
 * 1. Install dependencies: npm install puppeteer
 * 2. Make sure the app is running at localhost:5000
 * 3. Run script: node demo-automation.js
 */

const puppeteer = require('puppeteer');

// Demo configuration
const config = {
  baseUrl: 'http://localhost:5000',
  searchQuery: 'iron',
  checkoutInfo: {
    email: 'test@example.com',
    name: 'Test User',
    cardNumber: '4242 4242 4242 4242',
    expiry: '12/25',
    cvc: '123'
  }
};

(async () => {
  console.log('🤖 Starting checkout automation demo...');
  
  // Launch the browser
  const browser = await puppeteer.launch({
    headless: false, // Set to true for headless mode
    defaultViewport: null,
    args: ['--window-size=1280,800']
  });
  
  try {
    const page = await browser.newPage();
    console.log('🌐 Opening product finder app...');
    await page.goto(config.baseUrl, { waitUntil: 'networkidle2' });
    
    // Wait for the chat input to be visible
    await page.waitForSelector('#userInput');
    console.log('💬 Entering search query...');
    
    // Type the search query
    await page.type('#userInput', config.searchQuery);
    
    // Submit the search
    await page.click('.send-btn');
    
    // Wait for products to load
    console.log('🔍 Searching for products...');
    await page.waitForFunction(
      'document.querySelectorAll(".product-card").length > 0',
      { timeout: 10000 }
    );
    
    // Wait a moment to see the results
    await new Promise(r => setTimeout(r, 2000));
    
    console.log('🛍️ Selecting a product...');
    
    // Click the buy now button on the first product
    const buyButtons = await page.$$('.buy-now-btn');
    if (buyButtons.length > 0) {
      await buyButtons[0].click();
      
      // Wait for the new checkout page to open
      await new Promise(r => setTimeout(r, 3000));
      
      // Get all pages
      const pages = await browser.pages();
      const checkoutPage = pages[pages.length - 1];
      
      if (checkoutPage.url().includes('/checkout/')) {
        console.log('🔐 Filling checkout form...');
        
        // Fill checkout form
        await checkoutPage.type('#email', config.checkoutInfo.email);
        await checkoutPage.type('#name', config.checkoutInfo.name);
        await checkoutPage.type('#card', config.checkoutInfo.cardNumber);
        
        // Get all input fields in the card element
        const inputs = await checkoutPage.$$('.card-element input');
        if (inputs.length >= 3) {
          await inputs[1].type(config.checkoutInfo.expiry);
          await inputs[2].type(config.checkoutInfo.cvc);
        }
        
        // Submit payment
        console.log('💰 Submitting payment...');
        await checkoutPage.click('.pay-button');
        
        // Wait for success page
        await checkoutPage.waitForFunction(
          'window.location.href.includes("/success")',
          { timeout: 10000 }
        );
        
        console.log('✅ Checkout completed successfully!');
        await new Promise(r => setTimeout(r, 3000));
      } else {
        console.log('❌ Checkout page did not open correctly');
      }
    } else {
      console.log('❌ No products found or buy buttons not available');
    }
  } catch (error) {
    console.error('❌ Automation error:', error);
  } finally {
    // Close the browser
    await browser.close();
    console.log('🤖 Automation demo finished');
  }
})(); 