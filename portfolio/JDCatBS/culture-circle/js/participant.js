// Service Culture Circle - Participant Portal Logic

let currentParticipant = null;
let sessionToken = null;

// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    // Check for existing session
    const savedSession = sessionStorage.getItem('scc_participant_session');
    if (savedSession) {
        try {
            const session = JSON.parse(savedSession);
            currentParticipant = session.participant;
            sessionToken = session.token;

            // Check if consent is needed
            if (session.needs_consent) {
                showConsentScreen();
            } else {
                showPortalScreen();
                loadTranscripts();
            }
        } catch (e) {
            sessionStorage.removeItem('scc_participant_session');
        }
    }

    setupEventListeners();
    setupKeyInput();
});

function setupEventListeners() {
    // Login
    document.getElementById('loginBtn').addEventListener('click', handleLogin);
    document.getElementById('keyInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleLogin();
    });

    // Consent
    document.getElementById('consentCheckbox').addEventListener('change', (e) => {
        document.getElementById('acceptConsentBtn').disabled = !e.target.checked;
    });
    document.getElementById('acceptConsentBtn').addEventListener('click', handleAcceptConsent);
    document.getElementById('declineConsentBtn').addEventListener('click', handleDeclineConsent);

    // Portal
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);
    document.getElementById('requestEmailChangeBtn').addEventListener('click', showEmailChangeModal);
    document.getElementById('withdrawConsentBtn').addEventListener('click', handleWithdrawConsent);

    // Email change modal
    document.getElementById('cancelEmailChangeBtn').addEventListener('click', hideEmailChangeModal);
    document.getElementById('submitEmailChangeBtn').addEventListener('click', submitEmailChange);
}

function setupKeyInput() {
    const keyInput = document.getElementById('keyInput');

    // Auto-format key input (SCC-XXXX-XXXX-XXXX-XXXX)
    keyInput.addEventListener('input', (e) => {
        let value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '');

        // Remove SCC prefix if user typed it
        if (value.startsWith('SCC')) {
            value = value.substring(3);
        }

        // Format with dashes
        const parts = [];
        for (let i = 0; i < value.length && i < 16; i += 4) {
            parts.push(value.substring(i, i + 4));
        }

        if (parts.length > 0) {
            e.target.value = 'SCC-' + parts.join('-');
        } else {
            e.target.value = '';
        }
    });
}

// ============================================
// LOGIN
// ============================================
async function handleLogin() {
    const keyInput = document.getElementById('keyInput');
    const loginBtn = document.getElementById('loginBtn');
    const errorEl = document.getElementById('loginError');

    const loginKey = keyInput.value.trim().toUpperCase();

    if (!loginKey || loginKey.length < 19) {
        showError('Please enter a valid access key');
        return;
    }

    loginBtn.disabled = true;
    loginBtn.textContent = 'VERIFYING...';
    errorEl.classList.add('hidden');

    try {
        // Hash the key for lookup
        const keyHash = await hashKey(loginKey);

        // Find participant by key hash
        const { data: participant, error } = await supabase
            .from('participants')
            .select('id, name, email, status')
            .eq('login_key_hash', keyHash)
            .single();

        if (error || !participant) {
            throw new Error('Invalid access key');
        }

        if (participant.status === 'suspended') {
            throw new Error('Your account has been suspended. Please contact the study lead.');
        }

        // Check consent status
        const { data: consent } = await supabase
            .from('consent_records')
            .select('id')
            .eq('participant_id', participant.id)
            .is('withdrawal_at', null)
            .single();

        // Update last login
        await supabase
            .from('participants')
            .update({ last_login: new Date().toISOString(), status: 'active' })
            .eq('id', participant.id);

        // Log the access
        await logAudit('participant', participant.id, 'login', 'participant', participant.id, {});

        // Save session
        currentParticipant = participant;
        sessionToken = Date.now().toString(36) + Math.random().toString(36).substring(2);

        const sessionData = {
            participant,
            token: sessionToken,
            needs_consent: !consent
        };

        sessionStorage.setItem('scc_participant_session', JSON.stringify(sessionData));

        // Navigate to appropriate screen
        if (!consent) {
            showConsentScreen();
        } else {
            showPortalScreen();
            loadTranscripts();
        }

    } catch (error) {
        showError(error.message);
    } finally {
        loginBtn.disabled = false;
        loginBtn.textContent = 'ACCESS';
    }
}

function showError(message) {
    const errorEl = document.getElementById('loginError');
    errorEl.textContent = message;
    errorEl.classList.remove('hidden');
}

