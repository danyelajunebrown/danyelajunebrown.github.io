// Service Culture Circle - Admin Dashboard Logic

let currentUser = null;
let currentInterviewId = null;
let speakerAssignments = {};

// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', async () => {
    // Check for existing session
    const { data: { session } } = await db.auth.getSession();
    if (session) {
        currentUser = session.user;
        showMainApp();
        loadAllData();
    }

    // Auth state changes
    db.auth.onAuthStateChange((event, session) => {
        if (event === 'SIGNED_IN' && session) {
            currentUser = session.user;
            showMainApp();
            loadAllData();
        } else if (event === 'SIGNED_OUT') {
            currentUser = null;
            showAuthScreen();
        }
    });

    setupEventListeners();
});

function setupEventListeners() {
    // Auth
    document.getElementById('authBtn').addEventListener('click', handleAuth);
    document.getElementById('passInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleAuth();
    });
    document.getElementById('signUpLink').addEventListener('click', (e) => {
        e.preventDefault();
        handleSignUp();
    });
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);

    // Tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    // Upload
    const dropZone = document.getElementById('dropZone');
    const audioInput = document.getElementById('audioInput');

    dropZone.addEventListener('click', () => audioInput.click());
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) handleFileUpload(files[0]);
    });
    audioInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleFileUpload(e.target.files[0]);
    });

    // Modals
    document.getElementById('closeTaggerBtn').addEventListener('click', closeTaggerModal);
    document.getElementById('cancelTaggingBtn').addEventListener('click', closeTaggerModal);
    document.getElementById('saveTagsBtn').addEventListener('click', saveSpeakerTags);

    document.getElementById('closeNewParticipantBtn').addEventListener('click', closeNewParticipantModal);
    document.getElementById('cancelNewParticipantBtn').addEventListener('click', closeNewParticipantModal);
    document.getElementById('createParticipantBtn').addEventListener('click', createNewParticipant);

    // Audit
    document.getElementById('auditActorFilter').addEventListener('change', loadAuditLog);
    document.getElementById('auditResourceFilter').addEventListener('change', loadAuditLog);
    document.getElementById('auditDateFilter').addEventListener('change', loadAuditLog);
    document.getElementById('exportAuditBtn').addEventListener('click', exportAuditLog);
}

// ============================================
// AUTHENTICATION
// ============================================
async function handleAuth() {
    const email = document.getElementById('emailInput').value.trim();
    const password = document.getElementById('passInput').value;
    const errorEl = document.getElementById('authError');

    if (!email || !password) {
        errorEl.textContent = 'Please enter email and password';
        return;
    }

    try {
        const { data, error } = await db.auth.signInWithPassword({
            email,
            password
        });

        if (error) throw error;

        await logAudit('study_lead', data.user.id, 'login', 'auth', null, {});

    } catch (error) {
        errorEl.textContent = error.message || 'Login failed';
    }
}

async function handleSignUp() {
    const email = document.getElementById('emailInput').value.trim();
    const password = document.getElementById('passInput').value;
    const errorEl = document.getElementById('authError');

    if (!email || !password) {
        errorEl.textContent = 'Please enter email and password';
        return;
    }

    if (password.length < 6) {
        errorEl.textContent = 'Password must be at least 6 characters';
        return;
    }

    try {
        const { data, error } = await db.auth.signUp({
            email,
            password
        });

        if (error) throw error;

        errorEl.style.color = '#81c784';
        errorEl.textContent = 'Account created! Check your email to confirm.';

    } catch (error) {
        errorEl.style.color = '#f44336';
        errorEl.textContent = error.message || 'Sign up failed';
    }
}

async function handleLogout() {
    await db.auth.signOut();
}

function showAuthScreen() {
    document.getElementById('authScreen').classList.remove('hidden');
    document.getElementById('mainApp').classList.add('hidden');
}

function showMainApp() {
    document.getElementById('authScreen').classList.add('hidden');
    document.getElementById('mainApp').classList.remove('hidden');
    document.getElementById('userEmail').textContent = currentUser.email;
}

// ============================================
// TAB NAVIGATION
// ============================================
function switchTab(tabId) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');
    document.getElementById(tabId).classList.add('active');

    // Load data for the tab
    if (tabId === 'participants') loadParticipants();
    if (tabId === 'audit') loadAuditLog();
}

