# Testing Guide - Phase 1: Body Profile System

## What's Been Built

### Phase 0: Cleanup ✅
- Deleted duplicate `ButMakeItCunt.html` file
- Single source: `make-it-cunt/index.html`

### Phase 1: Body Measurement System ✅
- Purple gradient UI theme
- Comprehensive measurement input form
- Profile save/load/delete functionality
- localStorage persistence
- Tab navigation framework
- Status messaging system

## Testing Checklist

### 1. Visual Design
- [ ] Purple gradient background displays correctly
- [ ] White cards are readable and have proper shadows
- [ ] Tab buttons work and show active state (purple when selected)
- [ ] Buttons have hover effects (lift slightly)
- [ ] Mobile responsive (test by resizing browser window)

### 2. Form Input
- [ ] All 11 measurement fields accept numbers
- [ ] Profile name field accepts text
- [ ] Help tooltips (?) show on hover
- [ ] Can enter decimal values (e.g., 32.5)
- [ ] Validation prevents negative numbers
- [ ] Step increments work (0.25 inch steps)

### 3. Save Functionality
- [ ] Fill out all required fields (marked with *)
- [ ] Click "Save Body Profile"
- [ ] Green success message appears
- [ ] Profile appears in "Saved Body Profiles" section below
- [ ] Profile shows correct name and today's date
- [ ] Form clears after saving

### 4. Load Functionality
- [ ] Click "Load" button on a saved profile
- [ ] All form fields populate with saved measurements
- [ ] Blue info message shows which profile was loaded
- [ ] Page scrolls to top of form
- [ ] Optional fields (shoulders, torso) populate if they were saved

### 5. Delete Functionality
- [ ] Click "Delete" button on a saved profile
- [ ] Confirmation dialog appears asking "Are you sure?"
- [ ] Click "Cancel" - profile remains
- [ ] Click "Delete" again, then "OK" - profile is removed
- [ ] Blue info message confirms deletion

### 6. Persistence Testing
- [ ] Save a profile
- [ ] Refresh page (⌘+R or Ctrl+R)
- [ ] Profile still appears in saved list
- [ ] Close browser tab completely
- [ ] Reopen index.html
- [ ] Profile is still saved

### 7. Multiple Profiles
- [ ] Save 2-3 different profiles with different names
- [ ] All profiles appear in list
- [ ] Can load different profiles
- [ ] Can delete individual profiles
- [ ] Remaining profiles stay intact after deleting one

### 8. Tab Navigation
- [ ] Click "Garments" tab - shows "coming soon" message
- [ ] Click "Fit Analysis" tab - shows placeholder
- [ ] Click "Patterns" tab - shows placeholder
- [ ] Click "Feedback" tab - shows placeholder
- [ ] Click "Body Profile" tab - returns to measurement form

### 9. Clear Form Button
- [ ] Fill out some fields
- [ ] Click "Clear Form" button
- [ ] All fields reset to empty
- [ ] Blue info message confirms form cleared

### 10. Edge Cases
- [ ] Try to save with empty profile name - should show validation error
- [ ] Try to save with missing required measurements - should show validation error
- [ ] Try extremely large values (e.g., 999 inches) - should accept but may look odd
- [ ] Try very small values (e.g., 0.25 inches) - should accept
- [ ] Leave optional fields (shoulders, torso) empty - should save without them

## Known Limitations (Expected)
- Other tabs (Garments, Analysis, Patterns, Feedback) are placeholders
- No garment management yet
- No pattern generation yet
- No fit analysis yet
- No measurement diagrams/images yet

## Next Phase Preview
Phase 2 will add:
- Garment measurement input form
- Garment library management
- Fit issue checkboxes
- Fabric stretch % input
- Garment-specific profiles

## Report Issues
When testing, note:
1. What you were doing
2. What happened (actual)
3. What you expected (expected)
4. Browser and OS (if relevant)

Example: "Clicked Save button, but form didn't clear. Expected: form to reset after saving."

---

# Testing Guide - v3.0: Revopoint Inspire Scanner Integration

## What's Been Built (v3.0)

### Backend Modules ✅
- `mesh_processing.py` - PLY/OBJ/STL import, cleaning, alignment
- `body_model.py` - Anatomical landmarks, cross-sections, movement envelope
- `garment_model.py` - Seam detection, garment type classification
- `fit_analysis.py` - Body-garment delta, compression/gap detection
- `pattern_generator.py` - Shaped patterns (tapered, gussets), SVG export
- `app.py` - v3 API endpoints

