# System Patterns

## Architecture Overview

**Architecture Type**: Hybrid Client-Server Application (v3.0)

The application has evolved to a volumetric 3D processing system while maintaining v2.0 2D photo features.

The application follows a hybrid architecture with a vanilla JavaScript frontend and a Python/Flask backend for computer vision processing.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Browser Environment                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    index.html                              │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │              HTML Structure & Styles                │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │            JavaScript Application                   │  │  │
│  │  │                                                     │  │  │
│  │  │  • State Management    • Canvas Controller          │  │  │
│  │  │  • Measurement Engine  • Pattern Generator          │  │  │
│  │  │  • Profile Manager     • Backend API Client         │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                           │ HTTP/Fetch                          │
├───────────────────────────┼─────────────────────────────────────┤
│                           ↓                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Python/Flask Backend (:5050)                 │  │
│  │                                                           │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │  │
│  │  │ calibration │ │  garment_   │ │   body_measurer     │ │  │
│  │  │    .py      │ │ detector.py │ │      .py            │ │  │
│  │  │             │ │             │ │   (Phase 3)         │ │  │
│  │  │ ArUco       │ │ Edge detect │ │  MediaPipe +        │ │  │
│  │  │ detection   │ │ Contours    │ │  Depth Pro          │ │  │
│  │  └─────────────┘ └─────────────┘ └─────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Browser APIs                           │  │
│  │  • Canvas 2D      • FileReader      • localStorage        │  │
│  │  • Fetch          • Blob/URL        • FormData            │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## v3.0 Volumetric Processing Patterns

### Architecture (v3.0)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    v3.0 VOLUMETRIC PIPELINE                          │
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │ Body Scan    │    │ Garment Scan │    │ Analysis Engine      │  │
│  │ (PLY/OBJ)    │───►│ (PLY/OBJ)    │───►│                      │  │
│  └──────────────┘    └──────────────┘    │  mesh_processing.py  │  │
│                                          │  body_model.py       │  │
│                                          │  garment_model.py    │  │
│                                          │  fit_analysis.py     │  │
│                                          │  pattern_generator.py│  │
│                                          └──────────────────────┘  │
│                                                    │                │
│                                                    ▼                │
│                                          ┌──────────────────────┐  │
│                                          │ Shaped Patterns      │  │
│                                          │ (SVG Export)         │  │
│                                          └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 8. Mesh Processing Pipeline Pattern
**Pattern**: Multi-Library Processing Chain

v3.0 uses multiple libraries in sequence for mesh processing:

```python
class MeshProcessor:
    def load_mesh(self, file_path=None, file_bytes=None) -> ProcessedMesh:
        # Step 1: Load with trimesh (universal format support)
        mesh = trimesh.load(file_path)

        # Step 2: Clean with pymeshlab (advanced algorithms)
        if PYMESHLAB_AVAILABLE:
            mesh = self._clean_with_pymeshlab(mesh)

        # Step 3: Orient with PCA (principal component analysis)
        mesh = self._orient_with_pca(mesh)

        return ProcessedMesh(mesh, stats, processing_log)
```

**When to use**: All mesh import/processing operations.

**Why this pattern**:
- Each library has different strengths (trimesh: flexibility, pymeshlab: cleaning, open3d: alignment)
- Graceful degradation when libraries unavailable
- Processing log tracks what operations were applied

### 9. Cross-Section Analysis Pattern
**Pattern**: Height-Based Slicing for Body Understanding

Body landmarks are detected by analyzing horizontal cross-sections:

```python
def _generate_cross_sections(self, num_sections=100):
    """Slice body mesh at regular height intervals."""
    height_range = self.mesh.bounds[1][2] - self.mesh.bounds[0][2]

    for i in range(num_sections):
        height = min_z + (i / num_sections) * height_range

        # Intersect mesh with horizontal plane
        section = self.mesh.section(
            plane_origin=[0, 0, height],
            plane_normal=[0, 0, 1]
        )

        if section:
            self.cross_sections[height] = CrossSection(
                height=height,
                circumference=self._calculate_circumference(section),
                bounds=section.bounds
            )
```

**When to use**: Body landmark detection (waist, hip, bust identification).

**Why this pattern**:
- Waist = minimum circumference
- Hip = maximum circumference below waist
- Bust = maximum circumference above waist
- Works regardless of mesh pose

