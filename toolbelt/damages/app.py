"""
# app.py - Cloud Flask Application (for Render)
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import uuid
import json
from datetime import datetime
from werkzeug.utils import secure_filename
import boto3
from PIL import Image
import io

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///damages.db').replace('postgres://', 'postgresql://')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['WORKER_API_KEY'] = os.environ.get('WORKER_API_KEY', 'change-this-key')

# AWS S3 for photo storage
app.config['S3_BUCKET'] = os.environ.get('S3_BUCKET')
app.config['S3_KEY'] = os.environ.get('AWS_ACCESS_KEY_ID')
app.config['S3_SECRET'] = os.environ.get('AWS_SECRET_ACCESS_KEY')
app.config['S3_REGION'] = os.environ.get('AWS_REGION', 'us-east-1')

db = SQLAlchemy(app)

# Database Models
class CaptureSession(db.Model):
    __tablename__ = 'capture_sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    category = db.Column(db.String(50), nullable=False)
    object_type = db.Column(db.String(50), nullable=False)
    brand = db.Column(db.String(50))
    model = db.Column(db.String(50))
    age_months = db.Column(db.Integer)
    damage_severity = db.Column(db.Integer)
    damage_types = db.Column(db.Text)
    num_photos = db.Column(db.Integer)
    processing_status = db.Column(db.String(20), default='pending', index=True)
    notes = db.Column(db.Text)
    photos_url = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'category': self.category,
            'object_type': self.object_type,
            'brand': self.brand,
            'model': self.model,
            'age_months': self.age_months,
            'damage_severity': self.damage_severity,
            'damage_types': json.loads(self.damage_types) if self.damage_types else [],
            'num_photos': self.num_photos,
            'processing_status': self.processing_status,
            'notes': self.notes,
            'photos_url': json.loads(self.photos_url) if self.photos_url else []
        }

class ProcessingJob(db.Model):
    __tablename__ = 'processing_jobs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey('capture_sessions.id'))
    status = db.Column(db.String(20), default='queued', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    worker_id = db.Column(db.String(100))
    error_message = db.Column(db.Text)
    result_data = db.Column(db.Text)

class WearAnalysis(db.Model):
    __tablename__ = 'wear_analysis'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey('capture_sessions.id'))
    wear_percentage = db.Column(db.Float)
    critical_points = db.Column(db.Text)
    predicted_failure_days = db.Column(db.Integer)
    recommendations = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Helper functions
def upload_to_s3(file_data, filename):
    if not app.config['S3_BUCKET']:
        return f"/uploads/{filename}"
    
    s3 = boto3.client(
        's3',
        aws_access_key_id=app.config['S3_KEY'],
        aws_secret_access_key=app.config['S3_SECRET'],
        region_name=app.config['S3_REGION']
    )
    
    s3.upload_fileobj(
        file_data,
        app.config['S3_BUCKET'],
        filename,
        ExtraArgs={'ContentType': 'image/jpeg'}
    )
    
    return f"https://{app.config['S3_BUCKET']}.s3.{app.config['S3_REGION']}.amazonaws.com/{filename}"

# Routes
@app.route('/')
def index():
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
    
    photo_urls = []
    for i, file in enumerate(files):
        if file.filename:
            img = Image.open(file)
            img.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)
            
            filename = f"{session_id}/{i:03d}.jpg"
            url = upload_to_s3(buffer, filename)
            photo_urls.append(url)
    
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
        num_photos=len(photo_urls),
        notes=metadata.get('notes', ''),
        photos_url=json.dumps(photo_urls)
    )
    db.session.add(session)
    
    job = ProcessingJob(
        session_id=session_id,
        status='queued'
    )
    db.session.add(job)
    db.session.commit()
    
    return jsonify({
        'session_id': session_id,
        'message': f'Uploaded {len(photo_urls)} photos successfully',
        'processing_status': 'queued'
    })

@app.route('/api/sessions')
def get_sessions():
    sessions = CaptureSession.query.order_by(CaptureSession.timestamp.desc()).limit(100).all()
    return jsonify([s.to_dict() for s in sessions])

@app.route('/api/session/<session_id>')
def get_session_details(session_id):
    session = CaptureSession.query.get_or_404(session_id)
    analysis = WearAnalysis.query.filter_by(session_id=session_id).first()
    job = ProcessingJob.query.filter_by(session_id=session_id).first()
    
    return jsonify({
        'session': session.to_dict(),
        'analysis': {
            'wear_percentage': analysis.wear_percentage,
            'predicted_failure_days': analysis.predicted_failure_days,
            'recommendations': json.loads(analysis.recommendations) if analysis.recommendations else []
        } if analysis else None,
        'processing': {
            'status': job.status,
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'error': job.error_message
        } if job else None
    })

# Worker API endpoints
@app.route('/api/worker/jobs', methods=['GET'])
def get_pending_jobs():
    api_key = request.headers.get('X-API-Key')
    if api_key != app.config['WORKER_API_KEY']:
        return jsonify({'error': 'Unauthorized'}), 401
    
    jobs = ProcessingJob.query.filter_by(status='queued').order_by(ProcessingJob.created_at).limit(5).all()
    
    result = []
    for job in jobs:
        session = CaptureSession.query.get(job.session_id)
        result.append({
            'job_id': job.id,
            'session_id': job.session_id,
            'photos_url': json.loads(session.photos_url) if session.photos_url else [],
            'metadata': {
                'category': session.category,
                'object_type': session.object_type,
                'damage_severity': session.damage_severity
            }
        })
    
    return jsonify(result)

@app.route('/api/worker/jobs/<job_id>/start', methods=['POST'])
def start_job(job_id):
    api_key = request.headers.get('X-API-Key')
    if api_key != app.config['WORKER_API_KEY']:
        return jsonify({'error': 'Unauthorized'}), 401
    
    job = ProcessingJob.query.get_or_404(job_id)
    job.status = 'processing'
    job.started_at = datetime.utcnow()
    job.worker_id = request.json.get('worker_id', 'unknown')
    
    session = CaptureSession.query.get(job.session_id)
    session.processing_status = 'processing'
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/worker/jobs/<job_id>/complete', methods=['POST'])
def complete_job(job_id):
    api_key = request.headers.get('X-API-Key')
    if api_key != app.config['WORKER_API_KEY']:
        return jsonify({'error': 'Unauthorized'}), 401
    
    job = ProcessingJob.query.get_or_404(job_id)
    data = request.json
    
    job.status = 'completed'
    job.completed_at = datetime.utcnow()
    job.result_data = json.dumps(data.get('results', {}))
    
    session = CaptureSession.query.get(job.session_id)
    session.processing_status = 'completed'
    
    if 'analysis' in data:
        analysis = WearAnalysis(
            session_id=job.session_id,
            wear_percentage=data['analysis'].get('wear_percentage', 0),
            critical_points=json.dumps(data['analysis'].get('critical_points', [])),
            predicted_failure_days=data['analysis'].get('predicted_failure_days', 0),
            recommendations=json.dumps(data['analysis'].get('recommendations', []))
        )
        db.session.add(analysis)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/worker/jobs/<job_id>/fail', methods=['POST'])
def fail_job(job_id):
    api_key = request.headers.get('X-API-Key')
    if api_key != app.config['WORKER_API_KEY']:
        return jsonify({'error': 'Unauthorized'}), 401
    
    job = ProcessingJob.query.get_or_404(job_id)
    job.status = 'failed'
    job.completed_at = datetime.utcnow()
    job.error_message = request.json.get('error', 'Unknown error')
    
    session = CaptureSession.query.get(job.session_id)
    session.processing_status = 'failed'
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/viewer/<session_id>')
def viewer(session_id):
    return render_template('viewer.html', session_id=session_id)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)


"""