### Scanner Acquired ✅
- **Model**: Revopoint Inspire
- **Accuracy**: 0.2mm
- **Point Spacing**: ~0.3mm
- **Software**: Revo Scan 5
- **Formats**: PLY, OBJ, STL (PLY recommended)

## Pre-Testing Setup

### 1. Install Dependencies
```bash
cd server
source venv/bin/activate
pip install -r requirements.txt
```

**Expected packages:**
- trimesh>=4.0.0
- pymeshlab>=2023.12
- open3d>=0.17.0
- numpy-stl>=3.0.0
- svgwrite>=1.4.0
- Flask, opencv, numpy, scipy

**Troubleshooting:**
- If `pymeshlab` fails on Python 3.12+, use Python 3.8-3.11
- If `open3d` fails on macOS, try: `pip install open3d --no-cache-dir`

### 2. Start Backend Server
```bash
cd server
source venv/bin/activate
python app.py
```

**Expected output:**
```
Feature Status:
  Mesh Processing:    OK
  Body Model:         OK
  Garment Model:      OK
  Fit Analysis:       OK
  Pattern Generation: OK

* Running on http://127.0.0.1:5050
```

**If features show "NOT AVAILABLE":**
- Check missing dependencies
- Server will still start, but affected features won't work

### 3. Verify Health Endpoint
```bash
curl http://localhost:5050/api/health
```

**Expected JSON:**
```json
{
  "status": "healthy",
  "version": "3.0.0",
  "features": {
    "calibration": true,
    "garment_detection_2d": true,
    "mesh_processing": true,
    "body_model": true,
    "garment_model": true,
    "fit_analysis": true,
    "pattern_generation": true
  }
}
```

---

## Scanner Testing Workflow

### Phase 1: First Body Scan

**Scan Checklist:**
- [ ] Revo Scan 5 installed and Inspire connected
- [ ] Subject wearing form-fitting clothes
- [ ] Good lighting (diffuse, not harsh)
- [ ] Clear background
- [ ] Subject in T-pose or arms slightly away from body

**Scanning Process:**
1. Launch Revo Scan 5
2. Select "Body Scan" mode
3. Complete 360° scan (3-5 minutes)
4. Review coverage - fill any gaps
5. Export as **PLY** in **mm** units
6. Save to `~/Desktop/make-it-cunt-scans/body-scans/2025-12-22-body-01.ply`

**Quality Checks:**
- [ ] Full coverage (no large gaps)
- [ ] Arms separated from torso
- [ ] Minimal noise/artifacts
- [ ] File size: 10-50MB typical for body scan
- [ ] Can open in Revo Scan 5 preview

### Phase 2: Test Body Mesh Upload

**Using curl:**
```bash
curl -X POST http://localhost:5050/api/mesh/upload/body \
  -F "mesh=@/path/to/your/body-scan.ply" \
  -F "movement_profile=wild"
```

**Expected response:**
```json
{
  "success": true,
  "mesh_type": "body",
  "stats": {
    "vertex_count": 50000-200000,
    "face_count": 100000-400000,
    "dimensions": [400-600, 1600-2000, 200-400],
    "unit": "mm",
    "is_watertight": true/false
  },
  "landmarks": {
    "waist": [x, y, z],
    "hip": [x, y, z],
    "shoulder_left": [x, y, z],
    ...
  },
  "measurements": {
    "waist_circumference": 700-900,
    "hip_circumference": 900-1100,
    "inseam": 700-850,
    ...
  }
}
```

**What to Check:**
- [ ] `success: true`
- [ ] Vertex count reasonable (50k-200k typical)
- [ ] Dimensions in mm make sense (height ~1700mm = 170cm)
- [ ] Landmarks detected (waist, hip, shoulder)
- [ ] Measurements look realistic (waist ~800mm, hip ~1000mm)

**If it fails:**
- Check file format (must be PLY/OBJ/STL)
- Check units (should be mm)
- Check file isn't corrupted (re-export from Revo Scan 5)
- Check backend logs for error details

### Phase 3: First Garment Scan

**Garment Setup:**
- [ ] Garment on dress form (recommended) or flat
- [ ] Dress form adjusted to your proportions
- [ ] Garment sits naturally (not stretched/bunched)
- [ ] Plain background

