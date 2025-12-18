// Service Culture Circle - Supabase Configuration
// Replace these values with your Supabase project credentials

const SUPABASE_URL = 'https://ezttcqgkegfikrmftlmo.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV6dHRjcWdrZWdmaWtybWZ0bG1vIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYwNzM4OTcsImV4cCI6MjA4MTY0OTg5N30.pEnSBfcJB7rgdZWrHkdT4snqbKhgd71-ZSWOPH0kxeo';

// Initialize Supabase client
const db = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// API Keys (store securely - these are placeholders)
const CONFIG = {
    DEEPGRAM_API_KEY: 'YOUR_DEEPGRAM_API_KEY', // Only used in Edge Functions
    SENDGRID_API_KEY: 'YOUR_SENDGRID_API_KEY', // Only used in Edge Functions
    STUDY_LEAD_EMAIL: 'YOUR_EMAIL@example.com'
};

// Helper: Log audit event
async function logAudit(actorType, actorId, action, resourceType, resourceId, details = {}) {
    try {
        await supabase.from('audit_logs').insert({
            actor_type: actorType,
            actor_id: actorId,
            action: action,
            resource_type: resourceType,
            resource_id: resourceId,
            details: details,
            ip_address: null, // Set by Edge Function
            user_agent: navigator.userAgent
        });
    } catch (err) {
        console.error('Audit log failed:', err);
    }
}

// Helper: Generate login key
function generateLoginKey() {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    const segments = [];
    for (let i = 0; i < 4; i++) {
        let segment = '';
        for (let j = 0; j < 4; j++) {
            segment += chars[Math.floor(Math.random() * chars.length)];
        }
        segments.push(segment);
    }
    return `SCC-${segments.join('-')}`;
}

// Helper: Hash login key (client-side for verification display only)
async function hashKey(key) {
    const encoder = new TextEncoder();
    const data = encoder.encode(key);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

// Helper: Format timestamp
function formatTime(ms) {
    const seconds = Math.floor(ms / 1000);
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Helper: Format date
function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}
