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
    const { streamKey, clientId, mimeType, hasAudio } = req.body;

    if (!streamKey) {
        return res.status(400).json({ error: 'Stream key required' });
    }

    // Kill any existing stream for this client
    const existingStream = activeStreams.get(clientId);
    if (existingStream && existingStream.ffmpeg) {
        console.log(`Killing existing FFmpeg for client: ${clientId}`);
        existingStream.ffmpeg.stdin.end();
        existingStream.ffmpeg.kill('SIGTERM');
    }

    // Determine input format based on mimeType
    let inputFormat = 'webm';
    if (mimeType && mimeType.includes('mp4')) {
        inputFormat = 'mp4';
    }

    // Create fresh stream info
    // hasAudio: true means the incoming stream already contains audio (don't add silent)
    const streamInfo = {
        streamKey: streamKey,
        rtmpUrl: `rtmp://a.rtmp.youtube.com/live2/${streamKey}`,
        inputFormat: inputFormat,
        hasAudio: hasAudio || false,
        ffmpeg: null
    };
    activeStreams.set(clientId, streamInfo);

    console.log(`Stream registered for ${clientId}: ${streamInfo.rtmpUrl} (format: ${inputFormat}, hasAudio: ${streamInfo.hasAudio}, mimeType: ${mimeType})`);
    res.json({ success: true, clientId, hasAudio: streamInfo.hasAudio });
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
            console.log(`Starting FFmpeg for ${clientId} -> ${streamInfo.rtmpUrl}`);
            console.log(`hasAudio: ${streamInfo.hasAudio}, inputFormat: ${streamInfo.inputFormat}`);

            const inputFormat = streamInfo.inputFormat || 'webm';

            let ffmpegArgs;

            if (streamInfo.hasAudio) {
                // Stream already has audio - just transcode and forward
                console.log('Using real audio from stream');
                ffmpegArgs = [
                    '-f', inputFormat,
                    '-i', 'pipe:0',
                    '-c:v', 'libx264',
                    '-preset', 'veryfast',
                    '-tune', 'zerolatency',
                    '-g', '60',
                    '-keyint_min', '60',
                    '-c:a', 'aac',
                    '-ar', '44100',
                    '-b:a', '128k',
                    '-f', 'flv',
                    streamInfo.rtmpUrl
                ];
            } else {
                // No audio - add silent audio for YouTube
                console.log('Adding silent audio (no audio in stream)');
                ffmpegArgs = [
                    '-f', inputFormat,
                    '-i', 'pipe:0',
                    '-f', 'lavfi',
                    '-i', 'anullsrc=r=44100:cl=stereo',
                    '-c:v', 'libx264',
                    '-preset', 'veryfast',
                    '-tune', 'zerolatency',
                    '-g', '60',
                    '-keyint_min', '60',
                    '-c:a', 'aac',
                    '-ar', '44100',
                    '-b:a', '128k',
                    '-map', '0:v:0',
                    '-map', '1:a:0',
                    '-shortest',
                    '-f', 'flv',
                    streamInfo.rtmpUrl
                ];
            }

            ffmpeg = spawn('ffmpeg', ffmpegArgs);

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

        // Write data to FFmpeg
        if (streamInfo.ffmpeg && streamInfo.ffmpeg.stdin.writable) {
            streamInfo.ffmpeg.stdin.write(data);
        }
    });

    ws.on('close', () => {
        console.log(`Client disconnected: ${clientId}`);

        const streamInfo = activeStreams.get(clientId);
        if (streamInfo && streamInfo.ffmpeg) {
            streamInfo.ffmpeg.stdin.end();
            streamInfo.ffmpeg.kill('SIGTERM');
            streamInfo.ffmpeg = null;
        }
        activeStreams.delete(clientId);
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
