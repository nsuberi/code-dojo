"""GitHub API integration for fetching code diffs."""

import difflib
import re
import requests
from flask import current_app


def parse_github_url(url):
    """
    Parse a GitHub URL to extract owner and repo.

    Supports formats:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - github.com/owner/repo
    """
    # Remove .git suffix if present
    url = url.rstrip('/').rstrip('.git')

    # Extract owner and repo
    match = re.search(r'github\.com[/:]([^/]+)/([^/]+)', url)
    if match:
        return match.group(1), match.group(2)
    return None, None


def get_github_headers():
    """Get headers for GitHub API requests, including auth token if available."""
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Code-Dojo-App'
    }
    try:
        token = current_app.config.get('GITHUB_TOKEN')
        # Only use token if it's set and not a placeholder value
        if token and not token.startswith('your_') and len(token) > 20:
            headers['Authorization'] = f'token {token}'
    except RuntimeError:
        # Not in application context
        pass
    return headers


def fetch_file_content(owner, repo, branch, path, headers):
    """Fetch content of a single file from GitHub."""
    url = f'https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}'
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.text
        return None
    except requests.RequestException:
        return None


def generate_unified_diff(old_content, new_content, old_path, new_path):
    """
    Generate a unified diff between two file contents.

    Args:
        old_content: Content of the original file (or empty string if new)
        new_content: Content of the new file (or empty string if deleted)
        old_path: Path for the old file (a/filename)
        new_path: Path for the new file (b/filename)

    Returns:
        String containing the unified diff
    """
    old_lines = old_content.splitlines(keepends=True) if old_content else []
    new_lines = new_content.splitlines(keepends=True) if new_content else []

    # Ensure lines end with newlines for proper diff formatting
    if old_lines and not old_lines[-1].endswith('\n'):
        old_lines[-1] += '\n'
    if new_lines and not new_lines[-1].endswith('\n'):
        new_lines[-1] += '\n'

    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f'a/{old_path}',
        tofile=f'b/{new_path}',
        lineterm=''
    )

    return ''.join(diff)


