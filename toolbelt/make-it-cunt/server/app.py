"""
Make It Cunt v3.0 - Volumetric Garment Modification System

Local Flask server for:
- ArUco marker calibration (v2 feature)
- 3D mesh processing (body + garment scans)
- Volumetric fit analysis (body-garment delta)
- Pattern generation (shaped pieces, not rectangles!)

Run with: python app.py
Server runs at: http://localhost:5050
"""

import os
import sys
import json
import tempfile
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
from io import BytesIO
import numpy as np

# Import existing v2 modules
from calibration import calibrate_from_image, generate_aruco_card_svg
from garment_detector import detect_from_bytes, detect_garment, draw_keypoints_on_image
import cv2

# Import v3 volumetric modules
try:
    from mesh_processing import MeshProcessor, process_body_scan, process_garment_scan
    MESH_PROCESSING_AVAILABLE = True
except ImportError as e:
    MESH_PROCESSING_AVAILABLE = False
    print(f"Warning: Mesh processing unavailable: {e}")

try:
    from body_model import BodyModel, analyze_body_mesh
    BODY_MODEL_AVAILABLE = True
except ImportError as e:
    BODY_MODEL_AVAILABLE = False
    print(f"Warning: Body model unavailable: {e}")

try:
    from garment_model import GarmentModel, analyze_garment_mesh
    GARMENT_MODEL_AVAILABLE = True
except ImportError as e:
    GARMENT_MODEL_AVAILABLE = False
    print(f"Warning: Garment model unavailable: {e}")

try:
    from fit_analysis import FitAnalyzer, analyze_fit
    FIT_ANALYSIS_AVAILABLE = True
except ImportError as e:
    FIT_ANALYSIS_AVAILABLE = False
    print(f"Warning: Fit analysis unavailable: {e}")

try:
    from pattern_generator import PatternGenerator, generate_patterns
    PATTERN_GENERATOR_AVAILABLE = True
except ImportError as e:
    PATTERN_GENERATOR_AVAILABLE = False
    print(f"Warning: Pattern generator unavailable: {e}")


app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from the HTML app

# Server configuration
PORT = 5050
HOST = '127.0.0.1'

# In-memory storage for uploaded meshes (for session-based workflow)
mesh_storage = {
    'body': None,
    'garment': None
}


# ============================================================
# Health & Status
# ============================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint with feature availability."""
    return jsonify({
        'status': 'healthy',
        'version': '3.0.0',
        'features': {
            'calibration': True,
            'garment_detection_2d': True,
            'mesh_processing': MESH_PROCESSING_AVAILABLE,
            'body_model': BODY_MODEL_AVAILABLE,
            'garment_model': GARMENT_MODEL_AVAILABLE,
            'fit_analysis': FIT_ANALYSIS_AVAILABLE,
            'pattern_generation': PATTERN_GENERATOR_AVAILABLE
        }
    })


# ============================================================
# Scan Folder Auto-Detection
# ============================================================

SCAN_FOLDER_BASE = os.path.expanduser('~/Desktop/MakeItCunt-Scans')

@app.route('/api/scans/folder', methods=['GET'])
def get_scan_folder():
    """Return the scan folder path and any available scans."""
    body_folder = os.path.join(SCAN_FOLDER_BASE, 'body')
    garment_folder = os.path.join(SCAN_FOLDER_BASE, 'garment')

    # Ensure folders exist
    os.makedirs(body_folder, exist_ok=True)
    os.makedirs(garment_folder, exist_ok=True)

    def get_mesh_files(folder):
        """Get list of mesh files in folder, sorted by modification time (newest first)."""
        files = []
        if os.path.exists(folder):
            for f in os.listdir(folder):
                if f.lower().endswith(('.ply', '.obj', '.stl')):
                    path = os.path.join(folder, f)
                    files.append({
                        'name': f,
                        'path': path,
                        'size': os.path.getsize(path),
                        'modified': os.path.getmtime(path)
                    })
        return sorted(files, key=lambda x: x['modified'], reverse=True)

    return jsonify({
        'success': True,
        'folder': SCAN_FOLDER_BASE,
        'body_scans': get_mesh_files(body_folder),
        'garment_scans': get_mesh_files(garment_folder)
    })


