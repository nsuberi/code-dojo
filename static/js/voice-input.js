/**
 * Voice input component for articulation sessions
 * Uses Web Audio API for recording and sends to Whisper API
 */

class VoiceInput {
    constructor(options = {}) {
        this.onTranscription = options.onTranscription || (() => {});
        this.onError = options.onError || console.error;
        this.onStateChange = options.onStateChange || (() => {});
        this.sessionId = options.sessionId;

        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.stream = null;

        // UI state
        this.duration = 0;
        this.durationInterval = null;
    }

    getSupportedMimeType() {
        // List of MIME types to try, in order of preference
        const mimeTypes = [
            'audio/webm;codecs=opus',      // Chrome, Firefox, Edge
            'audio/webm',                   // Chrome, Firefox, Edge (fallback)
            'audio/mp4;codecs=mp4a.40.2',  // Safari (AAC)
            'audio/mp4',                    // Safari (fallback)
            'audio/ogg;codecs=opus',        // Firefox
            'audio/wav',                    // Most browsers (large files)
        ];

        // Find first supported MIME type
        for (const mimeType of mimeTypes) {
            if (MediaRecorder.isTypeSupported(mimeType)) {
                console.log('Using MIME type:', mimeType);
                return mimeType;
            }
        }

        // If none are explicitly supported, return null (browser will choose)
        console.log('No explicit MIME type supported, letting browser choose');
        return null;
    }

    async requestPermission() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            return true;
        } catch (error) {
            this.onError('Microphone permission denied');
            return false;
        }
    }

    async startRecording() {
        if (this.isRecording) return;

        // Request permission if not already granted
        if (!this.stream) {
            const granted = await this.requestPermission();
            if (!granted) return;
        }

        this.audioChunks = [];
        this.duration = 0;

        // Create media recorder with supported MIME type
        const mimeType = this.getSupportedMimeType();
        const options = mimeType ? { mimeType } : {};
        this.mediaRecorder = new MediaRecorder(this.stream, options);

        // Store the actual MIME type being used for blob creation
        this.recordingMimeType = this.mediaRecorder.mimeType;
        console.log('MediaRecorder started with MIME type:', this.recordingMimeType);

        this.mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                this.audioChunks.push(event.data);
            }
        };

        this.mediaRecorder.onstop = () => {
            this.processRecording();
        };

        // Start recording
        this.mediaRecorder.start();
        this.isRecording = true;
        this.onStateChange('recording');

        // Track duration
        this.durationInterval = setInterval(() => {
            this.duration++;
            this.onStateChange('recording', { duration: this.duration });
        }, 1000);

        // Record voice offer metric
        this.recordVoiceOffer();
    }

    stopRecording() {
        if (!this.isRecording) return;

        if (this.durationInterval) {
            clearInterval(this.durationInterval);
            this.durationInterval = null;
        }

        this.mediaRecorder.stop();
        this.isRecording = false;
        this.onStateChange('processing');
    }

    cancelRecording() {
        if (!this.isRecording) return;

        if (this.durationInterval) {
            clearInterval(this.durationInterval);
            this.durationInterval = null;
        }

        this.mediaRecorder.stop();
        this.isRecording = false;
        this.audioChunks = [];
        this.onStateChange('idle');
    }

    async processRecording() {
        if (this.audioChunks.length === 0) {
            this.onStateChange('idle');
            return;
        }

        // Use the MIME type that was actually used for recording
        const audioBlob = new Blob(this.audioChunks, { type: this.recordingMimeType || 'audio/webm' });

        try {
            // Use appropriate file extension based on MIME type
            const extension = this.recordingMimeType?.includes('mp4') ? 'mp4' :
                              this.recordingMimeType?.includes('ogg') ? 'ogg' :
                              this.recordingMimeType?.includes('wav') ? 'wav' : 'webm';

            const formData = new FormData();
            formData.append('audio', audioBlob, `recording.${extension}`);
            if (this.sessionId) {
                formData.append('session_id', this.sessionId);
            }

            const response = await fetch('/api/agent/voice/transcribe', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.onStateChange('transcribed', {
                    transcription: result.transcription,
                    duration: result.duration_seconds || this.duration
                });
                this.onTranscription(result.transcription, result.duration_seconds);
            } else {
                this.onError(result.error || 'Transcription failed');
                this.onStateChange('error', { error: result.error });
            }
        } catch (error) {
            this.onError('Failed to process recording: ' + error.message);
            this.onStateChange('error', { error: error.message });
        }
    }

    async recordVoiceOffer() {
        try {
            await fetch('/api/agent/voice/offer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: this.sessionId })
            });
        } catch (error) {
            console.error('Failed to record voice offer:', error);
        }
    }

    async recordVoiceDecline() {
        try {
            await fetch('/api/agent/voice/decline', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: this.sessionId })
            });
        } catch (error) {
            console.error('Failed to record voice decline:', error);
        }
    }

    destroy() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }
        if (this.durationInterval) {
            clearInterval(this.durationInterval);
        }
    }

    formatDuration(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
}

