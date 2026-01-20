"""GitHub Pull Request API integration."""

import re
import requests
from flask import current_app
from services.github import get_github_headers, parse_github_url


def parse_pr_url(pr_url):
    """
    Parse a GitHub PR URL to extract owner, repo, and PR number.

    Supports format: https://github.com/owner/repo/pull/123

    Args:
        pr_url: GitHub Pull Request URL string

    Returns:
        Dict with owner, repo, pr_number keys, or None if invalid
    """
    pattern = r'github\.com/([^/]+)/([^/]+)/pull/(\d+)'
    match = re.search(pattern, pr_url)

    if match:
        return {
            'owner': match.group(1),
            'repo': match.group(2),
            'pr_number': int(match.group(3))
        }
    return None


def validate_pr_url(pr_url):
    """
    Validate that a PR URL has correct format.

    Args:
        pr_url: GitHub Pull Request URL string

    Returns:
        Tuple of (bool, error_message). Returns (True, None) if valid.
    """
    if not pr_url or not isinstance(pr_url, str):
        return False, "PR URL is required"

    parsed = parse_pr_url(pr_url)
    if not parsed:
        return False, "Invalid GitHub PR URL format. Expected: https://github.com/owner/repo/pull/123"

    return True, None


def fetch_pr_metadata(owner, repo, pr_number):
    """
    Fetch Pull Request metadata from GitHub API.

    Args:
        owner: Repository owner username
        repo: Repository name
        pr_number: Pull request number

    Returns:
        Dict with PR metadata, or None if fetch failed
    """
    headers = get_github_headers()
    url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}'

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 403:
            # Rate limit exceeded
            return None

        if response.status_code == 404:
            # PR not found
            return None

        if response.status_code != 200:
            return None

        data = response.json()

        # Extract relevant metadata
        return {
            'number': data['number'],
            'title': data['title'],
            'body': data.get('body', ''),
            'state': data['state'],  # open, closed
            'merged': data.get('merged', False),
            'commits': data['commits'],
            'changed_files': data['changed_files'],
            'additions': data['additions'],
            'deletions': data['deletions'],
            'html_url': data['html_url'],
            'base': {
                'sha': data['base']['sha'],
                'ref': data['base']['ref'],
                'repo': {
                    'full_name': data['base']['repo']['full_name']
                }
            },
            'head': {
                'sha': data['head']['sha'],
                'ref': data['head']['ref']
            }
        }

    except requests.RequestException:
        return None


def validate_pr_base(pr_metadata, starter_repo_url):
    """
    Validate that PR's base repository matches the expected starter repository.

    Args:
        pr_metadata: PR metadata dict from fetch_pr_metadata()
        starter_repo_url: Expected starter repository URL

    Returns:
        Tuple of (bool, error_message). Returns (True, None) if valid.
    """
    if not pr_metadata or not starter_repo_url:
        return False, "Missing PR metadata or starter repository URL"

    # Parse starter repo URL to get owner/repo
    starter_owner, starter_repo = parse_github_url(starter_repo_url)
    if not starter_owner or not starter_repo:
        return False, "Invalid starter repository URL"

    expected_full_name = f"{starter_owner}/{starter_repo}"
    actual_full_name = pr_metadata['base']['repo']['full_name']

    if expected_full_name.lower() != actual_full_name.lower():
        return False, f"PR base repository '{actual_full_name}' does not match expected starter repository '{expected_full_name}'"

    return True, None


def fetch_pr_files(owner, repo, pr_number):
    """
    Fetch list of files changed in a Pull Request.

    Args:
        owner: Repository owner username
        repo: Repository name
        pr_number: Pull request number

    Returns:
        List of file dicts with filename, status, additions, deletions, patch
        Returns empty list if fetch failed
    """
    headers = get_github_headers()
    url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files'

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            return []

        files = response.json()

        # Extract relevant file information
        result = []
        for file in files:
            result.append({
                'filename': file['filename'],
                'status': file['status'],  # added, removed, modified, renamed
                'additions': file['additions'],
                'deletions': file['deletions'],
                'changes': file['changes'],
                'patch': file.get('patch', '')  # Unified diff patch (may be empty for binary files)
            })

        return result

    except requests.RequestException:
        return []


def pr_files_to_unified_diff(files):
    """
    Combine individual file patches into a single unified diff.

    Args:
        files: List of file dicts from fetch_pr_files()

    Returns:
        String containing full unified diff content
    """
    if not files:
        return ""

    diff_parts = []

    for file in files:
        filename = file['filename']
        status = file['status']
        patch = file.get('patch', '')

        if not patch:
            # No patch available (binary file or too large)
            diff_parts.append(f"diff --git a/{filename} b/{filename}\nBinary file changed or too large to display")
            continue

        # Add git-style header
        diff_header = f"diff --git a/{filename} b/{filename}\n"

        # Add status indicator
        if status == 'added':
            diff_header += "new file mode 100644\n"
        elif status == 'removed':
            diff_header += "deleted file mode 100644\n"
        elif status == 'renamed':
            diff_header += "renamed file\n"

        # The patch from GitHub API already includes the --- and +++ lines
        diff_parts.append(diff_header + patch)

    return '\n'.join(diff_parts)
