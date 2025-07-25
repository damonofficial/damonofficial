// ===== SELLAUTH INTEGRATION =====
// Configuration - Replace with your actual Sellauth credentials
const SELLAUTH_CONFIG = {
    // Replace with your actual Sellauth domain/shop ID
    shopId: 'your-shop-id',
    // Replace with your public API key
    publicKey: 'your-public-api-key',
    // Your Sellauth shop URL
    shopUrl: 'https://your-shop.sellauth.com',
    // API base URL
    apiUrl: 'https://api.sellauth.com/v1',
    // Webhook secret for verification (server-side only)
    webhookSecret: 'your-webhook-secret'
};

// Product mapping between your local products and Sellauth products
const PRODUCT_MAPPING = {
    'server-boosts': {
        sellAuthProductId: 'discord-server-boosts',
        category: 'Discord Services'
    },
    'discord-nitro': {
        sellAuthProductId: 'discord-nitro',
        category: 'Discord Services'
    },
    'nitro-tokens': {
        sellAuthProductId: 'nitro-tokens-uhq',
        category: 'Discord Services'
    },
    'discord-members': {
        sellAuthProductId: 'discord-members',
        category: 'Discord Services'
    },
    'aged-accounts': {
        sellAuthProductId: 'discord-aged-accounts',
        category: 'Discord Services'
    },
    'boost-tools': {
        sellAuthProductId: 'professional-boost-tools',
        category: 'Discord Tools'
    }
};

// ===== SELLAUTH API FUNCTIONS =====
class SellAuthIntegration {
    constructor(config) {
        this.config = config;
        this.cart = [];
        this.currentSession = null;
    }

    // Initialize Sellauth (call this when the page loads)
    async initialize() {
        try {
            // Check if we have any pending orders from URL parameters
            this.handleReturnFromCheckout();
            
            // Load any existing cart from localStorage
            this.loadCart();
            
            console.log('SellAuth integration initialized');
        } catch (error) {
            console.error('Failed to initialize SellAuth:', error);
        }
    }

    // Handle return from Sellauth checkout
    handleReturnFromCheckout() {
        const urlParams = new URLSearchParams(window.location.search);
        const status = urlParams.get('status');
        const orderId = urlParams.get('order_id');
        
        if (status && orderId) {
            switch (status) {
                case 'success':
                    this.handleSuccessfulPayment(orderId);
                    break;
                case 'cancelled':
                    this.handleCancelledPayment(orderId);
                    break;
                case 'failed':
                    this.handleFailedPayment(orderId);
                    break;
            }
            
            // Clean up URL parameters
            window.history.replaceState({}, document.title, window.location.pathname);
        }
    }

    // Create a checkout session
    async createCheckoutSession(orderData) {
        try {
            const checkoutData = this.prepareCheckoutData(orderData);
            
            // In a real implementation, you would make an API call to your backend
            // which would then communicate with Sellauth
            const response = await this.makeAPICall('/checkout/create', {
                method: 'POST',
                body: JSON.stringify(checkoutData)
            });
            
            if (response.success) {
                return response.checkout_url;
            } else {
                throw new Error(response.message || 'Failed to create checkout session');
            }
        } catch (error) {
            console.error('Error creating checkout session:', error);
            throw error;
        }
    }

    // Prepare checkout data for Sellauth
    prepareCheckoutData(orderData) {
        const product = PRODUCT_MAPPING[orderData.product];
        
        return {
            return_url: `${window.location.origin}?status=success&order_id={ORDER_ID}`,
            cancel_url: `${window.location.origin}?status=cancelled&order_id={ORDER_ID}`,
            items: [{
                product_id: product.sellAuthProductId,
                quantity: orderData.quantity,
                custom_fields: {
                    server_invite: orderData.serverInvite,
                    duration: orderData.duration
                }
            }],
            customer_email: null, // Will be collected during checkout
            metadata: {
                source: 'website',
                product_type: orderData.product,
                timestamp: new Date().toISOString()
            }
        };
    }

    // Make API call to your backend (which communicates with Sellauth)
    async makeAPICall(endpoint, options = {}) {
        // This is a mock implementation
        // In reality, you should make calls to your backend server
        // which then communicates with Sellauth using your private API key
        
        console.log('Mock API call to:', endpoint, options);
        
        // Simulate API response based on endpoint
        if (endpoint === '/checkout/create') {
            return {
                success: true,
                checkout_url: `${this.config.shopUrl}/checkout?session=mock_session_${Date.now()}`
            };
        }
        
        // For demo purposes, simulate other responses
        return { success: true, data: {} };
    }

    // Add item to cart
    addToCart(orderData) {
        const cartItem = {
            id: Date.now(),
            product: orderData.product,
            duration: orderData.duration,
            quantity: orderData.quantity,
            serverInvite: orderData.serverInvite,
            unitPrice: parseFloat(orderData.totalPrice.replace('$', '')) / orderData.quantity,
            totalPrice: parseFloat(orderData.totalPrice.replace('$', ''))
        };
        
        this.cart.push(cartItem);
        this.saveCart();
        this.updateCartUI();
        
        showNotification(`Added ${this.getProductName(orderData.product)} to cart!`, 'success');
    }