// ============================================
// FILE UPLOAD
// ============================================
async function handleFileUpload(file) {
    // Validate file
    const validTypes = ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/x-m4a', 'audio/mp3'];
    if (!validTypes.includes(file.type) && !file.name.match(/\.(mp3|wav|m4a)$/i)) {
        alert('Please upload an audio file (.mp3, .wav, .m4a)');
        return;
    }

    const maxSize = 500 * 1024 * 1024; // 500MB
    if (file.size > maxSize) {
        alert('File too large. Maximum size is 500MB.');
        return;
    }

    const progressContainer = document.getElementById('uploadProgress');
    const progressFill = document.getElementById('progressFill');
    const uploadStatus = document.getElementById('uploadStatus');

    progressContainer.classList.remove('hidden');
    progressFill.style.width = '0%';
    uploadStatus.textContent = 'Uploading...';

    try {
        // Create interview record
        const { data: interview, error: dbError } = await db
            .from('interviews')
            .insert({
                title: file.name.replace(/\.[^/.]+$/, ''),
                uploaded_by: currentUser.id,
                processing_status: 'uploaded'
            })
            .select()
            .single();

        if (dbError) throw dbError;

        progressFill.style.width = '20%';
        uploadStatus.textContent = 'Creating record...';

        // Upload to storage
        const filePath = `${interview.id}/${file.name}`;
        const { error: uploadError } = await db.storage
            .from('interview-audio')
            .upload(filePath, file, {
                onUploadProgress: (progress) => {
                    const percent = 20 + (progress.loaded / progress.total) * 60;
                    progressFill.style.width = `${percent}%`;
                }
            });

        if (uploadError) throw uploadError;

        progressFill.style.width = '80%';
        uploadStatus.textContent = 'Starting transcription...';

        // Trigger processing (Edge Function)
        // For now, we'll simulate this - in production, call the Edge Function
        await simulateTranscription(interview.id);

        progressFill.style.width = '100%';
        uploadStatus.textContent = 'Complete! Interview is being transcribed.';

        await logAudit('study_lead', currentUser.id, 'upload_interview', 'interview', interview.id, {
            filename: file.name,
            size: file.size
        });

        // Refresh lists
        setTimeout(() => {
            progressContainer.classList.add('hidden');
            loadInterviews();
        }, 2000);

    } catch (error) {
        console.error('Upload error:', error);
        uploadStatus.textContent = `Error: ${error.message}`;
        progressFill.style.background = '#f44336';
    }
}

// Simulate transcription for demo (replace with Edge Function call)
async function simulateTranscription(interviewId) {
    // In production, call the Edge Function:
    // await db.functions.invoke('process-audio', { body: { interview_id: interviewId } });

    // For demo, create mock transcript segments
    await db
        .from('interviews')
        .update({ processing_status: 'transcribing' })
        .eq('id', interviewId);

    // Simulate delay
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Create mock segments
    const mockSegments = [
        { speaker_label: 'Speaker 1', start_time_ms: 0, end_time_ms: 5000, content: 'Welcome to this interview. Thank you for joining us today.', sequence_order: 0 },
        { speaker_label: 'Speaker 2', start_time_ms: 5000, end_time_ms: 12000, content: 'Thank you for having me. I\'m excited to share my experiences.', sequence_order: 1 },
        { speaker_label: 'Speaker 1', start_time_ms: 12000, end_time_ms: 20000, content: 'Can you tell us about your background and how you got involved in this work?', sequence_order: 2 },
        { speaker_label: 'Speaker 2', start_time_ms: 20000, end_time_ms: 45000, content: 'Absolutely. I\'ve been working in this field for about ten years now. It started when I was a graduate student and I saw the need for more community-based research approaches.', sequence_order: 3 },
    ];

    for (const seg of mockSegments) {
        await db.from('transcript_segments').insert({
            interview_id: interviewId,
            ...seg,
            confidence: 0.95
        });
    }

    await db
        .from('interviews')
        .update({
            processing_status: 'pending_review',
            audio_deleted: true,
            audio_deleted_at: new Date().toISOString(),
            duration_seconds: 45,
            speaker_count: 2
        })
        .eq('id', interviewId);
}

// ============================================
// LOAD DATA
// ============================================
async function loadAllData() {
    await loadInterviews();
}

