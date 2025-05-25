document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const chatForm = document.getElementById('chatForm');
    const userInput = document.getElementById('userInput');
    const chatMessages = document.getElementById('chatMessages');
    const uploadBtn = document.getElementById('uploadBtn');
    const imageUpload = document.getElementById('imageUpload');
    const imagePreview = document.getElementById('imagePreview');
    const previewImg = document.getElementById('previewImg');
    const removeImage = document.getElementById('removeImage');
    const productsContainer = document.getElementById('productsContainer');
    const themeToggle = document.getElementById('themeToggle');
    const chatbotContainer = document.getElementById('chatbotContainer');
    const collapseBtn = document.getElementById('collapseBtn');
    const helpButton = document.getElementById('helpButton');
    const helpBox = document.getElementById('helpBox');
    const closeHelp = document.getElementById('closeHelp');
    
    // Set placeholder image
    const PLACEHOLDER_IMAGE = 'https://via.placeholder.com/150?text=No+Image';
    
    // State
    let currentImageFile = null;
    let retrievedIdx = null;
    let isReset = true;
    
    // Theme setup
    function setupTheme() {
        const currentTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', currentTheme);
        
        // Update toggle icon based on current theme
        if (currentTheme === 'dark') {
            themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
        } else {
            themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
        }
    }
    
    // Initialize theme
    setupTheme();
    
    // Theme toggle event handler
    themeToggle.addEventListener('click', function() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Update button icon
        if (newTheme === 'dark') {
            themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
        } else {
            themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
        }
    });
    
    // Function to update product grid based on available space
    function updateProductGrid() {
        const containerWidth = productsContainer.offsetWidth;
        const baseCardWidth = 220; // Base card width including padding and margins
        
        // Calculate how many cards can fit per row
        let cardsPerRow = Math.floor(containerWidth / baseCardWidth);
        
        // Cap at 5 cards per row maximum, minimum 1
        cardsPerRow = Math.min(Math.max(cardsPerRow, 1), 5);
        
        // Update card width to fit exactly the number of cards per row
        // Each card has 2% total margin (1% on each side)
        const cardWidthPercent = (100 / cardsPerRow) - 2;
        document.documentElement.style.setProperty('--cards-per-row', cardsPerRow);
        document.documentElement.style.setProperty('--card-width-percent', cardWidthPercent + '%');
    }
    
    // Collapse functionality
    collapseBtn.addEventListener('click', function() {
        chatbotContainer.classList.toggle('chatbot-collapsed');
        
        // Update product grid after collapse animation completes
        setTimeout(updateProductGrid, 300);
    });
    
    // Help box functionality
    helpButton.addEventListener('click', function() {
        helpBox.classList.toggle('visible');
    });
    
    closeHelp.addEventListener('click', function() {
        helpBox.classList.remove('visible');
    });
    
    // Call updateProductGrid on window resize
    window.addEventListener('resize', updateProductGrid);
    
    // Initialize grid on page load
    updateProductGrid();
    
    // Event Listeners
    chatForm.addEventListener('submit', handleChatSubmit);
    uploadBtn.addEventListener('click', () => imageUpload.click());
    imageUpload.addEventListener('change', handleImageUpload);
    removeImage.addEventListener('click', clearImagePreview);
    
    // Display bot typing indication
    function showBotTyping() {
        const typingElement = document.createElement('div');
        typingElement.className = 'message bot-message typing';
        typingElement.innerHTML = `
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        typingElement.id = 'botTyping';
        chatMessages.appendChild(typingElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Remove bot typing indication
    function hideBotTyping() {
        const typingElement = document.getElementById('botTyping');
        if (typingElement) {
            typingElement.remove();
        }
    }
    
    // Render star ratings based on a number (0-5)
    function renderStars(rating) {
        const fullStars = Math.floor(rating);
        const halfStar = rating % 1 >= 0.5;
        const emptyStars = 5 - fullStars - (halfStar ? 1 : 0);
        
        let starsHTML = '';
        // Full stars
        for (let i = 0; i < fullStars; i++) {
            starsHTML += '<i class="fas fa-star"></i>';
        }
        // Half star if needed
        if (halfStar) {
            starsHTML += '<i class="fas fa-star-half-alt"></i>';
        }
        // Empty stars
        for (let i = 0; i < emptyStars; i++) {
            starsHTML += '<i class="far fa-star"></i>';
        }
        
        return starsHTML;
    }
    
    // Add a new message to the chat
    function addMessage(text, sender, imageUrl = null) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}-message`;
        
        let messageContent = `<div class="message-content">`;
        
        if (imageUrl) {
            messageContent += `<img src="${imageUrl}" alt="Uploaded image" onerror="this.onerror=null; this.src='${PLACEHOLDER_IMAGE}';">`;
        }
        
        messageContent += `${text}</div>`;
        messageElement.innerHTML = messageContent;
        
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Handle file upload
    function handleImageUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        currentImageFile = file;
        const fileReader = new FileReader();
        
        fileReader.onload = function(e) {
            previewImg.src = e.target.result;
            imagePreview.classList.remove('hidden');
        };
        
        fileReader.readAsDataURL(file);
    }
    
    // Clear image preview
    function clearImagePreview() {
        imagePreview.classList.add('hidden');
        imageUpload.value = '';
        currentImageFile = null;
    }
    
    // Handle image error by replacing with placeholder
    function handleImageError(img) {
        console.log('Image failed to load:', img.src);
        img.onerror = null; // Prevent infinite loop
        img.src = PLACEHOLDER_IMAGE;
    }
    
    // Handle checkout process
    async function handleCheckout(product) {
        // Show loading in chat
        addMessage(`Processing your purchase for ${product.title || 'this product'}...`, 'bot');
        
        try {
            // Call the checkout API
            const response = await fetch('/api/checkout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ product_id: product.id })
            });
            
            if (!response.ok) {
                throw new Error('Checkout process failed');
            }
            
            const data = await response.json();
            
            if (data.success) {
                // Open Stripe checkout in a new window/tab
                window.open(data.checkout_url, '_blank');
                addMessage('You have been redirected to the payment page. Complete your purchase there.', 'bot');
            } else {
                throw new Error(data.error || 'Checkout process failed');
            }
            
        } catch (error) {
            console.error('Checkout error:', error);
            addMessage('Sorry, there was an error processing your checkout. Please try again.', 'bot');
        }
    }
    
    // Handle buy now button click
    function handleBuyNowClick(event, product) {
        event.preventDefault();
        event.stopPropagation();
        
        // Show confirmation in chat
        addMessage(`You selected: ${product.title || 'Product'}`, 'user');
        
        // Process checkout
        handleCheckout(product);
    }
    
    // Handle chat form submission
    async function handleChatSubmit(event) {
        event.preventDefault();
        
        const message = userInput.value.trim();
        
        // Check if we have an image for the first time submission
        if (isReset && !currentImageFile) {
            addMessage("Please upload an image to start the conversation.", "bot");
            return;
        }
        
        // Display user message
        if (message) {
            addMessage(message, 'user');
        }
        
        // Only show image in chat if it's a new image being uploaded
        if (currentImageFile && !currentImageFile.hasBeenSent) {
            const imageUrl = URL.createObjectURL(currentImageFile);
            addMessage('', 'user', imageUrl);
            currentImageFile.hasBeenSent = true;
        }
        
        // Clear input
        userInput.value = '';
        
        // Show bot typing indicator
        showBotTyping();
        
        try {
            // Build form data
            const formData = new FormData();
            if (message) {
                formData.append('text', message);
            }
            
            if (currentImageFile) {
                formData.append('image', currentImageFile);
            }
            
            formData.append('reset', isReset);
            
            if (retrievedIdx) {
                formData.append('retrieved_idx', JSON.stringify(retrievedIdx));
            }
            
            // Send request to API
            const response = await fetch('/api/search', {
                method: 'POST',
                body: formData
            });
            
            // Once first message is sent, following messages are modifications
            isReset = false;
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Network response was not ok');
            }
            
            const data = await response.json();
            console.log('Received data:', data); // Debug log
            
            // Save retrieved indices for future queries
            retrievedIdx = data.indices;
            
            // Hide typing indicator
            hideBotTyping();
            
            // Add bot response
            addMessage('Here are some products that match your request:', 'bot');
            
            // Display products
            displayProducts(data.products);
            
        } catch (error) {
            console.error('Error:', error);
            hideBotTyping();
            addMessage(`Sorry, I encountered an error: ${error.message}`, 'bot');
        }
        
        // Don't clear image preview after sending - keep it for subsequent requests
        // clearImagePreview();
    }
    
    // Display products in the products container
    function displayProducts(products) {
        // Clear the empty state if it exists
        productsContainer.innerHTML = '';
        
        if (!products || products.length === 0) {
            productsContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-search fa-3x"></i>
                    <h3>No products found</h3>
                    <p>Try a different search query</p>
                </div>
            `;
            return;
        }
        
        console.log('Displaying products:', products); // Debug log
        
        // Update grid layout before displaying products
        updateProductGrid();
        
        // Collect all unique tags for the filter section
        const allTags = {};
        products.forEach(product => {
            if (product.tags && Array.isArray(product.tags)) {
                product.tags.forEach(tag => {
                    allTags[tag] = (allTags[tag] || 0) + 1;
                });
            }
        });
        
        // Create the tag filters section if there are tags
        if (Object.keys(allTags).length > 0) {
            const tagsFilterSection = document.createElement('div');
            tagsFilterSection.className = 'tags-filter';
            tagsFilterSection.id = 'tagsFilter';
            
            // Add each tag as a filter option
            Object.entries(allTags).sort((a, b) => b[1] - a[1]).forEach(([tag, count]) => {
                const tagElement = document.createElement('span');
                tagElement.className = 'filter-tag';
                tagElement.dataset.tag = tag;
                tagElement.textContent = tag;
                tagElement.addEventListener('click', function() {
                    // Toggle active state
                    this.classList.toggle('active');
                    filterProductsByTags();
                });
                tagsFilterSection.appendChild(tagElement);
            });
            
            // Add to the products container
            productsContainer.appendChild(tagsFilterSection);
        }
        
        // Display each product
        products.forEach(product => {
            const productCard = document.createElement('div');
            productCard.className = 'product-card';
            productCard.dataset.tags = JSON.stringify(product.tags || []);
            
            // Make sure we have a valid image URL or use placeholder
            const imageUrl = product.image_url ? product.image_url : 
                             product.image_path ? product.image_path : PLACEHOLDER_IMAGE;
            console.log('Product image URL:', imageUrl); // Debug log
            
            productCard.innerHTML = `
                <img src="${imageUrl}" 
                     alt="${product.description || 'Product'}" 
                     class="product-image" 
                     onerror="this.onerror=null; this.src='${PLACEHOLDER_IMAGE}';">
                <div class="product-details">
                    <h3 class="product-title">${product.title || 'Product'}</h3>
                    <div class="product-rating">
                        <span class="stars">${renderStars(product.rating || 0)}</span>
                        <span class="rating-count">${product.rating || 0} (${product.rating_count || 0})</span>
                    </div>
                    <div class="product-price-container">
                        <span class="current-price">${product.price || '$19.99'}</span>
                        ${product.actual_price ? `<span class="original-price">${product.actual_price}</span>` : ''}
                        ${product.discount > 0 ? `<span class="discount-badge">${product.discount}% off</span>` : ''}
                    </div>
                    <div class="product-meta">${product.description || ''}</div>
                    <button class="buy-now-btn">Buy Now</button>
                </div>
                <div class="product-description-hover">
                    <h4>Product Details</h4>
                    <p>${product.description || 'No detailed description available for this product.'}</p>
                    ${product.rating ? `<p><strong>Rating:</strong> ${product.rating} out of 5 (${product.rating_count} reviews)</p>` : ''}
                    ${product.price ? `<p><strong>Price:</strong> ${product.price}${product.actual_price ? ` (Original: ${product.actual_price})` : ''}</p>` : ''}
                    ${product.discount > 0 ? `<p><strong>Discount:</strong> ${product.discount}% off</p>` : ''}
                </div>
            `;
            
            productsContainer.appendChild(productCard);
            
            // Add event listener to the buy now button
            const buyButton = productCard.querySelector('.buy-now-btn');
            buyButton.addEventListener('click', (event) => handleBuyNowClick(event, product));
            
            // Add manual event listeners for hover description
            const card = productCard;
            const description = productCard.querySelector('.product-description-hover');
            
            card.addEventListener('mouseenter', () => {
                description.style.opacity = '1';
                description.style.visibility = 'visible';
                
                // Track product view when user hovers on a product for at least 1 second
                if (!product.viewTracked) {
                    product.viewTimeout = setTimeout(() => {
                        trackProductView(product);
                        product.viewTracked = true;
                    }, 1000); // 1 second delay to ensure intentional view
                }
            });
            
            card.addEventListener('mouseleave', () => {
                description.style.opacity = '0';
                description.style.visibility = 'hidden';
                
                // Clear timeout if user leaves before threshold
                if (product.viewTimeout) {
                    clearTimeout(product.viewTimeout);
                }
            });
        });
        
        // Function to track product views
        function trackProductView(product) {
            // Extract product details for tracking
            const viewInfo = {
                product_id: product.id,
                product_data: {
                    title: product.title || '',
                    color: product.tags ? product.tags.find(tag => /color|black|white|blue|red|gray|silver/i.test(tag)) || '' : '',
                    specs: product.tags ? product.tags.filter(tag => !/color|black|white|blue|red|gray|silver/i.test(tag)).join(', ') : '',
                    price: product.price || '',
                    rating: product.rating || '',
                    rating_count: product.rating_count || ''
                }
            };
            
            // Send view tracking event
            fetch('/api/view-product', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(viewInfo)
            }).catch(err => console.error('Error tracking product view:', err));
        }
        
        // Function to filter products by selected tags
        function filterProductsByTags() {
            const selectedTags = Array.from(document.querySelectorAll('.filter-tag.active')).map(tag => tag.dataset.tag);
            
            // If no tags selected, show all products
            if (selectedTags.length === 0) {
                document.querySelectorAll('.product-card').forEach(card => {
                    card.style.display = 'flex';
                });
                return;
            }
            
            // Filter products based on selected tags
            document.querySelectorAll('.product-card').forEach(card => {
                let cardTags = [];
                try {
                    cardTags = JSON.parse(card.dataset.tags || '[]');
                } catch (e) {
                    console.error('Error parsing tags:', e);
                }
                
                // Check if the product has ANY of the selected tags (OR logic)
                const hasAnyTag = selectedTags.some(tag => cardTags.includes(tag));
                
                card.style.display = hasAnyTag ? 'flex' : 'none';
            });
        }
        
        // Force a small delay to ensure proper layout
        setTimeout(updateProductGrid, 100);
    }
    
    // Function to reset the chat
    window.resetChat = function() {
        chatMessages.innerHTML = `
            <div class="message bot-message">
                <div class="message-content">
                    Hello! I can help you find products. Upload an image or describe what you're looking for.
                </div>
            </div>
        `;
        
        productsContainer.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-store fa-3x"></i>
                <h3>No products selected</h3>
                <p>Use the chat to search for products by image or text</p>
                <p><a href="/test-images" target="_blank" class="small-link">Check Available Images</a></p>
            </div>
        `;
        
        isReset = true;
        retrievedIdx = null;
        clearImagePreview();
        
        // Also reset the session on the server
        fetch('/reset', {
            method: 'POST'
        });
    };
}); 