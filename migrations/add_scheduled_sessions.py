"""
Database Migration: Add scheduled_sessions table

This migration adds the scheduled_sessions table to track when students
schedule sensei sessions for their submissions.

Usage:
    python migrations/add_scheduled_sessions.py

This migration is idempotent - safe to run multiple times.
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


def table_exists(cursor, table_name):
    """Check if a table exists."""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def run_migration():
    """Execute the migration."""
    print("Starting migration: Add scheduled_sessions table")
    print("=" * 60)

    db_path = get_database_path()
    print(f"\nDatabase: {db_path}")

    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if table already exists
        print("\n1. Checking if scheduled_sessions table exists...")
        if table_exists(cursor, 'scheduled_sessions'):
            print("   ✓ Table already exists. Migration not needed.")
            conn.close()
            return

        # Create the new table
        print("\n2. Creating scheduled_sessions table...")
        cursor.execute("""
            CREATE TABLE scheduled_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                eligibility_reason VARCHAR(50),
                goals_passed INTEGER DEFAULT 0,
                goals_engaged INTEGER DEFAULT 0,
                total_goals INTEGER DEFAULT 0,
                scheduled_at DATETIME NOT NULL,
                session_completed_at DATETIME,
                notes TEXT,
                FOREIGN KEY (submission_id) REFERENCES submissions (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        # Create indexes for faster lookups
        print("\n3. Creating indexes...")
        cursor.execute("""
            CREATE INDEX idx_scheduled_sessions_submission
            ON scheduled_sessions (submission_id)
        """)
        cursor.execute("""
            CREATE INDEX idx_scheduled_sessions_user
            ON scheduled_sessions (user_id)
        """)

        conn.commit()
        print("   ✓ Table and indexes created successfully")
        print("\n✓ Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"\n✗ Migration failed: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("Code Dojo Database Migration")
    print("=" * 60)

    response = input("\nThis will add the scheduled_sessions table. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Migration cancelled.")
        sys.exit(0)

    run_migration()
    print("\n" + "=" * 60)
