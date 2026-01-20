"""Unit tests for GitHub PR service."""

import pytest
from unittest.mock import Mock, patch
from services.github_pr import (
    parse_pr_url,
    validate_pr_url,
    fetch_pr_metadata,
    validate_pr_base,
    fetch_pr_files,
    pr_files_to_unified_diff
)


class TestParsePrUrl:
    """Tests for parse_pr_url function."""

    def test_valid_pr_url(self):
        """Test parsing a valid PR URL."""
        url = "https://github.com/owner/repo/pull/123"
        result = parse_pr_url(url)

        assert result is not None
        assert result['owner'] == 'owner'
        assert result['repo'] == 'repo'
        assert result['pr_number'] == 123

    def test_valid_pr_url_with_trailing_slash(self):
        """Test parsing PR URL with trailing slash."""
        url = "https://github.com/owner/repo/pull/456/"
        result = parse_pr_url(url)

        assert result is not None
        assert result['owner'] == 'owner'
        assert result['repo'] == 'repo'
        assert result['pr_number'] == 456

    def test_invalid_pr_url_no_pull(self):
        """Test parsing URL without /pull/."""
        url = "https://github.com/owner/repo/issues/123"
        result = parse_pr_url(url)

        assert result is None

    def test_invalid_pr_url_no_number(self):
        """Test parsing URL without PR number."""
        url = "https://github.com/owner/repo/pull/"
        result = parse_pr_url(url)

        assert result is None

    def test_invalid_pr_url_malformed(self):
        """Test parsing completely invalid URL."""
        url = "not-a-url"
        result = parse_pr_url(url)

        assert result is None

    def test_pr_url_with_query_params(self):
        """Test parsing PR URL with query parameters."""
        url = "https://github.com/owner/repo/pull/789?tab=files"
        result = parse_pr_url(url)

        assert result is not None
        assert result['pr_number'] == 789


class TestValidatePrUrl:
    """Tests for validate_pr_url function."""

    def test_valid_url(self):
        """Test validation of valid PR URL."""
        url = "https://github.com/owner/repo/pull/123"
        is_valid, error = validate_pr_url(url)

        assert is_valid is True
        assert error is None

    def test_empty_url(self):
        """Test validation of empty URL."""
        is_valid, error = validate_pr_url("")

        assert is_valid is False
        assert "required" in error.lower()

    def test_none_url(self):
        """Test validation of None URL."""
        is_valid, error = validate_pr_url(None)

        assert is_valid is False
        assert "required" in error.lower()

    def test_invalid_format(self):
        """Test validation of invalid format."""
        url = "https://github.com/owner/repo"
        is_valid, error = validate_pr_url(url)

        assert is_valid is False
        assert "format" in error.lower()


class TestFetchPrMetadata:
    """Tests for fetch_pr_metadata function."""

    @patch('services.github_pr.requests.get')
    @patch('services.github_pr.get_github_headers')
    def test_fetch_successful(self, mock_headers, mock_get):
        """Test successful PR metadata fetch."""
        mock_headers.return_value = {'Accept': 'application/vnd.github.v3+json'}
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'number': 123,
            'title': 'Test PR',
            'body': 'Test description',
            'state': 'open',
            'merged': False,
            'commits': 5,
            'changed_files': 3,
            'additions': 100,
            'deletions': 50,
            'html_url': 'https://github.com/owner/repo/pull/123',
            'base': {
                'sha': 'abc123',
                'ref': 'main',
                'repo': {
                    'full_name': 'owner/repo'
                }
            },
            'head': {
                'sha': 'def456',
                'ref': 'feature-branch'
            }
        }
        mock_get.return_value = mock_response

        result = fetch_pr_metadata('owner', 'repo', 123)

        assert result is not None
        assert result['number'] == 123
        assert result['title'] == 'Test PR'
        assert result['state'] == 'open'
        assert result['commits'] == 5
        assert result['changed_files'] == 3

    @patch('services.github_pr.requests.get')
    @patch('services.github_pr.get_github_headers')
    def test_fetch_not_found(self, mock_headers, mock_get):
        """Test fetching non-existent PR."""
        mock_headers.return_value = {'Accept': 'application/vnd.github.v3+json'}
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = fetch_pr_metadata('owner', 'repo', 999)

        assert result is None

    @patch('services.github_pr.requests.get')
    @patch('services.github_pr.get_github_headers')
    def test_fetch_rate_limited(self, mock_headers, mock_get):
        """Test handling of rate limit."""
        mock_headers.return_value = {'Accept': 'application/vnd.github.v3+json'}
        mock_response = Mock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        result = fetch_pr_metadata('owner', 'repo', 123)

        assert result is None

    @patch('services.github_pr.requests.get')
    @patch('services.github_pr.get_github_headers')
    def test_fetch_network_error(self, mock_headers, mock_get):
        """Test handling of network error."""
        import requests
        mock_headers.return_value = {'Accept': 'application/vnd.github.v3+json'}
        mock_get.side_effect = requests.RequestException("Network error")

        result = fetch_pr_metadata('owner', 'repo', 123)

        assert result is None