### 10. Movement Envelope Pattern
**Pattern**: Configurable Ease Expansion

For dynamic fit (dance, movement), body mesh is expanded at stress points:

```python
EASE_PROFILES = {
    'standard': {'shoulder': 30, 'bust': 25, 'waist': 20, 'hip': 25, 'crotch': 40, 'knee': 30},
    'fitted': {'shoulder': 15, 'bust': 15, 'waist': 10, 'hip': 15, 'crotch': 25, 'knee': 20},
    'wild': {'shoulder': 80, 'bust': 50, 'waist': 30, 'hip': 50, 'crotch': 100, 'knee': 80}
}

def generate_movement_envelope(self, ease_profile='wild'):
    """Expand body mesh by ease values at key zones."""
    envelope_vertices = self.mesh.vertices.copy()

    for zone, ease_mm in EASE_PROFILES[ease_profile].items():
        zone_mask = self._get_zone_mask(zone)
        # Expand vertices along surface normals
        envelope_vertices[zone_mask] += self.mesh.vertex_normals[zone_mask] * (ease_mm / 1000)

    return MovementEnvelope(vertices=envelope_vertices, ease_profile=ease_profile)
```

**When to use**: Analyzing fit for active wear, dance costumes, performance garments.

**Why this pattern**:
- User's "wild" movement needs require extreme ease at shoulders (80mm), crotch (100mm)
- Garment must accommodate movement envelope, not just static body
- Profiles are configurable per use case

### 11. Delta Analysis Pattern (THE CORE)
**Pattern**: Surface-to-Surface Distance Mapping

The fundamental v3.0 innovation - comparing body volume to garment volume:

```python
def _compute_distance_map(self) -> np.ndarray:
    """Calculate signed distance from body surface to garment surface."""
    distances = np.zeros(len(self.body.mesh.vertices))

    for i, vertex in enumerate(self.body.mesh.vertices):
        # Find closest point on garment
        closest, distance, face_id = self.garment.mesh.nearest.on_surface([vertex])

        # Determine sign (inside/outside garment)
        garment_normal = self.garment.mesh.face_normals[face_id[0]]
        direction = vertex - closest[0]

        if np.dot(direction, garment_normal) < 0:
            distances[i] = -distance  # Body inside garment (compression)
        else:
            distances[i] = distance   # Body outside garment (gap)

    return distances
```

**When to use**: All fit analysis operations.

**Why this pattern**:
- Negative distance = compression (garment smaller than body = stress/ripping)
- Positive distance = gap (garment larger than body = tenting/excess)
- Zero = perfect fit at that point
- Enables targeted modification recommendations

### 12. Zone Classification Pattern
**Pattern**: Anatomical Region Mapping

Body vertices are classified into zones for targeted analysis:

```python
class BodyZone(Enum):
    SHOULDERS = "shoulders"
    BUST = "bust"
    WAIST = "waist"
    HIPS = "hips"
    CROTCH = "crotch"
    UPPER_ARM = "upper_arm"
    LOWER_ARM = "lower_arm"
    UPPER_LEG = "upper_leg"
    LOWER_LEG = "lower_leg"

def _classify_zone(self, vertex) -> BodyZone:
    """Classify a vertex into anatomical zone based on height and position."""
    height = vertex[2]
    total_height = self.body.mesh.bounds[1][2] - self.body.mesh.bounds[0][2]
    relative_height = (height - self.body.mesh.bounds[0][2]) / total_height

    if relative_height > 0.85:
        return BodyZone.SHOULDERS
    elif relative_height > 0.70:
        return BodyZone.BUST if abs(vertex[1]) > center_threshold else BodyZone.UPPER_ARM
    # ... etc
```

**When to use**: Generating zone-specific recommendations and patterns.

**Why this pattern**:
- Different zones need different modifications (gusset vs extension vs dart)
- Enables "add shoulder gusset" instead of generic "add ease"
- Maps to sewing terminology

### 13. Shaped Pattern Generation Pattern
**Pattern**: Geometry-Aware Pattern Pieces

v3.0 generates properly shaped patterns, not rectangles:

