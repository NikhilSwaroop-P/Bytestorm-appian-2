/**
 * AI Checkout Script
 * This script adds AI-powered checkout automation to the buy buttons.
 */

(function() {
  // Configuration
  const config = {
    enabled: true,
    apiKey: 'AIzaSyCDTRtFFd62Xv7YGvr3ksNYeeFvQycACP8',
    pollingInterval: 2000,
    debug: false
  };
  
  // Load CSS for AI checkout UI
  function loadStyles() {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '/static/css/ai-checkout.css';
    document.head.appendChild(link);
  }
  
  // Initialize the AI checkout functionality
  function initialize() {
    if (!config.enabled) return;
    
    console.log('Initializing AI Checkout Assistant...');
    loadStyles();
    
    // Add AI icon to buy buttons
    document.querySelectorAll('.buy-now-btn').forEach(button => {
      button.classList.add('ai-checkout-enabled');
      const originalText = button.textContent;
      button.innerHTML = `<i class="fas fa-robot"></i> ${originalText}`;
      
      // Replace click handler
      button.addEventListener('click', handleBuyButtonClick, { capture: true });
    });
    
    // Add floating AI assistant button
    addAssistantIcon();
  }
  
  // Add floating AI assistant icon
  function addAssistantIcon() {
    const assistant = document.createElement('div');
    assistant.className = 'ai-checkout-assistant';
    assistant.innerHTML = `
      <div class="ai-assistant-icon">
        <i class="fas fa-robot"></i>
      </div>
      <div class="ai-assistant-tooltip">
        AI Checkout Assistant
      </div>
    `;
    document.body.appendChild(assistant);
    
    // Add click handler to show info
    assistant.addEventListener('click', () => {
      showNotification(
        'AI Checkout Assistant',
        'Click any "Buy Now" button to use AI-powered checkout automation.',
        'info'
      );
    });
  }
  
  // Handle buy button clicks
  async function handleBuyButtonClick(event) {
    event.preventDefault();
    event.stopPropagation();
    
    const button = event.currentTarget;
    const originalHtml = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    button.disabled = true;
    
    try {
      // Get product info
      const productCard = button.closest('.product-card');
      const productId = productCard.dataset.productId || Math.random().toString(36).substring(2, 15);
      const productTitle = productCard.querySelector('.product-title').textContent;
      const productPrice = productCard.querySelector('.current-price').textContent;
      
      // Log to chat if available
      logToChat(`Starting checkout for ${productTitle}...`);
      
      // Create checkout session
      const checkoutResponse = await fetch('/api/checkout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ product_id: productId })
      });
      
      if (!checkoutResponse.ok) {
        throw new Error('Failed to create checkout session');
      }
      
      const checkoutData = await checkoutResponse.json();
      
      if (!checkoutData.success) {
        throw new Error(checkoutData.error || 'Failed to create checkout session');
      }
      
      // Open checkout URL in new window
      const checkoutWindow = window.open(checkoutData.checkout_url, 'checkout_window');
      
      // Show automation modal
      showAutomationModal(checkoutData.checkout_url, {
        id: productId,
        title: productTitle,
        price: productPrice
      });
      
    } catch (error) {
      console.error('Error starting checkout:', error);
      showNotification('Error', error.message, 'error');
      logToChat(`Error: ${error.message}`, 'error');
    } finally {
      // Restore button
      button.innerHTML = originalHtml;
      button.disabled = false;
    }
  }
  
  // Show automation modal
  function showAutomationModal(checkoutUrl, product) {
    const modal = document.createElement('div');
    modal.className = 'ai-checkout-modal';
    
    modal.innerHTML = `
      <div class="ai-checkout-modal-content">
        <span class="close">&times;</span>
        <h2>AI Checkout Assistant</h2>
        <p>Your checkout session has been created for <strong>${product.title}</strong>.</p>
        
        <div class="instructions">
          <h3>To complete the automated checkout:</h3>
          <ol>
            <li>A checkout window has opened for you to review</li>
            <li>The AI assistant will analyze and fill the form for you</li>
            <li>Click "Run Automation" below to start the process</li>
          </ol>
        </div>
        
        <div class="product-info">
          <p><strong>Product:</strong> ${product.title}</p>
          <p><strong>Price:</strong> ${product.price}</p>
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
    
    // Start automation button
    modal.querySelector('#startAutomation').addEventListener('click', async () => {
      await startCheckoutAutomation(modal, checkoutUrl, product);
    });
  }
  
  // Start checkout automation
  async function startCheckoutAutomation(modal, checkoutUrl, product) {
    const statusEl = modal.querySelector('#automationStatus');
    const controlsEl = modal.querySelector('.automation-controls');
    
    // Update UI
    statusEl.innerHTML = '<p>Starting automation...</p>';
    controlsEl.innerHTML = `
      <button id="cancelAutomation" class="automation-button cancel">Cancel</button>
    `;
    
    // Add cancel handler
    modal.querySelector('#cancelAutomation').addEventListener('click', () => {
      // TODO: Implement cancellation logic
      modal.remove();
    });
    
    try {
      // Start automation with backend API
      const response = await fetch('/api/automation/checkout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          checkout_url: checkoutUrl,
          product_info: product
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to start automation');
      }
      
      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'Failed to start automation');
      }
      
      // Poll for status updates
      await pollAutomationStatus(data.job_id, statusEl, controlsEl, modal);
      
    } catch (error) {
      console.error('Error starting automation:', error);
      statusEl.innerHTML += `<p class="error">Error: ${error.message}</p>`;
      
      // Reset controls
      controlsEl.innerHTML = `
        <button id="closeAutomation" class="automation-button">Close</button>
      `;
      
      modal.querySelector('#closeAutomation').addEventListener('click', () => {
        modal.remove();
      });
    }
  }
  
  // Poll for automation status
  async function pollAutomationStatus(jobId, statusEl, controlsEl, modal) {
    let completed = false;
    let attempts = 0;
    
    while (!completed && attempts < 30) {
      attempts++;
      
      try {
        const response = await fetch(`/api/automation/status/${jobId}`);
        
        if (!response.ok) {
          throw new Error('Failed to get automation status');
        }
        
        const data = await response.json();
        
        // Update status
        updateAutomationStatus(data, statusEl);
        
        // Check if completed
        if (data.status === 'completed' || data.status === 'failed') {
          completed = true;
          
          // Update controls
          controlsEl.innerHTML = `
            <button id="closeAutomation" class="automation-button">Close</button>
          `;
          
          modal.querySelector('#closeAutomation').addEventListener('click', () => {
            modal.remove();
          });
          
          // Log final status
          logToChat(
            data.status === 'completed' 
              ? `Checkout completed successfully!` 
              : `Checkout failed: ${data.error || 'Unknown error'}`,
            data.status === 'completed' ? 'success' : 'error'
          );
        } else {
          // Wait before polling again
          await new Promise(resolve => setTimeout(resolve, config.pollingInterval));
        }
        
      } catch (error) {
        console.error('Error polling automation status:', error);
        statusEl.innerHTML += `<p class="error">Error checking status: ${error.message}</p>`;
        completed = true;
      }
    }
    
    // If we reached max attempts without completion
    if (!completed) {
      statusEl.innerHTML += `<p class="error">Timed out waiting for completion</p>`;
      
      // Update controls
      controlsEl.innerHTML = `
        <button id="closeAutomation" class="automation-button">Close</button>
      `;
      
      modal.querySelector('#closeAutomation').addEventListener('click', () => {
        modal.remove();
      });
    }
  }
  
  // Update automation status UI
  function updateAutomationStatus(data, statusEl) {
    // Clear previous content
    statusEl.innerHTML = '';
    
    // Add logs
    if (data.logs && data.logs.length > 0) {
      data.logs.forEach(log => {
        if (log) {
          if (log.includes('successfully')) {
            statusEl.innerHTML += `<p class="success">${log}</p>`;
          } else if (log.includes('Error') || log.includes('failed')) {
            statusEl.innerHTML += `<p class="error">${log}</p>`;
          } else {
            statusEl.innerHTML += `<p>${log}</p>`;
          }
        }
      });
    }
    
    // Add progress if available
    if (data.progress !== undefined) {
      const percent = Math.min(100, Math.max(0, data.progress));
      statusEl.innerHTML += `
        <div class="progress-bar-container">
          <div class="progress-bar" style="width: ${percent}%"></div>
          <span class="progress-text">${percent}%</span>
        </div>
      `;
    }
  }
  
  // Show notification
  function showNotification(title, message, type = 'info') {
    // Check if we have a container already
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
  
  // Log message to chat interface if available
  function logToChat(message, type = 'info') {
    const chatMessages = document.getElementById('chatMessages');
    
    if (chatMessages) {
      const messageEl = document.createElement('div');
      messageEl.className = `message bot-message ${type}`;
      
      messageEl.innerHTML = `
        <div class="message-content">
          <i class="fas fa-robot"></i> ${message}
        </div>
      `;
      
      chatMessages.appendChild(messageEl);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
  }
  
  // Initialize when DOM is loaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
  } else {
    initialize();
  }
})(); 