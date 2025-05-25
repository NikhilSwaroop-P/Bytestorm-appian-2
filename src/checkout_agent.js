const puppeteer = require('puppeteer');

/**
 * Checkout Automation Agent
 * 
 * This script automates the checkout process using Puppeteer.
 * It intelligently fills in forms, selects the best coupon, and completes the checkout.
 */

class CheckoutAgent {
  constructor(config = {}) {
    this.config = {
      headless: false, // Set to true for production
      slowMo: 50, // Slow down operations for visual feedback
      baseUrl: 'http://localhost:5000',
      ...config
    };
    this.browser = null;
    this.page = null;
    this.logger = this.setupLogger();
  }

  setupLogger() {
    return {
      info: (message) => console.log(`[INFO] ${message}`),
      error: (message) => console.error(`[ERROR] ${message}`),
      success: (message) => console.log(`[SUCCESS] ${message}`)
    };
  }

  async initialize() {
    this.logger.info('Initializing checkout agent');
    this.browser = await puppeteer.launch({
      headless: this.config.headless,
      slowMo: this.config.slowMo,
      defaultViewport: { width: 1366, height: 768 }
    });
    this.page = await this.browser.newPage();
    await this.page.setDefaultNavigationTimeout(60000);
    this.logger.info('Checkout agent initialized');
  }

  async close() {
    if (this.browser) {
      await this.browser.close();
      this.logger.info('Browser closed');
    }
  }

  /**
   * Navigate to a product page and start the checkout process
   */
  async startCheckoutProcess(productId) {
    try {
      this.logger.info(`Starting checkout process for product ${productId}`);
      
      // Navigate to home page
      await this.page.goto(this.config.baseUrl, {
        waitUntil: 'networkidle2'
      });
      
      // Upload an image (assuming this is needed for the search)
      await this.uploadSampleImage();
      
      // Submit search to find products
      await this.submitSearch();
      
      // Find and click "Buy Now" on a product
      await this.selectProduct(productId);
      
      // The system should now navigate to checkout page
      await this.page.waitForNavigation({ waitUntil: 'networkidle2' });
      
      // Check if we're on the checkout page
      const currentUrl = this.page.url();
      if (currentUrl.includes('/checkout/')) {
        this.logger.success('Successfully navigated to checkout page');
        return true;
      } else {
        this.logger.error('Failed to navigate to checkout page');
        return false;
      }
    } catch (error) {
      this.logger.error(`Error starting checkout: ${error.message}`);
      return false;
    }
  }

  /**
   * Upload a sample image for product search
   */
  async uploadSampleImage() {
    this.logger.info('Uploading sample image');
    
    // Click the upload button
    await this.page.click('#uploadBtn');
    
    // Wait for file input to be available
    const inputUploadHandle = await this.page.$('#imageUpload');
    
    // Provide a sample image path - this should be adjusted to a valid local path
    const imagePath = './samples/sample_product.jpg';
    
    // Upload file
    await inputUploadHandle.uploadFile(imagePath);
    
    // Wait for image preview to appear
    await this.page.waitForSelector('#previewImg[src]', { visible: true });
    
    this.logger.info('Sample image uploaded successfully');
  }

  /**
   * Submit search query
   */
  async submitSearch(query = '') {
    this.logger.info('Submitting search');
    
    // Type search query if provided
    if (query) {
      await this.page.type('#userInput', query);
    }
    
    // Submit the form
    await this.page.click('#chatForm button[type="submit"]');
    
    // Wait for product results to load
    await this.page.waitForSelector('.product-card', { timeout: 10000 });
    
    this.logger.info('Search submitted, products loaded');
  }

  /**
   * Select a product to purchase
   */
  async selectProduct(productId = null) {
    this.logger.info('Selecting product');
    
    // Get all buy now buttons
    const buyButtons = await this.page.$$('.buy-now-btn');
    
    if (buyButtons.length === 0) {
      throw new Error('No products found with Buy Now buttons');
    }
    
    // If specific product ID is provided, find that product
    if (productId) {
      // Logic to find specific product by ID
      // For now, just click the first product
      await buyButtons[0].click();
    } else {
      // Click the first product's buy button
      await buyButtons[0].click();
    }
    
    this.logger.info('Product selected for purchase');
  }

