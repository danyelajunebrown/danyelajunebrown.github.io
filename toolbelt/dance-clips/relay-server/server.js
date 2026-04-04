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
    // Use larger probesize for fragmented MP4 — audio track metadata may come late
    args.push(
        '-probesize', '5M',
        '-analyzeduration', '5M',
        '-fflags', '+genpts+discardcorrupt',
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

    // Video: COPY — phone already encodes H.264, just remux to FLV
    // Re-encoding was causing 0.52x speed on the droplet, leading to buffer overflow after ~10min
    args.push('-c:v', 'copy');

    // Audio: re-encode to AAC 44100Hz (cheap, ensures YouTube compatibility)
    args.push(
        '-c:a', 'aac',
        '-ar', '44100',
        '-b:a', '128k'
    );

    if (streamInfo.hasAudio) {
        // EXPLICIT mapping — don't let FFmpeg guess
        // Note: iOS MP4 puts audio as stream 0, video as stream 1
        args.push(
            '-map', '0:v:0',
            '-map', '0:a:0'
        );
    } else {
        // Map video from input 0, silent audio from input 1
        args.push(
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-shortest'
        );
    }

    // Output
    args.push(
        '-f', 'flv',
        streamInfo.rtmpUrl
    );

    return args;
}

// Alternate FFmpeg args: if the muxed input has no audio track, use anullsrc fallback
function buildFFmpegArgsFallback(streamInfo) {
    const inputFormat = getInputFormat(streamInfo.mimeType);
    const args = [];

    args.push(
        '-probesize', '5M',
        '-analyzeduration', '5M',
        '-fflags', '+genpts+discardcorrupt',
        '-f', inputFormat,
        '-i', 'pipe:0',
        // Silent audio fallback
        '-f', 'lavfi',
        '-i', 'anullsrc=r=44100:cl=stereo'
    );

    args.push(
        '-c:v', 'copy',  // passthrough — no re-encoding
        '-c:a', 'aac',
        '-ar', '44100',
        '-b:a', '128k',
        '-map', '0:v:0',
        '-map', '1:a:0',
        '-shortest',
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
            function spawnFFmpeg(useFallback) {
                const label = useFallback ? 'FALLBACK (silent audio)' : 'PRIMARY (muxed audio)';
                const ffmpegArgs = useFallback
                    ? buildFFmpegArgsFallback(streamInfo)
                    : buildFFmpegArgs(streamInfo);

                console.log(`[${clientId}] Starting FFmpeg [${label}]:`);
                console.log(`  ffmpeg ${ffmpegArgs.join(' ')}`);

                const ffmpeg = spawn('ffmpeg', ffmpegArgs);

                ffmpeg.stderr.on('data', (chunk) => {
                    const line = chunk.toString().trim();
                    if (line) {
                        streamInfo.ffmpegLogs.push(line);
                        if (streamInfo.ffmpegLogs.length > 100) {
                            streamInfo.ffmpegLogs.shift();
                        }
                        // Log important lines (skip progress spam)
                        if (!line.startsWith('frame=') && !line.startsWith('size=')) {
                            console.log(`[${clientId}] FFmpeg: ${line}`);
                        }

                        // Detect audio mapping failure — retry with fallback
                        if (!useFallback && streamInfo.hasAudio &&
                            (line.includes('Stream map \'0:a:0\' matches no streams') ||
                             line.includes('Output file does not contain any stream'))) {
                            console.log(`[${clientId}] Audio track not found in input — retrying with silent audio fallback`);
                            streamInfo.ffmpegLogs.push('>>> RETRYING WITH SILENT AUDIO FALLBACK');
                            try { ffmpeg.kill('SIGTERM'); } catch(e) {}
                            // Respawn with fallback after a short delay
                            setTimeout(() => {
                                streamInfo.ffmpeg = spawnFFmpeg(true);
                                // Re-feed buffered data if we have it
                                if (streamInfo.initialBuffer && streamInfo.initialBuffer.length > 0) {
                                    console.log(`[${clientId}] Re-feeding ${streamInfo.initialBuffer.length} buffered chunks`);
                                    streamInfo.initialBuffer.forEach(buf => {
                                        if (streamInfo.ffmpeg && streamInfo.ffmpeg.stdin && streamInfo.ffmpeg.stdin.writable) {
                                            streamInfo.ffmpeg.stdin.write(buf);
                                        }
                                    });
                                }
                            }, 200);
                        }
                    }
                });

                ffmpeg.on('close', (code) => {
                    console.log(`[${clientId}] FFmpeg [${label}] exited with code ${code}`);
                    if (streamInfo.ffmpeg === ffmpeg) {
                        streamInfo.ffmpeg = null;
                    }
                });

                ffmpeg.on('error', (err) => {
                    console.error(`[${clientId}] FFmpeg spawn error: ${err.message}`);
                    streamInfo.ffmpegLogs.push('SPAWN ERROR: ' + err.message);
                });

                // Prevent EPIPE crash — if FFmpeg dies, don't let stdin write crash Node
                ffmpeg.stdin.on('error', (err) => {
                    if (err.code === 'EPIPE') {
                        console.warn(`[${clientId}] FFmpeg stdin EPIPE (FFmpeg exited) — ignoring`);
                    } else {
                        console.error(`[${clientId}] FFmpeg stdin error: ${err.message}`);
                    }
                });

                return ffmpeg;
            }

            // Buffer initial chunks so we can re-feed on fallback retry
            if (streamInfo.hasAudio) {
                streamInfo.initialBuffer = [];
            }

            streamInfo.ffmpeg = spawnFFmpeg(false);
        }

        // Buffer first few chunks for potential fallback retry
        if (streamInfo.initialBuffer && streamInfo.chunksReceived <= 10) {
            streamInfo.initialBuffer.push(Buffer.from(data));
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
