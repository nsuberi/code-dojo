"""
Database Migration: Add current_topic_thread_id column to agent_sessions table

This migration adds the current_topic_thread_id column to store the current topic's
thread ID for trace continuity across HTTP request boundaries in the articulation harness.

Usage:
    python migrations/add_topic_thread_id.py
    python migrations/add_topic_thread_id.py --rollback

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


def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    return column_name in columns


def run_migration():
    """Execute the migration."""
    print("Starting migration: Add current_topic_thread_id column")
    print("=" * 60)

    db_path = get_database_path()
    print(f"\nDatabase: {db_path}")

    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if column already exists
        print("\n1. Checking if current_topic_thread_id column exists...")
        if column_exists(cursor, 'agent_sessions', 'current_topic_thread_id'):
            print("   ✓ Column already exists. Migration not needed.")
            conn.close()
            return

        # Add the column
        print("\n2. Adding current_topic_thread_id column to agent_sessions...")
        cursor.execute("""
            ALTER TABLE agent_sessions
            ADD COLUMN current_topic_thread_id VARCHAR(100)
        """)

        conn.commit()
        print("   ✓ Column added successfully")
        print("\n✓ Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"\n✗ Migration failed: {e}")
        sys.exit(1)
    finally:
        conn.close()


def rollback():
    """Remove current_topic_thread_id column (SQLite requires table recreation)."""
    print("\nNote: SQLite doesn't support DROP COLUMN directly.")
    print("To rollback, you would need to recreate the table without the column.")
    print("This is a destructive operation and not implemented in this script.")
    print("\nIf you need to rollback, manually:")
    print("  1. Create new table without the column")
    print("  2. Copy data from old table")
    print("  3. Drop old table")
    print("  4. Rename new table")
    return False


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("Code Dojo Database Migration")
    print("=" * 60)

    if '--rollback' in sys.argv:
        rollback()
        sys.exit(0)

    response = input("\nThis will add current_topic_thread_id column to agent_sessions. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Migration cancelled.")
        sys.exit(0)

    run_migration()
    print("\n" + "=" * 60)