  /**
   * Analyze available coupons and select the best one
   */
  async selectBestCoupon() {
    this.logger.info('Analyzing available coupons');
    
    try {
      // Click to show available coupons
      await this.page.click('[onclick="toggleCoupons()"]');
      
      // Wait for coupon list to be visible
      await this.page.waitForSelector('#coupon-list', { visible: true });
      
      // Get all coupon elements
      const coupons = await this.page.$$('.coupon-item');
      this.logger.info(`Found ${coupons.length} available coupons`);
      
      if (coupons.length === 0) {
        this.logger.info('No coupons available');
        return null;
      }
      
      // Get product price for determining best coupon
      const priceText = await this.page.$eval('.item-price', el => el.textContent);
      const price = this.extractNumericPrice(priceText);
      
      // Get shipping price
      const shippingText = await this.page.$eval('#shipping', el => el.textContent);
      const shippingCost = this.extractNumericPrice(shippingText);
      
      // Analyze which coupon is best
      let bestCouponIndex = 0;
      let bestSavings = 0;
      
      for (let i = 0; i < coupons.length; i++) {
        const couponText = await this.page.evaluate(el => el.textContent, coupons[i]);
        
        // Determine potential savings from each coupon
        let savings = 0;
        
        if (couponText.includes('WELCOME10')) {
          // 10% off first order
          savings = price * 0.1;
        } else if (couponText.includes('FREESHIP')) {
          // Free shipping
          savings = shippingCost;
        } else if (couponText.includes('SAVE20') && price >= 100) {
          // ₹20 off orders over ₹100
          savings = 20;
        }
        
        if (savings > bestSavings) {
          bestSavings = savings;
          bestCouponIndex = i;
        }
      }
      
      // Click the best coupon
      await coupons[bestCouponIndex].click();
      
      // Get the applied coupon code
      const couponCode = await this.page.$eval('#promo_code', el => el.value);
      this.logger.success(`Applied best coupon: ${couponCode}`);
      
      return couponCode;
    } catch (error) {
      this.logger.error(`Error selecting coupon: ${error.message}`);
      return null;
    }
  }

  /**
   * Helper function to extract numeric price from text
   */
  extractNumericPrice(priceText) {
    const numericString = priceText.replace(/[^0-9.]/g, '');
    return parseFloat(numericString) || 0;
  }

  /**
   * Fill out shipping information
   */
  async fillShippingInfo(shippingInfo) {
    this.logger.info('Filling shipping information');
    
    const defaultShipping = {
      name: 'John Doe',
      street: '123 Main Street',
      city: 'Bangalore',
      state: 'Karnataka',
      zip: '560001',
      country: 'India',
      email: 'test@example.com'
    };
    
    const shipping = { ...defaultShipping, ...shippingInfo };
    
    // Check if there's a saved address already selected
    const savedAddress = await this.page.$('.address-card.selected');
    
    if (!savedAddress) {
      // Fill out the shipping form
      await this.page.type('#shipping_name', shipping.name);
      await this.page.type('#shipping_street', shipping.street);
      await this.page.type('#shipping_city', shipping.city);
      await this.page.type('#shipping_state', shipping.state);
      await this.page.type('#shipping_zip', shipping.zip);
      
      // Select country from dropdown
      await this.page.select('#shipping_country', shipping.country);
      
      // Fill email if the field exists (for guest checkout)
      const emailField = await this.page.$('#email');
      if (emailField) {
        await this.page.type('#email', shipping.email);
      }
    }
    
    this.logger.success('Shipping information completed');
  }

  /**
   * Select shipping method based on price and speed
   */
  async selectShippingMethod(preference = 'best_value') {
    this.logger.info(`Selecting shipping method with preference: ${preference}`);
    
    // Get all shipping options
    const shippingOptions = await this.page.$$('.shipping-option');
    
    if (shippingOptions.length === 0) {
      this.logger.error('No shipping options found');
      return;
    }
    
    let targetIndex = 0; // Default to first option (usually standard)
    
    if (preference === 'fastest') {
      // Select the fastest shipping (usually the last option)
      targetIndex = shippingOptions.length - 1;
    } else if (preference === 'cheapest') {
      // Select the cheapest shipping (usually the first option)
      targetIndex = 0;
    } else if (preference === 'best_value') {
      // For "best value", we might choose the middle option if available
      targetIndex = Math.min(1, shippingOptions.length - 1);
    }
    
    // Click the selected shipping option
    await shippingOptions[targetIndex].click();
    
    const selectedMethod = await this.page.evaluate(
      el => el.querySelector('.shipping-name').textContent,
      shippingOptions[targetIndex]
    );
    
    this.logger.success(`Selected shipping method: ${selectedMethod}`);
  }

  /**
   * Fill payment information
   */
  async fillPaymentInfo(paymentInfo) {
    this.logger.info('Filling payment information');
    
    const defaultPayment = {
      cardHolder: 'John Doe',
      cardNumber: '4111111111111111',
      cardExpiry: '12/25',
      cardCvv: '123'
    };
    
    const payment = { ...defaultPayment, ...paymentInfo };
    
    // Fill card details
    await this.page.type('#card_holder', payment.cardHolder);
    await this.page.type('#card_number', payment.cardNumber);
    await this.page.type('#card_expiry', payment.cardExpiry);
    await this.page.type('#card_cvv', payment.cardCvv);
    
    this.logger.success('Payment information completed');
  }

