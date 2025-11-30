# Technical Context

## Technology Stack

### Languages
- **HTML5**: Semantic markup, form controls, canvas element
- **CSS3**: Grid layout, flexbox, gradients, transitions, media queries
- **JavaScript (ES6+)**: Modern syntax including template literals, arrow functions, const/let, destructuring

### Frameworks
- **None**: Vanilla JavaScript implementation
- **Rationale**: 
  - Simple tool doesn't warrant framework overhead
  - Faster load time without framework bundle
  - Easier to understand and modify
  - No build process required

### Libraries
- **None**: Zero external dependencies
- **Why no libraries**:
  - Canvas API is native
  - FileReader is native
  - localStorage is native
  - SVG generation uses template strings
  - No need for jQuery, React, Vue, etc.

### Browser APIs Used
1. **Canvas API 2D Context**
   - Drawing images, shapes, lines
   - Coordinate capture
   - Visual measurement interface
   
2. **FileReader API**
   - Reading uploaded image files
   - Converting to Data URLs
   - Image preview functionality

3. **localStorage API**
   - Profile persistence
   - JSON serialization
   - Client-side data storage

4. **Blob & URL APIs**
   - Creating downloadable files
   - SVG file generation
   - Object URL creation/revocation

5. **Image API**
   - Loading uploaded images
   - Scaling to canvas dimensions
   - Aspect ratio calculations

## Development Tools

### IDE/Editor
- **Primary**: Visual Studio Code (inferred from environment)
- **Features Used**:
  - HTML/CSS/JS syntax highlighting
  - Live Server extension for local testing
  - Browser DevTools integration

### Version Control
- **System**: Git
- **Repository**: GitHub (danyelajunebrown.github.io)
- **Branch**: Main (commit: 7e73d7f747b551fd188087ad3feb72107dfdd410)
- **Structure**: Part of a larger portfolio/toolbelt project

### Package Manager
- **None Required**: No npm, yarn, or other package managers
- **Reason**: Zero dependencies = no package management needed

### Browser DevTools
- **Chrome/Firefox DevTools**:
  - Console for debugging state object
  - Canvas inspection
  - localStorage viewer
  - Network tab (confirms zero external requests)
  - Responsive design mode for mobile testing

## Build Process

### Build System
- **None**: No build step required
- **Deployment**: Direct file serving

### Development Workflow
```
1. Edit index.html
2. Save file
3. Refresh browser
4. Test functionality
5. Commit to git
```

### No Compilation/Transpilation
- Modern browser targets support ES6+
- No TypeScript, Babel, or transpilation
- No CSS preprocessing (Sass/Less)
- No minification or bundling

### Deployment Process
```
Local Development
    ↓
Git commit
    ↓
Git push to GitHub
    ↓
GitHub Pages (if enabled)
    OR
Direct file hosting
```

## Environment Setup

### Prerequisites
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Text editor or IDE
- Local web server (optional but recommended)

### Local Development Setup

**Option 1: Live Server (VSCode)**
```bash
1. Open folder in VSCode
2. Install Live Server extension
3. Right-click index.html
4. Select "Open with Live Server"
5. Browser opens at http://localhost:5500
```

**Option 2: Python HTTP Server**
```bash
# Python 3
cd make-it-cunt
python3 -m http.server 8000
# Open browser to http://localhost:8000
```

**Option 3: Node HTTP Server**
```bash
# Using npx (no install needed)
npx http-server
# Or install globally
npm install -g http-server
http-server
```

**Option 4: Direct File Access**
```
Simply open index.html in browser
file:///path/to/index.html
```

### No Environment Variables
- No .env files needed
- No API keys
- No configuration files
- Everything is self-contained

### No Database Setup
- Uses browser localStorage only
- No MongoDB, PostgreSQL, MySQL, etc.
- No database migrations

## Testing

### Testing Framework
- **None**: No Jest, Mocha, or Jasmine
- **Current Approach**: Manual browser testing

### Testing Strategy

**Manual Testing Checklist**:
1. Image upload functionality
2. Canvas click measurement (2 points)
3. Unit conversion toggle
4. Garment type selection
5. Custom width input
6. Extension calculation accuracy
7. SVG pattern generation
8. SVG download
9. PDF print dialog
10. Profile save/load/delete
11. Responsive layout (mobile)

**Cross-Browser Testing**:
- Chrome (primary)
- Firefox
- Safari (macOS/iOS)
- Edge

**Calculation Testing**:
```javascript
// Example test cases
// If canvas distance = 300px
// And real measurement = 30 inches
// Then scale = 10 px/inch
// If desired = 32 inches
// Then extension = 2 inches
```

### Future Testing Setup

**Potential Tools**:
- Jest for unit tests (calculation functions)
- Puppeteer for E2E tests
- Canvas testing libraries
- localStorage mocking

**Test Structure (Future)**:
```
tests/
├── unit/
│   ├── calculations.test.js
│   ├── conversions.test.js
│   └── svg-generation.test.js
├── integration/
│   ├── measurement-flow.test.js
│   └── profile-management.test.js
└── e2e/
    └── complete-workflow.test.js
```