```python
def _generate_extension(self, recommendation, garment) -> GeneratedPattern:
    """Generate tapered extension matching garment silhouette."""
    # Get garment width at extension location
    top_width = self._get_width_at_height(garment, recommendation.location[2])
    # Taper toward hem
    bottom_width = top_width * 0.92  # Slight taper

    # Create trapezoid, not rectangle
    outline = np.array([
        [0, 0],
        [top_width, 0],
        [top_width - (top_width - bottom_width) / 2, recommendation.amount],
        [(top_width - bottom_width) / 2, recommendation.amount]
    ])

    return GeneratedPattern(
        name=f"{recommendation.zone.value.title()} Extension",
        outline=outline,
        seam_allowance=15.0,  # mm
        notches=self._calculate_notches(outline),
        grain_line=GrainLine(start=[top_width/2, 0], end=[top_width/2, recommendation.amount])
    )

def _generate_gusset(self, recommendation, garment) -> GeneratedPattern:
    """Generate diamond or football gusset based on zone."""
    if recommendation.zone == BodyZone.CROTCH:
        # Football shape for crotch
        return self._generate_football_gusset(recommendation)
    else:
        # Diamond shape for other zones
        return self._generate_diamond_gusset(recommendation)
```

**When to use**: All pattern generation from fit recommendations.

**Why this pattern**:
- Tapered extensions follow garment silhouette
- Diamond gussets for shoulder/armhole stress
- Football gussets for crotch (curved seams)
- Not rectangles!

### 14. Feature Detection Pattern (Backend Startup)
**Pattern**: Capability Discovery at Import

Server determines available features at startup:

```python
# At module level
MESH_PROCESSING_AVAILABLE = False
BODY_MODEL_AVAILABLE = False
# ...

try:
    from mesh_processing import MeshProcessor
    MESH_PROCESSING_AVAILABLE = True
except ImportError:
    pass

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'version': '3.0.0',
        'features': {
            'mesh_processing': MESH_PROCESSING_AVAILABLE,
            'body_model': BODY_MODEL_AVAILABLE,
            'garment_model': GARMENT_MODEL_AVAILABLE,
            'fit_analysis': FIT_ANALYSIS_AVAILABLE,
            'pattern_generation': PATTERN_GENERATION_AVAILABLE,
            # v2 features
            'calibration': ARUCO_AVAILABLE,
            'garment_detection_2d': True
        }
    })
```

**When to use**: Server startup, health checks, frontend feature gating.

**Why this pattern**:
- Server starts even with missing dependencies
- Clear feature status for debugging
- Frontend can gate UI based on available features

---

## v2.0 Design Patterns (Maintained)

### 1. State Management Pattern
**Pattern**: Global State Object

The application uses a single `state` object to manage all frontend application state:

```javascript
const state = {
  canvas: null,        // Canvas DOM element
  ctx: null,           // 2D drawing context
  image: null,         // Uploaded image object
  points: [],          // Measurement points [{x, y}]
  unit: 'in',          // Current unit system
  scale: null,         // Pixels per unit conversion
  garmentWidths: {}    // Preset width values
};

// v2.0 additions
const photoState = {
  canvas: null,
  ctx: null,
  image: null,
  displayScale: 1,
  scale: null,         // Calibrated scale
  measurements: []
};

let backendAvailable = false;
let autoDetectedMeasurements = null;
let autoDetectedKeypoints = null;
```

**When to use**: All functions read from and write to these central state objects.

**Why this pattern**:
- Simple to understand and debug
- No framework overhead
- State is visible in browser console for debugging
- Easy to extend for new features

### 2. Backend Communication Pattern
**Pattern**: Async/Await Fetch with FormData

Backend calls use the Fetch API with FormData for file uploads:

```javascript
async function autoDetectGarment() {
  // Create FormData with image
  const blob = await new Promise(resolve =>
    tempCanvas.toBlob(resolve, 'image/jpeg', 0.9)
  );

  const formData = new FormData();
  formData.append('image', blob, 'garment.jpg');
  formData.append('garment_type', 'pants');

  // Send to backend
  const response = await fetch(`${BACKEND_URL}/api/measure/garment`, {
    method: 'POST',
    body: formData
  });

  const result = await response.json();

  if (result.success) {
    // Process results
  }
}
```

**When to use**: All backend API calls (calibration, detection, measurement).

**Why this pattern**:
- Modern async/await syntax
- FormData handles file uploads naturally
- Clean error handling with try/catch

