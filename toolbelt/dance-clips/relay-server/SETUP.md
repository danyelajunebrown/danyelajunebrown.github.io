# Relay Server Setup (DigitalOcean Droplet)

## Prerequisites
- DigitalOcean droplet with Ubuntu
- Domain name pointing to your droplet (for HTTPS)
- Your YouTube stream key from YouTube Studio

## Step 1: Install Dependencies

SSH into your droplet and run:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install FFmpeg
sudo apt install -y ffmpeg

# Verify installations
node --version
ffmpeg -version
```

## Step 2: Setup the Relay Server

```bash
# Create app directory
mkdir -p ~/dance-clips-relay
cd ~/dance-clips-relay

# Copy server files (upload package.json and server.js)
# Or clone from your repo

# Install dependencies
npm install
```

## Step 3: Setup HTTPS with Nginx + Let's Encrypt

WebSocket connections from HTTPS pages require WSS (secure WebSocket).

```bash
# Install Nginx and Certbot
sudo apt install -y nginx certbot python3-certbot-nginx

# Create Nginx config
sudo nano /etc/nginx/sites-available/dance-relay
```

Add this configuration (replace `your-domain.com`):

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

Enable the site and get SSL:

```bash
sudo ln -s /etc/nginx/sites-available/dance-relay /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

## Step 4: Run as a Service

Create a systemd service:

```bash
sudo nano /etc/systemd/system/dance-relay.service
```

Add:

```ini
[Unit]
Description=Dance Clips Relay Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/dance-clips-relay
ExecStart=/usr/bin/node server.js
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable dance-relay
sudo systemctl start dance-relay

# Check status
sudo systemctl status dance-relay
```

## Step 5: Configure Your App

In the dance-clips web app:

1. **Relay Server URL**: `wss://your-domain.com`
2. **YouTube Stream Key**: Get from YouTube Studio > Go Live > Stream key

Click "Save" on both fields. They'll persist across sessions.

## Testing

1. Open the dance-clips app
2. Allow camera/microphone
3. Click "Go Live to YouTube"
4. Check YouTube Studio - you should see your stream preview

## Troubleshooting

**Check relay server logs:**
```bash
sudo journalctl -u dance-relay -f
```

**Check if FFmpeg is receiving data:**
The logs will show FFmpeg output when streaming starts.

**Common issues:**
- "Connection error" = Check Nginx config and SSL
- Stream not appearing on YouTube = Verify stream key is correct
- Poor quality = Adjust `videoBitsPerSecond` in the frontend

## Firewall

If using UFW:
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 3001
```
