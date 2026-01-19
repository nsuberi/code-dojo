/**
 * Review Tab JavaScript (Section 5)
 * Orchestrates GemsUI + DigiTrainerUI in the Review tab
 */

class ReviewTab {
    constructor(goalId, submissionId) {
        this.goalId = goalId;
        this.submissionId = submissionId;
        this.currentCoreGoalId = null;
        this.digiTrainerSessionId = null;
    }

    async init() {
        // Setup gem click handlers
        this.setupGemClickHandlers();

        // Setup Digi-Trainer form
        this.setupDigiTrainerForm();

        // Check if we should auto-switch to review tab (if submission exists)
        this.checkAutoSwitchToReview();
    }

    setupGemClickHandlers() {
        const gems = document.querySelectorAll('.gem-item');
        gems.forEach(gem => {
            gem.addEventListener('click', () => {
                const goalId = gem.dataset.goalId;
                const title = gem.dataset.title;
                this.startDigiTrainer(goalId, title);
            });
        });
    }

    setupDigiTrainerForm() {
        const form = document.getElementById('digi-trainer-form');
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.sendDigiTrainerMessage();
            });
        }
    }

    async startDigiTrainer(coreGoalId, title) {
        this.currentCoreGoalId = coreGoalId;

        // Show the chat interface
        const chatContainer = document.getElementById('digi-trainer-chat');
        const topicTitle = document.getElementById('chat-topic-title');
        const messagesContainer = document.getElementById('digi-trainer-messages');

        if (chatContainer && topicTitle && messagesContainer) {
            chatContainer.style.display = 'block';
            topicTitle.textContent = title;
            messagesContainer.innerHTML = '';

            // Start Digi-Trainer session
            try {
                const response = await fetch(`/api/agent/articulation/${this.submissionId}/start`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        core_goal_id: coreGoalId
                    })
                });

                const data = await response.json();

                if (data.session_id) {
                    this.digiTrainerSessionId = data.session_id;
                }

                if (data.opening_message) {
                    this.addMessage('assistant', data.opening_message);
                }
            } catch (error) {
                console.error('Error starting Digi-Trainer session:', error);
                this.addMessage('assistant', 'Hello! Let\'s discuss your understanding of this topic. Can you explain how you approached this concept in your implementation?');
            }
        }
    }

    async sendDigiTrainerMessage() {
        const input = document.getElementById('digi-trainer-input');
        const sendBtn = document.getElementById('send-digi-trainer-btn');

        if (!input || !sendBtn) return;

        const message = input.value.trim();
        if (!message) return;

        // Disable button and show sending state
        sendBtn.disabled = true;
        sendBtn.textContent = 'Sending...';

        // Add user message to chat
        this.addMessage('user', message);

        // Clear input
        input.value = '';

        try {
            const response = await fetch(`/api/agent/articulation/${this.submissionId}/message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.digiTrainerSessionId,
                    message: message
                })
            });

            const data = await response.json();

            if (data.response) {
                this.addMessage('assistant', data.response);
            }

            // Update gem status if provided
            if (data.engaged) {
                this.updateGemStatus(this.currentCoreGoalId, 'engaged');
            }

            if (data.passed) {
                this.updateGemStatus(this.currentCoreGoalId, 'passed');
            }

        } catch (error) {
            console.error('Error sending message to Digi-Trainer:', error);
            this.addMessage('assistant', 'I apologize, but I encountered an error. Please try again.');
        } finally {
            sendBtn.disabled = false;
            sendBtn.textContent = 'Send';
        }
    }

    addMessage(role, content) {
        const messagesContainer = document.getElementById('digi-trainer-messages');
        if (!messagesContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = role === 'user' ? 'user-message' : 'sensei-message';
        messageDiv.innerHTML = `<p>${this.escapeHtml(content)}</p>`;
        messagesContainer.appendChild(messageDiv);

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    updateGemStatus(coreGoalId, status) {
        const gem = document.querySelector(`.gem-item[data-goal-id="${coreGoalId}"]`);
        if (gem) {
            gem.classList.remove('locked', 'engaged', 'passed');
            gem.classList.add(status);

            const icon = gem.querySelector('.gem-icon');
            if (icon) {
                if (status === 'passed') {
                    icon.textContent = '\uD83D\uDC8E'; // Diamond emoji
                } else if (status === 'engaged') {
                    icon.textContent = '\uD83D\uDD35'; // Blue circle
                }
            }
        }

        // Check if Sensei session should be unlocked
        this.checkSenseiUnlock();
    }

    checkSenseiUnlock() {
        const engagedGems = document.querySelectorAll('.gem-item.engaged, .gem-item.passed');
        const senseiSection = document.getElementById('sensei-session-section');

        if (engagedGems.length >= 1 && senseiSection) {
            // Update to show unlocked state
            const lockedDiv = senseiSection.querySelector('.sensei-locked');
            if (lockedDiv) {
                senseiSection.innerHTML = `
                    <div class="sensei-unlocked">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                            <path d="M2 17l10 5 10-5"></path>
                            <path d="M2 12l10 5 10-5"></path>
                        </svg>
                        <div>
                            <p>Your Sensei is here to help you level up. They'll assess where you are in your learning journey, identify concepts you're still working to embody, and suggest your next training exercises.</p>
                            <a href="/scheduling/book?goal_id=${this.goalId}" class="btn btn-primary">Schedule a Sensei Session</a>
                        </div>
                    </div>
                `;
            }
        }
    }

    checkAutoSwitchToReview() {
        // If there's a submission and we're coming from a submission redirect,
        // auto-switch to the review tab
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('tab') === 'review') {
            switchTab('review');
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Global functions for inline event handlers
function closeDigiTrainerChat() {
    const chatContainer = document.getElementById('digi-trainer-chat');
    if (chatContainer) {
        chatContainer.style.display = 'none';
    }
}

function endDigiTrainerDiscussion() {
    // Close the chat
    closeDigiTrainerChat();

    // Show synthesis modal or feedback
    alert('Discussion ended. Your progress has been saved.');
}

// Initialize ReviewTab when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Get goalId - try planning-harness first, then gems-container
    let goalId = null;
    const planningHarness = document.getElementById('planning-harness');
    const gemsContainer = document.getElementById('gems-container');

    if (planningHarness && planningHarness.dataset.goalId) {
        goalId = planningHarness.dataset.goalId;
    } else if (gemsContainer && gemsContainer.dataset.goalId) {
        goalId = gemsContainer.dataset.goalId;
    }

    // Get submissionId from the gems container
    const submissionId = gemsContainer ? gemsContainer.dataset.submissionId : null;

    if (goalId && submissionId) {
        window.reviewTab = new ReviewTab(goalId, submissionId);
        window.reviewTab.init();
    }
});
