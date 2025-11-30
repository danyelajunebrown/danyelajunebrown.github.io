# System Patterns

## Architecture Overview

**Architecture Type**: Single-Page Application (SPA) - Client-Side Only

The application follows a simple, monolithic architecture with all functionality contained in a single HTML file. No build process, no bundlers, no external dependencies.

```
┌─────────────────────────────────────────┐
│         Browser Environment             │
│  ┌───────────────────────────────────┐  │
│  │         index.html                │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │  HTML Structure & Styles   │  │  │
│  │  └─────────────────────────────┘  │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │  JavaScript Application     │  │  │
│  │  │                             │  │  │
│  │  │  • State Management         │  │  │
│  │  │  • Canvas Controller        │  │  │
│  │  │  • Measurement Engine       │  │  │
│  │  │  • Pattern Generator        │  │  │
│  │  │  • Profile Manager          │  │  │
│  │  └─────────────────────────────┘  │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │     Browser APIs Used             │  │
│  │  • Canvas 2D Context              │  │
│  │  • FileReader (image upload)      │  │
│  │  • localStorage (profiles)        │  │
│  │  • Blob/URL (downloads)           │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## Design Patterns

### 1. State Management Pattern
**Pattern**: Global State Object

The application uses a single `state` object to manage all application state:

```javascript
const state = {
  canvas: null,        // Canvas DOM element
  ctx: null,          // 2D drawing context
  image: null,        // Uploaded image object
  points: [],         // Measurement points [{x, y}]
  unit: 'in',         // Current unit system
  scale: null,        // Pixels per unit conversion
  garmentWidths: {}   // Preset width values
};
```

**When to use**: All functions read from and write to this central state object. No React/Vue state management needed for this simple app.

**Why this pattern**: 
- Simple to understand and debug
- No framework overhead
- Sufficient for single-page tool
- State is visible in browser console for debugging

### 2. Event-Driven Pattern
**Pattern**: DOM Event Handlers

Direct event binding through HTML attributes and addEventListener:

```javascript
// Inline handlers
<button onclick="generatePattern()">Generate</button>

// Programmatic listeners
state.canvas.addEventListener('click', (e) => { ... });
```

**When to use**: All user interactions trigger specific handler functions.

**Why this pattern**:
- No need for event bus or complex event system
- Direct, transparent connection between UI and logic
- Easy to trace user action to code execution

### 3. Calculation Engine Pattern
**Pattern**: Pure Functions with Clear Dependencies

Measurement and pattern calculations are isolated in specific functions:

```javascript
// Pure calculation function
function calculateExtension() {
  // 1. Read input values
  // 2. Validate inputs
  // 3. Calculate results
  // 4. Update display
}
```

**When to use**: Anytime measurements need recalculation.

**Why this pattern**:
- Calculations are deterministic and testable
- Clear input → process → output flow
- Easy to debug with known inputs

### 4. Canvas Rendering Pattern
**Pattern**: Clear-and-Redraw

Canvas is completely cleared and redrawn on every update:

```javascript
function drawCanvas() {
  state.ctx.clearRect(0, 0, width, height);  // Clear all
  if (state.image) { /* draw image */ }       // Layer 1
  state.points.forEach(...);                  // Layer 2: points
  if (state.points.length === 2) { ... }      // Layer 3: line
}
```

**When to use**: After any state change affecting visual display.

**Why this pattern**:
- Simple to reason about (no incremental updates)
- No need to track what changed
- Performance sufficient for low-frequency updates

### 5. SVG Generation Pattern
**Pattern**: Template String Builder

SVG patterns are generated using JavaScript template literals:

```javascript
const svg = `
  <svg xmlns="..." width="${width}" height="${height}">
    ${generateGrid(width, height)}
    <rect x="${x}" y="${y}" ... />
    <!-- More elements -->
  </svg>
`;
```

**When to use**: When generating pattern output.

**Why this pattern**:
- Readable and maintainable
- Easy to add/modify elements
- No DOM manipulation overhead
- Direct string-to-file for downloads

### 6. Profile Persistence Pattern
**Pattern**: localStorage with JSON Serialization

User profiles stored in browser localStorage:

```javascript
// Save
const profile = { name, garmentType, measurements, ... };
let profiles = JSON.parse(localStorage.getItem('garmentProfiles') || '[]');
profiles.push(profile);
localStorage.setItem('garmentProfiles', JSON.stringify(profiles));

// Load
const profiles = JSON.parse(localStorage.getItem('garmentProfiles') || '[]');
```

**When to use**: Profile save, load, delete operations.

**Why this pattern**:
- No server required
- Persists across browser sessions
- Simple API
- Appropriate for small data volumes

## Code Organization

### File Structure
```
index.html
├── <style>          # All CSS in head
├── <body>           # HTML structure
└── <script>         # All JavaScript inline
    ├── State initialization
    ├── Utility functions
    ├── Canvas functions
    ├── Measurement functions
    ├── Pattern generation
    ├── Profile management
    └── Event handlers
