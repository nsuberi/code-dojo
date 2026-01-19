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

        // Create media recorder
        this.mediaRecorder = new MediaRecorder(this.stream, {
            mimeType: 'audio/webm;codecs=opus'
        });

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

        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });

        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');
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
                        <button class="voice-record-btn" id="voice-start-btn">
                            <span class="mic-icon">🎤</span>
                            <span>Tap to Start Recording</span>
                        </button>
                        <p class="voice-hint">Or <a href="#" id="voice-text-switch">type instead</a></p>
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
                textEl.value = this.transcription;
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

// Export for use
window.VoiceInput = VoiceInput;
window.VoiceInputModal = VoiceInputModal;