**Scanning Process:**
1. Launch Revo Scan 5
2. Select "Object Scan" mode
3. Complete 360° scan of garment (2-4 minutes)
4. Remove dress form geometry (crop/erase in Revo Scan 5)
5. Export as **PLY** in **mm** units
6. Save to `~/Desktop/make-it-cunt-scans/garment-scans/pants/jeans-01.ply`

**Quality Checks:**
- [ ] All seams visible
- [ ] No dress form in export (garment only)
- [ ] Captures natural drape
- [ ] File size: 5-30MB typical for garment
- [ ] Waistband/hem clearly defined

### Phase 4: Test Garment Mesh Upload

**Using curl:**
```bash
curl -X POST http://localhost:5050/api/mesh/upload/garment \
  -F "mesh=@/path/to/your/garment-scan.ply" \
  -F "garment_type=pants"
```

**Expected response:**
```json
{
  "success": true,
  "mesh_type": "garment",
  "garment_type": "pants",
  "stats": {
    "vertex_count": 20000-100000,
    "dimensions": [300-500, 900-1100, 200-400],
    ...
  },
  "seams": [
    {"type": "inseam", "location": [x,y,z], ...},
    {"type": "outseam", "location": [x,y,z], ...}
  ]
}
```

**What to Check:**
- [ ] `success: true`
- [ ] Garment type detected (or specified)
- [ ] Seams detected
- [ ] Dimensions reasonable

### Phase 5: Fit Analysis Test

**Using curl (after uploading both body and garment):**
```bash
curl -X POST http://localhost:5050/api/analysis/fit
```

**Expected response:**
```json
{
  "success": true,
  "fit_analysis": {
    "issues": [
      {
        "type": "compression",
        "severity": "severe",
        "zone": "shoulders",
        "amount_mm": -25.5,
        "description": "Shoulder compression - risk of ripping"
      },
      {
        "type": "too_short",
        "severity": "moderate",
        "zone": "lower_leg",
        "amount_mm": -50,
        "description": "Pants 50mm too short"
      }
    ],
    "recommendations": [
      {
        "type": "gusset",
        "zone": "shoulders",
        "amount_mm": 45.5,
        "instructions": "Add diamond gusset at shoulder seam..."
      },
      {
        "type": "extension",
        "zone": "lower_leg",
        "amount_mm": 50,
        "instructions": "Add tapered extension at hem..."
      }
    ],
    "overall_fit_score": 62.0
  }
}
```

**What to Check:**
- [ ] Issues detected (compression, gaps, too_short, etc.)
- [ ] Severity levels make sense (minor/moderate/severe/critical)
- [ ] Zones identified (shoulders, bust, waist, hips, crotch, etc.)
- [ ] Recommendations generated for each issue
- [ ] Overall fit score (0-100, lower = worse fit)

**Expected Issues for Your Body Type:**
- Compression at shoulders (broad shoulders)
- Gap/tenting at bust (low projection)
- Too short on arms, legs, torso (long limbs)
- Movement conflicts if using "wild" profile

### Phase 6: Pattern Generation Test

**Using curl:**
```bash
curl -X POST http://localhost:5050/api/patterns/generate \
  -H "Content-Type: application/json" \
  -d '{
    "recommendations": [... from fit analysis ...],
    "garment_measurements": {... from garment upload ...}
  }'
```

**Expected response:**
```json
{
  "success": true,
  "patterns": [
    {
      "name": "Shoulder Gusset",
      "type": "gusset",
      "dimensions_mm": {"width": 65, "height": 97},
      "seam_allowance_mm": 15,
      "instructions": "Cut 2 pieces (mirror). Stitch into shoulder seam..."
    },
    {
      "name": "Leg Extension - Left",
      "type": "extension",
      "dimensions_mm": {"top_width": 280, "bottom_width": 260, "height": 50},
      "seam_allowance_mm": 15,
      "instructions": "Tapered extension. Match to leg hem..."
    }
  ],
  "svg_content": {
    "Shoulder Gusset": "<svg>...</svg>",
    "Leg Extension - Left": "<svg>...</svg>"
  }
}
```

**What to Check:**
- [ ] Patterns generated for each recommendation
- [ ] Pattern types: extension (tapered), gusset (diamond/football), dart, insert
- [ ] Dimensions in mm
- [ ] Seam allowance included (typically 15mm)
- [ ] SVG content present (can save to .svg file)
- [ ] Instructions provided

