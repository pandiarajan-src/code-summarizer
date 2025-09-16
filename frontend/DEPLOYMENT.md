# Code Summarizer Frontend Deployment Guide

This guide covers various deployment options for the Code Summarizer frontend application.

## 🚀 Quick Start (Development)

### Option 1: Using the Startup Script
```bash
cd frontend
./start.sh [PORT]
```

### Option 2: Manual Setup
```bash
# Using Python 3
python3 -m http.server 8080

# Using Node.js
npx serve . -p 8080

# Using PHP
php -S localhost:8080
```

Then open `http://localhost:8080` in your browser.

## 🐳 Docker Deployment

### Build and Run
```bash
cd frontend

# Build the Docker image
docker build -t code-summarizer-frontend .

# Run the container
docker run -d -p 8080:80 --name code-summarizer-frontend code-summarizer-frontend
```

### Docker Compose (Recommended)
Create `docker-compose.yml` in the project root:

```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "8080:80"
    depends_on:
      - api
    environment:
      - API_BASE_URL=http://api:8000

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
```

Run with:
```bash
docker-compose up -d
```

## ☁️ Cloud Deployments

### Vercel
1. Install Vercel CLI: `npm i -g vercel`
2. In the frontend directory: `vercel`
3. Configure API URL in production

### Netlify
1. Drag and drop the frontend folder to Netlify
2. Set environment variables for API configuration

### AWS S3 + CloudFront
1. Upload files to S3 bucket
2. Enable static website hosting
3. Configure CloudFront for global distribution

### Nginx (Production)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/code-summarizer;
    index index.html;

    # API proxy (optional)
    location /api/ {
        proxy_pass http://your-api-server:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

## 🔧 Configuration

### API Configuration
Update the API configuration in `index.html`:

```javascript
window.API_CONFIG = {
    baseUrl: 'https://your-api-domain.com',  // Production API URL
    endpoints: {
        health: '/api/health',
        analyze: '/api/analyze/upload',
        batchAnalyze: '/api/analyze/batch/upload',
        supportedTypes: '/api/analyze/supported-types',
        validate: '/api/analyze/validate'
    }
};
```

### Environment-Specific Configs

#### Development
```javascript
baseUrl: 'http://127.0.0.1:8000'
```

#### Production
```javascript
baseUrl: 'https://api.your-domain.com'
```

#### Docker
```javascript
baseUrl: 'http://api:8000'  // Using service name
```

## 🔒 Security Considerations

### HTTPS
Always use HTTPS in production:
```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/private.key;
    # ... other config
}
```

### CORS Configuration
Ensure the API server allows your frontend domain:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Content Security Policy
The included nginx.conf sets secure headers. Customize as needed:
```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; style-src 'self' 'unsafe-inline';" always;
```

## 📊 Monitoring & Analytics

### Health Checks
The frontend includes a health endpoint at `/health` for load balancers.

### Error Tracking
Add error tracking service (Sentry, etc.):
```javascript
// Add to app.js
window.addEventListener('error', (e) => {
    console.error('Frontend error:', e);
    // Send to tracking service
});
```

### Performance Monitoring
Use browser dev tools or services like:
- Google PageSpeed Insights
- GTmetrix
- Lighthouse

## 🚦 Load Testing

Test your deployment:
```bash
# Install hey (HTTP load testing tool)
# macOS: brew install hey
# Linux: Download from GitHub

# Test the frontend
hey -n 1000 -c 10 http://your-frontend-url/

# Test API integration
hey -n 100 -c 5 -m POST -H "Content-Type: multipart/form-data" \
    -D test-file.py http://your-api-url/api/analyze/upload
```

## 🔄 CI/CD Pipeline

### GitHub Actions Example
```yaml
name: Deploy Frontend
on:
  push:
    branches: [main]
    paths: ['frontend/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Deploy to Production
        run: |
          # Your deployment script
          rsync -avz frontend/ user@server:/var/www/code-summarizer/
```

## 🐛 Troubleshooting

### Common Issues

1. **CORS Errors**
   - Check API CORS configuration
   - Ensure correct API URL

2. **File Upload Fails**
   - Check file size limits
   - Verify API server is running
   - Check network connectivity

3. **Blank Page**
   - Check browser console for errors
   - Verify all dependencies are loaded
   - Check API configuration

4. **Performance Issues**
   - Enable gzip compression
   - Use CDN for static assets
   - Optimize images

### Debug Mode
Enable debug mode by opening browser console and running:
```javascript
localStorage.setItem('debug', 'true');
location.reload();
```

## 📱 Mobile Optimization

The frontend is responsive but consider:
- Touch-friendly interface
- Reduced file upload sizes
- Progressive Web App (PWA) features

### PWA Setup
Add to `index.html`:
```html
<link rel="manifest" href="manifest.json">
<meta name="theme-color" content="#0071c5">
```

Create `manifest.json`:
```json
{
  "name": "Code Summarizer",
  "short_name": "CodeSum",
  "description": "AI-powered code analysis tool",
  "start_url": "/",
  "display": "standalone",
  "theme_color": "#0071c5",
  "background_color": "#ffffff",
  "icons": [
    {
      "src": "icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    }
  ]
}
```

## 📈 Scaling

### Horizontal Scaling
- Use load balancer (nginx, HAProxy)
- Deploy multiple frontend instances
- CDN for global distribution

### Vertical Scaling
- Optimize bundle size
- Use lazy loading
- Implement caching strategies

## 🛠️ Maintenance

### Regular Tasks
1. Update dependencies
2. Security patch reviews
3. Performance monitoring
4. Backup configurations

### Version Updates
1. Test in staging environment
2. Gradual rollout
3. Monitor error rates
4. Rollback plan ready