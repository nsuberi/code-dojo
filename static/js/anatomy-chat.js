/**
 * Anatomy Chat - Vanilla JS for Socratic dialogue feature
 */

(function() {
    'use strict';

    // State
    let submissionId = null;
    let currentConversationId = null;
    let currentTopicId = null;
    let currentTopicName = null;
    let elements = [];
    let isLoading = false;

    // DOM Elements
    const anatomySection = document.getElementById('anatomy-section');
    if (!anatomySection) return;

    const elementsList = document.getElementById('anatomy-elements-list');
    const chatContainer = document.getElementById('chat-container');
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const chatSendBtn = document.getElementById('chat-send-btn');
    const chatEndBtn = document.getElementById('chat-end-btn');
    const chatTopicName = document.getElementById('chat-topic-name');
    const modalOverlay = document.getElementById('synthesis-modal-overlay');
    const modalContent = document.getElementById('synthesis-modal-content');
    const modalCloseBtn = document.getElementById('synthesis-modal-close');
    const modalDoneBtn = document.getElementById('synthesis-modal-done');

    // Get submission ID from data attribute
    submissionId = anatomySection.dataset.submissionId;

    /**
     * Initialize the anatomy feature
     */
    function init() {
        loadAnatomyElements();
        setupEventListeners();
    }

    /**
     * Set up event listeners
     */
    function setupEventListeners() {
        // Send message on button click
        if (chatSendBtn) {
            chatSendBtn.addEventListener('click', sendMessage);
        }

        // Send message on Enter (but Shift+Enter for new line)
        if (chatInput) {
            chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });

            // Auto-resize textarea
            chatInput.addEventListener('input', () => {
                chatInput.style.height = 'auto';
                chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
            });
        }

        // End conversation
        if (chatEndBtn) {
            chatEndBtn.addEventListener('click', endConversation);
        }

        // Modal close buttons
        if (modalCloseBtn) {
            modalCloseBtn.addEventListener('click', closeModal);
        }
        if (modalDoneBtn) {
            modalDoneBtn.addEventListener('click', closeModal);
        }
        if (modalOverlay) {
            modalOverlay.addEventListener('click', (e) => {
                if (e.target === modalOverlay) closeModal();
            });
        }

        // Escape key closes modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modalOverlay && modalOverlay.classList.contains('active')) {
                closeModal();
            }
        });
    }

    /**
     * Load anatomy elements from API
     */
    async function loadAnatomyElements() {
        if (!elementsList) return;

        elementsList.innerHTML = '<div class="anatomy-loading"><div class="spinner"></div> Loading topics...</div>';

        try {
            const response = await fetch(`/submissions/${submissionId}/anatomy`);
            const data = await response.json();

            if (data.error) {
                elementsList.innerHTML = `<p class="error">${data.error}</p>`;
                return;
            }

            elements = data.elements || [];
            renderElements();

        } catch (error) {
            console.error('Error loading anatomy elements:', error);
            elementsList.innerHTML = '<p class="error">Failed to load discussion topics.</p>';
        }
    }

    /**
     * Render anatomy elements in sidebar
     */
    function renderElements() {
        if (!elementsList) return;

        if (elements.length === 0) {
            elementsList.innerHTML = '<p class="empty-state">No discussion topics available.</p>';
            return;
        }

        elementsList.innerHTML = elements.map(el => `
            <div class="anatomy-element ${el.active_conversation_id ? 'has-conversation' : ''}"
                 data-id="${el.id}"
                 data-topic-id="${el.topic_id || ''}"
                 data-topic-name="${escapeHtml(el.name)}"
                 data-description="${escapeHtml(el.description || '')}"
                 data-analogies="${escapeHtml(el.analogies || '')}"
                 data-conversation-id="${el.active_conversation_id || ''}"
                 onclick="window.AnatomyChat.selectElement(this)">
                <div class="anatomy-element-name">${escapeHtml(el.name)}</div>
                ${el.description ? `<div class="anatomy-element-desc">${escapeHtml(el.description)}</div>` : ''}
                <span class="anatomy-element-badge ${el.source === 'admin' ? 'admin' : 'ai'}">
                    ${el.source === 'admin' ? 'Topic' : 'Detected'}
                </span>
            </div>
        `).join('');
    }

    /**
     * Select an element to discuss
     */
    function selectElement(elementDiv) {
        // Update active state
        document.querySelectorAll('.anatomy-element').forEach(el => el.classList.remove('active'));
        elementDiv.classList.add('active');

        // Get element data
        const topicId = elementDiv.dataset.topicId || null;
        const topicName = elementDiv.dataset.topicName;
        const description = elementDiv.dataset.description;
        const analogies = elementDiv.dataset.analogies;
        const conversationId = elementDiv.dataset.conversationId;

        currentTopicId = topicId;
        currentTopicName = topicName;

        // Update chat header
        if (chatTopicName) {
            chatTopicName.textContent = topicName;
        }

        // Show chat container, hide empty state
        if (chatContainer) {
            chatContainer.style.display = 'flex';
        }
        const emptyState = document.getElementById('chat-empty-state');
        if (emptyState) {
            emptyState.style.display = 'none';
        }

        // If there's an existing conversation, load it
        if (conversationId) {
            currentConversationId = conversationId;
            loadConversation(conversationId);
        } else {
            // Start new conversation
            currentConversationId = null;
            startNewConversation(topicId, topicName, description, analogies);
        }
    }

    /**
     * Start a new conversation
     */
    async function startNewConversation(topicId, topicName, description, analogies) {
        clearChat();
        showTypingIndicator();
        setLoading(true);

        try {
            const response = await fetch(`/submissions/${submissionId}/anatomy/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    topic_id: topicId || undefined,
                    topic_name: topicName,
                    topic_description: description,
                    analogies: analogies
                })
            });

            const data = await response.json();
            hideTypingIndicator();

            if (data.error) {
                addMessage('assistant', `Error: ${data.error}`);
                return;
            }

            currentConversationId = data.conversation_id;

            // Update element with conversation ID
            const elementDiv = document.querySelector(`.anatomy-element[data-topic-name="${escapeHtml(topicName)}"]`);
            if (elementDiv) {
                elementDiv.dataset.conversationId = currentConversationId;
                elementDiv.classList.add('has-conversation');
            }

            // Render conversation messages
            if (data.conversation && data.conversation.messages) {
                renderConversation(data.conversation);
            }

        } catch (error) {
            hideTypingIndicator();
            console.error('Error starting conversation:', error);
            addMessage('assistant', 'Failed to start conversation. Please try again.');
        } finally {
            setLoading(false);
        }
    }

    /**
     * Load an existing conversation
     */
    async function loadConversation(conversationId) {
        clearChat();
        setLoading(true);

        try {
            const response = await fetch(`/submissions/${submissionId}/anatomy/conversation/${conversationId}`);
            const data = await response.json();

            if (data.error) {
                addMessage('assistant', `Error: ${data.error}`);
                return;
            }

            if (data.conversation) {
                renderConversation(data.conversation);

                // If conversation ended, show synthesis
                if (data.conversation.status === 'ended' && data.conversation.synthesis_markdown) {
                    showSynthesisModal(data.conversation.synthesis_markdown);
                }
            }

        } catch (error) {
            console.error('Error loading conversation:', error);
            addMessage('assistant', 'Failed to load conversation.');
        } finally {
            setLoading(false);
        }
    }

    /**
     * Render a conversation's messages
     */
    function renderConversation(conversation) {
        clearChat();

        if (conversation.messages && conversation.messages.length > 0) {
            conversation.messages.forEach(msg => {
                addMessage(msg.role, msg.content, false);
            });
        }

        scrollToBottom();
    }

    /**
     * Send a message
     */
    async function sendMessage() {
        if (!chatInput || isLoading) return;

        const message = chatInput.value.trim();
        if (!message) return;

        // Clear input
        chatInput.value = '';
        chatInput.style.height = 'auto';

        // Add user message to chat
        addMessage('user', message);

        // Show typing indicator
        showTypingIndicator();
        setLoading(true);

        try {
            const response = await fetch(`/submissions/${submissionId}/anatomy/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    conversation_id: currentConversationId,
                    message: message
                })
            });

            const data = await response.json();
            hideTypingIndicator();

            if (data.error) {
                addMessage('assistant', `Error: ${data.error}`);
                return;
            }

            // Add assistant response
            addMessage('assistant', data.response);

        } catch (error) {
            hideTypingIndicator();
            console.error('Error sending message:', error);
            addMessage('assistant', 'Failed to send message. Please try again.');
        } finally {
            setLoading(false);
        }
    }

    /**
     * End the conversation and show synthesis
     */
    async function endConversation() {
        if (!currentConversationId || isLoading) return;

        if (!confirm('End this discussion and see your learning summary?')) return;

        setLoading(true);
        showTypingIndicator();

        try {
            const response = await fetch(`/submissions/${submissionId}/anatomy/end`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    conversation_id: currentConversationId
                })
            });

            const data = await response.json();
            hideTypingIndicator();

            if (data.error) {
                alert('Error: ' + data.error);
                return;
            }

            // Show synthesis modal
            if (data.synthesis) {
                showSynthesisModal(data.synthesis);
            }

            // Reset conversation state
            currentConversationId = null;

            // Refresh elements list to update states
            loadAnatomyElements();

        } catch (error) {
            hideTypingIndicator();
            console.error('Error ending conversation:', error);
            alert('Failed to end conversation. Please try again.');
        } finally {
            setLoading(false);
        }
    }

    /**
     * Add a message to the chat
     */
    function addMessage(role, content, scroll = true) {
        if (!chatMessages) return;

        const avatarHtml = role === 'assistant'
            ? `<img src="/static/assets/socratic-sensei.png" alt="Sensei" class="chat-message-avatar">`
            : `<div class="chat-message-avatar user-avatar">You</div>`;

        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role}`;
        messageDiv.innerHTML = `
            ${avatarHtml}
            <div class="chat-message-content">${escapeHtml(content)}</div>
        `;

        chatMessages.appendChild(messageDiv);

        if (scroll) {
            scrollToBottom();
        }
    }

    /**
     * Clear chat messages
     */
    function clearChat() {
        if (chatMessages) {
            chatMessages.innerHTML = '';
        }
    }

    /**
     * Show typing indicator
     */
    function showTypingIndicator() {
        if (!chatMessages) return;

        const indicator = document.createElement('div');
        indicator.className = 'chat-message assistant';
        indicator.id = 'typing-indicator';
        indicator.innerHTML = `
            <img src="/static/assets/socratic-sensei.png" alt="Sensei" class="chat-message-avatar">
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        chatMessages.appendChild(indicator);
        scrollToBottom();
    }

    /**
     * Hide typing indicator
     */
    function hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    /**
     * Show synthesis modal
     */
    function showSynthesisModal(synthesis) {
        if (!modalOverlay || !modalContent) return;

        // Simple markdown to HTML conversion
        const html = simpleMarkdownToHtml(synthesis);
        modalContent.innerHTML = `<div class="markdown-content">${html}</div>`;
        modalOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    /**
     * Close modal
     */
    function closeModal() {
        if (modalOverlay) {
            modalOverlay.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    /**
     * Set loading state
     */
    function setLoading(loading) {
        isLoading = loading;
        if (chatSendBtn) {
            chatSendBtn.disabled = loading;
        }
        if (chatInput) {
            chatInput.disabled = loading;
        }
    }

    /**
     * Scroll chat to bottom
     */
    function scrollToBottom() {
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    /**
     * Escape HTML special characters
     */
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Simple markdown to HTML converter
     */
    function simpleMarkdownToHtml(text) {
        if (!text) return '';

        return text
            // Headers
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            // Bold
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Italic
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Unordered lists
            .replace(/^\- (.*$)/gm, '<li>$1</li>')
            .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
            // Paragraphs
            .replace(/\n\n/g, '</p><p>')
            .replace(/^(.+)$/gm, function(match) {
                if (match.startsWith('<')) return match;
                return match;
            });
    }

    // Expose public API
    window.AnatomyChat = {
        selectElement: selectElement,
        refresh: loadAnatomyElements
    };

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
