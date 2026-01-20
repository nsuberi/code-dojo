/**
 * Articulation Harness UI for post-challenge verbal explanation
 */

class ArticulationHarnessUI {
    constructor(containerId, submissionId) {
        this.container = document.getElementById(containerId);
        this.submissionId = submissionId;
        this.sessionId = null;
        this.gemsUI = null;
        this.voiceModal = null;
        this.messages = [];
        this.currentGoal = null;
        this.useVoice = true;
    }

    async init() {
        this.render();
        await this.startSession();
    }

    render() {
        if (!this.container) return;

        this.container.innerHTML = `
            <div class="articulation-harness" id="articulation-harness">
                <div class="articulation-header">
                    <img src="/static/assets/socratic-sensei.png" alt="Digi Trainer" class="sensei-avatar">
                    <div class="header-text">
                        <h2>🎤 Talk Through Your Solution</h2>
                        <p>Practice explaining your code like you would to a colleague</p>
                    </div>
                </div>

                <div class="articulation-layout">
                    <!-- Sidebar with gems -->
                    <div class="articulation-sidebar">
                        <div id="gems-container"></div>
                    </div>

                    <!-- Main chat area -->
                    <div class="articulation-main">
                        <div class="chat-messages" id="articulation-messages">
                            <div class="loading-indicator">
                                <div class="spinner"></div>
                                Starting session...
                            </div>
                        </div>

                        <!-- Voice input area -->
                        <div class="input-area" id="input-area">
                            <div id="voice-input-container"></div>
                            <div id="text-input-container" style="display: none;">
                                <div class="text-input-form">
                                    <textarea
                                        id="text-input"
                                        placeholder="Type your explanation..."
                                        rows="3"
                                    ></textarea>
                                    <div class="input-actions">
                                        <button class="btn btn-secondary" id="switch-to-voice-btn">
                                            🎤 Switch to voice
                                        </button>
                                        <button class="btn btn-primary" id="send-text-btn">
                                            Send
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Initialize gems UI
        this.gemsUI = new GemsUI('gems-container', this.submissionId);
        this.gemsUI.onGoalClick = (goalId) => this.selectGoal(goalId);

        this.attachEventListeners();
    }

    attachEventListeners() {
        const sendTextBtn = document.getElementById('send-text-btn');
        const switchToVoiceBtn = document.getElementById('switch-to-voice-btn');
        const textInput = document.getElementById('text-input');

        if (sendTextBtn) {
            sendTextBtn.addEventListener('click', () => this.sendTextMessage());
        }

        if (switchToVoiceBtn) {
            switchToVoiceBtn.addEventListener('click', () => this.switchToVoice());
        }

        if (textInput) {
            textInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendTextMessage();
                }
            });
        }
    }

    async startSession() {
        try {
            const response = await fetch(`/api/agent/submissions/${this.submissionId}/articulation/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const data = await response.json();

            if (data.error) {
                this.showError(data.error);
                return;
            }

            this.sessionId = data.session_id;
            this.addMessage('assistant', data.opening_message);
            await this.gemsUI.loadProgress();

            // Initialize voice input
            this.initVoiceInput();

        } catch (error) {
            this.showError('Failed to start session: ' + error.message);
        }
    }

    initVoiceInput() {
        const voiceContainer = document.getElementById('voice-input-container');
        if (!voiceContainer) return;

        this.voiceModal = new VoiceInputModal('voice-input-container', {
            sessionId: this.sessionId,
            onSubmit: (text, mode, duration) => {
                this.sendMessage(text, mode, duration);
            },
            onCancel: (reason) => {
                if (reason === 'text_preferred') {
                    this.switchToText();
                }
            }
        });

        this.voiceModal.render();
    }

    switchToText() {
        this.useVoice = false;
        document.getElementById('voice-input-container').style.display = 'none';
        document.getElementById('text-input-container').style.display = 'block';
    }

    switchToVoice() {
        this.useVoice = true;
        document.getElementById('voice-input-container').style.display = 'block';
        document.getElementById('text-input-container').style.display = 'none';
    }

    async sendTextMessage() {
        const textInput = document.getElementById('text-input');
        if (!textInput) return;

        const message = textInput.value.trim();
        if (!message) return;

        textInput.value = '';
        await this.sendMessage(message, 'text');
    }

    async sendMessage(message, inputMode = 'text', voiceDuration = null) {
        this.addMessage('user', message, inputMode);

        try {
            const response = await fetch(`/api/agent/submissions/${this.submissionId}/articulation/message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    message: message,
                    input_mode: inputMode
                })
            });

            const data = await response.json();

            if (data.error) {
                this.showError(data.error);
                return;
            }

            this.addMessage('assistant', data.response);

            // Update gems if status changed
            if (data.gem_unlocked) {
                await this.gemsUI.loadProgress();
                this.showGemUnlockAnimation(data.gem_status);
            }

            // Update engagement
            if (data.engagement) {
                this.updateEngagementUI(data.engagement);
            }

            // Check if all complete
            if (data.all_complete) {
                this.showCompletionCelebration(data.engagement);
            }

        } catch (error) {
            this.showError('Failed to send message: ' + error.message);
        }
    }

    async selectGoal(goalId) {
        // This would focus the conversation on a specific goal
        const message = `Let's discuss goal ${goalId}`;
        await this.sendMessage(message, 'text');
    }

    addMessage(role, content, inputMode = null) {
        const messagesContainer = document.getElementById('articulation-messages');
        if (!messagesContainer) return;

        // Remove loading indicator if present
        const loadingEl = messagesContainer.querySelector('.loading-indicator');
        if (loadingEl) loadingEl.remove();

        const messageEl = document.createElement('div');
        messageEl.className = `chat-message chat-message-${role}`;

        if (role === 'assistant') {
            messageEl.innerHTML = `
                <img src="/static/assets/socratic-sensei.png" alt="Digi Trainer" class="message-avatar">
                <div class="message-content">
                    <div class="message-text">${this.formatMessage(content)}</div>
                </div>
            `;
        } else {
            messageEl.innerHTML = `
                <div class="message-content">
                    <div class="message-meta">${inputMode === 'voice' ? '🎤 ' : ''}You</div>
                    <div class="message-text">${this.escapeHtml(content)}</div>
                </div>
            `;
        }

        messagesContainer.appendChild(messageEl);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    formatMessage(content) {
        // Basic formatting - convert markdown-like syntax
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showError(message) {
        const messagesContainer = document.getElementById('articulation-messages');
        if (!messagesContainer) return;

        const errorEl = document.createElement('div');
        errorEl.className = 'chat-error';
        errorEl.textContent = message;
        messagesContainer.appendChild(errorEl);
    }

    showGemUnlockAnimation(status) {
        const overlay = document.createElement('div');
        overlay.className = 'gem-unlock-overlay';
        overlay.innerHTML = `
            <div class="gem-unlock-animation">
                <span class="gem-icon-large">${status === 'passed' ? '💎' : '🔵'}</span>
                <span class="gem-message">${status === 'passed' ? 'Mastery Achieved!' : 'Great Engagement!'}</span>
            </div>
        `;
        document.body.appendChild(overlay);

        setTimeout(() => {
            overlay.remove();
        }, 2000);
    }

    showCompletionCelebration(engagement) {
        const overlay = document.createElement('div');
        overlay.className = 'completion-overlay';
        overlay.innerHTML = `
            <div class="completion-content">
                <h2>🎉 Amazing Work!</h2>
                <p>You've explored all the key concepts.</p>
                <div class="completion-stats">
                    <span>💎 ${engagement.passed} mastered</span>
                    <span>🔵 ${engagement.engaged} engaged</span>
                </div>
                ${engagement.can_request_instructor ? '<p>✨ Instructor feedback is now available!</p>' : ''}
                <button class="btn btn-primary" onclick="this.closest('.completion-overlay').remove()">Continue</button>
            </div>
        `;
        document.body.appendChild(overlay);
    }

    updateEngagementUI(engagement) {
        // Update any engagement indicators in the UI
        // The gems UI will handle most of this
    }
}

// Export for use
window.ArticulationHarnessUI = ArticulationHarnessUI;