def fetch_github_diff(starter_repo_url, student_repo_url, branch='main'):
    """
    Fetch the diff between a starter repo and a student's repo.

    Uses GitHub API to fetch files and Python's difflib to generate
    proper unified diffs with +/- markers.

    Args:
        starter_repo_url: URL of the starter/template repository
        student_repo_url: URL of the student's forked/copied repository
        branch: Branch name in the student's repo to compare

    Returns:
        String containing unified diff content, or error message if failed
    """
    starter_owner, starter_repo = parse_github_url(starter_repo_url)
    student_owner, student_repo = parse_github_url(student_repo_url)

    if not all([starter_owner, starter_repo, student_owner, student_repo]):
        return None

    headers = get_github_headers()

    try:
        # Get list of files from student's branch
        student_tree_url = f'https://api.github.com/repos/{student_owner}/{student_repo}/git/trees/{branch}?recursive=1'
        student_resp = requests.get(student_tree_url, headers=headers, timeout=10)

        if student_resp.status_code == 403:
            return "GitHub API rate limit exceeded. Please try again later or configure a GitHub token."
        if student_resp.status_code != 200:
            return f"Error fetching student repo: {student_resp.status_code}"

        student_tree = student_resp.json()

        # Get list of files from starter's main branch
        starter_tree_url = f'https://api.github.com/repos/{starter_owner}/{starter_repo}/git/trees/main?recursive=1'
        starter_resp = requests.get(starter_tree_url, headers=headers, timeout=10)

        if starter_resp.status_code == 403:
            return "GitHub API rate limit exceeded. Please try again later or configure a GitHub token."
        if starter_resp.status_code != 200:
            return f"Error fetching starter repo: {starter_resp.status_code}"

        starter_tree = starter_resp.json()

        # Build maps of file paths to SHAs
        starter_files = {}
        for item in starter_tree.get('tree', []):
            if item['type'] == 'blob':
                starter_files[item['path']] = item['sha']

        student_files = {}
        for item in student_tree.get('tree', []):
            if item['type'] == 'blob':
                student_files[item['path']] = item['sha']

        # Files to compare - focus on key source files
        files_to_compare = [
            'app.py', 'models.py', 'config.py', 'seed_data.py',
            'main.py', 'server.py', 'index.py', 'routes.py'
        ]

        # Also include any .py files in common directories
        for path in list(student_files.keys()) + list(starter_files.keys()):
            if path.endswith('.py') and '/' not in path:
                if path not in files_to_compare:
                    files_to_compare.append(path)

        diff_parts = []

        # Check for modified and new files
        for path in files_to_compare:
            student_sha = student_files.get(path)
            starter_sha = starter_files.get(path)

            # Skip if file doesn't exist in student repo and starter repo
            if not student_sha and not starter_sha:
                continue

            # Skip if file is identical (same SHA)
            if student_sha == starter_sha:
                continue

            # Skip binary files (basic check)
            if path.endswith(('.pyc', '.pyo', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.woff', '.woff2', '.ttf', '.eot')):
                diff_parts.append(f"diff --git a/{path} b/{path}\nBinary file changed")
                continue

            # Fetch content from both repos
            starter_content = ''
            student_content = ''

            if starter_sha:
                starter_content = fetch_file_content(
                    starter_owner, starter_repo, 'main', path, headers
                ) or ''

            if student_sha:
                student_content = fetch_file_content(
                    student_owner, student_repo, branch, path, headers
                ) or ''

            # Skip if both are empty
            if not starter_content and not student_content:
                continue

            # Generate unified diff
            diff = generate_unified_diff(starter_content, student_content, path, path)

            if diff:
                # Add git-style header
                diff_header = f"diff --git a/{path} b/{path}\n"

                # Determine file status
                if not starter_sha:
                    diff_header += "new file mode 100644\n"
                elif not student_sha:
                    diff_header += "deleted file mode 100644\n"

                diff_parts.append(diff_header + diff)

        # Check for deleted files (in starter but not in student)
        for path in files_to_compare:
            if path in starter_files and path not in student_files:
                # File was deleted by student
                starter_content = fetch_file_content(
                    starter_owner, starter_repo, 'main', path, headers
                ) or ''

                if starter_content:
                    diff = generate_unified_diff(starter_content, '', path, path)
                    if diff:
                        diff_header = f"diff --git a/{path} b/{path}\ndeleted file mode 100644\n"
                        diff_parts.append(diff_header + diff)

        if diff_parts:
            return '\n'.join(diff_parts)
        else:
            return "No changes detected in key files."

    except requests.RequestException as e:
        return f"Error fetching from GitHub: {str(e)}"


def calculate_diff_stats(diff_content):
    """
    Calculate summary statistics from diff content.

    Args:
        diff_content: String containing unified diff

    Returns:
        Dict with file_count, total_additions, total_deletions
    """
    if not diff_content:
        return {'file_count': 0, 'total_additions': 0, 'total_deletions': 0}

    # Count files (each "diff --git" marks a new file)
    file_count = diff_content.count('diff --git')

    # Count additions and deletions
    # Lines starting with + but not +++ are additions
    # Lines starting with - but not --- are deletions
    lines = diff_content.split('\n')
    total_additions = 0
    total_deletions = 0

    for line in lines:
        if line.startswith('+') and not line.startswith('+++'):
            total_additions += 1
        elif line.startswith('-') and not line.startswith('---'):
            total_deletions += 1

    return {
        'file_count': file_count,
        'total_additions': total_additions,
        'total_deletions': total_deletions
    }


def fetch_github_diff_from_pr(pr_url):
    """
    Fetch diff from a GitHub Pull Request URL.

    Args:
        pr_url: GitHub Pull Request URL (e.g., https://github.com/owner/repo/pull/123)

    Returns:
        Tuple of (diff_content, error_message).
        Returns (diff_content, None) on success, (None, error_message) on failure.
    """
    # Import here to avoid circular import
    from services.github_pr import parse_pr_url, fetch_pr_files, pr_files_to_unified_diff

    # Parse PR URL
    parsed = parse_pr_url(pr_url)
    if not parsed:
        return None, "Invalid PR URL format"

    # Fetch PR files
    files = fetch_pr_files(parsed['owner'], parsed['repo'], parsed['pr_number'])

    if not files:
        return None, "Could not fetch PR files. The PR may not exist or may be private."

    # Convert to unified diff
    diff_content = pr_files_to_unified_diff(files)

    if not diff_content:
        return None, "No changes found in the PR"

    return diff_content, None
