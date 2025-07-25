# BoostHub - Premium Discord Services Website

A modern, responsive website for selling Discord services including server boosts, Nitro tokens, and more. Built with stunning gradients, glass morphism effects, smooth animations, and integrated with Sellauth for secure payment processing.

## 🌟 Features

### ✨ Design & UI/UX
- **Modern Glass Morphism Design** - Beautiful glassmorphism effects with backdrop blur
- **Stunning Gradient Animations** - Dynamic color-shifting backgrounds and gradients
- **Responsive Design** - Fully responsive across all devices (mobile, tablet, desktop)
- **Smooth Animations** - AOS (Animate On Scroll) library for smooth page transitions
- **Interactive Elements** - Hover effects, loading animations, and micro-interactions
- **Professional Typography** - Inter font family for clean, modern text

### 🚀 Performance & Functionality
- **Fast Loading** - Optimized images, CSS, and JavaScript for quick load times
- **SEO Optimized** - Proper meta tags, structured data, and semantic HTML
- **Progressive Enhancement** - Works without JavaScript, enhanced with JS
- **Lazy Loading** - Images and content load as needed
- **Accessible** - WCAG compliant with proper ARIA labels and keyboard navigation

### 💎 Product Features
- **Product Showcase** - Beautiful cards for Discord services
- **Interactive Modals** - Product configuration with real-time pricing
- **Smart Pricing** - Dynamic price calculation based on quantity and duration
- **Cart System** - Add multiple items to cart with localStorage persistence
- **Order Management** - Full order tracking and confirmation system

### 🔐 Payment Integration
- **Sellauth Integration** - Secure payment processing with Sellauth
- **Multiple Payment Methods** - PayPal, Stripe, cryptocurrencies
- **Secure Checkout** - Industry-standard security measures
- **Webhook Support** - Real-time order status updates
- **Automated Delivery** - Instant product delivery upon payment

### 📱 Additional Features
- **FAQ System** - Collapsible FAQ with smooth animations
- **Contact Forms** - Multiple ways for customers to get in touch
- **Review System** - Animated customer testimonials
- **Stats Counter** - Animated statistics on page load
- **Mobile Menu** - Smooth hamburger menu for mobile devices
- **Loading Screen** - Professional loading animation

## 🎨 Design Highlights

