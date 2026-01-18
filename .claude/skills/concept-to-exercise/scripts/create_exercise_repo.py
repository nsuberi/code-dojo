#!/usr/bin/env python3
"""
Git Repository Generator for Concept Exercises

This script helps create git repositories with before/after commits
for diagnosis exercises.

Usage:
    python create_exercise_repo.py --concept "flask-proxyfix" --output-dir /path
"""

import argparse
import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional


class ExerciseRepoBuilder:
    """Builds a git repository with before/after commits for a concept."""
    
    def __init__(self, concept_name: str, output_dir: str):
        self.concept_name = concept_name
        self.repo_path = Path(output_dir) / concept_name
        self.before_commit = None
        self.after_commit = None
    
    def initialize_repo(self):
        """Create the repository directory and initialize git."""
        print(f"📁 Creating repository at {self.repo_path}")
        
        # Create directory
        self.repo_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize git
        self._run_git(['init'])
        self._run_git(['config', 'user.name', 'Diagnosis Exercise Generator'])
        self._run_git(['config', 'user.email', 'exercises@example.com'])
        
        print("✅ Repository initialized")
    
    def write_files(self, files: Dict[str, str]):
        """Write files to the repository.
        
        Args:
            files: Dictionary mapping file paths to file contents
        """
        for filepath, content in files.items():
            full_path = self.repo_path / filepath
            
            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            full_path.write_text(content)
            print(f"  📝 Wrote {filepath}")
    
    def create_commit(self, message: str, state: str = 'before') -> str:
        """Create a git commit with all current files.
        
        Args:
            message: Commit message
            state: 'before' or 'after'
        
        Returns:
            Commit hash
        """
        # Stage all files
        self._run_git(['add', '.'])
        
        # Create commit
        self._run_git(['commit', '-m', message])
        
        # Get commit hash
        result = self._run_git(['rev-parse', 'HEAD'], capture_output=True)
        commit_hash = result.stdout.strip()
        
        if state == 'before':
            self.before_commit = commit_hash
        elif state == 'after':
            self.after_commit = commit_hash
        
        print(f"✅ Created commit: {commit_hash[:8]} ({state})")
        return commit_hash
    
    def get_diff_summary(self) -> str:
        """Get a summary of changes between before and after commits."""
        if not self.before_commit or not self.after_commit:
            return "No commits to compare"
        
        result = self._run_git([
            'diff', '--stat',
            self.before_commit,
            self.after_commit
        ], capture_output=True)
        
        return result.stdout
    
    def get_exercise_info(self) -> Dict:
        """Get information needed for the diagnosis exercise."""
        return {
            'repo_path': str(self.repo_path.absolute()),
            'concept_name': self.concept_name,
            'before_commit': self.before_commit,
            'after_commit': self.after_commit,
            'diff_summary': self.get_diff_summary()
        }
    
    def _run_git(self, args: List[str], capture_output: bool = False):
        """Run a git command in the repository."""
        cmd = ['git'] + args
        
        if capture_output:
            return subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
        else:
            subprocess.run(
                cmd,
                cwd=self.repo_path,
                check=True
            )


def main():
    parser = argparse.ArgumentParser(
        description="Create a git repository for a concept exercise"
    )
    parser.add_argument(
        '--concept',
        required=True,
        help='Concept name (e.g., "flask-proxyfix")'
    )
    parser.add_argument(
        '--output-dir',
        default='/home/claude/demo-repos',
        help='Directory to create repository in'
    )
    parser.add_argument(
        '--info-only',
        action='store_true',
        help='Only print repository info (assumes it exists)'
    )
    
    args = parser.parse_args()
    
    builder = ExerciseRepoBuilder(args.concept, args.output_dir)
    
    if args.info_only:
        # Just print info about existing repo
        builder.before_commit = subprocess.run(
            ['git', 'rev-list', '--max-parents=0', 'HEAD'],
            cwd=builder.repo_path,
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()
        
        builder.after_commit = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=builder.repo_path,
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()
        
        info = builder.get_exercise_info()
        print(json.dumps(info, indent=2))
    else:
        print(f"This is a helper script. It's designed to be called by Claude,")
        print(f"not run directly. Claude will use this to create exercise repos.")
        print()
        print(f"To create an exercise, ask Claude something like:")
        print(f'  "Create an exercise teaching [concept]"')
    
    return 0


if __name__ == '__main__':
    exit(main())