@app.route('/api/scans/load/<scan_type>', methods=['POST'])
def load_scan_from_folder(scan_type):
    """Load a scan from the scan folder by filename."""
    if scan_type not in ['body', 'garment']:
        return jsonify({'success': False, 'error': 'Invalid scan type'}), 400

    data = request.get_json() or {}
    filename = data.get('filename')

    if not filename:
        return jsonify({'success': False, 'error': 'No filename provided'}), 400

    folder = os.path.join(SCAN_FOLDER_BASE, scan_type)
    filepath = os.path.join(folder, filename)

    # Security: ensure path is within scan folder
    if not os.path.realpath(filepath).startswith(os.path.realpath(folder)):
        return jsonify({'success': False, 'error': 'Invalid path'}), 400

    if not os.path.exists(filepath):
        return jsonify({'success': False, 'error': 'File not found'}), 404

    try:
        with open(filepath, 'rb') as f:
            file_data = f.read()

        if scan_type == 'body':
            movement_profile = data.get('movement_profile', 'wild')
            result = process_body_scan(file_data, filename, movement_profile)
            if result['success']:
                mesh_storage['body'] = result
        else:
            garment_type = data.get('garment_type')
            result = process_garment_scan(file_data, filename, garment_type)
            if result['success']:
                mesh_storage['garment'] = result

        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ArUco Calibration (v2 features, maintained)
# ============================================================

@app.route('/api/calibrate', methods=['POST'])
def calibrate():
    """Calibrate scale from ArUco markers in uploaded image."""
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No image provided'}), 400

    image_file = request.files['image']
    marker_size = float(request.form.get('marker_size', 5.0))
    image_bytes = image_file.read()
    result = calibrate_from_image(image_bytes=image_bytes, marker_size_cm=marker_size)

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


@app.route('/api/calibration-card', methods=['GET'])
def get_calibration_card():
    """Generate and return the printable ArUco calibration card as SVG."""
    marker_size = float(request.args.get('marker_size', 5.0))
    svg_content = generate_aruco_card_svg(marker_size_cm=marker_size)

    return send_file(
        BytesIO(svg_content.encode('utf-8')),
        mimetype='image/svg+xml',
        as_attachment=True,
        download_name='aruco-calibration-card.svg'
    )


@app.route('/api/calibration-card/preview', methods=['GET'])
def preview_calibration_card():
    """Return calibration card SVG for inline display."""
    marker_size = float(request.args.get('marker_size', 5.0))
    svg_content = generate_aruco_card_svg(marker_size_cm=marker_size)
    return svg_content, 200, {'Content-Type': 'image/svg+xml'}


# ============================================================
# 2D Garment Detection (v2 features, maintained)
# ============================================================

@app.route('/api/measure/garment', methods=['POST'])
def measure_garment():
    """Auto-detect garment keypoints from 2D photo."""
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No image provided'}), 400

    image_file = request.files['image']
    garment_type = request.form.get('garment_type', None)
    scale_ppcm = request.form.get('scale_ppcm', None)

    if scale_ppcm:
        scale_ppcm = float(scale_ppcm)

    image_bytes = image_file.read()
    result = detect_from_bytes(image_bytes, garment_type, scale_ppcm)

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


@app.route('/api/measure/garment/visualize', methods=['POST'])
def visualize_garment_detection():
    """Detect garment and return image with keypoints drawn."""
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No image provided'}), 400

    image_file = request.files['image']
    garment_type = request.form.get('garment_type', None)
    scale_ppcm = request.form.get('scale_ppcm', None)

    if scale_ppcm:
        scale_ppcm = float(scale_ppcm)

    image_bytes = image_file.read()
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        return jsonify({'success': False, 'error': 'Failed to decode image'}), 400

    result = detect_garment(image, garment_type, scale_ppcm)

    if not result.success:
        return jsonify({'success': False, 'error': result.error}), 400

    vis_image = draw_keypoints_on_image(image, result.keypoints, result.contour)
    _, buffer = cv2.imencode('.jpg', vis_image, [cv2.IMWRITE_JPEG_QUALITY, 90])

    return send_file(BytesIO(buffer.tobytes()), mimetype='image/jpeg')


# ============================================================
# v3: 3D Mesh Upload & Processing
# ============================================================