### Color Scheme
- **Primary**: Discord Blue (#5865F2)
- **Secondary**: Pink (#EB459E) 
- **Accent**: Green (#57F287)
- **Background**: Dark theme with subtle gradients
- **Glass Effects**: Translucent elements with backdrop blur

### Gradient Combinations
- Discord gradient: `#5865F2 → #7289DA`
- Nitro gradient: `#FF73FA → #8B5CF6`
- Boost gradient: `#06FFA5 → #00D4FF`
- Background: `#667eea → #764ba2 → #f093fb`

## 🛠️ Installation & Setup

### Prerequisites
- Modern web browser
- Text editor (VS Code recommended)
- Basic knowledge of HTML/CSS/JavaScript
- Sellauth account for payment processing

### Quick Start

1. **Clone/Download the project**
   ```bash
   git clone [repository-url]
   cd discord-boost-website
   ```

2. **Open in your preferred editor**
   ```bash
   code . # For VS Code
   ```

3. **Configure Sellauth Integration**
   - Open `js/sellauth-integration.js`
   - Replace placeholder values in `SELLAUTH_CONFIG`:
     ```javascript
     const SELLAUTH_CONFIG = {
         shopId: 'your-actual-shop-id',
         publicKey: 'your-public-api-key',
         shopUrl: 'https://your-shop.sellauth.com',
         // ... other config
     };
     ```

4. **Update Product Mapping**
   - Modify `PRODUCT_MAPPING` to match your Sellauth products:
     ```javascript
     const PRODUCT_MAPPING = {
         'server-boosts': {
             sellAuthProductId: 'your-sellauth-product-id',
             category: 'Discord Services'
         },
         // ... other products
     };
     ```

5. **Customize Content**
   - Update company name, Discord server links
   - Modify product descriptions and pricing
   - Add your own branding and logo

6. **Launch**
   - Open `index.html` in your browser
   - Or deploy to your web hosting provider

## 📁 File Structure

```
discord-boost-website/
├── index.html              # Main HTML file
├── css/
│   └── styles.css          # Main stylesheet with all styles
├── js/
│   ├── main.js            # Core website functionality
│   └── sellauth-integration.js # Payment processing integration
├── assets/ (create this folder)
│   ├── images/            # Your images and logos
│   ├── favicon.ico        # Website favicon
│   └── og-image.jpg       # Social media preview image
└── README.md              # This file
```

## ⚙️ Configuration

### Sellauth Setup

1. **Create Sellauth Account**
   - Sign up at [sellauth.com](https://sellauth.com)
   - Set up your shop and products

2. **Get API Credentials**
   - Navigate to your shop settings
   - Generate API keys (public and private)
   - Note your shop ID and URL

3. **Configure Products**
   - Create products in Sellauth dashboard
   - Note the product IDs for mapping
   - Set up pricing and descriptions

4. **Webhook Configuration**
   - Set up webhook endpoint on your server
   - Configure webhook URL in Sellauth
   - Use webhook secret for verification

### Environment Variables (for production)

Create a `.env` file for sensitive data:
```env
SELLAUTH_SHOP_ID=your-shop-id
SELLAUTH_PUBLIC_KEY=your-public-key
SELLAUTH_PRIVATE_KEY=your-private-key
SELLAUTH_WEBHOOK_SECRET=your-webhook-secret
```

## 🎯 Customization Guide

### Changing Colors
1. Open `css/styles.css`
2. Modify CSS custom properties in `:root`:
   ```css
   :root {
     --primary-color: #your-color;
     --gradient-primary: linear-gradient(135deg, #color1, #color2);
   }
   ```

### Adding New Products
1. Add product data in `js/main.js` → `getProductData()`
2. Update product mapping in `js/sellauth-integration.js`
3. Create corresponding products in Sellauth dashboard

### Modifying Layout
- Edit HTML structure in `index.html`
- Adjust CSS Grid/Flexbox layouts in `styles.css`
- Update responsive breakpoints as needed

### Adding New Sections
1. Add HTML markup to `index.html`
2. Add corresponding CSS styles
3. Initialize any JavaScript functionality in `main.js`

## 🔧 Advanced Features

### Backend Integration
For production use, you'll need a backend server to:
- Handle Sellauth API calls securely
- Process webhooks
- Manage user accounts
- Handle order fulfillment

Example backend structure:
```
backend/
├── routes/
│   ├── checkout.js        # Checkout endpoint
│   ├── webhooks.js        # Webhook handler
│   └── products.js        # Product management
├── middleware/
│   ├── auth.js           # Authentication
│   └── validation.js     # Input validation
└── server.js             # Main server file
```

### Security Considerations
- Never expose private API keys in frontend code
- Use HTTPS for all communications
- Implement rate limiting
- Validate all user inputs
- Use CSP headers for XSS protection

## 🚀 Deployment

### Static Hosting (GitHub Pages, Netlify, Vercel)
1. Push code to GitHub repository
2. Connect to hosting platform
3. Configure build settings (if needed)
4. Set environment variables
5. Deploy

### Traditional Web Hosting
1. Upload files via FTP/SFTP
2. Configure web server (Apache/Nginx)
3. Set up SSL certificate
4. Configure domain and DNS

### Docker Deployment
```dockerfile
FROM nginx:alpine
COPY . /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 📊 Analytics & Monitoring

### Google Analytics
Add to `<head>` section:
```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

### Performance Monitoring
- Use Google PageSpeed Insights
- Implement Core Web Vitals tracking
- Monitor server response times
- Set up error tracking (Sentry, etc.)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Common Issues

**Q: Products not showing in checkout**
A: Check product mapping in `sellauth-integration.js` and ensure product IDs match your Sellauth dashboard.

**Q: Animations not working**
A: Ensure AOS library is loading correctly and check browser console for JavaScript errors.

**Q: Mobile menu not responsive**
A: Verify CSS media queries and ensure viewport meta tag is present.

### Getting Help
- Check the [Issues](https://github.com/your-repo/issues) page
- Join our Discord server for support
- Email: support@yourwebsite.com

## 🎉 Acknowledgments

- [AOS Library](https://michalsnik.github.io/aos/) for scroll animations
- [Font Awesome](https://fontawesome.com/) for icons
- [Inter Font](https://rsms.me/inter/) for typography
- [Sellauth](https://sellauth.com/) for payment processing
- Community feedback and contributions

## 🔄 Changelog

### v1.0.0 (Current)
- ✅ Initial release
- ✅ Modern glassmorphism design
- ✅ Sellauth integration
- ✅ Responsive mobile design
- ✅ Product management system
- ✅ Animated UI components

### Coming Soon
- 🔄 User dashboard
- 🔄 Order history
- 🔄 Advanced analytics
- 🔄 Multi-language support
- 🔄 Dark/Light theme toggle

---

**Made with ❤️ for the Discord community**

For questions or custom development work, feel free to reach out!