**Save SVG Pattern:**
```bash
# Extract SVG from response and save to file
curl ... | jq -r '.svg_content["Shoulder Gusset"]' > shoulder-gusset.svg
```

Open in browser or Inkscape to view pattern.

### Phase 7: Full Pipeline Test

**Using curl (all-in-one):**
```bash
curl -X POST http://localhost:5050/api/workflow/analyze-and-generate \
  -F "body_mesh=@body-scan.ply" \
  -F "garment_mesh=@garment-scan.ply" \
  -F "movement_profile=wild" \
  -F "garment_type=pants"
```

**Expected:**
- Complete fit analysis + pattern generation in one call
- Same structure as separate calls, but combined

---

## Expected Mesh Characteristics

### Body Scan (Revopoint Inspire)
| Metric | Expected Value |
|--------|----------------|
| Vertex Count | 50,000 - 200,000 |
| Face Count | 100,000 - 400,000 |
| File Size | 10-50 MB (PLY) |
| Dimensions (mm) | Width: 400-600, Height: 1600-2000, Depth: 200-400 |
| Point Spacing | ~0.3mm |
| Accuracy | 0.2mm |

### Garment Scan (Revopoint Inspire)
| Metric | Expected Value |
|--------|----------------|
| Vertex Count | 20,000 - 100,000 |
| Face Count | 40,000 - 200,000 |
| File Size | 5-30 MB (PLY) |
| Dimensions (mm) | Varies by garment type |

---

## Troubleshooting

### Backend Issues

**"Mesh Processing: NOT AVAILABLE"**
- Missing dependencies: `pip install trimesh pymeshlab open3d`
- Python version too new: Use Python 3.8-3.11 for pymeshlab

**"No mesh detected in image" or similar**
- Wrong file format (check extension)
- Corrupted file (re-export from Revo Scan 5)
- File too large (check server logs for memory issues)

**"Landmark detection failed"**
- Body scan incomplete (missing top or bottom)
- Body scan has noise/artifacts (clean in Revo Scan 5)
- Body scan upside down (backend should auto-correct, but may fail)

**"Fit analysis shows wrong dimensions"**
- Units mismatch (ensure both scans exported in mm)
- Scans not aligned (backend should auto-align, check logs)
- One scan much lower quality than other

### Scanner Issues

**Noisy scans**
- Improve lighting
- Scan slower
- Wear lighter colored, form-fitting clothes
- Clean scanner lens

**Gaps in coverage**
- Move slower
- Overlap more
- Do multiple passes

**Wrong scale in backend**
- Always export in **mm** from Revo Scan 5
- Backend auto-detects, but mm is most reliable

---

## Success Criteria

### First Body Scan Success
- [ ] Scan completes in Revo Scan 5
- [ ] Export to PLY succeeds
- [ ] Backend accepts upload
- [ ] Landmarks detected (waist, hip, shoulder)
- [ ] Measurements look realistic

### First Garment Scan Success
- [ ] Scan completes in Revo Scan 5
- [ ] Dress form removed from export
- [ ] Backend accepts upload
- [ ] Seams detected
- [ ] Garment type classified

### First Fit Analysis Success
- [ ] Both meshes uploaded
- [ ] Fit analysis completes
- [ ] Issues identified (compression, gaps, length)
- [ ] Recommendations generated
- [ ] Fit score calculated

### First Pattern Generation Success
- [ ] Patterns generated from recommendations
- [ ] SVG files created
- [ ] Patterns are shaped (not rectangles!)
- [ ] Can open SVG in browser/Inkscape
- [ ] Dimensions look correct

---

## Next Steps After First Successful Test

1. **Refine workflow** based on real scan experience
2. **Document any quirks** (e.g., "shoulders need extra passes")
3. **Create sample dataset** (body + garment pairs for testing)
4. **Build frontend UI** for mesh upload and visualization
5. **Add Three.js viewer** for 3D mesh inspection

---

## Report Issues

When testing v3.0, note:
1. **Scanner**: What happened during scan (tracking issues, gaps, etc.)
2. **Backend**: API endpoint, error message, expected vs actual
3. **File details**: Format, size, export settings from Revo Scan 5
4. **Logs**: Check terminal output from `python app.py`

Example: "Uploaded body PLY, got 'Landmark detection failed'. Body scan was 20MB PLY in mm, but missing bottom 20% of legs (scan stopped tracking). Re-scanning with slower movement."
