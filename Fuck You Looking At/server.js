/**
 * Server API for Gaze Detection Study
 * Receives and stores pseudonymized data from browser extension
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const { Pool } = require('pg');
const crypto = require('crypto');

const app = express();
const port = process.env.PORT || 3000;

// Database connection
const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'gaze_study',
  user: process.env.DB_USER || 'gaze_admin',
  password: process.env.DB_PASSWORD,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Middleware
app.use(helmet());
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || ['chrome-extension://*'],
  methods: ['POST', 'GET'],
  credentials: true
}));
app.use(express.json({ limit: '10mb' }));

// Rate limiting
const uploadLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 100, // Max 100 uploads per hour per IP
  message: { success: false, error: 'Too many upload requests' }
});

// Logging middleware
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
  next();
});

// Health check
app.get('/health', async (req, res) => {
  try {
    // Check database connection
    await pool.query('SELECT 1');
    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      database: 'connected'
    });
  } catch (error) {
    res.status(500).json({
      status: 'unhealthy',
      error: 'Database connection failed'
    });
  }
});

// Upload endpoint
app.post('/api/upload', uploadLimiter, async (req, res) => {
  const { participantId, batchId, eventCount, events } = req.body;
  
  // Validation
  if (!participantId || !batchId || !events || !Array.isArray(events)) {
    return res.status(400).json({
      success: false,
      error: 'Invalid request format'
    });
  }
  
  // Verify participant exists
  const participantExists = await verifyParticipant(participantId);
  if (!participantExists) {
    return res.status(403).json({
      success: false,
      error: 'Invalid participant ID'
    });
  }
  
  // Check for duplicate batch
  const isDuplicate = await checkDuplicateBatch(batchId);
  if (isDuplicate) {
    return res.json({
      success: true,
      message: 'Batch already processed',
      batchId: batchId
    });
  }
  
  const client = await pool.connect();
  
  try {
    await client.query('BEGIN');
    
    // Store batch metadata
    await client.query(
      `INSERT INTO upload_batches 
       (batch_id, participant_id, event_count, uploaded_at, ip_address) 
       VALUES ($1, $2, $3, NOW(), $4)`,
      [batchId, participantId, eventCount, req.ip]
    );
    
    // Store events
    for (const event of events) {
      // Validate event structure
      if (!validateEvent(event)) {
        throw new Error('Invalid event structure');
      }
      
      await client.query(
        `INSERT INTO events 
         (event_id, participant_id, batch_id, timestamp, 
          face_gaze_direction, gaze_on_face, distance_from_face,
          pupil_diameter, pupil_baseline, blink_event,
          context, url_domain, confidence_score, event_data)
         VALUES ($1, $2, $3, to_timestamp($4 / 1000.0), $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)`,
        [
          event.eventId,
          participantId,
          batchId,
          event.timestamp,
          event.faceGazeDirection,
          event.gazeOnFace,
          event.distanceFromFace,
          event.pupilDiameter,
          event.pupilBaseline,
          event.blinkEvent,
          event.context,
          event.url,
          event.confidenceScore,
          JSON.stringify(event) // Store full event for analysis
        ]
      );
    }
    
    // Update participant statistics
    await client.query(
      `UPDATE participants 
       SET total_events = total_events + $1,
           last_upload = NOW()
       WHERE participant_id = $2`,
      [eventCount, participantId]
    );
    
    await client.query('COMMIT');
    
    console.log(`Batch ${batchId} processed: ${eventCount} events from ${participantId}`);
    
    res.json({
      success: true,
      received: eventCount,
      batchId: batchId,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    await client.query('ROLLBACK');
    console.error('Upload error:', error);
    
    res.status(500).json({
      success: false,
      error: 'Failed to process upload'
    });
  } finally {
    client.release();
  }
});

// Participant registration (called during onboarding)
app.post('/api/register', async (req, res) => {
  const { participantId, consentTimestamp } = req.body;
  
  if (!participantId || !consentTimestamp) {
    return res.status(400).json({
      success: false,
      error: 'Invalid registration data'
    });
  }
  
  try {
    await pool.query(
      `INSERT INTO participants 
       (participant_id, consent_timestamp, registered_at, total_events)
       VALUES ($1, to_timestamp($2 / 1000.0), NOW(), 0)
       ON CONFLICT (participant_id) DO NOTHING`,
      [participantId, consentTimestamp]
    );
    
    res.json({
      success: true,
      participantId: participantId
    });
    
  } catch (error) {
    console.error('Registration error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to register participant'
    });
  }
});

// Withdrawal endpoint (delete all data for participant)
app.post('/api/withdraw', async (req, res) => {
  const { participantId, confirmationToken } = req.body;
  
  if (!participantId || !confirmationToken) {
    return res.status(400).json({
      success: false,
      error: 'Invalid withdrawal request'
    });
  }
  
  // Verify confirmation token (simple hash of participant ID + secret)
  const expectedToken = crypto
    .createHash('sha256')
    .update(participantId + process.env.WITHDRAWAL_SECRET)
    .digest('hex');
  
  if (confirmationToken !== expectedToken) {
    return res.status(403).json({
      success: false,
      error: 'Invalid confirmation token'
    });
  }
  
  const client = await pool.connect();
  
  try {
    await client.query('BEGIN');
    
    // Delete all events
    const eventsResult = await client.query(
      'DELETE FROM events WHERE participant_id = $1',
      [participantId]
    );
    
    // Delete all batches
    await client.query(
      'DELETE FROM upload_batches WHERE participant_id = $1',
      [participantId]
    );
    
    // Delete participant record
    await client.query(
      'DELETE FROM participants WHERE participant_id = $1',
      [participantId]
    );
    
    await client.query('COMMIT');
    
    console.log(`Participant ${participantId} withdrawn: ${eventsResult.rowCount} events deleted`);
    
    res.json({
      success: true,
      message: 'All data permanently deleted',
      eventsDeleted: eventsResult.rowCount
    });
    
  } catch (error) {
    await client.query('ROLLBACK');
    console.error('Withdrawal error:', error);
    
    res.status(500).json({
      success: false,
      error: 'Failed to process withdrawal'
    });
  } finally {
    client.release();
  }
});

// Statistics endpoint (for research team only)
app.get('/api/stats', requireAuth, async (req, res) => {
  try {
    const stats = await pool.query(`
      SELECT 
        COUNT(DISTINCT participant_id) as total_participants,
        COUNT(*) as total_events,
        SUM(CASE WHEN face_gaze_direction = 'toward_camera' THEN 1 ELSE 0 END) as looking_events,
        SUM(CASE WHEN face_gaze_direction = 'away' THEN 1 ELSE 0 END) as not_looking_events,
        AVG(pupil_diameter) as avg_pupil_diameter,
        AVG(distance_from_face) as avg_distance
      FROM events
    `);
    
    res.json({
      success: true,
      statistics: stats.rows[0]
    });
    
  } catch (error) {
    console.error('Stats error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve statistics'
    });
  }
});

// Helper functions

async function verifyParticipant(participantId) {
  const result = await pool.query(
    'SELECT 1 FROM participants WHERE participant_id = $1',
    [participantId]
  );
  return result.rows.length > 0;
}

async function checkDuplicateBatch(batchId) {
  const result = await pool.query(
    'SELECT 1 FROM upload_batches WHERE batch_id = $1',
    [batchId]
  );
  return result.rows.length > 0;
}

function validateEvent(event) {
  // Ensure critical fields are present and valid
  const required = [
    'eventId',
    'timestamp',
    'faceGazeDirection',
    'gazeOnFace',
    'distanceFromFace'
  ];
  
  for (const field of required) {
    if (!(field in event)) {
      console.error(`Missing field: ${field}`);
      return false;
    }
  }
  
  // Validate gazeOnFace is always false (critical filter)
  if (event.gazeOnFace !== false) {
    console.error('Invalid event: gazeOnFace must be false');
    return false;
  }
  
  // Validate faceGazeDirection
  if (!['toward_camera', 'away'].includes(event.faceGazeDirection)) {
    console.error('Invalid faceGazeDirection:', event.faceGazeDirection);
    return false;
  }
  
  return true;
}

// Simple auth middleware (for admin/research endpoints)
function requireAuth(req, res, next) {
  const apiKey = req.headers['x-api-key'];
  
  if (!apiKey || apiKey !== process.env.API_KEY) {
    return res.status(401).json({
      success: false,
      error: 'Unauthorized'
    });
  }
  
  next();
}

// Error handling
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({
    success: false,
    error: 'Internal server error'
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: 'Endpoint not found'
  });
});

// Start server
app.listen(port, () => {
  console.log(`Gaze Study API server running on port ${port}`);
  console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, closing server...');
  await pool.end();
  process.exit(0);
});

module.exports = app;
