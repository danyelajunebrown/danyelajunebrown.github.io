# For Damages

**Also known as:** WearAnalysis, Predictive Maintenance System

## What It Does

A computer vision and machine learning system that analyzes wear patterns on your belongings using photogrammetry. Creates 3D models of items and predicts when they'll fail so you can repair or replace them proactively.

## The Problem It Solves

You don't know when your favorite sneakers, jacket zipper, or phone case will fail until it's too late. This system:
- Documents wear progression over time
- Creates 3D models from photos
- Detects stains, damage, and wear patterns
- Predicts failure timelines
- Suggests maintenance and repairs

Perfect for building a 10-year dataset of personal item longevity.

## How It Works

1. **Photograph**: Take 25+ photos around your item (all angles)
2. **Upload**: Submit to the web dashboard with category tags
3. **Process**: COLMAP creates 3D photogrammetry reconstruction
4. **Analyze**: Computer vision detects wear patterns
5. **View**: Interactive 3D model with damage heatmap
6. **Track**: Compare over time to see progression

## Features

### Photogrammetry Reconstruction
- COLMAP-based 3D model generation
- Requires 25+ photos per item
- Automatic feature matching
- Dense point cloud generation
- Textured mesh export

### Category System
- **Sneakers**: Sole wear, stains, heel degradation
- **Clothing**: Fabric wear, tears, fading, stains
- **Zippers**: Teeth alignment, slider wear, separation
- **Technology**: Screens, ports, buttons, housing damage
- **Body**: Bruises, cuts, scars (medical documentation)
- **Misc**: Other belongings

### Wear Analysis
- Automated stain detection
- Wear pattern heatmaps
- Material degradation tracking
- Comparison between sessions
- Treatment recommendations

### Predictive Maintenance
- Failure timeline estimates
- Replacement suggestions
- Repair prioritization
- Cost-benefit analysis

### Web Dashboard
- Session management interface
- 3D model viewer (Three.js)
- Analysis results visualization
- Historical comparison tools
- Export capabilities

## Technical Details

### Technologies
**Backend:**
- Flask web framework
- SQLAlchemy ORM
- COLMAP photogrammetry engine
- OpenCV + PIL for image processing
- Python 3.x

**Frontend:**
- Three.js for 3D visualization
- Tailwind CSS styling
- Responsive design

**Storage:**
- Structured data directory
- Separate raw/processed organization
- Session-based UUID naming

### System Requirements
- Python 3.7+
- COLMAP installed (brew/apt)
- 4GB+ RAM recommended
- GPU optional but speeds processing

### API Endpoints
```
POST /api/upload        - Upload photo session
GET  /api/sessions      - List all sessions
GET  /api/session/<id>  - Session details + 3D model
GET  /api/download/<id> - Export model/data
```

### Data Directory Structure
```
data/
├── raw/
│   └── photogrammetry/
│       └── YYYY-MM-DD/
│           └── session_UUID/
│               ├── images/
│               │   ├── IMG_001.jpg
│               │   └── ...
│               └── metadata.json
└── processed/
    ├── 3d_models/
    │   └── session_UUID/
    │       ├── dense_point_cloud.ply
    │       ├── textured_mesh.obj
    │       └── analysis.json
    └── analysis_results/
        └── session_UUID.json
```

## Use Cases

1. **Sneaker Collectors**: Track sole wear, decide when to retire
2. **Minimalists**: Maximize item lifespan through data
3. **Warranty Claims**: Document damage progression with 3D evidence
4. **Medical**: Track bruise/injury healing over time
5. **Insurance**: Visual proof of item condition
6. **Researchers**: Study material longevity patterns
7. **Sustainability**: Extend product life, reduce waste

## Getting Started

### Installation
```bash
# Clone repo
git clone <repo-url>
cd for-damages

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install COLMAP
brew install colmap  # Mac
# OR
sudo apt-get install colmap  # Linux
```

### First Test - Sneaker Stains
1. Take 25+ photos of stained sneakers (360° coverage)
2. Run: `python app.py`
3. Open http://localhost:5000
4. Upload to "Sneakers" category
5. Wait for processing (2-10 minutes)
6. View 3D model and analysis

### Photography Tips
- **Overlap**: 60-80% overlap between photos
- **Angles**: High, middle, low positions
- **Lighting**: Consistent, diffused light
- **Coverage**: Every surface visible in multiple photos
- **Focus**: Sharp, clear images
- **Background**: Plain or consistent

## Future Enhancements

### AI/ML Improvements
- Damage severity classification
- Automatic material identification
- Lifespan prediction models trained on dataset
- Anomaly detection for manufacturing defects

### User Features
- Mobile app for easier photo capture
- AR overlay showing damage progression
- Maintenance reminder notifications
- Repair vendor recommendations
- Item value tracking over time

### Analysis Features
- Multi-item comparison
- Category-specific metrics
- Wear rate calculations
- Environmental factor tracking (weather, usage)
- Cost per wear analytics

### Data Platform
- Public anonymized dataset
- Material longevity database
- Brand reliability comparisons
- Community insights and tips

### Integration
- Smart home photo automation
- RFID tag item tracking
- Receipt and warranty scanning
- Shopping integration (replacement suggestions)

## File Structure

```
for-damages/
├── app.py                      # Flask application
├── worker.py                   # Background processing
├── damages.html                # Landing page
├── damages-worker.service      # systemd service
├── requirements.txt            # Python dependencies
├── requirements-worker.txt     # Worker dependencies
├── README.md                   # Setup instructions
├── templates/                  # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── upload.html
│   └── viewer.html
└── claude.md                   # This documentation
```

## Known Limitations

- COLMAP requires good photo quality and overlap
- Processing time increases with photo count
- Large datasets require significant storage
- 3D models can be memory-intensive to view
- No real-time processing (batch-based)
- Requires manual photo upload (no automation yet)

## Development Notes

- Worker process should run as background service
- Consider Redis/Celery for production job queue
- Database migrations needed for schema changes
- 3D viewer performance depends on polygon count
- COLMAP output can be 1GB+ per session
- Implement cleanup job for old sessions
- Add progress indicators for long processing jobs

## Privacy Considerations

- Photos may contain personal/identifying information
- "Body" category contains medical data
- Consider HIPAA compliance for medical use
- Implement data retention policies
- Allow user data export and deletion
- Secure uploads with authentication

## Research Potential

Building a 10-year dataset enables:
- Material science insights
- Manufacturing quality analysis
- Consumer behavior patterns
- Environmental impact studies
- Product design improvements
- Warranty and insurance modeling
