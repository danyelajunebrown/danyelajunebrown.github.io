# WearAnalysis - Predictive Maintenance System

Computer vision and ML system that analyzes wear patterns across personal belongings.

## Quick Start

### 1. Clone and Install
```bash
git clone <your-repo-url>
cd wear-analysis
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Install COLMAP
```bash
# Mac
brew install colmap

# Linux
sudo apt-get install colmap
```

### 3. Run Application
```bash
python app.py
```

Open http://localhost:5000

## First Test - Sneaker Stains

1. Take 25+ photos of your stained sneakers
2. Go to Upload page
3. Select "Sneakers" category
4. Upload photos
5. View 3D model and analysis

## Categories

1. Sneakers - sole wear, stains
2. Clothing - fabric wear, stains  
3. Zippers - teeth alignment, slider wear
4. Technology - device damage
5. Body - bruises, cuts
6. Misc - other items

## Features

- ✅ 3D photogrammetry reconstruction
- ✅ Automated wear analysis
- ✅ Stain detection and treatment
- ✅ Predictive failure estimates
- ✅ Web dashboard and 3D viewer

## Data Structure

```
data/
├── raw/photogrammetry/YYYY-MM-DD/session_UUID/
│   ├── images/
│   └── metadata.json
└── processed/
    ├── 3d_models/
    └── analysis_results/
```

## API Endpoints

- `POST /api/upload` - Upload photos
- `GET /api/sessions` - List sessions
- `GET /api/session/<id>` - Session details

## Tech Stack

- Flask + SQLAlchemy
- COLMAP photogrammetry
- Three.js 3D viewer
- OpenCV + PIL
- Tailwind CSS

Built for 10-year dataset collection.
