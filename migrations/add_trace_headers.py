"""
Database Migration: Add trace header columns to agent_sessions table

This migration adds:
- langsmith_trace_headers: Store serialized headers for parent trace context
- current_topic_trace_headers: Store serialized headers for topic trace context

These headers enable proper parent-child trace linking across HTTP request boundaries
in LangSmith, fixing the issue where child traces weren't nesting under parent traces.

Usage:
    python migrations/add_trace_headers.py
    python migrations/add_trace_headers.py --rollback

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
    print("Starting migration: Add trace header columns")
    print("=" * 60)

    db_path = get_database_path()
    print(f"\nDatabase: {db_path}")

    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        columns_to_add = [
            ('langsmith_trace_headers', 'TEXT'),
            ('current_topic_trace_headers', 'TEXT'),
        ]

        for column_name, column_type in columns_to_add:
            print(f"\n1. Checking if {column_name} column exists...")
            if column_exists(cursor, 'agent_sessions', column_name):
                print(f"   - Column {column_name} already exists. Skipping.")
                continue

            print(f"2. Adding {column_name} column to agent_sessions...")
            cursor.execute(f"""
                ALTER TABLE agent_sessions
                ADD COLUMN {column_name} {column_type}
            """)
            print(f"   + Column {column_name} added successfully")

        conn.commit()
        print("\n" + "=" * 60)
        print("Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"\nMigration failed: {e}")
        sys.exit(1)
    finally:
        conn.close()


def rollback():
    """Remove trace header columns (SQLite requires table recreation)."""
    print("\nNote: SQLite doesn't support DROP COLUMN directly.")
    print("To rollback, you would need to recreate the table without the columns.")
    print("This is a destructive operation and not implemented in this script.")
    print("\nIf you need to rollback, manually:")
    print("  1. Create new table without the columns")
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

    response = input("\nThis will add trace header columns to agent_sessions. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Migration cancelled.")
        sys.exit(0)

    run_migration()
    print("\n" + "=" * 60)
