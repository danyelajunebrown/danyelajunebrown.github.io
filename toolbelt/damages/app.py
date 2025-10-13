# app.py - Main Flask Application
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import uuid
import json
from datetime import datetime
from pathlib import Path
import subprocess
import shutil
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from PIL import Image

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wear_analysis.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'data/raw'
app.config['PROCESSED_FOLDER'] = 'data/processed'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max

db = SQLAlchemy(app)

# Create directories
os.makedirs('data/raw/photogrammetry', exist_ok=True)
os.makedirs('data/processed/3d_models', exist_ok=True)
os.makedirs('data/processed/analysis_results', exist_ok=True)
os.makedirs('static/uploads', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# Database Models
class CaptureSession(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(50), nullable=False)
    object_type = db.Column(db.String(50), nullable=False)
    brand = db.Column(db.String(50))
    model = db.Column(db.String(50))
    age_months = db.Column(db.Integer)
    damage_severity = db.Column(db.Integer)
    damage_types = db.Column(db.Text)
    num_photos = db.Column(db.Integer)
    processing_status = db.Column(db.String(20), default='pending')
    notes = db.Column(db.Text)

class ProcessedModel(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey('capture_session.id'))
    model_path = db.Column(db.String(255))
    mesh_vertices = db.Column(db.Integer)
    mesh_faces = db.Column(db.Integer)
    surface_area_mm2 = db.Column(db.Float)
    processing_time_minutes = db.Column(db.Float)
    quality_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class WearAnalysis(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id = db.Column(db.String(36), db.ForeignKey('processed_model.id'))
    wear_percentage = db.Column(db.Float)
    critical_points = db.Column(db.Text)
    predicted_failure_days = db.Column(db.Integer)
    recommendations = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StainAnalysis(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey('capture_session.id'))
    stain_type = db.Column(db.String(50))
    area_mm2 = db.Column(db.Float)
    location = db.Column(db.String(100))
    color_change_percentage = db.Column(db.Float)
    removability = db.Column(db.String(20))
    treatment_recommendations = db.Column(db.Text)
    before_cleaning_path = db.Column(db.String(255))
    after_cleaning_path = db.Column(db.String(255))
    cleaning_effectiveness = db.Column(db.Float)

# API Routes
@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/upload')
def upload_page():
    return render_template('upload.html')

@app.route('/api/upload', methods=['POST'])
def upload_photos():
    if 'photos' not in request.files:
        return jsonify({'error': 'No photos provided'}), 400
    
    files = request.files.getlist('photos')
    metadata = json.loads(request.form.get('metadata', '{}'))
    
    session_id = str(uuid.uuid4())
    timestamp = datetime.now()
    
    date_str = timestamp.strftime('%Y-%m-%d')
    session_folder = f"data/raw/photogrammetry/{date_str}/{session_id}"
    images_folder = f"{session_folder}/images"
    os.makedirs(images_folder, exist_ok=True)
    
    saved_files = []
    for i, file in enumerate(files):
        if file.filename:
            filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{metadata.get('category', 'unknown')}_{i:03d}.jpg"
            filepath = os.path.join(images_folder, filename)
            file.save(filepath)
            saved_files.append(filepath)
    
    session_metadata = {
        "session_id": session_id,
        "timestamp": timestamp.isoformat(),
        "category": metadata.get('category', 'unknown'),
        "object": {
            "type": metadata.get('object_type', ''),
            "brand": metadata.get('brand', ''),
            "model": metadata.get('model', ''),
            "age_months": metadata.get('age_months', 0),
        },
        "damage_assessment": {
            "severity": metadata.get('damage_severity', 5),
            "type": metadata.get('damage_types', []),
            "location": metadata.get('damage_location', ''),
        },
        "num_photos": len(saved_files),
        "notes": metadata.get('notes', '')
    }
    
    with open(f"{session_folder}/metadata.json", 'w') as f:
        json.dump(session_metadata, f, indent=2)
    
    session = CaptureSession(
        id=session_id,
        timestamp=timestamp,
        category=metadata.get('category', 'unknown'),
        object_type=metadata.get('object_type', ''),
        brand=metadata.get('brand', ''),
        model=metadata.get('model', ''),
        age_months=metadata.get('age_months', 0),
        damage_severity=metadata.get('damage_severity', 5),
        damage_types=json.dumps(metadata.get('damage_types', [])),
        num_photos=len(saved_files),
        notes=metadata.get('notes', '')
    )
    db.session.add(session)
    db.session.commit()
    
    process_session_async(session_id, images_folder)
    
    return jsonify({
        'session_id': session_id,
        'message': f'Uploaded {len(saved_files)} photos successfully',
        'processing_status': 'started'
    })

def process_session_async(session_id, images_folder):
    try:
        session = CaptureSession.query.get(session_id)
        session.processing_status = 'processing'
        db.session.commit()
        
        workspace = f"data/processed/3d_models/{session_id}"
        os.makedirs(workspace, exist_ok=True)
        
        start_time = datetime.now()
        
        cmd = [
            'colmap', 'automatic_reconstructor',
            '--image_path', images_folder,
            '--workspace_path', workspace,
            '--camera_model', 'PINHOLE'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        processing_time = (datetime.now() - start_time).total_seconds() / 60.0
        
        if result.returncode == 0:
            model_path = find_model_file(workspace)
            if model_path:
                model = ProcessedModel(
                    session_id=session_id,
                    model_path=model_path,
                    processing_time_minutes=processing_time,
                    quality_score=0.85
                )
                db.session.add(model)
                
                run_wear_analysis(model.id, model_path)
                
                session.processing_status = 'completed'
            else:
                session.processing_status = 'failed'
        else:
            session.processing_status = 'failed'
        
        db.session.commit()
        
    except Exception as e:
        session.processing_status = 'error'
        db.session.commit()
        print(f"Processing error: {e}")

def find_model_file(workspace):
    for root, dirs, files in os.walk(workspace):
        for file in files:
            if file.endswith('.ply'):
                return os.path.join(root, file)
    return None

def run_wear_analysis(model_id, model_path):
    analysis = WearAnalysis(
        model_id=model_id,
        wear_percentage=0.25,
        critical_points=json.dumps([
            {"location": [12.3, 4.5, 1.2], "severity": 8},
            {"location": [15.1, 6.2, 0.8], "severity": 6}
        ]),
        predicted_failure_days=45,
        recommendations=json.dumps([
            "Apply reinforcement patch at heel area",
            "Consider protective spray for fabric areas"
        ])
    )
    db.session.add(analysis)

@app.route('/api/sessions')
def get_sessions():
    sessions = CaptureSession.query.order_by(CaptureSession.timestamp.desc()).all()
    return jsonify([{
        'id': s.id,
        'timestamp': s.timestamp.isoformat(),
        'category': s.category,
        'object_type': s.object_type,
        'brand': s.brand,
        'damage_severity': s.damage_severity,
        'processing_status': s.processing_status,
        'num_photos': s.num_photos
    } for s in sessions])

@app.route('/api/session/<session_id>')
def get_session_details(session_id):
    session = CaptureSession.query.get_or_404(session_id)
    model = ProcessedModel.query.filter_by(session_id=session_id).first()
    analysis = None
    if model:
        analysis = WearAnalysis.query.filter_by(model_id=model.id).first()
    
    return jsonify({
        'session': {
            'id': session.id,
            'timestamp': session.timestamp.isoformat(),
            'category': session.category,
            'object_type': session.object_type,
            'brand': session.brand,
            'processing_status': session.processing_status,
            'notes': session.notes
        },
        'model': {
            'id': model.id if model else None,
            'quality_score': model.quality_score if model else None,
            'processing_time': model.processing_time_minutes if model else None
        } if model else None,
        'analysis': {
            'wear_percentage': analysis.wear_percentage if analysis else None,
            'predicted_failure_days': analysis.predicted_failure_days if analysis else None,
            'recommendations': json.loads(analysis.recommendations) if analysis and analysis.recommendations else []
        } if analysis else None
    })

@app.route('/viewer/<session_id>')
def model_viewer(session_id):
    return render_template('viewer.html', session_id=session_id)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
