"""
Database Migration: Replace repo_url+branch with pr_url

This migration updates the submissions table to use Pull Request URLs
instead of separate repository URL and branch fields.

Usage:
    python migrations/migrate_to_pr_url.py

IMPORTANT: This migration performs a clean break - it drops the old columns
without attempting to migrate existing data. Ensure you have a database
backup before running this migration.
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from sqlalchemy import text


def run_migration():
    """Execute the migration."""
    print("Starting migration: Replace repo_url+branch with pr_url")
    print("=" * 60)

    with app.app_context():
        try:
            # Check if columns already exist to prevent re-running
            print("\n1. Checking current database schema...")
            result = db.session.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='submissions'
                AND column_name IN ('pr_url', 'repo_url', 'branch')
            """))
            existing_columns = [row[0] for row in result]

            if 'pr_url' in existing_columns:
                print("   ⚠️  PR URL columns already exist. Migration may have been run already.")
                response = input("   Continue anyway? (yes/no): ")
                if response.lower() != 'yes':
                    print("   Migration cancelled.")
                    return

            if 'repo_url' not in existing_columns:
                print("   ⚠️  Old columns (repo_url, branch) not found. Database may already be migrated.")
                return

            # Add new columns
            print("\n2. Adding new PR columns...")
            db.session.execute(text("""
                ALTER TABLE submissions
                ADD COLUMN IF NOT EXISTS pr_url VARCHAR(500),
                ADD COLUMN IF NOT EXISTS pr_number INTEGER,
                ADD COLUMN IF NOT EXISTS pr_title VARCHAR(500),
                ADD COLUMN IF NOT EXISTS pr_state VARCHAR(20),
                ADD COLUMN IF NOT EXISTS pr_base_sha VARCHAR(40),
                ADD COLUMN IF NOT EXISTS pr_head_sha VARCHAR(40)
            """))
            print("   ✓ New columns added successfully")

            # Remove old columns (clean break as per requirements)
            print("\n3. Removing old columns (repo_url, branch)...")
            db.session.execute(text("""
                ALTER TABLE submissions
                DROP COLUMN IF EXISTS repo_url,
                DROP COLUMN IF EXISTS branch
            """))
            print("   ✓ Old columns removed successfully")

            # Make pr_url required (NOT NULL)
            print("\n4. Setting pr_url as required field...")
            db.session.execute(text("""
                ALTER TABLE submissions
                ALTER COLUMN pr_url SET NOT NULL
            """))
            print("   ✓ pr_url set as required")

            # Commit the changes
            db.session.commit()
            print("\n" + "=" * 60)
            print("✅ Migration completed successfully!")
            print("=" * 60)

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Migration failed: {str(e)}")
            print("   Database changes have been rolled back.")
            sys.exit(1)


def rollback_migration():
    """Rollback the migration (restore old schema)."""
    print("Rolling back migration: Restore repo_url+branch")
    print("=" * 60)

    with app.app_context():
        try:
            # Add back old columns
            print("\n1. Adding back old columns (repo_url, branch)...")
            db.session.execute(text("""
                ALTER TABLE submissions
                ADD COLUMN IF NOT EXISTS repo_url VARCHAR(500),
                ADD COLUMN IF NOT EXISTS branch VARCHAR(100) DEFAULT 'main'
            """))
            print("   ✓ Old columns restored")

            # Remove new columns
            print("\n2. Removing PR columns...")
            db.session.execute(text("""
                ALTER TABLE submissions
                DROP COLUMN IF EXISTS pr_url,
                DROP COLUMN IF EXISTS pr_number,
                DROP COLUMN IF EXISTS pr_title,
                DROP COLUMN IF EXISTS pr_state,
                DROP COLUMN IF EXISTS pr_base_sha,
                DROP COLUMN IF EXISTS pr_head_sha
            """))
            print("   ✓ PR columns removed")

            # Commit the changes
            db.session.commit()
            print("\n" + "=" * 60)
            print("✅ Rollback completed successfully!")
            print("=" * 60)

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Rollback failed: {str(e)}")
            sys.exit(1)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Database migration for PR URL support')
    parser.add_argument('--rollback', action='store_true',
                        help='Rollback the migration (restore old schema)')

    args = parser.parse_args()

    if args.rollback:
        confirm = input("⚠️  This will rollback the migration. Are you sure? (yes/no): ")
        if confirm.lower() == 'yes':
            rollback_migration()
        else:
            print("Rollback cancelled.")
    else:
        print("\n⚠️  IMPORTANT: This migration will drop the repo_url and branch columns.")
        print("   All existing submission data will need to be re-submitted with PR URLs.")
        print("   Make sure you have a database backup before proceeding.\n")

        confirm = input("Continue with migration? (yes/no): ")
        if confirm.lower() == 'yes':
            run_migration()
        else:
            print("Migration cancelled.")