@app.route('/api/mesh/upload/body', methods=['POST'])
def upload_body_mesh():
    """
    Upload and process a 3D body scan.

    Request:
        - Form data with 'mesh' file (PLY, OBJ, or STL)
        - Optional 'movement_profile': 'default' or 'wild'

    Response:
        {
            'success': bool,
            'mesh_type': 'body',
            'stats': {...},
            'landmarks': {...},
            'measurements': {...}
        }
    """
    if not MESH_PROCESSING_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Mesh processing not available. Install trimesh, open3d, or pymeshlab.'
        }), 501

    if 'mesh' not in request.files:
        return jsonify({'success': False, 'error': 'No mesh file provided'}), 400

    mesh_file = request.files['mesh']
    filename = mesh_file.filename
    movement_profile = request.form.get('movement_profile', 'wild')

    # Read and process mesh
    mesh_bytes = mesh_file.read()

    try:
        processor = MeshProcessor()
        mesh = processor.load_mesh(file_bytes=mesh_bytes, filename=filename)
        mesh = processor.clean_mesh(mesh)
        mesh = processor.orient_body(mesh)

        # Analyze body
        if BODY_MODEL_AVAILABLE:
            body_analysis = analyze_body_mesh(
                mesh.vertices, mesh.faces, movement_profile
            )
        else:
            body_analysis = {}

        # Store for later use
        mesh_storage['body'] = {
            'vertices': mesh.vertices,
            'faces': mesh.faces,
            'stats': mesh.stats.to_dict(),
            'analysis': body_analysis
        }

        return jsonify({
            'success': True,
            'mesh_type': 'body',
            'stats': mesh.stats.to_dict(),
            'processing_log': mesh.processing_log,
            **body_analysis
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/mesh/upload/garment', methods=['POST'])
def upload_garment_mesh():
    """
    Upload and process a 3D garment scan.

    Request:
        - Form data with 'mesh' file (PLY, OBJ, or STL)
        - Optional 'garment_type': 'pants', 'shirt', 'dress', etc.

    Response:
        {
            'success': bool,
            'mesh_type': 'garment',
            'garment_type': str,
            'stats': {...},
            'seams': [...],
            'measurements': {...}
        }
    """
    if not MESH_PROCESSING_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Mesh processing not available. Install trimesh, open3d, or pymeshlab.'
        }), 501

    if 'mesh' not in request.files:
        return jsonify({'success': False, 'error': 'No mesh file provided'}), 400

    mesh_file = request.files['mesh']
    filename = mesh_file.filename
    garment_type = request.form.get('garment_type', None)

    mesh_bytes = mesh_file.read()

    try:
        processor = MeshProcessor()
        mesh = processor.load_mesh(file_bytes=mesh_bytes, filename=filename)
        mesh = processor.clean_mesh(mesh)
        mesh = processor.orient_garment(mesh, garment_type or "pants")

        # Analyze garment
        if GARMENT_MODEL_AVAILABLE:
            garment_analysis = analyze_garment_mesh(
                mesh.vertices, mesh.faces, garment_type
            )
        else:
            garment_analysis = {}

        # Store for later use
        mesh_storage['garment'] = {
            'vertices': mesh.vertices,
            'faces': mesh.faces,
            'stats': mesh.stats.to_dict(),
            'analysis': garment_analysis
        }

        return jsonify({
            'success': True,
            'mesh_type': 'garment',
            'stats': mesh.stats.to_dict(),
            'processing_log': mesh.processing_log,
            **garment_analysis
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ============================================================
# v3: Fit Analysis
# ============================================================

@app.route('/api/analysis/fit', methods=['POST'])
def analyze_fit_endpoint():
    """
    Perform fit analysis comparing body to garment.

    Uses previously uploaded body and garment meshes, or accepts new uploads.

    Request (option 1 - use stored meshes):
        - No files, just POST to endpoint

    Request (option 2 - upload both):
        - 'body_mesh': Body PLY/OBJ/STL file
        - 'garment_mesh': Garment PLY/OBJ/STL file
        - Optional 'movement_profile': 'default' or 'wild'
        - Optional 'garment_type': 'pants', 'shirt', etc.

    Response:
        {
            'success': bool,
            'fit_analysis': {
                'issues': [...],
                'recommendations': [...],
                'overall_fit_score': float
            },
            'body_summary': {...},
            'garment_summary': {...}
        }
    """
    if not FIT_ANALYSIS_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Fit analysis not available. Check dependencies.'
        }), 501

    movement_profile = request.form.get('movement_profile', 'wild')
    garment_type = request.form.get('garment_type', None)

    # Check if new meshes are being uploaded
    if 'body_mesh' in request.files and 'garment_mesh' in request.files:
        # Process new uploads
        try:
            processor = MeshProcessor()

            # Body
            body_file = request.files['body_mesh']
            body_bytes = body_file.read()
            body_mesh = processor.load_mesh(file_bytes=body_bytes, filename=body_file.filename)
            body_mesh = processor.clean_mesh(body_mesh)
            body_mesh = processor.orient_body(body_mesh)

            # Garment
            garment_file = request.files['garment_mesh']
            garment_bytes = garment_file.read()
            garment_mesh = processor.load_mesh(file_bytes=garment_bytes, filename=garment_file.filename)
            garment_mesh = processor.clean_mesh(garment_mesh)
            garment_mesh = processor.orient_garment(garment_mesh, garment_type or "pants")

            # Align
            body_mesh, garment_mesh = processor.align_meshes(body_mesh, garment_mesh)

            body_vertices = body_mesh.vertices
            body_faces = body_mesh.faces
            garment_vertices = garment_mesh.vertices
            garment_faces = garment_mesh.faces

        except Exception as e:
            return jsonify({'success': False, 'error': f'Mesh processing error: {str(e)}'}), 400

    elif mesh_storage['body'] and mesh_storage['garment']:
        # Use stored meshes
        body_vertices = mesh_storage['body']['vertices']
        body_faces = mesh_storage['body']['faces']
        garment_vertices = mesh_storage['garment']['vertices']
        garment_faces = mesh_storage['garment']['faces']

    else:
        return jsonify({
            'success': False,
            'error': 'No meshes available. Upload body and garment meshes first, or include them in this request.'
        }), 400

    # Perform analysis
    try:
        result = analyze_fit(
            body_vertices, body_faces,
            garment_vertices, garment_faces,
            movement_profile, garment_type
        )

        return jsonify({
            'success': True,
            **result
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ============================================================
# v3: Pattern Generation
# ============================================================

@app.route('/api/patterns/generate', methods=['POST'])
def generate_patterns_endpoint():
    """
    Generate pattern pieces from fit analysis recommendations.

    Request:
        - JSON body with 'recommendations' and 'garment_measurements'
        - Or POST with no body to use last fit analysis results

    Response:
        {
            'success': bool,
            'patterns': [...],
            'svg_content': {...}
        }
    """
    if not PATTERN_GENERATOR_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Pattern generation not available. Install svgwrite.'
        }), 501

    data = request.get_json() or {}

    recommendations = data.get('recommendations', [])
    garment_data = data.get('garment_measurements', {})
    fabric_type = data.get('fabric_type', 'default')

    if not recommendations:
        return jsonify({
            'success': False,
            'error': 'No recommendations provided. Run fit analysis first.'
        }), 400

    try:
        result = generate_patterns(recommendations, garment_data, fabric_type)

        return jsonify({
            'success': True,
            **result
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/patterns/download/<pattern_name>', methods=['GET'])
def download_pattern(pattern_name):
    """
    Download a specific pattern piece as SVG.

    URL params:
        - pattern_name: Name of the pattern piece

    Query params:
        - scale: Scale factor (default 1.0 = actual size in mm)
    """
    # This would retrieve from a pattern cache
    # For now, return a placeholder
    return jsonify({
        'success': False,
        'error': 'Pattern download requires running generate first'
    }), 400


# ============================================================
# v3: Full Workflow Endpoint
# ============================================================

@app.route('/api/workflow/analyze-and-generate', methods=['POST'])
def full_workflow():
    """
    Complete workflow: upload meshes, analyze fit, generate patterns.

    Request:
        - 'body_mesh': Body PLY/OBJ/STL file
        - 'garment_mesh': Garment PLY/OBJ/STL file
        - Optional 'movement_profile': 'default' or 'wild'
        - Optional 'garment_type': 'pants', 'shirt', etc.
        - Optional 'fabric_type': 'woven', 'knit', 'denim'

    Response:
        {
            'success': bool,
            'fit_analysis': {...},
            'patterns': [...],
            'svg_content': {...}
        }
    """
    if not all([MESH_PROCESSING_AVAILABLE, FIT_ANALYSIS_AVAILABLE, PATTERN_GENERATOR_AVAILABLE]):
        missing = []
        if not MESH_PROCESSING_AVAILABLE:
            missing.append('mesh_processing')
        if not FIT_ANALYSIS_AVAILABLE:
            missing.append('fit_analysis')
        if not PATTERN_GENERATOR_AVAILABLE:
            missing.append('pattern_generation')
        return jsonify({
            'success': False,
            'error': f'Missing features: {", ".join(missing)}'
        }), 501

    if 'body_mesh' not in request.files or 'garment_mesh' not in request.files:
        return jsonify({
            'success': False,
            'error': 'Both body_mesh and garment_mesh files required'
        }), 400

    movement_profile = request.form.get('movement_profile', 'wild')
    garment_type = request.form.get('garment_type', 'pants')
    fabric_type = request.form.get('fabric_type', 'default')

    try:
        processor = MeshProcessor()

        # Process body
        body_file = request.files['body_mesh']
        body_bytes = body_file.read()
        body_mesh = processor.load_mesh(file_bytes=body_bytes, filename=body_file.filename)
        body_mesh = processor.clean_mesh(body_mesh)
        body_mesh = processor.orient_body(body_mesh)

        # Process garment
        garment_file = request.files['garment_mesh']
        garment_bytes = garment_file.read()
        garment_mesh = processor.load_mesh(file_bytes=garment_bytes, filename=garment_file.filename)
        garment_mesh = processor.clean_mesh(garment_mesh)
        garment_mesh = processor.orient_garment(garment_mesh, garment_type)

        # Align meshes
        body_mesh, garment_mesh = processor.align_meshes(body_mesh, garment_mesh)

        # Run fit analysis
        fit_result = analyze_fit(
            body_mesh.vertices, body_mesh.faces,
            garment_mesh.vertices, garment_mesh.faces,
            movement_profile, garment_type
        )

        # Extract recommendations for pattern generation
        recommendations = fit_result.get('fit_analysis', {}).get('recommendations', [])

        # Get garment measurements for pattern context
        garment_measurements = fit_result.get('garment_summary', {}).get('measurements', {})

        # Generate patterns
        if recommendations:
            pattern_result = generate_patterns(recommendations, garment_measurements, fabric_type)
        else:
            pattern_result = {'patterns': [], 'svg_content': {}}

        return jsonify({
            'success': True,
            'fit_analysis': fit_result.get('fit_analysis', {}),
            'body_summary': fit_result.get('body_summary', {}),
            'garment_summary': fit_result.get('garment_summary', {}),
            'patterns': pattern_result.get('patterns', []),
            'svg_content': pattern_result.get('svg_content', {})
        })

    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 400


# ============================================================
# Mesh Status (for debugging)
# ============================================================

@app.route('/api/mesh/status', methods=['GET'])
def mesh_status():
    """Check what meshes are currently loaded."""
    return jsonify({
        'body_loaded': mesh_storage['body'] is not None,
        'garment_loaded': mesh_storage['garment'] is not None,
        'body_stats': mesh_storage['body']['stats'] if mesh_storage['body'] else None,
        'garment_stats': mesh_storage['garment']['stats'] if mesh_storage['garment'] else None
    })


@app.route('/api/mesh/clear', methods=['POST'])
def clear_meshes():
    """Clear stored meshes."""
    mesh_storage['body'] = None
    mesh_storage['garment'] = None
    return jsonify({'success': True, 'message': 'Meshes cleared'})


# ============================================================
# Main
# ============================================================

def print_startup_message():
    """Print helpful startup message."""
    print("\n" + "=" * 60)
    print("  Make It Cunt v3.0 - Volumetric Garment Modification")
    print("=" * 60)
    print(f"\n  Server running at: http://{HOST}:{PORT}")
    print("\n  Feature Status:")
    print(f"    Mesh Processing:    {'OK' if MESH_PROCESSING_AVAILABLE else 'MISSING'}")
    print(f"    Body Model:         {'OK' if BODY_MODEL_AVAILABLE else 'MISSING'}")
    print(f"    Garment Model:      {'OK' if GARMENT_MODEL_AVAILABLE else 'MISSING'}")
    print(f"    Fit Analysis:       {'OK' if FIT_ANALYSIS_AVAILABLE else 'MISSING'}")
    print(f"    Pattern Generation: {'OK' if PATTERN_GENERATOR_AVAILABLE else 'MISSING'}")
    print("\n  New v3 Endpoints:")
    print("    POST /api/mesh/upload/body       - Upload 3D body scan")
    print("    POST /api/mesh/upload/garment    - Upload 3D garment scan")
    print("    POST /api/analysis/fit           - Run fit analysis")
    print("    POST /api/patterns/generate      - Generate pattern pieces")
    print("    POST /api/workflow/analyze-and-generate - Full pipeline")
    print("\n  Legacy v2 Endpoints:")
    print("    GET  /api/health                 - Health check")
    print("    POST /api/calibrate              - ArUco calibration")
    print("    GET  /api/calibration-card       - Download ArUco card")
    print("    POST /api/measure/garment        - 2D garment detection")
    print("\n" + "=" * 60 + "\n")


if __name__ == '__main__':
    print_startup_message()
    app.run(host=HOST, port=PORT, debug=True)
