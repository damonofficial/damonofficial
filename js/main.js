// ===== GLOBAL VARIABLES =====
let isLoading = true;
let currentProductModal = null;
let reviewsInterval = null;

// ===== DOM CONTENT LOADED =====
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the website
    initializeWebsite();
});

// ===== INITIALIZE WEBSITE =====
function initializeWebsite() {
    // Show loading screen
    showLoadingScreen();
    
    // Initialize AOS (Animate On Scroll)
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 800,
            easing: 'ease-out-cubic',
            once: true,
            offset: 50
        });
    }
    
    // Initialize all components
    initializeNavigation();
    initializeHeroAnimations();
    initializeScrollEffects();
    initializeFAQ();
    initializeContactForm();
    initializeReviewsAnimation();
    initializeStatsCounter();
    initializeMobileMenu();
    
    // Hide loading screen after a delay
    setTimeout(() => {
        hideLoadingScreen();
    }, 2000);
}

// ===== LOADING SCREEN =====
function showLoadingScreen() {
    const loadingScreen = document.getElementById('loading-screen');
    if (loadingScreen) {
        loadingScreen.classList.remove('hidden');
    }
}

function hideLoadingScreen() {
    const loadingScreen = document.getElementById('loading-screen');
    if (loadingScreen) {
        loadingScreen.classList.add('hidden');
        setTimeout(() => {
            loadingScreen.style.display = 'none';
        }, 500);
    }
    isLoading = false;
}

// ===== NAVIGATION =====
function initializeNavigation() {
    const navbar = document.getElementById('navbar');
    const navLinks = document.querySelectorAll('.nav-link');
    
    // Navbar scroll effect
    window.addEventListener('scroll', () => {
        if (window.scrollY > 100) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
    
    // Smooth scroll for navigation links
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                const offsetTop = targetElement.offsetTop - 80;
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
            
            // Close mobile menu if open
            closeMobileMenu();
        });
    });
}

// ===== MOBILE MENU =====
function initializeMobileMenu() {
    const navToggle = document.getElementById('nav-toggle');
    const navMenu = document.getElementById('nav-menu');
    
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            navToggle.classList.toggle('active');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!navToggle.contains(e.target) && !navMenu.contains(e.target)) {
                closeMobileMenu();
            }
        });
    }
}

function closeMobileMenu() {
    const navMenu = document.getElementById('nav-menu');
    const navToggle = document.getElementById('nav-toggle');
    
    if (navMenu && navToggle) {
        navMenu.classList.remove('active');
        navToggle.classList.remove('active');
    }
}

// ===== HERO ANIMATIONS =====
function initializeHeroAnimations() {
    // Animate statistics counters
    const statNumbers = document.querySelectorAll('.stat-number[data-count]');
    
    const animateCounter = (element) => {
        const target = parseFloat(element.getAttribute('data-count'));
        const duration = 2000;
        const step = target / (duration / 16);
        let current = 0;
        
        const counter = setInterval(() => {
            current += step;
            if (current >= target) {
                current = target;
                clearInterval(counter);
            }
            
            if (target > 1000000) {
                element.textContent = (current / 1000000).toFixed(1) + 'M';
            } else if (target > 1000) {
                element.textContent = Math.floor(current / 1000) + 'K';
            } else {
                element.textContent = current.toFixed(1);
            }
        }, 16);
    };
    
    // Intersection Observer for counters
    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                counterObserver.unobserve(entry.target);
            }
        });
    });
    
    statNumbers.forEach(stat => {
        counterObserver.observe(stat);
    });
}

// ===== SCROLL EFFECTS =====
function initializeScrollEffects() {
    // Parallax effect for hero background
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        const parallax = document.querySelector('.animated-bg');
        
        if (parallax) {
            const speed = scrolled * 0.5;
            parallax.style.transform = `translateY(${speed}px)`;
        }
    });
    
    // Show/hide scroll indicator
    const scrollIndicator = document.querySelector('.scroll-indicator');
    if (scrollIndicator) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 100) {
                scrollIndicator.style.opacity = '0';
            } else {
                scrollIndicator.style.opacity = '1';
            }
        });
    }
}

