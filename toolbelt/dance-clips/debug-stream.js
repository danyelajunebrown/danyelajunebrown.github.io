const puppeteer = require('puppeteer-core');

const PAGE_URL = 'https://danyelajunebrown.github.io/toolbelt/dance-clips/';

// Colors for console output
const colors = {
    reset: '\x1b[0m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    magenta: '\x1b[35m',
    cyan: '\x1b[36m'
};

function log(type, message, data = '') {
    const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
    const colorMap = {
        'CONSOLE': colors.cyan,
        'NETWORK': colors.blue,
        'ERROR': colors.red,
        'INFO': colors.green,
        'WARN': colors.yellow,
        'API': colors.magenta
    };
    const color = colorMap[type] || colors.reset;
    console.log(`${color}[${timestamp}] [${type}]${colors.reset} ${message}`, data ? data : '');
}

async function main() {
    log('INFO', 'Starting Puppeteer debug session...');
    log('INFO', 'Connecting to Chrome via remote debugging...');
    log('WARN', '');
    log('WARN', '===========================================');
    log('WARN', 'IMPORTANT: Chrome must be started with remote debugging enabled');
    log('WARN', 'If this fails, close all Chrome windows and run:');
    log('WARN', '');
    log('WARN', '/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\');
    log('WARN', '  --remote-debugging-port=9222');
    log('WARN', '===========================================');
    log('WARN', '');

    let browser;
    try {
        browser = await puppeteer.connect({
            browserURL: 'http://127.0.0.1:9222',
            defaultViewport: null
        });
        log('INFO', 'Connected to Chrome!');
    } catch (err) {
        log('ERROR', 'Could not connect to Chrome remote debugging.');
        log('ERROR', 'Please close all Chrome windows and restart Chrome with:');
        log('ERROR', '');
        log('ERROR', '/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222');
        log('ERROR', '');
        process.exit(1);
    }

    const page = await browser.newPage();
    log('INFO', 'New page created');

    // Capture ALL console messages
    page.on('console', msg => {
        const type = msg.type().toUpperCase();
        const text = msg.text();

        if (text.includes('Stream status:')) {
            log('CONSOLE', `>>> ${text}`, '<<<');
        } else if (text.includes('error') || text.includes('Error')) {
            log('ERROR', text);
        } else if (text.includes('Stream') || text.includes('stream')) {
            log('CONSOLE', text);
        } else {
            log('CONSOLE', text);
        }
    });

    // Capture network requests
    page.on('request', request => {
        const url = request.url();
        if (url.includes('youtube.com/youtube/v3') || url.includes('dance.danyelica.fish')) {
            log('API', `>> ${request.method()} ${url.split('?')[0]}`);
        }
    });

    // Capture network responses
    page.on('response', async response => {
        const url = response.url();
        if (url.includes('youtube.com/youtube/v3')) {
            const status = response.status();
            const statusText = status >= 400 ? colors.red + status + colors.reset : colors.green + status + colors.reset;

            try {
                const body = await response.json();
                log('API', `<< ${statusText} ${url.split('?')[0]}`);

                if (url.includes('liveStreams') && body.items) {
                    const streamStatus = body.items[0]?.status;
                    if (streamStatus) {
                        log('API', `   Stream Status: ${JSON.stringify(streamStatus)}`);
                    }
                }
                if (url.includes('liveBroadcasts') && body.id) {
                    log('API', `   Broadcast ID: ${body.id}`);
                }
            } catch (e) {
                log('API', `<< ${statusText} ${url.split('?')[0]}`);
            }
        } else if (url.includes('dance.danyelica.fish')) {
            log('API', `<< ${response.status()} ${url}`);
        }
    });

    // Capture page errors
    page.on('pageerror', error => {
        log('ERROR', `Page error: ${error.message}`);
    });

    // Monitor WebSocket connections
    const client = await page.target().createCDPSession();
    await client.send('Network.enable');

    client.on('Network.webSocketCreated', ({requestId, url}) => {
        log('NETWORK', `WebSocket created: ${url}`);
    });

    client.on('Network.webSocketFrameSent', ({requestId, timestamp, response}) => {
        const size = response.payloadData?.length || 0;
        if (size > 100) {  // Only log actual video data, not small messages
            log('NETWORK', `WebSocket sent: ${size} bytes`);
        }
    });

    client.on('Network.webSocketFrameReceived', ({requestId, timestamp, response}) => {
        log('NETWORK', `WebSocket received: ${response.payloadData}`);
    });

    client.on('Network.webSocketClosed', ({requestId, timestamp}) => {
        log('NETWORK', 'WebSocket closed');
    });

    log('INFO', `Navigating to ${PAGE_URL}`);

    await page.goto(PAGE_URL, { waitUntil: 'networkidle2', timeout: 60000 });

    const currentUrl = page.url();
    log('INFO', `Current URL: ${currentUrl}`);

    if (currentUrl.includes('accounts.google.com')) {
        log('WARN', '===========================================');
        log('WARN', 'OAUTH LOGIN REQUIRED');
        log('WARN', 'Please log in manually in the browser window');
        log('WARN', 'The script will continue monitoring after login');
        log('WARN', '===========================================');

        await page.waitForNavigation({
            waitUntil: 'networkidle2',
            timeout: 300000
        }).catch(() => {});
    }

    log('INFO', 'Monitoring page state...');

    // Check background color periodically
    setInterval(async () => {
        try {
            const bgColor = await page.evaluate(() => {
                return window.getComputedStyle(document.body).backgroundColor;
            });

            const isGreen = bgColor.includes('34, 197, 94') || bgColor.includes('22c55e');
            const isRed = bgColor.includes('239, 68, 68') || bgColor.includes('ef4444');

            if (isGreen) {
                log('INFO', '>>> SCREEN IS GREEN (streaming) <<<');
            } else if (isRed) {
                log('INFO', '>>> SCREEN IS RED (not streaming) <<<');
            }
        } catch (e) {}
    }, 5000);

    log('INFO', 'Debug session active. Press Ctrl+C to exit.');
    await new Promise(() => {});
}

main().catch(err => {
    log('ERROR', 'Fatal error:', err.message);
    console.error(err);
    process.exit(1);
});