### 3. Graceful Degradation Pattern
**Pattern**: Feature Detection with Fallback

The application checks backend availability and adjusts features:

```javascript
const BACKEND_URL = 'http://localhost:5050';
let backendAvailable = false;

async function checkBackendHealth() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/health`);
    const data = await response.json();
    backendAvailable = data.status === 'healthy';
    updateBackendStatus(backendAvailable);
  } catch (err) {
    backendAvailable = false;
    updateBackendStatus(false);
  }
}

// UI adjusts based on backend availability
if (backendAvailable) {
  showAutoDetectButton();
} else {
  showManualModeOnly();
}
```

**When to use**: On page load and when attempting backend operations.

**Why this pattern**:
- Users can still use manual mode without backend
- Clear status indication
- No errors when backend is unavailable

### 4. Computer Vision Pipeline Pattern (Backend)
**Pattern**: Sequential Processing Pipeline

Backend detection follows a clear pipeline:

```python
# garment_detector.py
def detect_pants_keypoints(image, scale_ppcm=None):
    # Step 1: Preprocessing
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Step 2: Edge Detection
    edges = cv2.Canny(blurred, 50, 150)

    # Step 3: Contour Finding
    contours, _ = cv2.findContours(edges, ...)
    garment_contour = find_largest_contour(contours)

    # Step 4: Keypoint Extraction
    keypoints = extract_keypoints_from_contour(garment_contour)

    # Step 5: Measurement Calculation
    measurements = calculate_measurements(keypoints, scale_ppcm)

    return DetectionResult(keypoints, measurements, contour)
```

**When to use**: All image processing operations.

**Why this pattern**:
- Each step is testable independently
- Easy to debug by inspecting intermediate results
- Clear data flow through pipeline

### 5. Canvas Rendering Pattern
**Pattern**: Clear-and-Redraw with Layers

Canvas is completely cleared and redrawn with layers on every update:

```javascript
function drawAutoDetectedKeypoints(keypoints) {
  redrawCanvas();  // Layer 0: Image

  const ctx = photoState.ctx;

  // Layer 1: Keypoints
  keypoints.forEach(kp => {
    ctx.beginPath();
    ctx.arc(kp.x * scale, kp.y * scale, 10, 0, Math.PI * 2);
    ctx.fillStyle = getColorForKeypoint(kp.name);
    ctx.fill();
  });

  // Layer 2: Measurement Lines
  if (kpMap['crotch_point'] && kpMap['left_hem']) {
    drawMeasurementLine(ctx, kpMap['crotch_point'], kpMap['left_hem'], '#9b59b6', 'Inseam');
  }

  // Layer 3: Labels
  keypoints.forEach(kp => {
    drawLabel(ctx, kp.name, kp.x, kp.y);
  });
}
```

**When to use**: After any state change affecting visual display.

**Why this pattern**:
- Simple to reason about (no incremental updates)
- Predictable layer ordering
- Easy to add new visualization layers

### 6. API Response Pattern (Backend)
**Pattern**: Consistent JSON Response Structure

All backend endpoints return consistent response structures:

```python
# Success response
return jsonify({
    'success': True,
    'garment_type': 'pants',
    'measurements': {
        'waist_flat': 40.5,
        'inseam': 78.2,
        'rise': 28.3
    },
    'keypoints': [
        {'name': 'waist_left', 'x': 150, 'y': 50, 'confidence': 0.9},
        ...
    ]
})

# Error response
return jsonify({
    'success': False,
    'error': 'No garment detected in image.'
}), 400
```

**When to use**: All API endpoints.

**Why this pattern**:
- Frontend can check `success` field consistently
- Error messages are user-friendly
- Easy to add new fields without breaking clients

### 7. Data Class Pattern (Backend)
**Pattern**: Dataclasses for Structured Results

Python dataclasses for clean data structures:

```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class Keypoint:
    name: str
    x: int
    y: int
    confidence: float = 1.0

@dataclass
class Measurement:
    name: str
    value_px: float
    value_cm: Optional[float] = None

@dataclass
class DetectionResult:
    success: bool
    garment_type: str
    keypoints: List[Keypoint] = field(default_factory=list)
    measurements: Dict[str, float] = field(default_factory=dict)
    contour: Optional[np.ndarray] = None
    error: Optional[str] = None
