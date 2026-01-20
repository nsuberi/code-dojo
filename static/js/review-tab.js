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
        this.voiceInline = null;
    }

    async init() {
        console.log('[ReviewTab] Initializing with goalId:', this.goalId, 'submissionId:', this.submissionId);

        // Setup gem click handlers
        this.setupGemClickHandlers();

        // Setup Digi-Trainer form
        this.setupDigiTrainerForm();

        console.log('[ReviewTab] Initialization complete');
    }

    setupGemClickHandlers() {
        const gems = document.querySelectorAll('.gem-item');
        console.log('[ReviewTab] Found gem items:', gems.length);

        gems.forEach((gem, index) => {
            const computedStyle = window.getComputedStyle(gem);
            console.log(`[ReviewTab] Gem ${index} display:`, computedStyle.display, 'visibility:', computedStyle.visibility);

            gem.addEventListener('click', () => {
                const goalId = gem.dataset.goalId;
                const title = gem.dataset.title;
                console.log('[ReviewTab] Gem clicked:', goalId, title);
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

        // Voice input button is now handled by VoiceInputInline
        // No need for separate handler here
    }

    initVoiceInput() {
        if (this.voiceInline) return; // Already initialized

        console.log('[ReviewTab] Initializing inline voice input');

        this.voiceInline = new VoiceInputInline(
            'digi-trainer-input',
            'voice-input-btn',
            {
                sessionId: this.digiTrainerSessionId,
                onTranscription: (text, duration) => {
                    // Text is already in textarea via VoiceInputInline
                    // Optionally auto-send the message
                    // For now, let user review and click Send manually
                    console.log('[ReviewTab] Transcription received:', text.substring(0, 50) + '...');
                }
            }
        );
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
                const response = await fetch(`/api/agent/submissions/${this.submissionId}/articulation/start`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        core_goal_id: coreGoalId
                    })
                });

                const data = await response.json();

                if (data.session_id) {
                    this.digiTrainerSessionId = data.session_id;
                    // Initialize voice input now that we have a session ID
                    this.initVoiceInput();
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
            const response = await fetch(`/api/agent/submissions/${this.submissionId}/articulation/message`, {
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

// Load PR stats and populate
async function loadPRStats(submissionId) {
    try {
        const response = await fetch(`/submissions/${submissionId}/files`);
        const data = await response.json();

        // Calculate totals
        const totalFiles = data.files.length;
        const totalAdditions = data.files.reduce((sum, f) => sum + f.additions, 0);
        const totalDeletions = data.files.reduce((sum, f) => sum + f.deletions, 0);

        // Update stats display
        const statsContainer = document.querySelector(`#pr-stats-${submissionId}`);
        if (statsContainer) {
            const filesEl = statsContainer.querySelector('[data-stat="files"]');
            const additionsEl = statsContainer.querySelector('[data-stat="additions"]');
            const deletionsEl = statsContainer.querySelector('[data-stat="deletions"]');

            if (filesEl) filesEl.textContent = totalFiles;
            if (additionsEl) additionsEl.textContent = `+${totalAdditions}`;
            if (deletionsEl) deletionsEl.textContent = `-${totalDeletions}`;
        }

        return data.files;
    } catch (error) {
        console.error('Error loading PR stats:', error);
    }
}

// Load and display code changes
async function loadCodeChanges(submissionId) {
    const diffViewer = document.getElementById('diff-viewer');

    try {
        const response = await fetch(`/submissions/${submissionId}/files`);
        const data = await response.json();
        const files = data.files;

        // Clear loading placeholder
        if (diffViewer) {
            diffViewer.innerHTML = '';
        }

        // Show file list
        const fileList = document.getElementById('file-list');
        if (fileList) {
            fileList.style.display = 'block';
        }

        // Render file tree
        renderFileTree(files);

        // Auto-expand first file
        if (files.length > 0) {
            renderFileDiff(files[0], 0);
        }
    } catch (error) {
        console.error('Error loading code changes:', error);
        if (diffViewer) {
            diffViewer.innerHTML = `
                <div class="no-diff" style="color: #ef4444;">
                    Error loading code changes: ${error.message}
                </div>
            `;
        }
    }
}

// Render file tree list
function renderFileTree(files) {
    const fileListEl = document.getElementById('file-list');
    if (!fileListEl) return;

    let html = '<div class="file-tree">';
    files.forEach((file, index) => {
        const statusIcon = getFileStatusIcon(file.status);
        const statusClass = `file-status-${file.status}`;

        html += `
            <div class="file-tree-item ${statusClass}" onclick="toggleFileDiff(${index})">
                <div class="file-info">
                    <span class="file-icon">${statusIcon}</span>
                    <span class="file-name">${escapeHtmlUtil(file.filename)}</span>
                </div>
                <div class="file-stats">
                    <span class="text-success">+${file.additions}</span>
                    <span class="text-danger">-${file.deletions}</span>
                    <svg class="expand-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                </div>
            </div>
            <div id="diff-container-${index}" class="diff-container" style="display:none;">
                <!-- Diff content goes here -->
            </div>
        `;
    });
    html += '</div>';

    fileListEl.innerHTML = html;

    // Store files data for later access
    window.prFiles = files;
}

// Toggle file diff display
function toggleFileDiff(fileIndex) {
    const container = document.getElementById(`diff-container-${fileIndex}`);
    if (!container) return;

    const isVisible = container.style.display !== 'none';

    if (isVisible) {
        container.style.display = 'none';
    } else {
        // Load diff if not already loaded
        if (container.innerHTML === '') {
            renderFileDiff(window.prFiles[fileIndex], fileIndex);
        }
        container.style.display = 'block';
    }
}

// Render individual file diff
function renderFileDiff(file, fileIndex) {
    const container = document.getElementById(`diff-container-${fileIndex}`);
    if (!container) return;

    if (!file.patch) {
        container.innerHTML = '<div class="no-diff">No diff available (binary file or too large)</div>';
        return;
    }

    // Parse and render diff
    const diffHtml = parseDiffToHtml(file.patch);
    container.innerHTML = `
        <div class="diff-viewer">
            <div class="diff-file-header">
                <span class="diff-file-name">${escapeHtmlUtil(file.filename)}</span>
            </div>
            <div class="diff-content">
                ${diffHtml}
            </div>
        </div>
    `;
}

// Parse unified diff patch to HTML
function parseDiffToHtml(patch) {
    const lines = patch.split('\n');
    let html = '';
    let oldLineNum = 0;
    let newLineNum = 0;

    lines.forEach(line => {
        if (line.startsWith('@@')) {
            // Hunk header
            const match = line.match(/@@ -(\d+),?\d* \+(\d+),?\d* @@/);
            if (match) {
                oldLineNum = parseInt(match[1]);
                newLineNum = parseInt(match[2]);
            }
            html += `<div class="diff-line hunk"><div class="line-content">${escapeHtmlUtil(line)}</div></div>`;
        } else if (line.startsWith('+') && !line.startsWith('+++')) {
            html += `
                <div class="diff-line add">
                    <div class="line-number"></div>
                    <div class="line-number">${newLineNum}</div>
                    <div class="line-content">${escapeHtmlUtil(line)}</div>
                </div>
            `;
            newLineNum++;
        } else if (line.startsWith('-') && !line.startsWith('---')) {
            html += `
                <div class="diff-line remove">
                    <div class="line-number">${oldLineNum}</div>
                    <div class="line-number"></div>
                    <div class="line-content">${escapeHtmlUtil(line)}</div>
                </div>
            `;
            oldLineNum++;
        } else if (line.startsWith(' ')) {
            html += `
                <div class="diff-line context">
                    <div class="line-number">${oldLineNum}</div>
                    <div class="line-number">${newLineNum}</div>
                    <div class="line-content">${escapeHtmlUtil(line)}</div>
                </div>
            `;
            oldLineNum++;
            newLineNum++;
        }
    });

    return html;
}

// Helper functions
function getFileStatusIcon(status) {
    switch(status) {
        case 'added': return '📄+';
        case 'modified': return '📝';
        case 'removed': return '🗑️';
        case 'renamed': return '📋';
        default: return '📄';
    }
}

function escapeHtmlUtil(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Helper function to get user-friendly descriptions for steps
function getDisplayDescription(step, description) {
    const stepDescriptions = {
        'initialize': 'Setting up analysis',
        'route_analysis': 'Determining analysis type',
        'run_basic_review': 'Analyzing your code',
        'basic_review.detect_approach': 'Identifying your implementation approach',
        'basic_review.analyze_architecture': 'Mapping code structure',
        'basic_review.evaluate_universal': 'Checking best practices',
        'basic_review.evaluate_approach': 'Evaluating approach-specific patterns',
        'basic_review.evaluate_tests': 'Analyzing test coverage',
        'basic_review.analyze_security': 'Running security checks',
        'basic_review.generate_alternatives': 'Comparing alternative solutions',
        'basic_review.synthesize': 'Synthesizing feedback',
        'run_arch_analysis': 'Analyzing architecture',
        'enrich_feedback': 'Cross-referencing insights',
        'synthesize': 'Creating personalized feedback',
        'save_results': 'Saving results'
    };

    return stepDescriptions[step] || description;
}

// Progress tracking via Server-Sent Events
function trackAnalysisProgress(submissionId) {
    const progressContainer = document.getElementById(`analysis-progress-${submissionId}`);
    if (!progressContainer) return;

    const progressBar = progressContainer.querySelector('.progress-bar-fill');
    const progressPercentage = progressContainer.querySelector('.progress-percentage');
    const stepDescription = progressContainer.querySelector('.current-step-description');
    const steps = progressContainer.querySelectorAll('.step');

    // Connect to SSE endpoint
    const eventSource = new EventSource(`/submissions/${submissionId}/progress-stream`);

    eventSource.addEventListener('message', (event) => {
        const data = JSON.parse(event.data);

        // Update progress bar
        progressBar.style.width = data.progress + '%';
        progressPercentage.textContent = data.progress + '%';

        // Update step description with user-friendly message
        const displayDescription = getDisplayDescription(data.step, data.description);
        stepDescription.textContent = displayDescription;

        // Handle sub-steps (e.g., "basic_review.detect_approach")
        const mainStep = data.step.split('.')[0];

        // Update step indicators
        steps.forEach(step => {
            const stepName = step.getAttribute('data-step');
            const icon = step.querySelector('.step-icon');

            // Check if this is the current step or its parent
            if (stepName === data.step || stepName === mainStep) {
                icon.textContent = '●';  // Active
                step.classList.add('active');
                step.classList.remove('complete');
            } else if (data.progress > getStepProgress(stepName)) {
                icon.textContent = '✓';  // Complete
                step.classList.add('complete');
                step.classList.remove('active');
            }
        });

        // Complete
        if (data.status === 'complete') {
            eventSource.close();
            setTimeout(() => {
                location.reload();  // Refresh to show feedback
            }, 1000);
        }

        // Error
        if (data.status === 'error') {
            eventSource.close();
            stepDescription.textContent = data.description || 'Error during analysis. Please refresh the page.';
            stepDescription.style.color = '#ef4444';
        }
    });

    eventSource.addEventListener('error', (error) => {
        console.error('SSE error:', error);
        eventSource.close();
        stepDescription.textContent = 'Connection error. Please refresh the page.';
        stepDescription.style.color = '#ef4444';
    });

    function getStepProgress(stepName) {
        const weights = {
            'initialize': 5,
            'route_analysis': 8,
            'run_basic_review': 58,
            'run_arch_analysis': 78,
            'enrich_feedback': 85,
            'synthesize': 95,
            'save_results': 100
        };
        return weights[stepName] || 0;
    }
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

    // Get submissionId from the gems container or pr-stats
    let submissionId = gemsContainer ? gemsContainer.dataset.submissionId : null;

    // Also check pr-stats for submissionId
    if (!submissionId) {
        const prStats = document.querySelector('[data-submission-id]');
        if (prStats) {
            submissionId = prStats.dataset.submissionId;
        }
    }

    if (goalId && submissionId) {
        window.reviewTab = new ReviewTab(goalId, submissionId);
        window.reviewTab.init();
    }

    // Auto-load PR stats and code changes when review tab is opened
    if (submissionId) {
        loadPRStats(submissionId);
        loadCodeChanges(submissionId);
    }

    // Auto-start progress tracking for pending submissions
    const progressContainers = document.querySelectorAll('.analysis-progress');
    progressContainers.forEach(container => {
        const sid = container.getAttribute('data-submission-id');
        if (sid) {
            trackAnalysisProgress(sid);
        }
    });
});
