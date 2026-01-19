/**
 * Plan editor component for pre-challenge planning
 */

class PlanEditor {
    constructor(containerId, goalId) {
        this.container = document.getElementById(containerId);
        this.goalId = goalId;
        this.sessionId = null;
        this.plan = null;
        this.isEditing = false;
    }

    render() {
        if (!this.container) return;

        const content = this.plan?.plan_content || '';
        const coverage = this.plan?.coverage || {};
        const coveredCount = this.plan?.coverage_count || 0;

        this.container.innerHTML = `
            <div class="plan-editor">
                <div class="plan-header">
                    <h3>YOUR PLAN</h3>
                    <div class="plan-actions">
                        <button class="btn btn-sm btn-secondary" id="plan-edit-btn">
                            ${this.isEditing ? 'Preview' : 'Edit'}
                        </button>
                        <button class="btn btn-sm btn-primary" id="plan-export-btn">
                            Export →
                        </button>
                    </div>
                </div>

                <div class="plan-content">
                    ${this.isEditing ? `
                        <textarea id="plan-textarea" class="plan-textarea">${content}</textarea>
                    ` : `
                        <div class="plan-preview markdown-content" id="plan-preview">
                            ${this.formatMarkdown(content) || '<p class="empty-plan">Your plan will build here as you discuss with Sensei...</p>'}
                        </div>
                    `}
                </div>

                <div class="plan-footer">
                    <small>Coverage: ${coveredCount} concepts addressed</small>
                </div>
            </div>
        `;

        this.attachEventListeners();
    }

    attachEventListeners() {
        const editBtn = document.getElementById('plan-edit-btn');
        const exportBtn = document.getElementById('plan-export-btn');
        const textarea = document.getElementById('plan-textarea');

        if (editBtn) {
            editBtn.addEventListener('click', () => this.toggleEdit());
        }

        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportPlan());
        }

        if (textarea) {
            textarea.addEventListener('input', () => this.onContentChange(textarea.value));
        }
    }

    toggleEdit() {
        if (this.isEditing) {
            // Save changes
            const textarea = document.getElementById('plan-textarea');
            if (textarea && this.plan) {
                this.plan.plan_content = textarea.value;
                this.savePlan(textarea.value);
            }
        }
        this.isEditing = !this.isEditing;
        this.render();
    }

    async savePlan(content) {
        if (!this.sessionId) return;

        try {
            await fetch(`/api/agent/goals/${this.goalId}/plan/update`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    content: content
                })
            });
        } catch (error) {
            console.error('Error saving plan:', error);
        }
    }

    async exportPlan() {
        try {
            const url = this.sessionId
                ? `/api/agent/goals/${this.goalId}/plan/export?session_id=${this.sessionId}`
                : `/api/agent/goals/${this.goalId}/plan/export`;

            const response = await fetch(url);
            const data = await response.json();

            if (data.error) {
                alert('Error exporting plan: ' + data.error);
                return;
            }

            // Copy to clipboard
            await navigator.clipboard.writeText(data.markdown);
            alert('Plan copied to clipboard! You can paste it into Claude, Cursor, or any coding tool.');

        } catch (error) {
            console.error('Error exporting plan:', error);
            alert('Failed to export plan');
        }
    }

    updatePlan(plan) {
        this.plan = plan;
        this.render();
    }

    setSessionId(sessionId) {
        this.sessionId = sessionId;
    }

    onContentChange(content) {
        // Debounced save
        if (this.saveTimeout) {
            clearTimeout(this.saveTimeout);
        }
        this.saveTimeout = setTimeout(() => {
            this.savePlan(content);
        }, 1000);
    }

    formatMarkdown(content) {
        if (!content) return '';
        // Basic markdown to HTML conversion
        // In production, use a proper markdown library
        return content
            .replace(/^## (.*$)/gim, '<h4>$1</h4>')
            .replace(/^- (.*$)/gim, '<li>$1</li>')
            .replace(/\n/g, '<br>')
            .replace(/<li>/g, '<ul><li>')
            .replace(/<\/li><br>/g, '</li></ul>');
    }
}

// Export for use
window.PlanEditor = PlanEditor;
