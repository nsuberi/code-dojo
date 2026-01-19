/**
 * Gems UI for displaying mastery progress (post-challenge)
 */

class GemsUI {
    constructor(containerId, submissionId) {
        this.container = document.getElementById(containerId);
        this.submissionId = submissionId;
        this.progress = [];
        this.engagement = null;
    }

    async loadProgress() {
        try {
            const response = await fetch(`/api/agent/submissions/${this.submissionId}/progress`);
            const data = await response.json();

            if (data.error) {
                console.error('Error loading progress:', data.error);
                return;
            }

            this.progress = data.progress;
            this.engagement = data.engagement;
            this.render();
        } catch (error) {
            console.error('Error loading progress:', error);
        }
    }

    getGemIcon(progress) {
        const status = progress?.effective_status || progress?.status || 'locked';
        const isExpired = progress?.is_expired;

        if (isExpired) {
            return '⟳'; // Expired - needs renewal
        }

        switch (status) {
            case 'passed':
                return '💎';
            case 'engaged':
                return '🔵';
            case 'in_progress':
                return '⚪';
            default:
                return '○';
        }
    }

    getGemClass(progress) {
        const status = progress?.effective_status || progress?.status || 'locked';
        const isExpired = progress?.is_expired;

        if (isExpired) {
            return 'gem-expired';
        }

        return `gem-${status}`;
    }

    render() {
        if (!this.container) return;

        // Render mastery indicator
        const gemsDisplay = this.progress.map(p => this.getGemIcon(p.progress)).join(' ');
        const validCount = this.engagement?.valid_count || 0;
        const totalCount = this.engagement?.total || this.progress.length;
        const neededForSensei = Math.max(0, Math.ceil(totalCount / 2) - validCount);

        const html = `
            <div class="mastery-indicator">
                <span class="mastery-label">MASTERY</span>
                <span class="gems-display">${gemsDisplay}</span>
                <span class="gems-count">(${validCount}/${totalCount}${neededForSensei > 0 ? ` - need ${neededForSensei} more for Sensei` : ' - Sensei unlocked!'})</span>
            </div>

            <div class="topics-grid">
                ${this.progress.map((p, i) => this.renderGoalButton(p, i)).join('')}
            </div>

            <div class="progress-summary">
                <span class="stat-passed">${this.engagement?.passed || 0} mastered</span> ·
                <span class="stat-engaged">${this.engagement?.engaged || 0} engaged</span> ·
                <span class="stat-expired">${this.engagement?.expired || 0} expired</span>
            </div>

            ${this.engagement?.can_request_sensei ? `
                <div class="sensei-unlock-notice">
                    ✨ <strong>Sensei feedback unlocked!</strong> You can now request a review.
                </div>
            ` : ''}
        `;

        this.container.innerHTML = html;

        // Add click handlers
        this.container.querySelectorAll('.topic-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const goalId = btn.dataset.goalId;
                this.onGoalClick(goalId);
            });
        });
    }

    renderGoalButton(progressData, index) {
        const goal = progressData.goal;
        const progress = progressData.progress;
        const gemIcon = this.getGemIcon(progress);
        const gemClass = this.getGemClass(progress);
        const isExpired = progress?.is_expired;

        return `
            <button class="topic-btn ${gemClass}"
                    data-goal-id="${goal.id}"
                    data-status="${progress?.status || 'locked'}">
                <span class="gem-icon ${gemClass}">${gemIcon}</span>
                <div class="topic-info">
                    <span class="topic-title">${goal.title}</span>
                    ${isExpired ? '<span class="expired-badge">⟳ Renew</span>' : ''}
                </div>
            </button>
        `;
    }

    onGoalClick(goalId) {
        // Override this method to handle goal clicks
        console.log('Goal clicked:', goalId);
    }

    updateGem(coreGoalId, newStatus) {
        // Update a specific gem's status
        const item = this.progress.find(p => p.goal.id === parseInt(coreGoalId));
        if (item) {
            item.progress.status = newStatus;
            item.progress.effective_status = newStatus;
            this.render();
        }
    }
}

// Export for use
window.GemsUI = GemsUI;