// ===== FAQ FUNCTIONALITY =====
function initializeFAQ() {
    const faqItems = document.querySelectorAll('.faq-item');
    
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        question.addEventListener('click', () => {
            const isActive = item.classList.contains('active');
            
            // Close all FAQ items
            faqItems.forEach(faq => {
                faq.classList.remove('active');
            });
            
            // Open clicked item if it wasn't active
            if (!isActive) {
                item.classList.add('active');
            }
        });
    });
}

function toggleFAQ(element) {
    const faqItem = element.parentElement;
    const isActive = faqItem.classList.contains('active');
    
    // Close all FAQ items
    document.querySelectorAll('.faq-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Open clicked item if it wasn't active
    if (!isActive) {
        faqItem.classList.add('active');
    }
}

// ===== CONTACT FORM =====
function initializeContactForm() {
    const form = document.getElementById('contact-form');
    if (form) {
        form.addEventListener('submit', submitContactForm);
    }
}

function submitContactForm(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const data = {
        name: formData.get('name'),
        email: formData.get('email'),
        subject: formData.get('subject'),
        message: formData.get('message')
    };
    
    // Show loading state
    const submitBtn = event.target.querySelector('.btn-submit');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
    submitBtn.disabled = true;
    
    // Simulate form submission (replace with actual API call)
    setTimeout(() => {
        // Reset form
        event.target.reset();
        
        // Show success message
        showNotification('Message sent successfully! We\'ll get back to you soon.', 'success');
        
        // Reset button
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }, 2000);
}

// ===== REVIEWS ANIMATION =====
function initializeReviewsAnimation() {
    const reviewsWrapper = document.getElementById('reviews-wrapper');
    if (!reviewsWrapper) return;
    
    // Clone reviews for infinite scroll
    const reviews = reviewsWrapper.innerHTML;
    reviewsWrapper.innerHTML = reviews + reviews;
    
    // Pause animation on hover
    reviewsWrapper.addEventListener('mouseenter', () => {
        reviewsWrapper.style.animationPlayState = 'paused';
    });
    
    reviewsWrapper.addEventListener('mouseleave', () => {
        reviewsWrapper.style.animationPlayState = 'running';
    });
}

// ===== STATS COUNTER =====
function initializeStatsCounter() {
    const observerOptions = {
        threshold: 0.5,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counters = entry.target.querySelectorAll('.stat-number[data-count]');
                counters.forEach(counter => {
                    animateStatCounter(counter);
                });
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    const statsContainers = document.querySelectorAll('.hero-stats, .review-stats');
    statsContainers.forEach(container => {
        observer.observe(container);
    });
}

function animateStatCounter(element) {
    const target = parseFloat(element.getAttribute('data-count'));
    const duration = 2000;
    const increment = target / (duration / 16);
    let current = 0;
    
    const updateCounter = () => {
        current += increment;
        if (current >= target) {
            current = target;
        }
        
        // Format the number
        let displayValue;
        if (target >= 1000000) {
            displayValue = (current / 1000000).toFixed(1) + 'M';
        } else if (target >= 1000) {
            displayValue = Math.floor(current / 1000) + 'K';
        } else if (target % 1 !== 0) {
            displayValue = current.toFixed(1);
        } else {
            displayValue = Math.floor(current);
        }
        
        element.textContent = displayValue;
        
        if (current < target) {
            requestAnimationFrame(updateCounter);
        }
    };
    
    updateCounter();
}

// ===== PRODUCT MODALS =====
function openProductModal(productType) {
    const modalHTML = createProductModalHTML(productType);
    const modalContainer = document.getElementById('modal-container');
    
    modalContainer.innerHTML = modalHTML;
    
    const modal = modalContainer.querySelector('.product-modal');
    const backdrop = modalContainer.querySelector('.modal-backdrop');
    
    // Show modal with animation
    setTimeout(() => {
        modal.classList.add('show');
        backdrop.classList.add('show');
    }, 10);
    
    // Close modal handlers
    backdrop.addEventListener('click', closeProductModal);
    modal.querySelector('.modal-close').addEventListener('click', closeProductModal);
    
    // Initialize product options
    initializeProductOptions(productType);
    
    currentProductModal = productType;
}

function createProductModalHTML(productType) {
    const products = getProductData();
    const product = products[productType];
    
    if (!product) return '';
    
    return `
        <div class="modal-backdrop">
            <div class="product-modal">
                <div class="modal-header">
                    <h2 class="modal-title">${product.title}</h2>
                    <button class="modal-close">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <div class="modal-content">
                    <div class="product-options">
                        <div class="option-group">
                            <label for="duration">Duration:</label>
                            <select id="duration" class="option-select">
                                ${product.durations.map(duration => 
                                    `<option value="${duration.value}" data-price="${duration.price}">
                                        ${duration.label} - $${duration.price}
                                    </option>`
                                ).join('')}
                            </select>
                        </div>
                        
                        <div class="option-group">
                            <label for="quantity">Quantity:</label>
                            <input type="number" id="quantity" value="1" min="1" max="100" class="option-input">
                        </div>
                        
                        <div class="option-group">
                            <label for="server-invite">Server Invite Link:</label>
                            <input type="url" id="server-invite" placeholder="https://discord.gg/..." class="option-input">
                        </div>
                    </div>
                    
                    <div class="pricing-summary">
                        <div class="price-breakdown">
                            <div class="price-item">
                                <span>Unit Price:</span>
                                <span id="unit-price">$${product.durations[0].price}</span>
                            </div>
                            <div class="price-item">
                                <span>Quantity:</span>
                                <span id="price-quantity">1</span>
                            </div>
                            <div class="price-item total">
                                <span>Total:</span>
                                <span id="total-price">$${product.durations[0].price}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="modal-actions">
                        <button class="btn-modal-secondary" onclick="closeProductModal()">
                            Cancel
                        </button>
                        <button class="btn-modal-primary" onclick="proceedToCheckout()">
                            <i class="fas fa-shopping-cart"></i>
                            Add to Cart
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function initializeProductOptions(productType) {
    const durationSelect = document.getElementById('duration');
    const quantityInput = document.getElementById('quantity');
    const unitPriceElement = document.getElementById('unit-price');
    const quantityElement = document.getElementById('price-quantity');
    const totalPriceElement = document.getElementById('total-price');
    
    function updatePrice() {
        const selectedOption = durationSelect.options[durationSelect.selectedIndex];
        const unitPrice = parseFloat(selectedOption.dataset.price);
        const quantity = parseInt(quantityInput.value) || 1;
        const total = unitPrice * quantity;
        
        unitPriceElement.textContent = `$${unitPrice.toFixed(2)}`;
        quantityElement.textContent = quantity;
        totalPriceElement.textContent = `$${total.toFixed(2)}`;
    }
    
    durationSelect.addEventListener('change', updatePrice);
    quantityInput.addEventListener('input', updatePrice);
}

function closeProductModal() {
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
    
    currentProductModal = null;
}

function proceedToCheckout() {
    const serverInvite = document.getElementById('server-invite').value;
    const duration = document.getElementById('duration').value;
    const quantity = document.getElementById('quantity').value;
    const totalPrice = document.getElementById('total-price').textContent;
    
    if (!serverInvite) {
        showNotification('Please provide a server invite link', 'error');
        return;
    }
    
    // Here you would integrate with Sellauth
    const orderData = {
        product: currentProductModal,
        duration: duration,
        quantity: parseInt(quantity),
        serverInvite: serverInvite,
        totalPrice: totalPrice
    };
    
    // For now, show a success message
    showNotification('Redirecting to checkout...', 'info');
    closeProductModal();
    
    // This is where you'd call the Sellauth integration
    setTimeout(() => {
        initiateSellAuthCheckout(orderData);
    }, 1000);
}

// ===== UTILITY FUNCTIONS =====
function scrollToProducts() {
    const productsSection = document.getElementById('products');
    if (productsSection) {
        const offsetTop = productsSection.offsetTop - 80;
        window.scrollTo({
            top: offsetTop,
            behavior: 'smooth'
        });
    }
}

function openDiscord() {
    window.open('https://discord.gg/your-server', '_blank');
}

function openLoginModal() {
    showNotification('Login feature coming soon!', 'info');
}

function openTicketSystem() {
    showNotification('Ticket system coming soon!', 'info');
}

function openTerms() {
    showNotification('Terms of Service page coming soon!', 'info');
}

function openPrivacy() {
    showNotification('Privacy Policy page coming soon!', 'info');
}

function openRefundPolicy() {
    showNotification('Refund Policy page coming soon!', 'info');
}

function openCookiePolicy() {
    showNotification('Cookie Policy page coming soon!', 'info');
}

// ===== NOTIFICATION SYSTEM =====
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${getNotificationIcon(type)}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="closeNotification(this)">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Add to DOM
    document.body.appendChild(notification);
    
    // Show with animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        closeNotification(notification.querySelector('.notification-close'));
    }, 5000);
}

function getNotificationIcon(type) {
    switch (type) {
        case 'success': return 'fa-check-circle';
        case 'error': return 'fa-exclamation-circle';
        case 'warning': return 'fa-exclamation-triangle';
        default: return 'fa-info-circle';
    }
}

function closeNotification(button) {
    const notification = button.closest('.notification');
    if (notification) {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }
}

// ===== PRODUCT DATA =====
function getProductData() {
    return {
        'server-boosts': {
            title: 'Discord Server Boosts',
            durations: [
                { label: '1 Month', value: '1m', price: 5.99 },
                { label: '3 Months', value: '3m', price: 15.99 },
                { label: '6 Months', value: '6m', price: 29.99 },
                { label: '12 Months', value: '12m', price: 55.99 }
            ]
        },
        'discord-nitro': {
            title: 'Discord Nitro',
            durations: [
                { label: '1 Month', value: '1m', price: 7.99 },
                { label: '3 Months', value: '3m', price: 21.99 },
                { label: '6 Months', value: '6m', price: 41.99 },
                { label: '12 Months', value: '12m', price: 79.99 }
            ]
        },
        'nitro-tokens': {
            title: 'Nitro Tokens (UHQ)',
            durations: [
                { label: '10 Tokens', value: '10', price: 1.99 },
                { label: '25 Tokens', value: '25', price: 4.49 },
                { label: '50 Tokens', value: '50', price: 8.99 },
                { label: '100 Tokens', value: '100', price: 16.99 }
            ]
        },
        'discord-members': {
            title: 'Discord Members',
            durations: [
                { label: '100 Members', value: '100', price: 2.99 },
                { label: '250 Members', value: '250', price: 6.99 },
                { label: '500 Members', value: '500', price: 12.99 },
                { label: '1000 Members', value: '1000', price: 24.99 }
            ]
        },
        'aged-accounts': {
            title: 'Discord Aged Accounts',
            durations: [
                { label: '2016 Account', value: '2016', price: 8.99 },
                { label: '2017 Account', value: '2017', price: 7.99 },
                { label: '2018 Account', value: '2018', price: 6.99 },
                { label: '2019 Account', value: '2019', price: 5.99 }
            ]
        },
        'boost-tools': {
            title: 'Professional Boost Tools',
            durations: [
                { label: 'Basic Tool', value: 'basic', price: 19.99 },
                { label: 'Pro Tool', value: 'pro', price: 39.99 },
                { label: 'Enterprise Tool', value: 'enterprise', price: 79.99 },
                { label: 'Ultimate Package', value: 'ultimate', price: 149.99 }
            ]
        }
    };
}

// ===== KEYBOARD SHORTCUTS =====
document.addEventListener('keydown', (e) => {
    // ESC to close modals
    if (e.key === 'Escape') {
        if (currentProductModal) {
            closeProductModal();
        }
    }
    
    // Ctrl/Cmd + K to focus search (if implemented)
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        // Implement search functionality
    }
});

// ===== PERFORMANCE OPTIMIZATIONS =====
// Debounce function for scroll events
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle function for resize events
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// ===== WINDOW EVENTS =====
window.addEventListener('resize', throttle(() => {
    // Handle window resize
    if (window.innerWidth > 768) {
        closeMobileMenu();
    }
}, 250));

// Prevent zooming on iOS
document.addEventListener('touchstart', (e) => {
    if (e.touches.length > 1) {
        e.preventDefault();
    }
});

// Add CSS for notifications and modals
const additionalCSS = `
/* Notification Styles */
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(20px);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 1rem 1.5rem;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 1rem;
    min-width: 300px;
    z-index: var(--z-toast);
    transform: translateX(400px);
    opacity: 0;
    transition: all var(--animation-base);
}

.notification.show {
    transform: translateX(0);
    opacity: 1;
}

.notification-success {
    border-color: var(--accent-color);
}

.notification-error {
    border-color: var(--danger-color);
}

.notification-warning {
    border-color: var(--warning-color);
}

.notification-content {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex: 1;
}

.notification-close {
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 0.25rem;
    border-radius: var(--radius-sm);
    transition: color var(--animation-fast);
}

.notification-close:hover {
    color: var(--text-primary);
}

/* Modal Styles */
.modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(5px);
    z-index: var(--z-modal-backdrop);
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    visibility: hidden;
    transition: all var(--animation-base);
}

.modal-backdrop.show {
    opacity: 1;
    visibility: visible;
}

.product-modal {
    background: rgba(17, 17, 21, 0.95);
    backdrop-filter: blur(20px);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-2xl);
    width: 90%;
    max-width: 600px;
    max-height: 90vh;
    overflow-y: auto;
    transform: scale(0.9) translateY(50px);
    opacity: 0;
    transition: all var(--animation-base);
}