```

### Function Naming Conventions
- **Action functions**: `verbNoun()` - e.g., `generatePattern()`, `loadImage()`, `saveProfile()`
- **Calculation functions**: `calculateX()` - e.g., `calculateExtension()`
- **Update functions**: `updateX()` - e.g., `updateStatus()`, `updateGarmentType()`
- **Conversion functions**: `xToY()` - e.g., `inToCm()`, `cmToIn()`
- **Draw functions**: `drawX()` - e.g., `drawCanvas()`

### Separation of Concerns

**Visual Layer** (HTML/CSS):
- Semantic HTML structure
- CSS for all styling (no inline styles)
- Responsive grid layout
- Color-coded status messages

**Logic Layer** (JavaScript):
- State management
- Business logic (calculations)
- Canvas rendering
- SVG generation
- Data persistence

**No Data Layer**: No server, no database, no API calls

## Data Flow

### Measurement Flow
```
User Action: Click Canvas
    ↓
Capture Coordinates (scaled to canvas resolution)
    ↓
Store in state.points[]
    ↓
Redraw Canvas (visualize points)
    ↓
If 2 points → Calculate pixel distance
    ↓
User enters real-world measurement
    ↓
Calculate scale (pixels per unit)
    ↓
Calculate extension needed
    ↓
Display calculations
```

### Pattern Generation Flow
```
User Action: Generate Pattern
    ↓
Validate inputs (lengths, seam allowance)
    ↓
Get garment width (preset or custom)
    ↓
Calculate pattern dimensions
    ↓
Build SVG string with:
    • Rectangle shapes
    • Dimension lines
    • Labels and text
    • Grid overlay
    • Instructions
    ↓
Insert into DOM
    ↓
Enable download buttons
```

### Unit Conversion Flow
```
User Action: Toggle Units
    ↓
Read all numeric inputs
    ↓
Apply conversion function (in↔cm)
    ↓
Update all input values
    ↓
Update all unit labels
    ↓
Update state.unit
    ↓
Recalculate patterns
```

## Integration Patterns

### Image Upload Integration
```javascript
FileReader API
    ↓
Read as DataURL
    ↓
Create Image object
    ↓
Load handler fires
    ↓
Scale to canvas size
    ↓
Store in state.image
    ↓
Redraw canvas with image
```

### Download Integration
```javascript
// SVG Download
SVG Element → outerHTML
    ↓
Create Blob
    ↓
Create Object URL
    ↓
Create <a> element
    ↓
Trigger click
    ↓
Revoke URL

// PDF "Download" (Print)
Open new window
    ↓
Write SVG + print styles
    ↓
Trigger print dialog
    ↓
User saves as PDF
```

## Security Considerations

### Client-Side Security
1. **No Server Communication**: No XSS or CSRF vulnerabilities
2. **localStorage Only**: Data stays in user's browser
3. **File Upload**: Only reads image files, no execution
4. **No User Input Rendering**: All user input is numeric or goes into value attributes
5. **SVG Generation**: Template literals with numeric values only (no user strings in SVG)

### Data Privacy
- All data processing happens client-side
- No analytics or tracking
- No external resources loaded (no CDN dependencies)
- Profile data never leaves user's browser

### Input Validation
- Numeric inputs use HTML5 input types (`type="number"`)
- Min/max/step attributes enforce valid ranges
- JavaScript validation before calculations
- Graceful error handling with user feedback

## Performance Considerations

### Optimization Strategies
1. **Canvas Size**: Fixed resolution balances quality and performance
2. **Redraw on Demand**: Only redraw canvas when state changes
3. **No Animation**: Static rendering reduces CPU usage
4. **Inline Everything**: No network requests after initial load
5. **Lazy Evaluation**: SVG only generated when user clicks button

### Browser Compatibility
- **Target**: Modern browsers (Chrome, Firefox, Safari, Edge)
- **Required APIs**: Canvas 2D, FileReader, localStorage, Blob
- **Fallback**: None (tool requires these APIs)
- **Testing**: Manual testing across browsers

## Error Handling Pattern

### User-Facing Errors
```javascript
function updateStatus(message, type = 'info') {
  const statusEl = document.getElementById('status');
  statusEl.textContent = message;
  statusEl.className = `status ${type}`; // info, success, warning
}
```

**Error Types**:
- **Warning** (yellow): Missing input, invalid state
- **Success** (green): Operation completed
- **Info** (blue): Instructions, neutral updates

### Validation Pattern
```javascript
// Early return with feedback
if (!valid) {
  updateStatus('Error message', 'warning');
  return;
}
// Continue with operation
```

## Testing Approach

### Current Testing
- **Manual Testing**: Browser-based testing with real user workflows
- **Visual Verification**: Generated patterns checked visually
- **Cross-Browser**: Tested on major browsers
- **Calculation Verification**: Known measurements tested for accuracy

### Future Testing Considerations
- Unit tests for calculation functions
- Canvas rendering tests
- SVG generation tests
- localStorage mocking for profile tests
- E2E tests for complete user workflows

## Extensibility Points

### Areas for Future Enhancement
1. **Measurement System**: Could add multi-point measurement for complex garments
2. **Pattern Types**: Architecture supports adding new pattern generators
3. **Export Formats**: Easy to add new export functions (DXF, JSON, etc.)
4. **Garment Library**: Can expand preset garment types
5. **Calculation Engine**: Can add more complex pattern math (curves, darts)

### Plugin Architecture (Future)
Currently monolithic, but could be refactored to:
- Pattern generator plugins
- Export format plugins
- Measurement tool plugins
- Garment type plugins