    // Remove item from cart
    removeFromCart(itemId) {
        this.cart = this.cart.filter(item => item.id !== itemId);
        this.saveCart();
        this.updateCartUI();
    }

    // Clear cart
    clearCart() {
        this.cart = [];
        this.saveCart();
        this.updateCartUI();
    }

    // Save cart to localStorage
    saveCart() {
        localStorage.setItem('sellauth_cart', JSON.stringify(this.cart));
    }

    // Load cart from localStorage
    loadCart() {
        const savedCart = localStorage.getItem('sellauth_cart');
        if (savedCart) {
            this.cart = JSON.parse(savedCart);
            this.updateCartUI();
        }
    }

    // Update cart UI
    updateCartUI() {
        const cartCount = this.cart.reduce((sum, item) => sum + item.quantity, 0);
        const cartTotal = this.cart.reduce((sum, item) => sum + item.totalPrice, 0);
        
        // Update cart indicators (you can add these elements to your HTML)
        const cartCountElements = document.querySelectorAll('.cart-count');
        const cartTotalElements = document.querySelectorAll('.cart-total');
        
        cartCountElements.forEach(el => {
            el.textContent = cartCount;
            el.style.display = cartCount > 0 ? 'inline' : 'none';
        });
        
        cartTotalElements.forEach(el => {
            el.textContent = `$${cartTotal.toFixed(2)}`;
        });
    }

    // Get product name
    getProductName(productType) {
        const products = getProductData();
        return products[productType]?.title || productType;
    }

    // Handle successful payment
    handleSuccessfulPayment(orderId) {
        showNotification('Payment successful! Your order is being processed.', 'success');
        this.clearCart();
        
        // You might want to redirect to a thank you page or show order details
        setTimeout(() => {
            this.showOrderConfirmation(orderId);
        }, 2000);
    }

    // Handle cancelled payment
    handleCancelledPayment(orderId) {
        showNotification('Payment was cancelled. Your cart items are still saved.', 'warning');
    }

    // Handle failed payment
    handleFailedPayment(orderId) {
        showNotification('Payment failed. Please try again or contact support.', 'error');
    }