function handleLogout() {
    sessionStorage.removeItem('scc_participant_session');
    currentParticipant = null;
    sessionToken = null;
    showLoginScreen();
}

// ============================================
// SCREENS
// ============================================
function showLoginScreen() {
    document.getElementById('loginScreen').classList.remove('hidden');
    document.getElementById('consentScreen').classList.add('hidden');
    document.getElementById('portalScreen').classList.add('hidden');
    document.getElementById('keyInput').value = '';
    document.getElementById('loginError').classList.add('hidden');
}

function showConsentScreen() {
    document.getElementById('loginScreen').classList.add('hidden');
    document.getElementById('consentScreen').classList.remove('hidden');
    document.getElementById('portalScreen').classList.add('hidden');
    loadConsentForm();
}

function showPortalScreen() {
    document.getElementById('loginScreen').classList.add('hidden');
    document.getElementById('consentScreen').classList.add('hidden');
    document.getElementById('portalScreen').classList.remove('hidden');

    document.getElementById('participantName').textContent = currentParticipant.name;
    document.getElementById('participantEmail').textContent = currentParticipant.email;
}

// ============================================
// CONSENT
// ============================================
async function loadConsentForm() {
    try {
        const { data: consentForm } = await supabase
            .from('consent_forms')
            .select('*')
            .eq('is_active', true)
            .order('version', { ascending: false })
            .limit(1)
            .single();

        if (consentForm) {
            // Simple markdown-like rendering
            const content = consentForm.content
                .replace(/## (.*)/g, '<h2>$1</h2>')
                .replace(/### (.*)/g, '<h3>$1</h3>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/- (.*)/g, '<li>$1</li>')
                .replace(/\n\n/g, '</p><p>')
                .replace(/\n/g, '<br>');

            document.getElementById('consentContent').innerHTML = `<p>${content}</p>`;
            document.getElementById('consentContent').dataset.formId = consentForm.id;
        }
    } catch (error) {
        console.error('Error loading consent form:', error);
        document.getElementById('consentContent').innerHTML = '<p>Error loading consent form. Please contact the study lead.</p>';
    }
}

async function handleAcceptConsent() {
    const checkbox = document.getElementById('consentCheckbox');
    if (!checkbox.checked) return;

    const consentFormId = document.getElementById('consentContent').dataset.formId;

    try {
        // Create consent record
        const { error } = await supabase
            .from('consent_records')
            .insert({
                participant_id: currentParticipant.id,
                consent_form_id: consentFormId,
                user_agent: navigator.userAgent
            });

        if (error) throw error;

        // Log the action
        await logAudit('participant', currentParticipant.id, 'consent_accepted', 'consent', null, {
            consent_form_id: consentFormId
        });

        // Update session
        const session = JSON.parse(sessionStorage.getItem('scc_participant_session'));
        session.needs_consent = false;
        sessionStorage.setItem('scc_participant_session', JSON.stringify(session));

        // Show portal
        showPortalScreen();
        loadTranscripts();

    } catch (error) {
        alert('Error recording consent: ' + error.message);
    }
}

function handleDeclineConsent() {
    if (confirm('If you decline consent, you will not be able to access your interview transcripts. Are you sure?')) {
        handleLogout();
    }
}

// ============================================
// TRANSCRIPTS
// ============================================
async function loadTranscripts() {
    try {
        // Get all interviews where this participant has segments
        const { data: segments } = await supabase
            .from('transcript_segments')
            .select(`
                *,
                interviews:interview_id (
                    id,
                    title,
                    recorded_at,
                    uploaded_at
                )
            `)
            .eq('participant_id', currentParticipant.id)
            .order('sequence_order');

        if (!segments || segments.length === 0) {
            document.getElementById('transcriptsList').innerHTML = `
                <div class="empty-state">
                    <p>No transcripts available yet</p>
                    <p style="font-size: 11px;">You will be notified when new content is ready</p>
                </div>
            `;
            return;
        }

        // Group by interview
        const interviewMap = {};
        segments.forEach(seg => {
            const interviewId = seg.interviews.id;
            if (!interviewMap[interviewId]) {
                interviewMap[interviewId] = {
                    interview: seg.interviews,
                    segments: []
                };
            }
            interviewMap[interviewId].segments.push(seg);
        });

        // Also get other segments from these interviews for context
        const interviewIds = Object.keys(interviewMap);
        const { data: allSegments } = await supabase
            .from('transcript_segments')
            .select('*')
            .in('interview_id', interviewIds)
            .order('sequence_order');

        // Build full transcript with markers
        const container = document.getElementById('transcriptsList');
        container.innerHTML = '';

        for (const interviewId of interviewIds) {
            const { interview, segments: mySegments } = interviewMap[interviewId];
            const mySegmentIds = new Set(mySegments.map(s => s.id));

            const interviewSegments = allSegments.filter(s => s.interview_id === interviewId);

            const card = document.createElement('div');
            card.className = 'interview-card';

            const header = document.createElement('div');
            header.className = 'interview-header';
            header.innerHTML = `
                <div>
                    <h3>${interview.title}</h3>
                    <div class="meta">${formatDate(interview.recorded_at || interview.uploaded_at)}</div>
                </div>
                <span class="toggle">&#9660;</span>
            `;

            const segmentsDiv = document.createElement('div');
            segmentsDiv.className = 'interview-segments';

            interviewSegments.forEach(seg => {
                const isMySegment = mySegmentIds.has(seg.id);
                const segDiv = document.createElement('div');
                segDiv.className = isMySegment ? 'my-segment' : 'other-segment';

                if (isMySegment) {
                    segDiv.innerHTML = `
                        <div class="timestamp">${formatTime(seg.start_time_ms)} - ${formatTime(seg.end_time_ms)}</div>
                        <p>${seg.content}</p>
                    `;
                } else {
                    segDiv.innerHTML = `
                        <div class="speaker">[Other participant]</div>
                        <p>[Content hidden for privacy]</p>
                    `;
                }

                segmentsDiv.appendChild(segDiv);
            });

            header.addEventListener('click', () => {
                segmentsDiv.classList.toggle('expanded');
                header.querySelector('.toggle').innerHTML = segmentsDiv.classList.contains('expanded') ? '&#9650;' : '&#9660;';

                // Log access
                if (segmentsDiv.classList.contains('expanded')) {
                    logAudit('participant', currentParticipant.id, 'view_transcript', 'interview', interviewId, {});
                }
            });

            card.appendChild(header);
            card.appendChild(segmentsDiv);
            container.appendChild(card);
        }

    } catch (error) {
        console.error('Error loading transcripts:', error);
        document.getElementById('transcriptsList').innerHTML = `
            <div class="empty-state">
                <p>Error loading transcripts</p>
                <p style="font-size: 11px;">${error.message}</p>
            </div>
        `;
    }
}

// ============================================
// EMAIL CHANGE
// ============================================
function showEmailChangeModal() {
    document.getElementById('emailChangeModal').classList.remove('hidden');
    document.getElementById('emailChangeModal').style.display = 'flex';
    document.getElementById('newEmailInput').value = '';
    document.getElementById('emailChangeError').classList.add('hidden');
}

function hideEmailChangeModal() {
    document.getElementById('emailChangeModal').classList.add('hidden');
    document.getElementById('emailChangeModal').style.display = 'none';
}

async function submitEmailChange() {
    const newEmail = document.getElementById('newEmailInput').value.trim();
    const errorEl = document.getElementById('emailChangeError');

    if (!newEmail || !newEmail.includes('@')) {
        errorEl.textContent = 'Please enter a valid email address';
        errorEl.classList.remove('hidden');
        return;
    }

    if (newEmail === currentParticipant.email) {
        errorEl.textContent = 'New email must be different from current email';
        errorEl.classList.remove('hidden');
        return;
    }

    try {
        const { error } = await supabase
            .from('email_change_requests')
            .insert({
                participant_id: currentParticipant.id,
                old_email: currentParticipant.email,
                new_email: newEmail
            });

        if (error) throw error;

        await logAudit('participant', currentParticipant.id, 'request_email_change', 'participant', currentParticipant.id, {
            new_email: newEmail
        });

        hideEmailChangeModal();
        alert('Email change request submitted. The study lead will review your request.');

    } catch (error) {
        errorEl.textContent = error.message;
        errorEl.classList.remove('hidden');
    }
}

// ============================================
// WITHDRAW CONSENT
// ============================================
async function handleWithdrawConsent() {
    const reason = prompt('Please provide a reason for withdrawing consent (optional):');

    if (!confirm('Are you sure you want to withdraw your consent? You will lose access to your interview transcripts.')) {
        return;
    }

    try {
        // Update consent record
        await supabase
            .from('consent_records')
            .update({
                withdrawal_at: new Date().toISOString(),
                withdrawal_reason: reason || null
            })
            .eq('participant_id', currentParticipant.id)
            .is('withdrawal_at', null);

        await logAudit('participant', currentParticipant.id, 'consent_withdrawn', 'consent', null, {
            reason: reason || 'No reason provided'
        });

        alert('Your consent has been withdrawn. You will be logged out.');
        handleLogout();

    } catch (error) {
        alert('Error withdrawing consent: ' + error.message);
    }
}