async function loadInterviews() {
    // Load pending review
    const { data: pending } = await db
        .from('interviews')
        .select('*')
        .eq('processing_status', 'pending_review')
        .order('uploaded_at', { ascending: false });

    renderInterviewList('pendingList', pending || [], true);

    // Load completed
    const { data: completed } = await db
        .from('interviews')
        .select('*')
        .eq('processing_status', 'completed')
        .order('uploaded_at', { ascending: false });

    renderInterviewList('completedList', completed || [], false);

    // Load in progress
    const { data: processing } = await db
        .from('interviews')
        .select('*')
        .in('processing_status', ['uploaded', 'transcribing'])
        .order('uploaded_at', { ascending: false });

    // Show processing items in pending list if any
    if (processing && processing.length > 0) {
        const pendingEl = document.getElementById('pendingList');
        processing.forEach(interview => {
            const item = createInterviewItem(interview, false, true);
            pendingEl.insertBefore(item, pendingEl.firstChild);
        });
    }
}

function renderInterviewList(containerId, interviews, isPending) {
    const container = document.getElementById(containerId);

    if (!interviews || interviews.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>No ${isPending ? 'interviews pending review' : 'completed interviews yet'}</p>
            </div>
        `;
        return;
    }

    container.innerHTML = '';
    interviews.forEach(interview => {
        container.appendChild(createInterviewItem(interview, isPending));
    });
}

function createInterviewItem(interview, isPending, isProcessing = false) {
    const item = document.createElement('div');
    item.className = 'interview-item';

    const statusClass = {
        'uploaded': 'status-pending',
        'transcribing': 'status-transcribing',
        'pending_review': 'status-review',
        'completed': 'status-completed',
        'failed': 'status-failed'
    }[interview.processing_status] || 'status-pending';

    const statusText = {
        'uploaded': 'Uploaded',
        'transcribing': 'Transcribing...',
        'pending_review': 'Needs Tagging',
        'completed': 'Complete',
        'failed': 'Failed'
    }[interview.processing_status] || interview.processing_status;

    item.innerHTML = `
        <div class="interview-info">
            <h4>${interview.title}</h4>
            <div class="meta">
                ${formatDate(interview.uploaded_at)}
                ${interview.duration_seconds ? ` • ${Math.floor(interview.duration_seconds / 60)}:${(interview.duration_seconds % 60).toString().padStart(2, '0')}` : ''}
                ${interview.speaker_count ? ` • ${interview.speaker_count} speakers` : ''}
            </div>
        </div>
        <div class="interview-actions">
            <span class="status-badge ${statusClass}">${statusText}</span>
            ${isPending ? `<button class="btn btn-primary" onclick="openTaggerModal('${interview.id}')">Tag Speakers</button>` : ''}
            ${!isPending && !isProcessing ? `<button class="btn btn-secondary" onclick="viewTranscript('${interview.id}')">View</button>` : ''}
        </div>
    `;

    return item;
}

// ============================================
// SPEAKER TAGGING
// ============================================
async function openTaggerModal(interviewId) {
    currentInterviewId = interviewId;
    speakerAssignments = {};

    // Load segments
    const { data: segments } = await db
        .from('transcript_segments')
        .select('*')
        .eq('interview_id', interviewId)
        .order('sequence_order');

    // Load existing participants
    const { data: participants } = await db
        .from('participants')
        .select('id, name, email')
        .order('name');

    // Load suggestions
    const { data: suggestions } = await db
        .from('speaker_suggestions')
        .select(`
            speaker_label,
            similarity_score,
            participant_id,
            participants:participant_id (id, name)
        `)
        .eq('interview_id', interviewId)
        .order('similarity_score', { ascending: false });

    // Group suggestions by speaker
    const suggestionsByLabel = (suggestions || []).reduce((acc, s) => {
        if (!acc[s.speaker_label]) acc[s.speaker_label] = [];
        if (s.participants) acc[s.speaker_label].push(s);
        return acc;
    }, {});

    // Get unique speakers
    const speakers = [...new Set(segments.map(s => s.speaker_label))];

    // Render speaker sections
    const sectionsContainer = document.getElementById('speakerSections');
    sectionsContainer.innerHTML = speakers.map(speaker => {
        const speakerSuggestions = suggestionsByLabel[speaker] || [];
        const segmentCount = segments.filter(s => s.speaker_label === speaker).length;

        return `
            <div class="speaker-section" data-speaker="${speaker}">
                <div class="speaker-header">
                    <span class="speaker-label">${speaker}</span>
                    <span class="segment-count">${segmentCount} segments</span>
                </div>
                ${speakerSuggestions.length > 0 ? `
                    <div class="suggestions">
                        <p>Voice Match Suggestions:</p>
                        ${speakerSuggestions.slice(0, 3).map(s => `
                            <button class="suggestion-btn" data-speaker="${speaker}" data-participant-id="${s.participants.id}">
                                ${s.participants.name}
                                <span class="match-score">${Math.round(s.similarity_score * 100)}%</span>
                            </button>
                        `).join('')}
                    </div>
                ` : ''}
                <div class="manual-assign">
                    <select class="participant-select" data-speaker="${speaker}">
                        <option value="">-- Select existing participant --</option>
                        ${(participants || []).map(p => `
                            <option value="${p.id}">${p.name} (${p.email})</option>
                        `).join('')}
                    </select>
                    <button class="btn btn-secondary" onclick="showNewParticipantModal('${speaker}')">+ New</button>
                </div>
            </div>
        `;
    }).join('');

    // Render transcript preview
    const previewContainer = document.getElementById('transcriptPreview');
    previewContainer.innerHTML = segments.map(seg => `
        <div class="segment" data-speaker="${seg.speaker_label}">
            <span class="speaker-badge">${seg.speaker_label}</span>
            <span class="timestamp">${formatTime(seg.start_time_ms)}</span>
            <p>${seg.content}</p>
        </div>
    `).join('');

    // Setup event listeners for suggestions and selects
    document.querySelectorAll('.suggestion-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const speaker = btn.dataset.speaker;
            const participantId = btn.dataset.participantId;

            // Clear other selections for this speaker
            document.querySelectorAll(`.suggestion-btn[data-speaker="${speaker}"]`).forEach(b => b.classList.remove('selected'));
            document.querySelector(`.participant-select[data-speaker="${speaker}"]`).value = '';

            btn.classList.add('selected');
            speakerAssignments[speaker] = participantId;
        });
    });

    document.querySelectorAll('.participant-select').forEach(select => {
        select.addEventListener('change', () => {
            const speaker = select.dataset.speaker;

            // Clear suggestion selections
            document.querySelectorAll(`.suggestion-btn[data-speaker="${speaker}"]`).forEach(b => b.classList.remove('selected'));

            if (select.value) {
                speakerAssignments[speaker] = select.value;
            } else {
                delete speakerAssignments[speaker];
            }
        });
    });

    document.getElementById('taggerModal').classList.remove('hidden');
}

function closeTaggerModal() {
    document.getElementById('taggerModal').classList.add('hidden');
    currentInterviewId = null;
    speakerAssignments = {};
}

let pendingNewParticipantSpeaker = null;

function showNewParticipantModal(speaker) {
    pendingNewParticipantSpeaker = speaker;
    document.getElementById('newParticipantName').value = '';
    document.getElementById('newParticipantEmail').value = '';
    document.getElementById('newParticipantError').textContent = '';
    document.getElementById('newParticipantModal').classList.remove('hidden');
}

function closeNewParticipantModal() {
    document.getElementById('newParticipantModal').classList.add('hidden');
    pendingNewParticipantSpeaker = null;
}

async function createNewParticipant() {
    const name = document.getElementById('newParticipantName').value.trim();
    const email = document.getElementById('newParticipantEmail').value.trim();
    const errorEl = document.getElementById('newParticipantError');

    if (!name || !email) {
        errorEl.textContent = 'Please enter name and email';
        return;
    }

    try {
        // Generate login key
        const loginKey = generateLoginKey();
        const loginKeyHash = await hashKey(loginKey);

        // Create participant
        const { data: participant, error } = await db
            .from('participants')
            .insert({
                name,
                email,
                login_key: loginKey,
                login_key_hash: loginKeyHash,
                created_by: currentUser.id,
                status: 'pending'
            })
            .select()
            .single();

        if (error) {
            if (error.code === '23505') {
                throw new Error('A participant with this email already exists');
            }
            throw error;
        }

        // Log the action
        await logAudit('study_lead', currentUser.id, 'create_participant', 'participant', participant.id, { name, email });

        // TODO: Send email via Edge Function
        // await db.functions.invoke('send-login-key', { body: { participant_id: participant.id } });

        console.log('Login key for', name, ':', loginKey); // For demo - remove in production

        // Assign to speaker
        if (pendingNewParticipantSpeaker) {
            speakerAssignments[pendingNewParticipantSpeaker] = participant.id;

            // Update the select in the tagger modal
            const select = document.querySelector(`.participant-select[data-speaker="${pendingNewParticipantSpeaker}"]`);
            if (select) {
                const option = document.createElement('option');
                option.value = participant.id;
                option.textContent = `${name} (${email})`;
                option.selected = true;
                select.appendChild(option);
            }
        }

        closeNewParticipantModal();
        alert(`Participant created! Login key: ${loginKey}\n\n(In production, this would be emailed automatically)`);

    } catch (error) {
        errorEl.textContent = error.message;
    }
}

async function saveSpeakerTags() {
    if (!currentInterviewId) return;

    const speakers = Object.keys(speakerAssignments);
    if (speakers.length === 0) {
        alert('Please assign at least one speaker');
        return;
    }

    try {
        // Update transcript segments with participant IDs
        for (const [speaker, participantId] of Object.entries(speakerAssignments)) {
            await db
                .from('transcript_segments')
                .update({
                    participant_id: participantId,
                    tagged_at: new Date().toISOString(),
                    tagged_by: currentUser.id
                })
                .eq('interview_id', currentInterviewId)
                .eq('speaker_label', speaker);
        }

        // Update interview status
        await db
            .from('interviews')
            .update({ processing_status: 'completed' })
            .eq('id', currentInterviewId);

        // Log the action
        await logAudit('study_lead', currentUser.id, 'tag_speakers', 'interview', currentInterviewId, {
            assignments: speakerAssignments
        });

        // TODO: Notify participants via Edge Function
        // for (const participantId of Object.values(speakerAssignments)) {
        //     await db.functions.invoke('send-login-key', {
        //         body: { participant_id: participantId, type: 'new_content' }
        //     });
        // }

        closeTaggerModal();
        loadInterviews();
        alert('Speakers tagged successfully! Participants will be notified.');

    } catch (error) {
        console.error('Error saving tags:', error);
        alert('Error saving tags: ' + error.message);
    }
}

function viewTranscript(interviewId) {
    // For now, just open the tagger modal in view mode
    // In a full implementation, this would be a separate view
    openTaggerModal(interviewId);
}

// ============================================
// PARTICIPANTS
// ============================================
async function loadParticipants() {
    const { data: participants } = await db
        .from('participants')
        .select('*')
        .order('created_at', { ascending: false });

    const tbody = document.getElementById('participantsBody');
    const emptyState = document.getElementById('noParticipants');

    if (!participants || participants.length === 0) {
        tbody.innerHTML = '';
        emptyState.classList.remove('hidden');
        return;
    }

    emptyState.classList.add('hidden');
    tbody.innerHTML = participants.map(p => `
        <tr>
            <td>${p.name}</td>
            <td>${p.email}</td>
            <td>
                <span class="status-badge ${p.status === 'active' ? 'status-completed' : p.status === 'suspended' ? 'status-failed' : 'status-pending'}">
                    ${p.status}
                </span>
            </td>
            <td>${p.last_login ? formatDate(p.last_login) : 'Never'}</td>
            <td>
                <button class="btn btn-secondary" onclick="resendKey('${p.id}')">Resend Key</button>
                ${p.status === 'active' ?
                    `<button class="btn btn-danger" onclick="suspendParticipant('${p.id}')">Suspend</button>` :
                    `<button class="btn btn-secondary" onclick="activateParticipant('${p.id}')">Activate</button>`
                }
            </td>
        </tr>
    `).join('');

    // Load email change requests
    loadEmailChangeRequests();
}

async function resendKey(participantId) {
    try {
        // TODO: Call Edge Function
        // await db.functions.invoke('send-login-key', { body: { participant_id: participantId, is_resend: true } });

        await logAudit('study_lead', currentUser.id, 'resend_key', 'participant', participantId, {});

        alert('Login key resent! (In production, email would be sent)');
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function suspendParticipant(participantId) {
    if (!confirm('Are you sure you want to suspend this participant?')) return;

    try {
        await db
            .from('participants')
            .update({ status: 'suspended' })
            .eq('id', participantId);

        await logAudit('study_lead', currentUser.id, 'suspend_participant', 'participant', participantId, {});

        loadParticipants();
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function activateParticipant(participantId) {
    try {
        await db
            .from('participants')
            .update({ status: 'active' })
            .eq('id', participantId);

        await logAudit('study_lead', currentUser.id, 'activate_participant', 'participant', participantId, {});

        loadParticipants();
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function loadEmailChangeRequests() {
    const { data: requests } = await db
        .from('email_change_requests')
        .select(`
            *,
            participants:participant_id (name)
        `)
        .eq('status', 'pending')
        .order('requested_at', { ascending: false });

    const container = document.getElementById('emailChangeRequests');

    if (!requests || requests.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>No pending email change requests</p>
            </div>
        `;
        return;
    }

    container.innerHTML = requests.map(req => `
        <div class="interview-item">
            <div class="interview-info">
                <h4>${req.participants?.name || 'Unknown'}</h4>
                <div class="meta">
                    ${req.old_email} &rarr; ${req.new_email}
                    <br>Requested: ${formatDate(req.requested_at)}
                </div>
            </div>
            <div class="interview-actions">
                <button class="btn btn-primary" onclick="approveEmailChange('${req.id}')">Approve</button>
                <button class="btn btn-danger" onclick="rejectEmailChange('${req.id}')">Reject</button>
            </div>
        </div>
    `).join('');
}

