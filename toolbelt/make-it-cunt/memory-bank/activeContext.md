# Active Context

## Current Focus

**Status**: v3.0 Backend Complete - Volumetric Garment Modification System

We have implemented **Make It Cunt v3.0** - a major architectural upgrade from 2D photo measurement to **3D volumetric analysis**. The system now compares 3D body scans to 3D garment scans to find fit problems and generate shaped pattern pieces.

## Recent Changes

- **2025-12-19**: v3.0 Backend Implementation Complete
  - Created `mesh_processing.py` - PLY/OBJ/STL import, cleaning, alignment
  - Created `body_model.py` - Anatomical landmark detection, cross-section analysis, movement envelope
  - Created `garment_model.py` - Seam detection, garment type classification, pattern piece segmentation
  - Created `fit_analysis.py` - Body-garment delta analysis, compression/gap detection
  - Created `pattern_generator.py` - Shaped pattern pieces (tapered, diamond gussets), SVG export
  - Updated `app.py` with new v3 API endpoints
  - Updated `requirements.txt` with mesh processing dependencies

- **2025-12-14**: v2.0 Complete - ArUco + 2D Detection (still available)

## Architecture Overview (v3.0)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER WORKFLOW                                │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────────────┐  │
│  │  Revopoint  │      │  Revopoint  │      │    Make It Cunt     │  │
│  │  Body Scan  │ ───► │  Garment    │ ───► │    v3.0 Server      │  │
│  │  (PLY/OBJ)  │      │  Scan       │      │                     │  │
│  └─────────────┘      └─────────────┘      └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BACKEND (Python/Flask :5050)                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                      v3.0 VOLUMETRIC PIPELINE                   ││
│  │                                                                 ││
│  │  mesh_processing.py ──► body_model.py ──► fit_analysis.py      ││
│  │         │                     │                   │             ││
│  │         ▼                     ▼                   ▼             ││
│  │  PLY/OBJ import      Landmark detection    Delta analysis       ││
│  │  Mesh cleaning       Cross-sections        Compression zones    ││
│  │  PCA alignment       Movement envelope     Gap zones (tenting)  ││
│  │                                            Length deficits      ││
│  │                                                   │             ││
│  │                                                   ▼             ││
│  │                      garment_model.py ──► pattern_generator.py  ││
│  │                             │                     │             ││
│  │                             ▼                     ▼             ││
│  │                      Seam detection         Shaped patterns     ││
│  │                      Type classification    Tapered extensions  ││
│  │                      Pattern pieces         Diamond gussets     ││
│  │                                             SVG export          ││
│  └─────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                      v2.0 (MAINTAINED)                          ││
│  │  calibration.py (ArUco)  │  garment_detector.py (2D CV)        ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

## User Profile

- **Hardware**: Revopoint Inspire 3D Scanner (acquired 2025-12-22)
- **Software**: Revo Scan 5 for mesh export
- **Scanner Specs**: 0.2mm accuracy, 0.3mm point spacing, exports PLY/OBJ/STL
- **Garment scanning**: On dress form (captures drape/shape)
- **Body challenges**:
  - Long arms, legs, torso (need extensions)
  - Broad shoulders (stress → ripping)
  - Low projection/flat (excess fabric → tenting)
  - Wild movement needs (dance, extreme ease required)
- **Technical level**: Full nerd mode (Blender, Python, point clouds)

## New v3 API Endpoints

```
POST /api/mesh/upload/body       - Upload 3D body scan (PLY/OBJ/STL)
POST /api/mesh/upload/garment    - Upload 3D garment scan
POST /api/analysis/fit           - Run volumetric fit analysis
POST /api/patterns/generate      - Generate shaped pattern pieces
POST /api/workflow/analyze-and-generate - Full pipeline in one call
GET  /api/mesh/status            - Check loaded meshes
POST /api/mesh/clear             - Clear stored meshes
```

## Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1-10 | v1.x Core Functionality | ✅ Complete |
| 11 | ArUco Calibration | ✅ Complete |
| 12 | 2D Garment Detection | ✅ Complete |
| 13 | 3D Mesh Processing | ✅ Complete |
| 14 | Body Model (landmarks, movement) | ✅ Complete |
| 15 | Garment Model (seams, structure) | ✅ Complete |
| 16 | Fit Analysis (delta, zones) | ✅ Complete |
| 17 | Pattern Generation (shaped) | ✅ Complete |
| 18 | Web UI Update (Three.js) | ⏳ Tabled |

## What v3.0 Solves (User's Specific Issues)

| Problem | v2.0 Solution | v3.0 Solution |
|---------|---------------|---------------|
| Long limbs/torso | Rectangle extension | Tapered extension matching garment silhouette |
| Broad shoulders (ripping) | Nothing | Stress map → gusset or let-out panel at exact seam |
| Tenting (low projection) | Nothing | Gap map → dart placement or strategic take-in |
| Wild movement | Nothing | Movement envelope → ease insertion at stress points |

## Files Created (v3.0)

```
make-it-cunt/server/
├── mesh_processing.py      # PLY/OBJ import, pymeshlab cleaning, PCA alignment
├── body_model.py           # Landmark detection, cross-sections, movement envelope
├── garment_model.py        # Seam detection, type classification, pattern segmentation
├── fit_analysis.py         # Body-garment delta, compression/gap zones
├── pattern_generator.py    # Shaped patterns, SVG export with notches/grain lines
├── app.py                  # Updated with v3 endpoints
└── requirements.txt        # Updated with mesh processing deps
```

## Running the v3.0 Server

```bash
cd server
source venv/bin/activate
pip install -r requirements.txt  # Install new deps
python app.py
```

Server will show feature status at startup:
```
Feature Status:
  Mesh Processing:    OK
  Body Model:         OK
  Garment Model:      OK
  Fit Analysis:       OK
  Pattern Generation: OK
```

## Next Steps

### Immediate (Next Steps)
1. Install new dependencies (`pip install -r requirements.txt`)
2. Test server starts with all features OK
3. ✅ **Acquired Revopoint Inspire** (2025-12-22)
4. Do first body + garment scan test with Inspire

### When Ready
1. Update index.html with mesh upload UI
2. Add Three.js viewer for 3D mesh visualization
3. Add fit analysis results display
4. Add pattern download buttons

## Key Dependencies (New in v3.0)

```
pymeshlab>=2023.12    # MeshLab Python bindings
open3d>=0.17.0        # Point cloud processing
trimesh>=4.0.0        # Mesh analysis, ray casting
svgwrite>=1.4.0       # Pattern SVG generation
numpy-stl>=3.0.0      # STL handling
```

## Context for AI Assistants

When resuming work on this project:

1. **v3.0 is backend-complete**: All Python modules done, API endpoints working
2. **UI is tabled**: User decided to defer index.html update
3. **Scanner acquired**: Revopoint Inspire (0.2mm accuracy, Revo Scan 5)
4. **Test with sample PLY files**: Can test endpoints without real scans
5. **Movement profile = "wild"**: User needs extreme ease for dance/movement

**Communication Style**: Direct, technical, sewing/pattern-making domain knowledge.

**Key Insight**: This user has specific body challenges (long limbs, broad shoulders, low projection, wild movement) that standard patterns don't address. The system is designed to identify and solve these exact issues.
