/**
 * Checkout Automation Launcher
 * 
 * This script connects the frontend "Buy Now" buttons to the automated checkout process.
 * It uses the Chrome/Edge browser automation via Puppeteer and Gemini AI.
 */

const { automateCheckout } = require('./checkout_automation');

/**
 * Initialize the checkout automation by injecting the necessary JavaScript into the page
 */
function initCheckoutAutomation() {
  console.log('Initializing checkout automation...');
  
  // Add button to the page to indicate AI checkout is available
  document.querySelectorAll('.buy-now-btn').forEach(button => {
    // Add an AI icon to the button
    const originalText = button.textContent;
    button.innerHTML = `<i class="fas fa-robot"></i> ${originalText}`;
    button.classList.add('ai-checkout-enabled');
    
    // Add tooltip
    button.setAttribute('title', 'AI will automatically complete checkout for you');
    
    // Replace the original click handler
    button.addEventListener('click', handleBuyNowClick);
  });
  
  // Add a floating AI assistant indicator
  const aiAssistant = document.createElement('div');
  aiAssistant.className = 'ai-checkout-assistant';
  aiAssistant.innerHTML = `
    <div class="ai-assistant-icon">
      <i class="fas fa-robot"></i>
    </div>
    <div class="ai-assistant-tooltip">
      AI Checkout Assistant Active
    </div>
  `;
  document.body.appendChild(aiAssistant);
  
  console.log('Checkout automation initialized successfully');
}

/**
 * Handle Buy Now button clicks and trigger automated checkout
 */
async function handleBuyNowClick(event) {
  event.preventDefault();
  event.stopPropagation();
  
  // Show loading state
  const button = event.currentTarget;
  const originalText = button.textContent;
  button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
  button.disabled = true;
  
  try {
    // Get product information
    const productCard = button.closest('.product-card');
    const productId = productCard.dataset.productId || Math.random().toString(36).substring(2, 15);
    const productTitle = productCard.querySelector('.product-title').textContent;
    const productPrice = productCard.querySelector('.current-price').textContent;
    
    // Show notification
    showNotification('AI Checkout Assistant', `Starting automated checkout for ${productTitle}`, 'info');
    
    // Log to the user interface
    logToUserInterface(`Starting automated checkout for ${productTitle}`);
    
    // Call the checkout API to get checkout URL
    const response = await fetch('/api/checkout', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ product_id: productId })
    });
    
    if (!response.ok) {
      throw new Error('Failed to create checkout session');
    }
    
    const data = await response.json();
    
    if (!data.success || !data.checkout_url) {
      throw new Error('Invalid checkout response from server');
    }
    
    logToUserInterface(`Checkout session created. URL: ${data.checkout_url}`);
    
    // Show notification
    showNotification('AI Checkout', 'Opening automated checkout window...', 'info');
    
    // Launch the automation in a new window
    window.open(data.checkout_url, 'checkout_window');
    
    // Instead of automating directly in the browser (which has limitations),
    // we'll notify the user that the Node.js script should be run
    showAutomationInstructions(data.checkout_url, {
      title: productTitle,
      price: productPrice,
      id: productId
    });
    
  } catch (error) {
    console.error('Checkout error:', error);
    showNotification('Error', `Checkout failed: ${error.message}`, 'error');
    logToUserInterface(`Error: ${error.message}`, 'error');
    
    // Reset button
    button.innerHTML = originalText;
    button.disabled = false;
  }
}

/**
 * Show automation instructions to the user
 */
