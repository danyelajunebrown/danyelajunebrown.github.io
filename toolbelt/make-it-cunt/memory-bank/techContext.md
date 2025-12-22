# Technical Context

## Technology Stack

### Frontend (Unchanged from v2)
- **HTML5**: Semantic markup, canvas element
- **CSS3**: Grid, flexbox, gradients
- **JavaScript (ES6+)**: Vanilla JS, no frameworks
- **Three.js**: (Planned for v3 UI) 3D mesh visualization

### Backend (v3.0 - Significantly Expanded)

#### Core Framework
- **Flask 3.0+**: Lightweight web server
- **Flask-CORS 4.0+**: Cross-origin requests

#### Mesh Processing (NEW in v3.0)
- **trimesh 4.0+**: Primary mesh library (PLY/OBJ/STL import, ray casting)
- **pymeshlab 2023.12+**: MeshLab Python bindings (cleaning, hole filling, smoothing)
- **open3d 0.17+**: Point cloud processing, mesh alignment
- **numpy-stl 3.0+**: STL file handling

#### Pattern Generation (NEW in v3.0)
- **svgwrite 1.4+**: SVG pattern generation with notches, grain lines

#### Computer Vision (v2 - Maintained)
- **OpenCV (opencv-contrib-python) 4.8+**: ArUco, edge detection
- **NumPy 1.24+**: Array operations
- **SciPy 1.11+**: Scientific computing, signal processing
- **Pillow 10.0+**: Image I/O

#### Optional
- **MediaPipe 0.10+**: Body pose detection (photo-based, not used in v3 mesh flow)

## v3.0 Module Architecture

```
server/
├── app.py                  # Flask routes, feature detection
├── mesh_processing.py      # PLY/OBJ/STL import, cleaning, alignment
├── body_model.py           # Landmark detection, cross-sections, movement envelope
├── garment_model.py        # Seam detection, type classification, pattern pieces
├── fit_analysis.py         # Body-garment delta, compression/gap detection
├── pattern_generator.py    # Shaped patterns, SVG export
├── calibration.py          # ArUco detection (v2)
├── garment_detector.py     # 2D keypoint detection (v2)
└── requirements.txt
```

## API Endpoints (v3.0)

### Health & Status
```
GET /api/health
Response: {
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

### Mesh Upload
```
POST /api/mesh/upload/body
Body: FormData with 'mesh' file (PLY/OBJ/STL), optional 'movement_profile'
Response: {
  "success": true,
  "mesh_type": "body",
  "stats": {...},
  "landmarks": {...},
  "measurements": {...}
}

POST /api/mesh/upload/garment
Body: FormData with 'mesh' file, optional 'garment_type'
Response: {
  "success": true,
  "mesh_type": "garment",
  "garment_type": "pants",
  "stats": {...},
  "seams": [...],
  "measurements": {...}
}
```

### Fit Analysis
```
POST /api/analysis/fit
Body: Uses stored meshes, or upload both 'body_mesh' and 'garment_mesh'
Response: {
  "success": true,
  "fit_analysis": {
    "issues": [
      {
        "type": "compression",
        "severity": "severe",
        "zone": "shoulders",
        "amount_mm": -25.5,
        "description": "Shoulder compression - risk of ripping"
      }
    ],
    "recommendations": [
      {
        "type": "gusset",
        "zone": "shoulders",
        "amount_mm": 45.5,
        "instructions": "Add diamond gusset at shoulder seam..."
      }
    ],
    "overall_fit_score": 62.0
  }
}
```

### Pattern Generation
```
POST /api/patterns/generate
Body: JSON with 'recommendations' and 'garment_measurements'
Response: {
  "success": true,
  "patterns": [
    {
      "name": "Shoulder Gusset",
      "type": "gusset",
      "dimensions_mm": {"width": 65, "height": 97},
      "seam_allowance_mm": 15
    }
  ],
  "svg_content": {
    "Shoulder Gusset": "<svg>...</svg>"
  }
}
```

### Full Workflow
```
POST /api/workflow/analyze-and-generate
Body: FormData with 'body_mesh', 'garment_mesh', optional params
Response: Complete fit analysis + generated patterns in one call
```

## Data Structures (v3.0)

### ProcessedMesh
```python
@dataclass
class ProcessedMesh:
    mesh: Any                    # trimesh.Trimesh
    mesh_type: MeshType          # BODY or GARMENT
    stats: MeshStats             # vertex_count, dimensions, etc.
    vertices: np.ndarray         # Nx3
    faces: np.ndarray            # Mx3
    normals: Optional[np.ndarray]
    processing_log: List[str]
