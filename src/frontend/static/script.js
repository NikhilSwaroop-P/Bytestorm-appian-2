// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Chat functionality
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    const productsContainer = document.querySelector('.products');
    
    // Initialize with a welcome message
    addBotMessage("Hello! I'm your shopping assistant. How can I help you today?");
    
    // Handle chat submissions
    if (chatForm) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const message = chatInput.value.trim();
            if (message === '') return;
            
            // Add user message to chat
            addUserMessage(message);
            
            // Clear input
            chatInput.value = '';
            
            // Show typing indicator
            addTypingIndicator();
            
            // Send request to server
            fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'message': message
                })
            })
            .then(response => response.json())
            .then(data => {
                // Remove typing indicator
                removeTypingIndicator();
                
                // Add bot response
                addBotMessage(data.response);
                
                // Update product listings with the search results
                if (data.products && productsContainer) {
                    updateProducts(data.products);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                removeTypingIndicator();
                addBotMessage("Sorry, I'm having trouble connecting right now. Please try again later.");
            });
        });
    }
    
    // Search functionality
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const query = searchInput.value.trim();
            if (query === '') return;
            
            fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'query': query
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.products && productsContainer) {
                    updateProducts(data.products);
                    
                    // Also add a message in the chatbot
                    addBotMessage(`Here are some products related to "${query}"`);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    }
    
    // Helper function to add user message to chat
    function addUserMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', 'user-message');
        messageElement.textContent = message;
        chatMessages.appendChild(messageElement);
        
        // Scroll to bottom of chat
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Helper function to add bot message to chat
    function addBotMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', 'bot-message');
        messageElement.textContent = message;
        chatMessages.appendChild(messageElement);
        
        // Scroll to bottom of chat
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Add typing indicator
    function addTypingIndicator() {
        const typingElement = document.createElement('div');
        typingElement.classList.add('message', 'bot-message', 'typing-indicator');
        typingElement.innerHTML = '<span>.</span><span>.</span><span>.</span>';
        typingElement.id = 'typing-indicator';
        chatMessages.appendChild(typingElement);
        
        // Scroll to bottom of chat
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Remove typing indicator
    function removeTypingIndicator() {
        const typingElement = document.getElementById('typing-indicator');
        if (typingElement) {
            typingElement.remove();
        }
    }
    
    // Update product grid with search results
    function updateProducts(products) {
        productsContainer.innerHTML = '';
        
        products.forEach(product => {
            const productCard = createProductCard(product);
            productsContainer.appendChild(productCard);
        });
    }
    
    // Create a product card element
    function createProductCard(product) {
        const card = document.createElement('div');
        card.classList.add('product-card');
        
        let stars = '★'.repeat(Math.floor(product.rating)) + 
                   (product.rating % 1 >= 0.5 ? '½' : '') + 
                   '☆'.repeat(5 - Math.ceil(product.rating));
        
        card.innerHTML = `
            <img src="${product.image_path}" alt="${product.name}" class="product-image">
            <div class="product-details">
                <h3 class="product-title">${product.name}</h3>
                <div class="product-category">${product.category} / ${product.sub_category}</div>
                <div class="product-price">
                    <span class="discount-price">${product.discount_price}</span>
                    <span class="actual-price">${product.actual_price}</span>
                </div>
                <div class="product-rating">
                    <span class="rating-stars">${stars}</span>
                    <span class="rating-count">(${product.rating_count})</span>
                </div>
            </div>
        `;
        
        // Add click event to view product details
        card.addEventListener('click', function() {
            window.location.href = `/product/${product.id}`;
        });
        
        return card;
    }
}); 