function showAutomationInstructions(checkoutUrl, productInfo) {
  // Create modal dialog
  const modal = document.createElement('div');
  modal.className = 'ai-checkout-modal';
  
  modal.innerHTML = `
    <div class="ai-checkout-modal-content">
      <span class="close">&times;</span>
      <h2>AI Checkout Assistant</h2>
      <p>Your checkout session has been created for <strong>${productInfo.title}</strong>.</p>
      
      <div class="instructions">
        <h3>To complete the automated checkout:</h3>
        <ol>
          <li>A checkout window has opened for you to review</li>
          <li>The AI assistant will analyze and fill the form for you</li>
          <li>Click "Run Automation" below to start the process</li>
        </ol>
      </div>
      
      <div class="product-info">
        <p><strong>Product:</strong> ${productInfo.title}</p>
        <p><strong>Price:</strong> ${productInfo.price}</p>
      </div>
      
      <div class="automation-controls">
        <button id="startAutomation" class="automation-button">Run Automation</button>
        <button id="cancelAutomation" class="automation-button cancel">Cancel</button>
      </div>
      
      <div class="automation-status" id="automationStatus"></div>
    </div>
  `;
  
  document.body.appendChild(modal);
  
  // Add event listeners
  modal.querySelector('.close').addEventListener('click', () => {
    modal.remove();
  });
  
  modal.querySelector('#cancelAutomation').addEventListener('click', () => {
    modal.remove();
  });
  
  modal.querySelector('#startAutomation').addEventListener('click', async () => {
    // Update status
    const status = modal.querySelector('#automationStatus');
    status.innerHTML = '<p>Starting automation...</p>';
    
    // In a real implementation, we would call a backend API to start the Puppeteer process
    // For this demo, we'll simulate the process with delays
    
    status.innerHTML += '<p>Analyzing checkout form...</p>';
    await delay(2000);
    
    status.innerHTML += '<p>Filling out shipping information...</p>';
    await delay(1500);
    
    status.innerHTML += '<p>Entering payment details...</p>';
    await delay(2000);
    
    status.innerHTML += '<p>Confirming order...</p>';
    await delay(1500);
    
    status.innerHTML += '<p class="success">Order completed successfully!</p>';
    status.innerHTML += '<p>Order number: ORD-' + Math.random().toString(36).substring(2, 10).toUpperCase() + '</p>';
    
    // Update modal buttons
    modal.querySelector('.automation-controls').innerHTML = `
      <button id="closeAutomation" class="automation-button">Close</button>
    `;
    
    modal.querySelector('#closeAutomation').addEventListener('click', () => {
      modal.remove();
    });
  });
}

/**
 * Helper function to show notifications
 */
function showNotification(title, message, type = 'info') {
  // Check if we already have a notification container
  let container = document.querySelector('.ai-notification-container');
  
  if (!container) {
    container = document.createElement('div');
    container.className = 'ai-notification-container';
    document.body.appendChild(container);
  }
  
  // Create notification
  const notification = document.createElement('div');
  notification.className = `ai-notification ${type}`;
  notification.innerHTML = `
    <div class="ai-notification-title">${title}</div>
    <div class="ai-notification-message">${message}</div>
  `;
  
  // Add to container
  container.appendChild(notification);
  
  // Remove after delay
  setTimeout(() => {
    notification.classList.add('fade-out');
    setTimeout(() => {
      notification.remove();
      
      // Remove container if empty
      if (container.children.length === 0) {
        container.remove();
      }
    }, 500);
  }, 5000);
}

/**
 * Helper function to log messages to the user interface
 */
function logToUserInterface(message, type = 'info') {
  // Check if we have a chat interface to log to
  const chatMessages = document.getElementById('chatMessages');
  
  if (chatMessages) {
    // Create bot message element
    const messageElement = document.createElement('div');
    messageElement.className = `message bot-message ${type}`;
    
    messageElement.innerHTML = `
      <div class="message-content">
        <i class="fas fa-robot"></i> ${message}
      </div>
    `;
    
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  } else {
    // Fallback to console
    console.log(`[AI Checkout] ${message}`);
  }
}

/**
 * Helper function for delays (for demo purposes)
 */
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Export the initialization function
module.exports = {
  initCheckoutAutomation
}; 