```

**When to use**: All structured data in backend.

**Why this pattern**:
- Type hints for clarity
- Default values reduce boilerplate
- Easy to serialize to JSON

## Code Organization

### Frontend Structure (index.html)
```
<style>          # All CSS in head
<body>           # HTML structure
<script>         # All JavaScript inline
  ├── Configuration (BACKEND_URL, constants)
  ├── State initialization (state, photoState)
  ├── Backend communication functions
  ├── Canvas functions
  ├── Measurement functions
  ├── Pattern generation
  ├── Profile management
  ├── Auto-detection functions
  └── Event handlers
```

### Backend Structure (server/)
```
server/
├── app.py               # Flask routes, request handling
├── calibration.py       # ArUco detection, scale calculation
├── garment_detector.py  # Keypoint detection algorithms
├── body_measurer.py     # MediaPipe integration (Phase 3)
├── lidar_processor.py   # Mesh processing (Phase 4)
├── requirements.txt     # Python dependencies
└── venv/                # Virtual environment
```

## Data Flow

### Auto-Detection Flow
```
User: Upload Image
    ↓
Frontend: Display on Canvas
    ↓
User: Click "Auto-Detect Garment"
    ↓
Frontend: Convert canvas to JPEG blob
    ↓
Frontend: POST to /api/measure/garment
    ↓
Backend: Decode image with OpenCV
    ↓
Backend: Run detection pipeline
    ↓
Backend: Return keypoints + measurements
    ↓
Frontend: Draw keypoints on canvas
    ↓
Frontend: Display measurements table
    ↓
User: Review/adjust if needed
```

### Calibration Flow
```
User: Upload photo with ArUco card
    ↓
Frontend: POST to /api/calibrate
    ↓
Backend: Detect ArUco markers
    ↓
Backend: Calculate pixels per cm
    ↓
Backend: Return scale + confidence
    ↓
Frontend: Store scale for future measurements
    ↓
Frontend: Convert pixel measurements to real-world units
```

## Security Considerations

### Backend Security
- **Local binding**: Flask binds to 127.0.0.1 only
- **No authentication**: Designed for single-user local use
- **File validation**: Only processes image MIME types
- **No external calls**: All processing is local
- **CORS configured**: Only allows localhost origins

### Frontend Security
- All data processing happens client-side or localhost
- No analytics or tracking
- Profile data stays in localStorage
- No external resources loaded

## Error Handling Pattern

### Frontend Error Handling
```javascript
try {
  const response = await fetch(url, options);
  const result = await response.json();

  if (result.success) {
    // Handle success
  } else {
    showStatus('photoStatus', result.error || 'Operation failed.', 'error');
  }
} catch (err) {
  console.error('Error:', err);
  showStatus('photoStatus', 'Connection failed. Is the backend running?', 'error');
}
```

### Backend Error Handling
```python
try:
    # Process image
    result = detect_garment(image)
    return jsonify(result.to_dict())
except Exception as e:
    return jsonify({
        'success': False,
        'error': str(e)
    }), 500
```

## Extensibility Points

### Adding New Garment Types
1. Create detection function in `garment_detector.py`:
   ```python
   def detect_shirt_keypoints(image, scale_ppcm=None):
       # Shirt-specific detection logic
   ```
2. Add to dispatcher in `detect_garment()`:
   ```python
   if garment_type == 'shirt':
       return detect_shirt_keypoints(image, scale_ppcm)
   ```
3. Update frontend keypoint colors and measurement labels

### Adding New Measurements
1. Add keypoint extraction in backend
2. Add measurement calculation
3. Add to response structure
4. Update frontend display table

### Adding New Backend Features
1. Create new Python module (e.g., `body_measurer.py`)
2. Add routes in `app.py`
3. Update health check to reflect feature status
4. Add frontend UI and API calls

## Testing Approach

### Backend Testing
```python
# Test with curl
curl -X POST -F "image=@pants.jpg" http://localhost:5050/api/measure/garment

# Test in Python
def test_pants_detection():
    image = cv2.imread('test_pants.jpg')
    result = detect_garment(image, 'pants')
    assert result.success
    assert 'waist_flat' in result.measurements
```

### Frontend Testing
- Manual testing with real images
- Console logging for debugging
- Network tab for API responses
- Visual verification of keypoint placement