.product-modal.show {
    transform: scale(1) translateY(0);
    opacity: 1;
}

.modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 2rem 2rem 1rem;
    border-bottom: 1px solid var(--border-color);
}

.modal-title {
    font-size: var(--fs-2xl);
    font-weight: 700;
    color: var(--text-primary);
}

.modal-close {
    background: none;
    border: none;
    color: var(--text-secondary);
    font-size: var(--fs-xl);
    cursor: pointer;
    padding: 0.5rem;
    border-radius: var(--radius-lg);
    transition: all var(--animation-fast);
}

.modal-close:hover {
    color: var(--text-primary);
    background: rgba(255, 255, 255, 0.1);
}

.modal-content {
    padding: 2rem;
}

.option-group {
    margin-bottom: 1.5rem;
}

.option-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 600;
    color: var(--text-primary);
}

.option-select,
.option-input {
    width: 100%;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    color: var(--text-primary);
    font-family: inherit;
    transition: all var(--animation-fast);
}

.option-select:focus,
.option-input:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(88, 101, 242, 0.1);
}

.pricing-summary {
    background: rgba(255, 255, 255, 0.05);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    margin: 2rem 0;
}

.price-breakdown {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.price-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: var(--text-secondary);
}

.price-item.total {
    border-top: 1px solid var(--border-color);
    padding-top: 0.75rem;
    font-weight: 700;
    font-size: var(--fs-lg);
    color: var(--text-primary);
}

.modal-actions {
    display: flex;
    gap: 1rem;
    justify-content: flex-end;
}

.btn-modal-secondary,
.btn-modal-primary {
    padding: 1rem 2rem;
    border: none;
    border-radius: var(--radius-lg);
    font-weight: 600;
    cursor: pointer;
    transition: all var(--animation-base);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.btn-modal-secondary {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
}

.btn-modal-secondary:hover {
    background: rgba(255, 255, 255, 0.2);
}

.btn-modal-primary {
    background: var(--gradient-discord);
    color: white;
}

.btn-modal-primary:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-glow);
}

@media (max-width: 768px) {
    .notification {
        right: 10px;
        left: 10px;
        min-width: auto;
    }
    
    .product-modal {
        width: 95%;
        margin: 1rem;
    }
    
    .modal-header,
    .modal-content {
        padding: 1.5rem 1rem;
    }
    
    .modal-actions {
        flex-direction: column;
    }
}
`;

// Inject additional CSS
const style = document.createElement('style');
style.textContent = additionalCSS;
document.head.appendChild(style);