  /**
   * Complete the order
   */
  async completeOrder() {
    this.logger.info('Completing order');
    
    // Scroll to the bottom of the page to ensure the button is visible
    await this.page.evaluate(() => {
      window.scrollTo(0, document.body.scrollHeight);
    });
    
    // Wait a moment for any dynamic content to load
    await this.page.waitForTimeout(1000);
    
    // Click the complete order button
    await this.page.click('.btn-success.btn-block');
    
    // Wait for navigation to the success page
    await this.page.waitForNavigation({ waitUntil: 'networkidle2' });
    
    // Check if we're on the order confirmation page
    const isSuccess = await this.page.evaluate(() => {
      return window.location.href.includes('/checkout/success/') || 
             document.querySelector('.confirmation-title') !== null;
    });
    
    if (isSuccess) {
      this.logger.success('Order completed successfully!');
      
      // Capture order number for reference
      const orderNumber = await this.page.evaluate(() => {
        const orderElement = document.querySelector('.order-number');
        return orderElement ? orderElement.textContent.trim() : 'Unknown';
      });
      
      this.logger.info(`Order reference: ${orderNumber}`);
      return true;
    } else {
      this.logger.error('Failed to complete order');
      return false;
    }
  }

  /**
   * Run the complete checkout process
   */
  async runFullCheckout(options = {}) {
    try {
      await this.initialize();
      
      const {
        productId = null,
        shippingInfo = {},
        paymentInfo = {},
        shippingPreference = 'best_value'
      } = options;
      
      // Start checkout process
      const checkoutStarted = await this.startCheckoutProcess(productId);
      if (!checkoutStarted) return false;
      
      // Allow page to fully load
      await this.page.waitForTimeout(2000);
      
      // Scroll through the page while performing actions
      await this.scrollToSection('.checkout-panel:nth-child(1)');
      
      // Fill shipping information
      await this.fillShippingInfo(shippingInfo);
      
      // Scroll to shipping method section
      await this.scrollToSection('.checkout-panel:nth-child(2)');
      
      // Select shipping method
      await this.selectShippingMethod(shippingPreference);
      
      // Scroll to payment section
      await this.scrollToSection('.checkout-panel:nth-child(3)');
      
      // Fill payment information
      await this.fillPaymentInfo(paymentInfo);
      
      // Scroll to sidebar and find coupons
      await this.scrollToSection('.checkout-sidebar');
      
      // Select the best coupon
      await this.selectBestCoupon();
      
      // Scroll to complete order button
      await this.scrollToSection('.btn-success.btn-block');
      
      // Complete the order
      const orderCompleted = await this.completeOrder();
      
      if (orderCompleted) {
        // Take a screenshot of the confirmation page
        await this.page.screenshot({ path: 'order_confirmation.png' });
      }
      
      return orderCompleted;
    } catch (error) {
      this.logger.error(`Checkout process failed: ${error.message}`);
      
      // Take screenshot of error state
      await this.page.screenshot({ path: 'checkout_error.png' });
      return false;
    } finally {
      await this.close();
    }
  }

  /**
   * Helper method to scroll to a specific section
   */
  async scrollToSection(selector) {
    try {
      const element = await this.page.$(selector);
      if (element) {
        await this.page.evaluate(el => {
          el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, element);
        await this.page.waitForTimeout(500); // Wait for scroll to complete
      }
    } catch (error) {
      this.logger.error(`Error scrolling to section ${selector}: ${error.message}`);
    }
  }
}

// Example usage
async function runDemo() {
  const agent = new CheckoutAgent({
    baseUrl: 'http://localhost:5000',
    headless: false,
    slowMo: 100 // Slowed down for demonstration
  });
  
  const result = await agent.runFullCheckout({
    shippingInfo: {
      name: 'Test User',
      street: '123 Main St',
      city: 'Bangalore',
      state: 'Karnataka',
      zip: '560001',
      country: 'India',
      email: 'test@example.com'
    },
    paymentInfo: {
      cardHolder: 'Test User',
      cardNumber: '4242424242424242',
      cardExpiry: '12/25',
      cardCvv: '123'
    },
    shippingPreference: 'best_value'
  });
  
  console.log(`Checkout automation ${result ? 'successful' : 'failed'}`);
}

// Export the agent class
module.exports = { CheckoutAgent, runDemo };

// Run the demo if this file is executed directly
if (require.main === module) {
  runDemo();
} 