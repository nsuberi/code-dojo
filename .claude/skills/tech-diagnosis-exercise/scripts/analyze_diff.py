#!/usr/bin/env python3
"""
Git Diff Analyzer for Diagnosis Exercises

This script analyzes a git diff and extracts structured information useful
for creating technical diagnosis exercises.

Usage:
    python analyze_diff.py <before-commit> <after-commit> [--repo-path /path/to/repo]
"""

import subprocess
import argparse
import json
import re
from pathlib import Path
from collections import defaultdict


def run_git_command(cmd, repo_path="."):
    """Run a git command and return the output."""
    result = subprocess.run(
        cmd,
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout


def get_commit_info(commit_hash, repo_path="."):
    """Get commit message and metadata."""
    cmd = ["git", "show", "--no-patch", "--format=%H%n%an%n%ae%n%ad%n%s%n%b", commit_hash]
    output = run_git_command(cmd, repo_path)
    lines = output.split('\n')
    
    return {
        "hash": lines[0] if len(lines) > 0 else "",
        "author": lines[1] if len(lines) > 1 else "",
        "email": lines[2] if len(lines) > 2 else "",
        "date": lines[3] if len(lines) > 3 else "",
        "subject": lines[4] if len(lines) > 4 else "",
        "body": '\n'.join(lines[5:]) if len(lines) > 5 else ""
    }


def categorize_file_type(filepath):
    """Categorize a file based on its path and extension."""
    path = Path(filepath)
    ext = path.suffix.lower()
    name = path.name.lower()
    
    # Configuration files
    if name in ['config.py', 'settings.py', '.env', 'dockerfile', 'docker-compose.yml']:
        return "config"
    if ext in ['.yaml', '.yml', '.toml', '.ini', '.conf']:
        return "config"
    
    # Infrastructure
    if 'terraform' in str(path) or 'ansible' in str(path):
        return "infrastructure"
    if ext in ['.tf', '.tfvars']:
        return "infrastructure"
    
    # Application code
    if ext in ['.py', '.js', '.ts', '.java', '.go', '.rb', '.php', '.cs']:
        return "application"
    
    # Templates/Views
    if ext in ['.html', '.jinja', '.jinja2', '.jsx', '.vue', '.erb']:
        return "template"
    
    # Styles
    if ext in ['.css', '.scss', '.sass', '.less']:
        return "style"
    
    # Database
    if 'migration' in str(path) or 'schema' in str(path):
        return "database"
    if ext in ['.sql']:
        return "database"
    
    # Tests
    if 'test' in str(path) or ext == '.test.js':
        return "test"
    
    # Documentation
    if ext in ['.md', '.txt', '.rst']:
        return "documentation"
    
    return "other"


def parse_diff(before_commit, after_commit, repo_path="."):
    """Parse the diff between two commits."""
    cmd = ["git", "diff", before_commit, after_commit]
    diff_output = run_git_command(cmd, repo_path)
    
    # Also get list of changed files with stats
    cmd_stat = ["git", "diff", "--stat", before_commit, after_commit]
    stat_output = run_git_command(cmd_stat, repo_path)
    
    # Parse changed files
    changed_files = defaultdict(lambda: {
        "additions": 0,
        "deletions": 0,
        "category": "other",
        "changes": []
    })
    
    current_file = None
    current_hunk = None
    
    for line in diff_output.split('\n'):
        # New file diff
        if line.startswith('diff --git'):
            # Extract filename
            match = re.search(r'b/(.+)$', line)
            if match:
                current_file = match.group(1)
                changed_files[current_file]["category"] = categorize_file_type(current_file)
        
        # Hunk header
        elif line.startswith('@@'):
            if current_file:
                current_hunk = {
                    "header": line,
                    "added_lines": [],
                    "removed_lines": [],
                    "context_lines": []
                }
                changed_files[current_file]["changes"].append(current_hunk)
        
        # Added line
        elif line.startswith('+') and not line.startswith('+++'):
            if current_hunk is not None:
                current_hunk["added_lines"].append(line[1:])
                changed_files[current_file]["additions"] += 1
        
        # Removed line
        elif line.startswith('-') and not line.startswith('---'):
            if current_hunk is not None:
                current_hunk["removed_lines"].append(line[1:])
                changed_files[current_file]["deletions"] += 1
        
        # Context line
        elif current_hunk is not None and line.startswith(' '):
            current_hunk["context_lines"].append(line[1:])
    
    return dict(changed_files)


def identify_key_changes(changed_files):
    """Identify the most significant changes for the diagnosis exercise."""
    insights = {
        "import_changes": [],
        "function_changes": [],
        "config_changes": [],
        "new_files": [],
        "deleted_files": []
    }
    
    for filepath, data in changed_files.items():
        category = data["category"]
        
        # Look for import/dependency changes
        for change in data["changes"]:
            for line in change["added_lines"]:
                if any(keyword in line for keyword in ["import ", "from ", "require(", "use "]):
                    insights["import_changes"].append({
                        "file": filepath,
                        "line": line.strip()
                    })
            
            # Look for function/class definitions
            for line in change["added_lines"]:
                if any(keyword in line for keyword in ["def ", "class ", "function ", "const "]):
                    insights["function_changes"].append({
                        "file": filepath,
                        "line": line.strip(),
                        "type": "added"
                    })
        
        # Config file changes
        if category == "config":
            insights["config_changes"].append({
                "file": filepath,
                "additions": data["additions"],
                "deletions": data["deletions"]
            })
    
    return insights


def generate_analysis_summary(before_commit, after_commit, repo_path="."):
    """Generate a complete analysis summary."""
    before_info = get_commit_info(before_commit, repo_path)
    after_info = get_commit_info(after_commit, repo_path)
    changed_files = parse_diff(before_commit, after_commit, repo_path)
    insights = identify_key_changes(changed_files)
    
    # Categorize changes
    by_category = defaultdict(list)
    for filepath, data in changed_files.items():
        by_category[data["category"]].append(filepath)
    
    summary = {
        "commits": {
            "before": before_info,
            "after": after_info
        },
        "changed_files": changed_files,
        "insights": insights,
        "by_category": dict(by_category),
        "stats": {
            "total_files_changed": len(changed_files),
            "total_additions": sum(f["additions"] for f in changed_files.values()),
            "total_deletions": sum(f["deletions"] for f in changed_files.values())
        }
    }
    
    return summary


def print_readable_summary(summary):
    """Print a human-readable summary."""
    print("=" * 80)
    print("GIT DIFF ANALYSIS FOR DIAGNOSIS EXERCISE")
    print("=" * 80)
    print()
    
    print("COMMITS:")
    print(f"  Before: {summary['commits']['before']['hash'][:8]}")
    print(f"          {summary['commits']['before']['subject']}")
    print(f"  After:  {summary['commits']['after']['hash'][:8]}")
    print(f"          {summary['commits']['after']['subject']}")
    print()
    
    print("STATISTICS:")
    print(f"  Files changed: {summary['stats']['total_files_changed']}")
    print(f"  Lines added:   {summary['stats']['total_additions']}")
    print(f"  Lines deleted: {summary['stats']['total_deletions']}")
    print()
    
    print("CHANGES BY CATEGORY:")
    for category, files in summary['by_category'].items():
        print(f"  {category.upper()}: {len(files)} file(s)")
        for f in files[:3]:  # Show first 3
            additions = summary['changed_files'][f]['additions']
            deletions = summary['changed_files'][f]['deletions']
            print(f"    - {f} (+{additions}/-{deletions})")
        if len(files) > 3:
            print(f"    ... and {len(files) - 3} more")
    print()
    
    print("KEY INSIGHTS:")
    if summary['insights']['import_changes']:
        print(f"  • New imports/dependencies: {len(summary['insights']['import_changes'])}")
        for imp in summary['insights']['import_changes'][:3]:
            print(f"    - {imp['line']}")
    
    if summary['insights']['config_changes']:
        print(f"  • Configuration changes: {len(summary['insights']['config_changes'])}")
        for cfg in summary['insights']['config_changes']:
            print(f"    - {cfg['file']}")
    
    if summary['insights']['function_changes']:
        print(f"  • New functions/classes: {len(summary['insights']['function_changes'])}")
    
    print()
    print("SUGGESTED LAYERS FOR DIAGNOSIS EXERCISE:")
    
    # Suggest layers based on categories
    layers = set()
    for category in summary['by_category'].keys():
        if category == "application":
            layers.add("Application Logic Layer")
        elif category == "config":
            layers.add("Configuration Layer")
        elif category == "infrastructure":
            layers.add("Infrastructure Layer")
        elif category == "template":
            layers.add("Presentation Layer")
        elif category == "database":
            layers.add("Data Layer")
    
    for layer in sorted(layers):
        print(f"  • {layer}")
    
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze git diff for creating diagnosis exercises"
    )
    parser.add_argument("before_commit", help="Before commit hash")
    parser.add_argument("after_commit", help="After commit hash")
    parser.add_argument("--repo-path", default=".", help="Path to git repository")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    try:
        summary = generate_analysis_summary(
            args.before_commit,
            args.after_commit,
            args.repo_path
        )
        
        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print_readable_summary(summary)
    
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e}")
        print(f"Make sure the commits exist and the repo path is correct")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
