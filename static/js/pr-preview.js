// Real-time PR preview functionality
document.addEventListener('DOMContentLoaded', function() {
    const prUrlInput = document.getElementById('pr_url');

    // Only run if we're on a page with the PR URL input
    if (!prUrlInput) return;

    const prPreview = document.getElementById('pr-preview');
    const prPreviewContent = document.getElementById('pr-preview-content');
    const prPreviewError = document.getElementById('pr-preview-error');
    const prPreviewStatus = document.getElementById('pr-preview-status');
    const goalIdInput = document.querySelector('input[name="goal_id"]');
    const goalId = goalIdInput ? goalIdInput.value : null;

    let debounceTimer;

    prUrlInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => validateAndPreviewPR(), 500);
    });

    prUrlInput.addEventListener('blur', function() {
        validateAndPreviewPR();
    });

    async function validateAndPreviewPR() {
        const prUrl = prUrlInput.value.trim();

        if (!prUrl) {
            prPreview.style.display = 'none';
            return;
        }

        // Basic format validation
        const prUrlPattern = /https:\/\/github\.com\/[^/]+\/[^/]+\/pull\/\d+/;
        if (!prUrlPattern.test(prUrl)) {
            showError('Invalid PR URL format. Expected: https://github.com/username/repo/pull/123');
            return;
        }

        // Fetch PR metadata from backend
        try {
            const url = `/submissions/api/validate-pr?url=${encodeURIComponent(prUrl)}${goalId ? '&goal_id=' + goalId : ''}`;
            const response = await fetch(url);
            const data = await response.json();

            if (data.valid) {
                showPreview(data.pr);
            } else {
                showError(data.error);
            }
        } catch (error) {
            showError('Could not validate PR. Check your connection.');
        }
    }

    function showPreview(pr) {
        prPreviewError.style.display = 'none';
        prPreviewContent.style.display = 'block';
        prPreview.style.display = 'block';

        // Status badge
        let statusClass = 'status-open';
        let statusText = pr.state.toUpperCase();
        if (pr.merged) {
            statusClass = 'status-merged';
            statusText = 'MERGED';
        } else if (pr.state === 'closed') {
            statusClass = 'status-closed';
        }
        prPreviewStatus.className = `pr-status-badge ${statusClass}`;
        prPreviewStatus.textContent = statusText;

        // PR details
        prPreviewContent.innerHTML = `
            <div class="pr-preview-title">
                <strong>#${pr.number}</strong> ${escapeHtml(pr.title)}
            </div>
            <div class="pr-preview-stats">
                <span>${pr.changed_files} file${pr.changed_files !== 1 ? 's' : ''} changed</span>
                <span class="text-success">+${pr.additions}</span>
                <span class="text-danger">-${pr.deletions}</span>
            </div>
            <a href="${pr.html_url}" target="_blank" class="pr-preview-link">View on GitHub →</a>
        `;
    }

    function showError(message) {
        prPreview.style.display = 'block';
        prPreviewContent.style.display = 'none';
        prPreviewError.style.display = 'block';
        prPreviewError.textContent = message;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});
