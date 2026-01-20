"""
SQLite-compatible Database Migration: Replace repo_url+branch with pr_url

SQLite doesn't support ALTER COLUMN, so we need to recreate the table.

Usage:
    python migrations/migrate_to_pr_url_sqlite.py

IMPORTANT: This migration performs a clean break - it drops the old columns.
Ensure you have a database backup before running this migration.
"""

import sys
import os
import sqlite3

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_database_path():
    """Get the database path from config."""
    try:
        from app import app
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        # Extract path from sqlite:///path
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            # If relative path, check instance folder first, then make it absolute
            if not os.path.isabs(db_path):
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

                # Check instance folder first (Flask default for SQLite)
                instance_path = os.path.join(base_dir, 'instance', db_path)
                if os.path.exists(instance_path):
                    return instance_path

                # Otherwise use relative to base directory
                db_path = os.path.join(base_dir, db_path)
            return db_path
        else:
            print("Error: This script only supports SQLite databases")
            sys.exit(1)
    except Exception as e:
        print(f"Error getting database path: {e}")
        sys.exit(1)


def run_migration():
    """Execute the migration."""
    print("Starting SQLite migration: Replace repo_url+branch with pr_url")
    print("=" * 60)

    db_path = get_database_path()
    print(f"\nDatabase: {db_path}")

    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check current schema
        print("\n1. Checking current database schema...")
        cursor.execute("PRAGMA table_info(submissions)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'pr_url' in column_names:
            print("   ⚠️  PR URL columns already exist. Migration may have been run already.")
            response = input("   Continue anyway? (yes/no): ")
            if response.lower() != 'yes':
                print("   Migration cancelled.")
                conn.close()
                return

        if 'repo_url' not in column_names:
            print("   ⚠️  Old columns (repo_url, branch) not found. Database may already be migrated.")
            conn.close()
            return

        # Get existing data
        print("\n2. Reading existing submissions...")
        cursor.execute("SELECT COUNT(*) FROM submissions")
        count = cursor.fetchone()[0]
        print(f"   Found {count} existing submission(s)")

        if count > 0:
            print("\n   ⚠️  WARNING: This will delete all existing submissions!")
            print("   The old repo_url/branch data cannot be converted to PR URLs.")
            print("   Users will need to re-submit with PR URLs.")
            response = input("   Continue and delete existing submissions? (yes/no): ")
            if response.lower() != 'yes':
                print("   Migration cancelled.")
                conn.close()
                return

        # Create new table with updated schema
        print("\n3. Creating new submissions table...")
        cursor.execute("""
            CREATE TABLE submissions_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                goal_id INTEGER NOT NULL,
                pr_url VARCHAR(500) NOT NULL,
                pr_number INTEGER,
                pr_title VARCHAR(500),
                pr_state VARCHAR(20),
                pr_base_sha VARCHAR(40),
                pr_head_sha VARCHAR(40),
                status VARCHAR(50) DEFAULT 'pending',
                created_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (goal_id) REFERENCES learning_goals(id)
            )
        """)
        print("   ✓ New table created")

        # Drop old table
        print("\n4. Dropping old submissions table...")
        cursor.execute("DROP TABLE submissions")
        print("   ✓ Old table dropped")

        # Rename new table
        print("\n5. Renaming new table...")
        cursor.execute("ALTER TABLE submissions_new RENAME TO submissions")
        print("   ✓ Table renamed")

        # Drop dependent tables (they'll be recreated by the app)
        print("\n6. Dropping dependent tables (will be recreated)...")
        try:
            cursor.execute("DROP TABLE IF EXISTS ai_feedback")
            cursor.execute("DROP TABLE IF EXISTS instructor_feedback")
            print("   ✓ Dependent tables dropped")
        except Exception as e:
            print(f"   Note: {e}")

        # Commit changes
        conn.commit()
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Restart your Flask application")
        print("2. The app will recreate dependent tables (ai_feedback, instructor_feedback)")
        print("3. Users can now submit PRs using PR URLs")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {str(e)}")
        print("   Database changes have been rolled back.")
        sys.exit(1)
    finally:
        conn.close()


def rollback_migration():
    """Rollback the migration (restore old schema)."""
    print("Rolling back migration: Restore repo_url+branch")
    print("=" * 60)

    db_path = get_database_path()
    print(f"\nDatabase: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Create old table structure
        print("\n1. Creating old submissions table...")
        cursor.execute("""
            CREATE TABLE submissions_old (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                goal_id INTEGER NOT NULL,
                repo_url VARCHAR(500) NOT NULL,
                branch VARCHAR(100) DEFAULT 'main',
                status VARCHAR(50) DEFAULT 'pending',
                created_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (goal_id) REFERENCES learning_goals(id)
            )
        """)
        print("   ✓ Old table structure created")

        # Drop new table
        print("\n2. Dropping new submissions table...")
        cursor.execute("DROP TABLE submissions")
        print("   ✓ New table dropped")

        # Rename old table
        print("\n3. Renaming old table...")
        cursor.execute("ALTER TABLE submissions_old RENAME TO submissions")
        print("   ✓ Table renamed")

        # Commit changes
        conn.commit()
        print("\n" + "=" * 60)
        print("✅ Rollback completed successfully!")
        print("=" * 60)

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Rollback failed: {str(e)}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='SQLite database migration for PR URL support')
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
        print("\n⚠️  IMPORTANT: This migration will delete all existing submissions.")
        print("   The old repo_url/branch data cannot be converted to PR URLs.")
        print("   Make sure you have a database backup before proceeding.\n")

        confirm = input("Continue with migration? (yes/no): ")
        if confirm.lower() == 'yes':
            run_migration()
        else:
            print("Migration cancelled.")