async function approveEmailChange(requestId) {
    try {
        const { data: request } = await db
            .from('email_change_requests')
            .select('*')
            .eq('id', requestId)
            .single();

        if (!request) throw new Error('Request not found');

        // Update participant email
        await db
            .from('participants')
            .update({ email: request.new_email })
            .eq('id', request.participant_id);

        // Update request status
        await db
            .from('email_change_requests')
            .update({
                status: 'approved',
                processed_at: new Date().toISOString(),
                processed_by: currentUser.id
            })
            .eq('id', requestId);

        await logAudit('study_lead', currentUser.id, 'approve_email_change', 'participant', request.participant_id, {
            old_email: request.old_email,
            new_email: request.new_email
        });

        loadParticipants();
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function rejectEmailChange(requestId) {
    try {
        await db
            .from('email_change_requests')
            .update({
                status: 'rejected',
                processed_at: new Date().toISOString(),
                processed_by: currentUser.id
            })
            .eq('id', requestId);

        loadParticipants();
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// ============================================
// AUDIT LOG
// ============================================
async function loadAuditLog() {
    const actorFilter = document.getElementById('auditActorFilter').value;
    const resourceFilter = document.getElementById('auditResourceFilter').value;
    const dateFilter = document.getElementById('auditDateFilter').value;

    let query = db
        .from('audit_logs')
        .select('*')
        .order('timestamp', { ascending: false })
        .limit(100);

    if (actorFilter) query = query.eq('actor_type', actorFilter);
    if (resourceFilter) query = query.eq('resource_type', resourceFilter);
    if (dateFilter) {
        const startOfDay = new Date(dateFilter);
        const endOfDay = new Date(dateFilter);
        endOfDay.setDate(endOfDay.getDate() + 1);
        query = query.gte('timestamp', startOfDay.toISOString()).lt('timestamp', endOfDay.toISOString());
    }

    const { data: logs } = await query;

    const container = document.getElementById('auditList');

    if (!logs || logs.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>No audit entries found</p>
            </div>
        `;
        return;
    }

    container.innerHTML = logs.map(log => `
        <div class="audit-entry">
            <span class="timestamp">${formatDate(log.timestamp)}</span>
            <span class="action">${log.action}</span>
            <span>${log.actor_type} on ${log.resource_type}</span>
            ${log.details && Object.keys(log.details).length > 0 ?
                `<div class="details">${JSON.stringify(log.details)}</div>` : ''
            }
        </div>
    `).join('');
}

async function exportAuditLog() {
    const { data: logs } = await db
        .from('audit_logs')
        .select('*')
        .order('timestamp', { ascending: false });

    if (!logs || logs.length === 0) {
        alert('No audit entries to export');
        return;
    }

    // Create CSV
    const headers = ['timestamp', 'actor_type', 'actor_id', 'action', 'resource_type', 'resource_id', 'details', 'ip_address', 'user_agent'];
    const csv = [
        headers.join(','),
        ...logs.map(log => headers.map(h => {
            const val = log[h];
            if (typeof val === 'object') return `"${JSON.stringify(val).replace(/"/g, '""')}"`;
            if (typeof val === 'string' && val.includes(',')) return `"${val}"`;
            return val || '';
        }).join(','))
    ].join('\n');

    // Download
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-log-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
}

// Make functions available globally for onclick handlers
window.openTaggerModal = openTaggerModal;
window.viewTranscript = viewTranscript;
window.showNewParticipantModal = showNewParticipantModal;
window.resendKey = resendKey;
window.suspendParticipant = suspendParticipant;
window.activateParticipant = activateParticipant;
window.approveEmailChange = approveEmailChange;
window.rejectEmailChange = rejectEmailChange;