## Performance Considerations

### Load Time
- **Target**: < 2 seconds
- **Actual**: Sub-second (single HTML file)
- **No external resources**: No CDN delays
- **No network requests**: After initial load

### Runtime Performance
- **Canvas rendering**: < 16ms per frame (not animated)
- **Calculation speed**: Instant (< 1ms)
- **SVG generation**: < 100ms for typical patterns
- **localStorage access**: < 10ms

### Memory Usage
- **State object**: Minimal (< 1KB)
- **Uploaded images**: Limited by browser (typically < 10MB)
- **Canvas memory**: 800x600 = 480,000 pixels
- **Profile storage**: Limited by localStorage (5-10MB)

### Optimization Opportunities
1. Lazy load large features (currently N/A)
2. Image compression before canvas rendering
3. Debounce calculation on rapid input changes
4. Virtual scrolling for large profile lists
5. Web Worker for heavy calculations (not needed currently)

## Browser Compatibility

### Minimum Browser Versions
- **Chrome**: 49+ (March 2016)
- **Firefox**: 44+ (January 2016)
- **Safari**: 10+ (September 2016)
- **Edge**: 14+ (August 2016)

### Required Features
- ✅ Canvas API 2D Context
- ✅ FileReader API
- ✅ localStorage API
- ✅ ES6 (const, let, arrow functions, template literals)
- ✅ CSS Grid
- ✅ CSS Flexbox

### Polyfills
- **None needed** for target browsers
- All features natively supported

### Progressive Enhancement
- Core functionality requires JavaScript
- No JavaScript fallback provided (tool is inherently interactive)
- Canvas is essential (no fallback)

## Deployment

### Hosting Options

**Option 1: GitHub Pages**
```bash
# Enable GitHub Pages in repo settings
# Point to main branch / root or /docs folder
# URL: https://danyelajunebrown.github.io/toolbelt/make-it-cunt
```

**Option 2: Static Hosting**
- Netlify (drag-and-drop)
- Vercel
- AWS S3 + CloudFront
- Firebase Hosting

**Option 3: Traditional Web Hosting**
- Any shared hosting
- FTP upload
- cPanel file manager

### Deployment Requirements
- Static file hosting
- HTTPS (recommended)
- No server-side processing needed
- No database required

### CI/CD
- **Current**: Manual deployment
- **Future**: GitHub Actions for automated deployment

```yaml
# Potential GitHub Actions workflow
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./toolbelt/make-it-cunt
```

## File Size & Performance Metrics

### Current File Sizes
- **index.html**: ~30KB (HTML + CSS + JavaScript)
- **claude.md**: ~4KB (documentation)
- **Total**: ~34KB uncompressed

### Network Performance
- **Total Download**: ~34KB (gzip: ~10KB)
- **Requests**: 1 (just the HTML file)
- **Time to Interactive**: < 500ms (on good connection)

### Lighthouse Scores (Target)
- **Performance**: 95+
- **Accessibility**: 90+
- **Best Practices**: 90+
- **SEO**: 80+

## Security Considerations

### HTTPS
- **Required**: No, but recommended
- **Benefit**: Secure localStorage access
- **Implementation**: Enable on hosting platform

### Content Security Policy
- **Current**: None
- **Recommended**: 
  ```
  Content-Security-Policy: default-src 'self' 'unsafe-inline'
  ```
- **Reason**: All code is inline, no external resources

### localStorage Security
- **Risk**: Low (no sensitive data)
- **Mitigation**: Data stays in user's browser
- **Consideration**: User can clear at any time

### Input Sanitization
- **Numeric inputs**: Validated by HTML5 input types
- **Text inputs**: Only used for profile names (not rendered as HTML)
- **SVG generation**: No user strings injected

## Development Dependencies (None)

### Why No Dependencies
1. **Simplicity**: Easy to understand and modify
2. **Performance**: Zero network overhead
3. **Maintainability**: No dependency updates needed
4. **Security**: No supply chain vulnerabilities
5. **Compatibility**: No breaking changes from dependencies

### Trade-offs
- **Pro**: Simple, fast, secure
- **Con**: No advanced framework features
- **Con**: Manual DOM manipulation
- **Pro**: Perfect for this use case

## Future Technical Considerations

### Potential Additions
1. **TypeScript**: Type safety for calculations
2. **Testing Framework**: Automated test coverage
3. **Build Process**: Minification, tree-shaking
4. **PWA Features**: Service worker, offline capability
5. **WebAssembly**: High-performance pattern calculations

### Scalability
- Current architecture suitable for current scope
- If features grow significantly, consider:
  - Framework adoption (React/Vue)
  - Module bundler (Webpack/Vite)
  - State management library
  - Component architecture

### Technical Debt
- **Minimal**: Simple architecture = low debt
- **Monitoring**: Track file size growth
- **Refactoring**: Consider if crossing 50KB or adding 10+ features
