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
    res.json({
        status: 'ok',
        activeStreams: activeStreams.size,
        uptime: Math.round(process.uptime()),
        streams: Array.from(activeStreams.entries()).map(([id, info]) => ({
            clientId: id,
            hasAudio: info.hasAudio,
            mimeType: info.mimeType,
            bytesReceived: info.bytesReceived,
            chunksReceived: info.chunksReceived,
            ffmpegRunning: !!(info.ffmpeg && !info.ffmpeg.killed),
            startedAt: info.startedAt
        }))
    });
});

// Debug endpoint for a specific client
app.get('/debug/:clientId', (req, res) => {
    const info = activeStreams.get(req.params.clientId);
    if (!info) {
        return res.status(404).json({ error: 'No stream found for this client' });
    }
    res.json({
        clientId: req.params.clientId,
        hasAudio: info.hasAudio,
        mimeType: info.mimeType,
        bytesReceived: info.bytesReceived,
        chunksReceived: info.chunksReceived,
        ffmpegRunning: !!(info.ffmpeg && !info.ffmpeg.killed),
        ffmpegLogs: info.ffmpegLogs.slice(-20), // last 20 log lines
        startedAt: info.startedAt
    });
});

// Determine FFmpeg input format from browser mimeType
function getInputFormat(mimeType) {
    if (!mimeType) return 'mp4';
    if (mimeType.includes('webm')) return 'webm';
    if (mimeType.includes('mp4')) return 'mp4';
    return 'mp4';
}

// Start streaming endpoint
app.post('/start-stream', (req, res) => {
    const { streamKey, clientId, mimeType, hasAudio } = req.body;

    if (!streamKey) {
        return res.status(400).json({ error: 'Stream key required' });
    }

    // Kill any existing stream for this client
    const existing = activeStreams.get(clientId);
    if (existing && existing.ffmpeg) {
        console.log(`[${clientId}] Killing existing FFmpeg`);
        try {
            existing.ffmpeg.stdin.end();
            existing.ffmpeg.kill('SIGTERM');
        } catch (e) {}
    }

    const streamInfo = {
        streamKey,
        rtmpUrl: `rtmp://a.rtmp.youtube.com/live2/${streamKey}`,
        mimeType: mimeType || 'video/mp4',
        hasAudio: !!hasAudio,
        ffmpeg: null,
        bytesReceived: 0,
        chunksReceived: 0,
        ffmpegLogs: [],
        startedAt: new Date().toISOString()
    };
    activeStreams.set(clientId, streamInfo);

    console.log(`[${clientId}] Stream registered`);
    console.log(`  RTMP: ${streamInfo.rtmpUrl}`);
    console.log(`  mimeType: ${streamInfo.mimeType}`);
    console.log(`  hasAudio: ${streamInfo.hasAudio}`);

    res.json({ success: true, clientId });
});

// Stop streaming endpoint
app.post('/stop-stream', (req, res) => {
    const { clientId } = req.body;

    const streamInfo = activeStreams.get(clientId);
    if (streamInfo) {
        console.log(`[${clientId}] Stop requested — received ${streamInfo.chunksReceived} chunks (${formatBytes(streamInfo.bytesReceived)})`);
        if (streamInfo.ffmpeg) {
            try {
                streamInfo.ffmpeg.stdin.end();
                streamInfo.ffmpeg.kill('SIGTERM');
            } catch (e) {}
        }
    }
    activeStreams.delete(clientId);

    res.json({ success: true });
});

// Build FFmpeg arguments based on stream configuration
function buildFFmpegArgs(streamInfo) {
    const inputFormat = getInputFormat(streamInfo.mimeType);
    const args = [];

    // Input: piped video (+ possibly audio) from browser
    args.push(
        '-probesize', '2M',
        '-analyzeduration', '2M',
        '-f', inputFormat,
        '-i', 'pipe:0'
    );

    if (!streamInfo.hasAudio) {
        // No audio from browser — generate silent audio (YouTube requires audio)
        args.push(
            '-f', 'lavfi',
            '-i', 'anullsrc=r=44100:cl=stereo'
        );
    }

    // Video encoding
    args.push(
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-tune', 'zerolatency',
        '-g', '60',
        '-keyint_min', '60',
        '-b:v', '2500k',
        '-maxrate', '2500k',
        '-bufsize', '5000k'
    );

    // Audio encoding
    args.push(
        '-c:a', 'aac',
        '-ar', '44100',
        '-b:a', '128k'
    );

    if (!streamInfo.hasAudio) {
        // Map video from input 0, audio from input 1 (silent)
        args.push(
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-shortest'
        );
    }
    // When hasAudio=true, FFmpeg auto-maps the single input's video+audio tracks

    // Output
    args.push(
        '-f', 'flv',
        streamInfo.rtmpUrl
    );

    return args;
}

