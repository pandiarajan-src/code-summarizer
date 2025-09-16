# Code Summarizer Frontend

A modern, responsive web interface for the Code Summarizer API. This frontend provides an intuitive way to upload code files and receive AI-powered analysis reports.

## Features

- **Single Page Application**: Clean, responsive interface optimized for both desktop and mobile
- **File Upload**: Support for single files and ZIP archives with drag-and-drop functionality
- **Progress Tracking**: Real-time upload and analysis progress with visual indicators
- **Markdown Preview**: Live preview of analysis results with syntax highlighting
- **Download Reports**: Save analysis results as markdown files
- **Supported Languages**: Modal popup showing all supported programming languages
- **Intel-inspired Design**: Professional sky blue theme with modern UI elements
- **Cross-browser Compatibility**: Works on all modern browsers
- **Configurable API**: Easy configuration for different API endpoints

## Quick Start

1. **Setup the API Server** (from the parent directory):
   ```bash
   cd ..
   make run-api
   ```

2. **Serve the Frontend**:
   ```bash
   # Using Python (if available)
   python -m http.server 8080

   # Using Node.js (if available)
   npx serve .

   # Or simply open index.html in your browser
   open index.html
   ```

3. **Access the Application**:
   Open your browser and navigate to `http://localhost:8080`

## Configuration

### API Configuration

Edit the API configuration in `index.html`:

```javascript
window.API_CONFIG = {
    baseUrl: 'http://127.0.0.1:8000',  // Change this to your API server URL
    endpoints: {
        health: '/health',
        analyze: '/analyze/upload',
        batchAnalyze: '/analyze/batch/upload',
        supportedTypes: '/analyze/supported-types',
        validate: '/analyze/validate'
    }
};
```

### For Different Environments

- **Development**: `http://127.0.0.1:8000`
- **Production**: Update to your production API URL
- **Docker**: Use container networking (e.g., `http://api:8000`)

## File Structure

```
frontend/
├── index.html          # Main HTML file
├── css/
│   └── styles.css      # Intel-inspired styling
├── js/
│   └── app.js          # Main application logic
├── assets/             # Static assets (if needed)
└── README.md           # This file
```

## Browser Compatibility

- **Chrome/Chromium**: 90+
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+

## Dependencies

The application uses CDN-hosted libraries:
- **Marked.js**: Markdown parsing and rendering
- **DOMPurify**: XSS protection for user-generated content

No build process or package manager required!

## Features Overview

### Upload Section
- **Browse Button**: Select files from your computer
- **File Information**: Display selected file names and count
- **Options**: Extract archives, verbose output
- **Progress Tracking**: Visual progress bar with status indicators

### Analysis Features
- **Single File Analysis**: Direct analysis for individual files
- **Batch Analysis**: Automatic batching for multiple files or ZIP archives
- **Real-time Progress**: Upload and analysis progress tracking
- **Error Handling**: User-friendly error messages and recovery

### Results Display
- **Markdown Preview**: Rendered markdown with syntax highlighting
- **Download Functionality**: Save results as `.md` files
- **Metadata Display**: Analysis statistics and timing information
- **Clear Results**: Reset interface for new analysis

### Modal Features
- **Supported Languages**: Popup showing all supported file types
- **Categorized Display**: Languages grouped by type (Web, Systems, etc.)
- **Keyboard Navigation**: ESC key to close modals

## Security Features

- **XSS Protection**: All user content sanitized with DOMPurify
- **CORS Handling**: Proper cross-origin request handling
- **File Validation**: Client-side file type validation
- **Content Security**: Safe markdown rendering

## Performance Optimizations

- **Lazy Loading**: Progressive enhancement for better initial load
- **Efficient DOM Updates**: Minimal reflows and repaints
- **Memory Management**: Proper cleanup of file objects and URLs
- **Responsive Images**: Optimized for different screen sizes

## Customization

### Themes
The application uses CSS custom properties for easy theming:

```css
:root {
    --primary-blue: #0071c5;
    --light-blue: #87ceeb;
    --dark-blue: #004c87;
    /* ... other variables */
}
```

### API Integration
The modular JavaScript design allows easy extension:

```javascript
class CodeSummarizerApp {
    // Add new methods or override existing ones
    customAnalysisMethod() {
        // Your custom logic
    }
}
```

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Check if the API server is running
   - Verify the `baseUrl` in configuration
   - Check browser console for CORS errors

2. **File Upload Issues**
   - Ensure files are under size limits
   - Check supported file types
   - Verify network connectivity

3. **Blank Results**
   - Check API response in browser dev tools
   - Verify API returns markdown_output
   - Check console for JavaScript errors

### Development Tips

1. **Enable Debug Mode**: Open browser dev tools for detailed logging
2. **Network Tab**: Monitor API requests and responses
3. **Console Logs**: Check for JavaScript errors and warnings

## Contributing

When making changes:

1. **Test Across Browsers**: Ensure compatibility
2. **Responsive Design**: Test on different screen sizes
3. **API Integration**: Verify all endpoints work correctly
4. **Accessibility**: Maintain keyboard navigation and screen reader support

## License

This frontend is part of the Code Summarizer project. See the main project license for details.