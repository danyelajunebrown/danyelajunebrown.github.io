const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const cors = require('cors');
const { spawn } = require('child_process');

const app = express();
app.use(cors());
app.use(express.json());

const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Store active streams
const activeStreams = new Map();

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'ok', activeStreams: activeStreams.size });
});

// Start streaming endpoint - receives stream key
app.post('/start-stream', (req, res) => {
    const { streamKey, clientId } = req.body;

    if (!streamKey) {
        return res.status(400).json({ error: 'Stream key required' });
    }

    // Store stream key for this client
    const streamInfo = activeStreams.get(clientId) || {};
    streamInfo.streamKey = streamKey;
    streamInfo.rtmpUrl = `rtmp://a.rtmp.youtube.com/live2/${streamKey}`;
    activeStreams.set(clientId, streamInfo);

    res.json({ success: true, clientId });
});

// Stop streaming endpoint
app.post('/stop-stream', (req, res) => {
    const { clientId } = req.body;

    const streamInfo = activeStreams.get(clientId);
    if (streamInfo && streamInfo.ffmpeg) {
        streamInfo.ffmpeg.stdin.end();
        streamInfo.ffmpeg.kill('SIGTERM');
    }
    activeStreams.delete(clientId);

    res.json({ success: true });
});

wss.on('connection', (ws, req) => {
    // Extract client ID from query string
    const url = new URL(req.url, 'http://localhost');
    const clientId = url.searchParams.get('clientId');

    console.log(`Client connected: ${clientId}`);

    let ffmpeg = null;

    ws.on('message', (data) => {
        const streamInfo = activeStreams.get(clientId);

        if (!streamInfo || !streamInfo.streamKey) {
            console.log('No stream key configured for client:', clientId);
            return;
        }

        // Initialize FFmpeg if not started
        if (!ffmpeg && !streamInfo.ffmpeg) {
            console.log('Starting FFmpeg for client:', clientId);

            ffmpeg = spawn('ffmpeg', [
                '-i', 'pipe:0',           // Input from stdin (WebM from browser)
                '-c:v', 'libx264',        // Video codec
                '-preset', 'veryfast',    // Fast encoding for live
                '-tune', 'zerolatency',   // Low latency
                '-c:a', 'aac',            // Audio codec
                '-ar', '44100',           // Audio sample rate
                '-b:a', '128k',           // Audio bitrate
                '-f', 'flv',              // Output format
                streamInfo.rtmpUrl        // YouTube RTMP endpoint
            ]);

            ffmpeg.stderr.on('data', (data) => {
                console.log(`FFmpeg: ${data}`);
            });

            ffmpeg.on('close', (code) => {
                console.log(`FFmpeg exited with code ${code}`);
                if (streamInfo) {
                    streamInfo.ffmpeg = null;
                }
            });

            ffmpeg.on('error', (err) => {
                console.error('FFmpeg error:', err);
            });

            streamInfo.ffmpeg = ffmpeg;
            activeStreams.set(clientId, streamInfo);
        }

        // Write video data to FFmpeg
        if (streamInfo.ffmpeg && streamInfo.ffmpeg.stdin.writable) {
            streamInfo.ffmpeg.stdin.write(data);
        }
    });

    ws.on('close', () => {
        console.log(`Client disconnected: ${clientId}`);
        const streamInfo = activeStreams.get(clientId);
        if (streamInfo && streamInfo.ffmpeg) {
            streamInfo.ffmpeg.stdin.end();
        }
    });

    ws.on('error', (err) => {
        console.error('WebSocket error:', err);
    });
});

const PORT = process.env.PORT || 3001;
server.listen(PORT, () => {
    console.log(`Relay server running on port ${PORT}`);
    console.log(`WebSocket endpoint: ws://localhost:${PORT}`);
});
