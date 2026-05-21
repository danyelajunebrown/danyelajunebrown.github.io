# Project Brief

## The Feels - DBT Skills Tracker

A web application for tracking emotions and DBT (Dialectical Behavior Therapy) skills. Users can log their feelings using an interactive feelings wheel, track intensity levels (1-5), record DBT skills used, and generate weekly diary cards for their therapy work.

It also includes an immersive companion experience: a Meta Quest 3 passthrough-AR walk through the diary owner's entire emotional history, plus a live spectator view onlookers can watch on their phones via a QR code.

## Core Features
- Interactive feelings wheel with hierarchical emotion selection
- Intensity tracking (1-5 scale)
- DBT skill selection from common DBT techniques
- Weekly diary card generation with drag-and-drop entry organization
- PDF export of diary cards
- User authentication via Supabase
- Change-password action in the app header
- **VR/AR kiosk** (`vr.html`): a passthrough-AR walk on Meta Quest 3 through every logged feeling
- **Live spectator view** (`live.html`): a synced companion view onlookers watch in real time
- **QR page** (`qr.html`): scannable code that sends onlookers to the spectator view

## Tech Stack
- HTML/CSS/JavaScript (vanilla)
- Supabase for authentication and database
- html2canvas + jsPDF for PDF generation
- A-Frame 1.6.0 + WebXR (`immersive-ar`) for the VR kiosk

## Files
- `index.html` - main diary card app
- `vr.html` - Meta Quest 3 passthrough-AR kiosk experience
- `live.html` - live spectator companion view
- `qr.html` - QR code page linking onlookers to the spectator view