    // Show order confirmation
    showOrderConfirmation(orderId) {
        const modalHTML = `
            <div class="modal-backdrop">
                <div class="product-modal">
                    <div class="modal-header">
                        <h2 class="modal-title">Order Confirmed!</h2>
                        <button class="modal-close" onclick="closeOrderModal()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <div class="modal-content">
                        <div class="success-message">
                            <div class="success-icon">
                                <i class="fas fa-check-circle"></i>
                            </div>
                            <h3>Thank you for your purchase!</h3>
                            <p>Your order has been confirmed and is being processed.</p>
                            
                            <div class="order-details">
                                <div class="detail-item">
                                    <span>Order ID:</span>
                                    <span>${orderId}</span>
                                </div>
                                <div class="detail-item">
                                    <span>Status:</span>
                                    <span class="status-processing">Processing</span>
                                </div>
                                <div class="detail-item">
                                    <span>Delivery:</span>
                                    <span>Usually within 30 seconds</span>
                                </div>
                            </div>
                            
                            <p class="small-text">
                                You will receive an email confirmation shortly. 
                                If you have any questions, please contact our support team.
                            </p>
                        </div>
                        
                        <div class="modal-actions">
                            <button class="btn-modal-secondary" onclick="openDiscord()">
                                <i class="fab fa-discord"></i>
                                Join Discord
                            </button>
                            <button class="btn-modal-primary" onclick="closeOrderModal()">
                                <i class="fas fa-home"></i>
                                Continue Shopping
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        const modalContainer = document.getElementById('modal-container');
        modalContainer.innerHTML = modalHTML;
        
        const modal = modalContainer.querySelector('.product-modal');
        const backdrop = modalContainer.querySelector('.modal-backdrop');
        
        setTimeout(() => {
            modal.classList.add('show');
            backdrop.classList.add('show');
        }, 10);
    }

    // Checkout with multiple items
    async checkoutCart() {
        if (this.cart.length === 0) {
            showNotification('Your cart is empty!', 'warning');
            return;
        }
        
        try {
            const checkoutData = {
                items: this.cart,
                totalAmount: this.cart.reduce((sum, item) => sum + item.totalPrice, 0)
            };
            
            const checkoutUrl = await this.createCheckoutSession(checkoutData);
            
            // Redirect to Sellauth checkout
            window.location.href = checkoutUrl;
        } catch (error) {
            showNotification('Failed to create checkout. Please try again.', 'error');
            console.error('Checkout error:', error);
        }
    }

    // Direct checkout for single item
    async directCheckout(orderData) {
        try {
            const checkoutUrl = await this.createCheckoutSession(orderData);
            
            // Redirect to Sellauth checkout
            window.location.href = checkoutUrl;
        } catch (error) {
            showNotification('Failed to create checkout. Please try again.', 'error');
            console.error('Checkout error:', error);
        }
    }
}

// ===== INITIALIZE SELLAUTH =====
const sellAuth = new SellAuthIntegration(SELLAUTH_CONFIG);

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    sellAuth.initialize();
});

// ===== GLOBAL FUNCTIONS FOR INTEGRATION =====
// This function is called from main.js
function initiateSellAuthCheckout(orderData) {
    sellAuth.directCheckout(orderData);
}

// Cart management functions
function addToCart(orderData) {
    sellAuth.addToCart(orderData);
}

function removeFromCart(itemId) {
    sellAuth.removeFromCart(itemId);
}

function checkoutCart() {
    sellAuth.checkoutCart();
}

function clearCart() {
    sellAuth.clearCart();
}

// Close order confirmation modal
function closeOrderModal() {
    const modalContainer = document.getElementById('modal-container');
    const modal = modalContainer.querySelector('.product-modal');
    const backdrop = modalContainer.querySelector('.modal-backdrop');
    
    if (modal && backdrop) {
        modal.classList.remove('show');
        backdrop.classList.remove('show');
        
        setTimeout(() => {
            modalContainer.innerHTML = '';
        }, 300);
    }
}

// ===== WEBHOOK HANDLING (FOR SERVER-SIDE) =====
// This is an example of how you would handle webhooks on your server
function handleSellAuthWebhook(payload, signature) {
    // Verify webhook signature
    const crypto = require('crypto');
    const expectedSignature = crypto
        .createHmac('sha256', SELLAUTH_CONFIG.webhookSecret)
        .update(JSON.stringify(payload))
        .digest('hex');
    
    if (signature !== expectedSignature) {
        throw new Error('Invalid webhook signature');
    }
    
    // Handle different webhook events
    switch (payload.event) {
        case 'payment.completed':
            handlePaymentCompleted(payload.data);
            break;
        case 'payment.failed':
            handlePaymentFailed(payload.data);
            break;
        case 'order.created':
            handleOrderCreated(payload.data);
            break;
        case 'order.delivered':
            handleOrderDelivered(payload.data);
            break;
        default:
            console.log('Unhandled webhook event:', payload.event);
    }
}

function handlePaymentCompleted(data) {
    console.log('Payment completed:', data);
    // Process the order, deliver products, send confirmation emails, etc.
}

function handlePaymentFailed(data) {
    console.log('Payment failed:', data);
    // Handle failed payment, maybe retry or notify customer
}

function handleOrderCreated(data) {
    console.log('Order created:', data);
    // Log order creation, update inventory, etc.
}

function handleOrderDelivered(data) {
    console.log('Order delivered:', data);
    // Update order status, send delivery confirmation, etc.
}

// ===== UTILITY FUNCTIONS =====
// Validate server invite URL
function isValidDiscordInvite(url) {
    const discordInviteRegex = /^https?:\/\/(discord\.gg\/|discordapp\.com\/invite\/)[a-zA-Z0-9]+$/;
    return discordInviteRegex.test(url);
}

// Format price for display
function formatPrice(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

// Generate order reference
function generateOrderReference() {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substr(2, 5);
    return `ORD-${timestamp}-${random}`.toUpperCase();
}

// ===== DEMO MODE WARNING =====
if (SELLAUTH_CONFIG.shopId === 'your-shop-id') {
    console.warn(`
    🚨 SELLAUTH DEMO MODE 🚨
    
    This is running in demo mode. To connect to your actual Sellauth shop:
    
    1. Replace SELLAUTH_CONFIG values with your actual:
       - shopId
       - publicKey
       - shopUrl
       - apiUrl
    
    2. Set up your backend API endpoints to communicate with Sellauth
    
    3. Update PRODUCT_MAPPING with your actual Sellauth product IDs
    
    4. Test thoroughly before going live!
    `);
}

// Add additional CSS for success modal
const successModalCSS = `
.success-message {
    text-align: center;
    padding: 2rem 0;
}

.success-icon {
    font-size: 4rem;
    color: var(--accent-color);
    margin-bottom: 1rem;
}

.success-message h3 {
    font-size: var(--fs-2xl);
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 1rem;
}

.success-message p {
    color: var(--text-secondary);
    margin-bottom: 2rem;
}

.order-details {
    background: rgba(255, 255, 255, 0.05);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    margin: 2rem 0;
}

.detail-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0;
    color: var(--text-secondary);
}

.detail-item span:last-child {
    color: var(--text-primary);
    font-weight: 600;
}

.status-processing {
    color: var(--warning-color) !important;
}

.small-text {
    font-size: var(--fs-sm);
    color: var(--text-muted);
    line-height: 1.5;
}
`;

// Inject success modal CSS
const successStyle = document.createElement('style');
successStyle.textContent = successModalCSS;
document.head.appendChild(successStyle);