wss.on('connection', (ws, req) => {
    const url = new URL(req.url, 'http://localhost');
    const clientId = url.searchParams.get('clientId');

    console.log(`[${clientId}] WebSocket connected`);

    ws.on('message', (data) => {
        const streamInfo = activeStreams.get(clientId);

        if (!streamInfo || !streamInfo.streamKey) {
            console.log(`[${clientId}] No stream key configured — dropping data`);
            return;
        }

        // Track stats
        streamInfo.bytesReceived += data.length;
        streamInfo.chunksReceived++;

        if (streamInfo.chunksReceived % 30 === 0) {
            console.log(`[${clientId}] ${streamInfo.chunksReceived} chunks, ${formatBytes(streamInfo.bytesReceived)} total`);
        }

        // Initialize FFmpeg on first data
        if (!streamInfo.ffmpeg) {
            const ffmpegArgs = buildFFmpegArgs(streamInfo);
            console.log(`[${clientId}] Starting FFmpeg:`);
            console.log(`  ffmpeg ${ffmpegArgs.join(' ')}`);

            const ffmpeg = spawn('ffmpeg', ffmpegArgs);

            ffmpeg.stderr.on('data', (chunk) => {
                const line = chunk.toString().trim();
                if (line) {
                    // Store recent logs for debug endpoint
                    streamInfo.ffmpegLogs.push(line);
                    if (streamInfo.ffmpegLogs.length > 100) {
                        streamInfo.ffmpegLogs.shift();
                    }
                    // Log important lines (skip progress spam)
                    if (!line.startsWith('frame=') && !line.startsWith('size=')) {
                        console.log(`[${clientId}] FFmpeg: ${line}`);
                    }
                }
            });

            ffmpeg.on('close', (code) => {
                console.log(`[${clientId}] FFmpeg exited with code ${code}`);
                streamInfo.ffmpeg = null;
            });

            ffmpeg.on('error', (err) => {
                console.error(`[${clientId}] FFmpeg spawn error: ${err.message}`);
                streamInfo.ffmpegLogs.push('SPAWN ERROR: ' + err.message);
            });

            streamInfo.ffmpeg = ffmpeg;
        }

        // Write data to FFmpeg stdin
        if (streamInfo.ffmpeg && streamInfo.ffmpeg.stdin && streamInfo.ffmpeg.stdin.writable) {
            const ok = streamInfo.ffmpeg.stdin.write(data);
            if (!ok) {
                // Backpressure — FFmpeg can't keep up
                if (streamInfo.chunksReceived % 50 === 0) {
                    console.warn(`[${clientId}] FFmpeg stdin backpressure`);
                }
            }
        } else {
            if (streamInfo.chunksReceived % 50 === 0) {
                console.warn(`[${clientId}] FFmpeg stdin not writable`);
            }
        }
    });

    ws.on('close', () => {
        console.log(`[${clientId}] WebSocket disconnected`);
        const streamInfo = activeStreams.get(clientId);
        if (streamInfo) {
            console.log(`[${clientId}] Final: ${streamInfo.chunksReceived} chunks, ${formatBytes(streamInfo.bytesReceived)}`);
            if (streamInfo.ffmpeg) {
                try {
                    streamInfo.ffmpeg.stdin.end();
                    streamInfo.ffmpeg.kill('SIGTERM');
                } catch (e) {}
                streamInfo.ffmpeg = null;
            }
        }
        activeStreams.delete(clientId);
    });

    ws.on('error', (err) => {
        console.error(`[${clientId}] WebSocket error: ${err.message}`);
    });
});

function formatBytes(b) {
    if (b < 1024) return b + ' B';
    if (b < 1048576) return (b / 1024).toFixed(1) + ' KB';
    return (b / 1048576).toFixed(1) + ' MB';
}

const PORT = process.env.PORT || 3001;
server.listen(PORT, () => {
    console.log(`Relay server running on port ${PORT}`);
    console.log(`HTTP: http://localhost:${PORT}`);
    console.log(`WebSocket: ws://localhost:${PORT}`);
});