```

### BodyModel Output
```python
{
    'landmarks': {
        'waist': [x, y, z],
        'hip': [x, y, z],
        'shoulder_left': [x, y, z],
        ...
    },
    'measurements': {
        'waist_circumference': 780.0,  # mm
        'hip_circumference': 980.0,
        'inseam': 820.0,
        ...
    },
    'movement_envelope': {
        'ease_profile': 'wild',
        'ease_map': {
            'shoulder': 80.0,  # mm
            'crotch': 100.0,
            ...
        }
    }
}
```

### FitIssue
```python
@dataclass
class FitIssue:
    issue_type: FitIssueType     # COMPRESSION, GAP, TOO_SHORT, MOVEMENT_CONFLICT
    severity: FitIssueSeverity   # MINOR, MODERATE, SEVERE, CRITICAL
    body_zone: BodyZone          # SHOULDERS, BUST, WAIST, HIPS, etc.
    location: np.ndarray         # 3D location
    amount: float                # mm (negative=compression, positive=gap)
    description: str
    affected_vertices: List[int]
```

### GeneratedPattern
```python
@dataclass
class GeneratedPattern:
    name: str
    piece_type: PatternPieceType  # EXTENSION, GUSSET, DART, INSERT_PANEL
    outline: np.ndarray           # 2D polygon points
    cut_line: np.ndarray
    stitch_line: np.ndarray
    seam_allowance: float         # mm
    notches: List[Notch]
    grain_line: Optional[GrainLine]
    instructions: str
    dimensions_mm: Tuple[float, float]
```

## Dependencies (requirements.txt v3.0)

```
# Core
flask>=3.0.0
flask-cors>=4.0.0
numpy>=1.24.0
scipy>=1.11.0

# Mesh Processing (NEW)
trimesh>=4.0.0
pymeshlab>=2023.12
open3d>=0.17.0
numpy-stl>=3.0.0

# Pattern Generation (NEW)
svgwrite>=1.4.0

# Image/CV (v2)
opencv-contrib-python>=4.8.0
pillow>=10.0.0
```

## Installation Notes

### Basic Install
```bash
cd server
source venv/bin/activate
pip install -r requirements.txt
```

### Troubleshooting

**pymeshlab on Python 3.12+**: Not supported. Use Python 3.8-3.11.

**open3d on macOS**:
```bash
pip install open3d --no-cache-dir
```

**Missing features**: Server starts with available features. Check startup message for status.

## Hardware Requirements

### Minimum
- **CPU**: Any modern processor
- **RAM**: 8GB (mesh processing is memory-intensive)
- **Disk**: 2GB free (for Python environment + mesh files)
- **Scanner**: Revopoint Inspire or similar (exports PLY/OBJ/STL)

### Recommended
- **CPU**: Apple Silicon M1+ or Intel i5+
- **RAM**: 16GB+
- **Disk**: 5GB free
- **Scanner**: Revopoint Inspire

### Revopoint Inspire Specifications
- **Accuracy**: 0.2mm (single image)
- **Point Distance**: ~0.3mm (spacing between points)
- **Depth Camera**: 1MP
- **RGB Camera**: 1MP
- **Export Formats**: PLY, OBJ, STL, FBX, GLTF, 3MF, ASC
- **Software**: Revo Scan 5
- **Recommended Export**: PLY format (best compatibility with mesh processing pipeline)
- **Native Units**: mm (matches backend defaults)

### NOT Required
- **NVIDIA GPU**: All processing is CPU-based
- **iPhone with LiDAR**: Nice to have, but not required (handheld scanner preferred)

## Performance Expectations

### Processing Times (Estimated)
- **Mesh load + clean**: 1-3 seconds
- **Body landmark detection**: 2-5 seconds
- **Garment analysis**: 1-3 seconds
- **Fit analysis**: 3-10 seconds (depends on mesh complexity)
- **Pattern generation**: < 1 second per pattern

### Memory Usage
- **Backend idle**: ~300MB
- **With meshes loaded**: 500MB-1GB (depends on scan resolution)
- **During analysis**: Up to 2GB peak

## Security Considerations

- **Local only**: Flask binds to 127.0.0.1
- **No auth**: Designed for single-user local use
- **File handling**: Only processes mesh files (PLY/OBJ/STL)
- **No external calls**: All processing is local
- **In-memory storage**: Meshes stored in memory, cleared on restart