class TestValidatePrBase:
    """Tests for validate_pr_base function."""

    def test_matching_base(self):
        """Test validation when base matches."""
        pr_metadata = {
            'base': {
                'repo': {
                    'full_name': 'owner/starter-repo'
                }
            }
        }
        starter_repo_url = "https://github.com/owner/starter-repo"

        is_valid, error = validate_pr_base(pr_metadata, starter_repo_url)

        assert is_valid is True
        assert error is None

    def test_matching_base_case_insensitive(self):
        """Test validation with different casing."""
        pr_metadata = {
            'base': {
                'repo': {
                    'full_name': 'Owner/Starter-Repo'
                }
            }
        }
        starter_repo_url = "https://github.com/owner/starter-repo"

        is_valid, error = validate_pr_base(pr_metadata, starter_repo_url)

        assert is_valid is True
        assert error is None

    def test_mismatched_base(self):
        """Test validation when base doesn't match."""
        pr_metadata = {
            'base': {
                'repo': {
                    'full_name': 'owner/wrong-repo'
                }
            }
        }
        starter_repo_url = "https://github.com/owner/starter-repo"

        is_valid, error = validate_pr_base(pr_metadata, starter_repo_url)

        assert is_valid is False
        assert 'does not match' in error

    def test_missing_metadata(self):
        """Test validation with missing metadata."""
        is_valid, error = validate_pr_base(None, "https://github.com/owner/repo")

        assert is_valid is False
        assert 'missing' in error.lower()

    def test_invalid_starter_url(self):
        """Test validation with invalid starter URL."""
        pr_metadata = {
            'base': {
                'repo': {
                    'full_name': 'owner/repo'
                }
            }
        }

        is_valid, error = validate_pr_base(pr_metadata, "not-a-valid-url")

        assert is_valid is False
        assert 'invalid' in error.lower()


class TestFetchPrFiles:
    """Tests for fetch_pr_files function."""

    @patch('services.github_pr.requests.get')
    @patch('services.github_pr.get_github_headers')
    def test_fetch_files_successful(self, mock_headers, mock_get):
        """Test successful file fetch."""
        mock_headers.return_value = {'Accept': 'application/vnd.github.v3+json'}
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'filename': 'app.py',
                'status': 'modified',
                'additions': 10,
                'deletions': 5,
                'changes': 15,
                'patch': '@@ -1,3 +1,4 @@\n+new line\n old line'
            },
            {
                'filename': 'test.py',
                'status': 'added',
                'additions': 20,
                'deletions': 0,
                'changes': 20,
                'patch': '@@ -0,0 +1,20 @@\n+test code'
            }
        ]
        mock_get.return_value = mock_response

        result = fetch_pr_files('owner', 'repo', 123)

        assert len(result) == 2
        assert result[0]['filename'] == 'app.py'
        assert result[0]['status'] == 'modified'
        assert result[1]['filename'] == 'test.py'
        assert result[1]['status'] == 'added'

    @patch('services.github_pr.requests.get')
    @patch('services.github_pr.get_github_headers')
    def test_fetch_files_empty(self, mock_headers, mock_get):
        """Test fetching PR with no files."""
        mock_headers.return_value = {'Accept': 'application/vnd.github.v3+json'}
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        result = fetch_pr_files('owner', 'repo', 123)

        assert result == []

    @patch('services.github_pr.requests.get')
    @patch('services.github_pr.get_github_headers')
    def test_fetch_files_error(self, mock_headers, mock_get):
        """Test handling of fetch error."""
        mock_headers.return_value = {'Accept': 'application/vnd.github.v3+json'}
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = fetch_pr_files('owner', 'repo', 123)

        assert result == []


class TestPrFilesToUnifiedDiff:
    """Tests for pr_files_to_unified_diff function."""

    def test_convert_single_file(self):
        """Test converting single file to diff."""
        files = [
            {
                'filename': 'app.py',
                'status': 'modified',
                'patch': '@@ -1,3 +1,4 @@\n+new line\n old line'
            }
        ]

        result = pr_files_to_unified_diff(files)

        assert 'diff --git a/app.py b/app.py' in result
        assert '@@ -1,3 +1,4 @@' in result

    def test_convert_multiple_files(self):
        """Test converting multiple files to diff."""
        files = [
            {
                'filename': 'app.py',
                'status': 'modified',
                'patch': '@@ -1,3 +1,4 @@\n+new line'
            },
            {
                'filename': 'test.py',
                'status': 'added',
                'patch': '@@ -0,0 +1,10 @@\n+test code'
            }
        ]

        result = pr_files_to_unified_diff(files)

        assert 'diff --git a/app.py b/app.py' in result
        assert 'diff --git a/test.py b/test.py' in result
        assert 'new file mode 100644' in result

    def test_convert_deleted_file(self):
        """Test converting deleted file to diff."""
        files = [
            {
                'filename': 'old.py',
                'status': 'removed',
                'patch': '@@ -1,10 +0,0 @@\n-deleted code'
            }
        ]

        result = pr_files_to_unified_diff(files)

        assert 'diff --git a/old.py b/old.py' in result
        assert 'deleted file mode 100644' in result

    def test_convert_renamed_file(self):
        """Test converting renamed file to diff."""
        files = [
            {
                'filename': 'new_name.py',
                'status': 'renamed',
                'patch': '@@ -1,3 +1,3 @@\n-old line\n+new line'
            }
        ]

        result = pr_files_to_unified_diff(files)

        assert 'diff --git a/new_name.py b/new_name.py' in result
        assert 'renamed file' in result

    def test_convert_binary_file(self):
        """Test converting file with no patch (binary)."""
        files = [
            {
                'filename': 'image.png',
                'status': 'added',
                'patch': ''
            }
        ]

        result = pr_files_to_unified_diff(files)

        assert 'diff --git a/image.png b/image.png' in result
        assert 'Binary file changed' in result

    def test_convert_empty_list(self):
        """Test converting empty file list."""
        result = pr_files_to_unified_diff([])

        assert result == ""
