# System Patterns

## Architecture
Single-page HTML application with vanilla JavaScript. All client-side rendering.

## Key Components

### Authentication
- Supabase Auth for user management
- Session persistence via Supabase

### Feelings Wheel
- SVG-based rotating wheel
- Touch and mouse drag support
- Hierarchical emotion selection (inner/middle/outer rings)

### Diary Card Generation
- Weekly report with date range selection
- Drag-and-drop entry reorganization
- Entries grouped by day of week

### PDF Generation Flow
1. User clicks "Download PDF" button
2. Success/error alerts are hidden
3. Container is temporarily expanded to show full content
4. html2canvas captures with scrollWidth/scrollHeight
5. Canvas is converted to PNG image
6. jsPDF creates landscape A4 PDF
7. Content is centered both horizontally and vertically
8. PDF is saved

## FIXED: PDF Implementation

### Previous Issues (Now Fixed)
1. "Generating PDF" message appeared on output - alerts not hidden
2. Diary card truncated - only viewport captured, not full scrollable content
3. Content shifted left - incorrect centering calculation
4. Empty space on right/bottom - wrong scaling logic

### Current Implementation (Fixed)
```javascript
// 1. Hide overlays
successAlertEl.style.display = 'none';
errorAlertEl.style.display = 'none';

// 2. Expand container for full capture
reportText.style.overflow = 'visible';
reportText.style.maxHeight = 'none';
reportText.style.height = 'auto';

// 3. Capture with full dimensions
const canvas = await html2canvas(reportText, {
    windowWidth: scrollWidth,
    windowHeight: scrollHeight
});

// 4. Proper centering
const x = (pageWidth - imgWidth) / 2;
const y = (pageHeight - imgHeight) / 2;
```

## Data Flow
- Diary entries stored in Supabase `diary_entries` table
- Fetched by date range for weekly reports
- Client-side grouping by day of week
- Drag-and-drop updates timestamps in database