/**
 * Voice Input Modal UI Component
 */
class VoiceInputModal {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.onSubmit = options.onSubmit || (() => {});
        this.onCancel = options.onCancel || (() => {});
        this.sessionId = options.sessionId;

        this.voiceInput = null;
        this.transcription = '';
        this.duration = 0;
        this.state = 'idle'; // idle, recording, processing, transcribed, editing
    }

    render() {
        if (!this.container) return;

        this.container.innerHTML = `
            <div class="voice-input-modal">
                <div class="voice-input-header">
                    <h3>🎤 Talk Through Your Code</h3>
                    <p>Explain your implementation verbally - practice for code reviews and interviews.</p>
                </div>

                <div class="voice-input-body">
                    <div class="voice-state voice-state-idle" id="voice-state-idle">
                        <div class="recording-indicator">
                            <span class="recording-dot"></span>
                            <span class="recording-time" id="initial-recording-time">0:00</span>
                        </div>
                        <p class="voice-hint">Initializing microphone...</p>
                    </div>

                    <div class="voice-state voice-state-recording" id="voice-state-recording" style="display: none;">
                        <div class="recording-indicator">
                            <span class="recording-dot"></span>
                            <span class="recording-time" id="recording-time">0:00</span>
                        </div>
                        <button class="voice-stop-btn" id="voice-stop-btn">
                            <span>⬛</span> Stop Recording
                        </button>
                        <button class="voice-cancel-btn" id="voice-cancel-btn">Cancel</button>
                    </div>

                    <div class="voice-state voice-state-processing" id="voice-state-processing" style="display: none;">
                        <div class="processing-spinner"></div>
                        <p>Transcribing your explanation...</p>
                    </div>

                    <div class="voice-state voice-state-transcribed" id="voice-state-transcribed" style="display: none;">
                        <label>Your explanation (you can edit before sending):</label>
                        <textarea id="transcription-text" class="transcription-textarea" rows="4"></textarea>
                        <div class="transcription-actions">
                            <button class="btn btn-primary" id="voice-submit-btn">Send</button>
                            <button class="btn btn-secondary" id="voice-rerecord-btn">Re-record</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.attachEventListeners();
    }

    attachEventListeners() {
        const startBtn = document.getElementById('voice-start-btn');
        const stopBtn = document.getElementById('voice-stop-btn');
        const cancelBtn = document.getElementById('voice-cancel-btn');
        const submitBtn = document.getElementById('voice-submit-btn');
        const rerecordBtn = document.getElementById('voice-rerecord-btn');
        const textSwitch = document.getElementById('voice-text-switch');

        if (startBtn) {
            startBtn.addEventListener('click', () => this.startRecording());
        }

        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stopRecording());
        }

        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.cancelRecording());
        }

        if (submitBtn) {
            submitBtn.addEventListener('click', () => this.submitTranscription());
        }

        if (rerecordBtn) {
            rerecordBtn.addEventListener('click', () => this.resetToIdle());
        }

        if (textSwitch) {
            textSwitch.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchToText();
            });
        }
    }

    async startRecording() {
        if (!this.voiceInput) {
            this.voiceInput = new VoiceInput({
                sessionId: this.sessionId,
                onTranscription: (text, duration) => {
                    this.transcription = text;
                    this.duration = duration;
                },
                onError: (error) => {
                    console.error('Voice error:', error);
                    this.resetToIdle();
                },
                onStateChange: (state, data) => {
                    this.handleStateChange(state, data);
                }
            });
        }

        await this.voiceInput.startRecording();
    }

    stopRecording() {
        if (this.voiceInput) {
            this.voiceInput.stopRecording();
        }
    }

    cancelRecording() {
        if (this.voiceInput) {
            this.voiceInput.cancelRecording();
        }
        this.resetToIdle();
    }

    handleStateChange(state, data = {}) {
        // Hide all states
        ['idle', 'recording', 'processing', 'transcribed'].forEach(s => {
            const el = document.getElementById(`voice-state-${s}`);
            if (el) el.style.display = 'none';
        });

        // Show current state
        const currentEl = document.getElementById(`voice-state-${state}`);
        if (currentEl) currentEl.style.display = 'block';

        // Update state-specific UI
        if (state === 'recording' && data.duration !== undefined) {
            const timeEl = document.getElementById('recording-time');
            if (timeEl) {
                timeEl.textContent = this.voiceInput.formatDuration(data.duration);
            }
        }

        if (state === 'transcribed') {
            const textEl = document.getElementById('transcription-text');
            if (textEl) {
                // Use data.transcription first (more reliable), fallback to this.transcription
                textEl.value = data.transcription || this.transcription;
            }
        }

        this.state = state;
    }

    resetToIdle() {
        this.transcription = '';
        this.handleStateChange('idle');
    }

    submitTranscription() {
        const textEl = document.getElementById('transcription-text');
        const finalText = textEl ? textEl.value : this.transcription;

        if (finalText.trim()) {
            this.onSubmit(finalText, 'voice', this.duration);
        }
    }

    switchToText() {
        if (this.voiceInput) {
            this.voiceInput.recordVoiceDecline();
        }
        this.onCancel('text_preferred');
    }

    destroy() {
        if (this.voiceInput) {
            this.voiceInput.destroy();
        }
    }
}

/**
 * Inline Voice Input Component
 * Provides inline recording experience without modal overlay
 */
class VoiceInputInline {
    constructor(inputId, buttonId, options = {}) {
        this.inputElement = document.getElementById(inputId);
        this.buttonElement = document.getElementById(buttonId);
        this.onTranscription = options.onTranscription || (() => {});
        this.sessionId = options.sessionId;

        this.voiceInput = null;
        this.statusOverlay = null;
        this.state = 'idle';

        this.init();
    }

    init() {
        if (!this.inputElement || !this.buttonElement) {
            console.error('VoiceInputInline: Required elements not found');
            return;
        }

        // Create status overlay element
        this.createStatusOverlay();

        // Attach button click handler
        this.buttonElement.addEventListener('click', (e) => {
            e.preventDefault();
            this.handleButtonClick();
        });

        // Initialize VoiceInput instance
        this.voiceInput = new VoiceInput({
            sessionId: this.sessionId,
            onTranscription: (text, duration) => {
                this.handleTranscription(text, duration);
            },
            onError: (error) => {
                this.handleError(error);
            },
            onStateChange: (state, data) => {
                this.handleStateChange(state, data);
            }
        });
    }

    createStatusOverlay() {
        // Create overlay element
        this.statusOverlay = document.createElement('div');
        this.statusOverlay.className = 'voice-status-overlay';

        // Insert before the form (parent of textarea)
        const form = this.inputElement.closest('form');
        if (form && form.parentNode) {
            form.parentNode.insertBefore(this.statusOverlay, form);
        }
    }

    handleButtonClick() {
        if (this.state === 'idle') {
            this.startRecording();
        } else if (this.state === 'recording') {
            this.stopRecording();
        }
    }

    async startRecording() {
        if (!this.voiceInput) return;

        this.updateButtonState('recording');
        await this.voiceInput.startRecording();
    }

    stopRecording() {
        if (!this.voiceInput) return;

        this.voiceInput.stopRecording();
    }

    updateButtonState(state) {
        this.state = state;
        this.buttonElement.setAttribute('data-state', state);

        // Add/remove recording class for styling
        if (state === 'recording') {
            this.buttonElement.classList.add('recording');
        } else {
            this.buttonElement.classList.remove('recording');
        }

        // Disable button during processing
        if (state === 'processing') {
            this.buttonElement.disabled = true;
        } else {
            this.buttonElement.disabled = false;
        }
    }

    showStatus(state, data = {}) {
        if (!this.statusOverlay) return;

        // Update overlay class
        this.statusOverlay.className = 'voice-status-overlay active ' + state;

        // Update content based on state
        let content = '';

        switch (state) {
            case 'recording':
                const duration = data.duration || 0;
                const formattedTime = this.formatDuration(duration);
                content = `
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <div class="voice-recording-dot"></div>
                        <span style="font-weight: 600;">Recording...</span>
                        <span class="voice-recording-time">${formattedTime}</span>
                    </div>
                `;
                break;

            case 'processing':
                content = `
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <div class="voice-processing-spinner"></div>
                        <span style="font-weight: 600;">Transcribing...</span>
                    </div>
                `;
                break;

            case 'error':
                content = `
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <span style="font-size: 20px;">⚠️</span>
                        <span style="font-weight: 600;">${data.message || 'An error occurred'}</span>
                    </div>
                `;
                break;

            default:
                // Hide overlay for idle/transcribed states
                this.statusOverlay.classList.remove('active');
                return;
        }

        this.statusOverlay.innerHTML = content;
    }

    handleStateChange(state, data = {}) {
        console.log('VoiceInputInline state change:', state, data);

        switch (state) {
            case 'recording':
                this.updateButtonState('recording');
                this.showStatus('recording', data);
                break;

            case 'processing':
                this.updateButtonState('processing');
                this.showStatus('processing');
                break;

            case 'transcribed':
                this.updateButtonState('idle');
                this.showStatus('idle');
                break;

            case 'error':
                this.updateButtonState('idle');
                this.showStatus('error', data);
                // Auto-hide error after 5 seconds
                setTimeout(() => {
                    if (this.state === 'idle') {
                        this.showStatus('idle');
                    }
                }, 5000);
                break;

            case 'idle':
                this.updateButtonState('idle');
                this.showStatus('idle');
                break;
        }
    }

    handleTranscription(text, duration) {
        // Populate textarea directly
        this.inputElement.value = text;

        // Focus the textarea so user can edit if needed
        this.inputElement.focus();

        // Call the onTranscription callback
        this.onTranscription(text, duration);
    }

    handleError(error) {
        console.error('VoiceInputInline error:', error);

        const errorMessages = {
            'Microphone permission denied': 'Microphone access denied. Please enable in browser settings.',
            'Failed to process recording': 'Connection failed. Please try again.',
            'No speech detected': 'No speech detected. Please speak clearly.'
        };

        const message = errorMessages[error] || error;
        this.handleStateChange('error', { error, message });
    }

    formatDuration(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    destroy() {
        if (this.voiceInput) {
            this.voiceInput.destroy();
        }
        if (this.statusOverlay && this.statusOverlay.parentNode) {
            this.statusOverlay.parentNode.removeChild(this.statusOverlay);
        }
    }
}

// Export for use
window.VoiceInput = VoiceInput;
window.VoiceInputModal = VoiceInputModal;
window.VoiceInputInline = VoiceInputInline;
