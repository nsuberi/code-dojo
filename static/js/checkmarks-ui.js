/**
 * Checkmarks UI for plan coverage (pre-challenge)
 */

class CheckmarksUI {
    constructor(containerId, goalId) {
        this.container = document.getElementById(containerId);
        this.goalId = goalId;
        this.coverage = {};
        this.goals = [];
    }

    async loadCoverage() {
        try {
            const response = await fetch(`/api/agent/goals/${this.goalId}/plan/coverage`);
            const data = await response.json();

            if (data.error) {
                console.error('Error loading coverage:', data.error);
                return;
            }

            this.coverage = data.goals || {};
            this.render();
        } catch (error) {
            console.error('Error loading coverage:', error);
        }
    }

    setGoals(goals) {
        this.goals = goals;
        this.render();
    }

    updateCoverage(coverage) {
        this.coverage = coverage.goals || coverage;
        this.render();
    }

    render() {
        if (!this.container) return;

        const coveredCount = Object.values(this.coverage).filter(v => v).length;
        const totalCount = Object.keys(this.coverage).length || this.goals.length;

        const html = `
            <div class="coverage-indicator">
                <h4>COVERAGE (${coveredCount}/${totalCount})</h4>
            </div>
            <div class="coverage-list">
                ${this.renderCheckmarks()}
            </div>
        `;

        this.container.innerHTML = html;
    }

    renderCheckmarks() {
        if (this.goals.length > 0) {
            return this.goals.map(goal => {
                const covered = this.coverage[goal.id] || this.coverage[String(goal.id)];
                return this.renderCheckmark(goal.title, covered);
            }).join('');
        }

        return Object.entries(this.coverage).map(([id, covered]) => {
            return this.renderCheckmark(`Goal ${id}`, covered);
        }).join('');
    }

    renderCheckmark(title, covered) {
        const icon = covered ? '✓' : '○';
        const className = covered ? 'covered' : 'not-covered';

        return `
            <div class="coverage-item ${className}">
                <span class="check-icon">${icon}</span>
                <span class="check-title">${title}</span>
            </div>
        `;
    }
}

// Export for use
window.CheckmarksUI = CheckmarksUI;
