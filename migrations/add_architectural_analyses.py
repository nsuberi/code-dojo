"""
Database Migration: Add architectural_analyses table

This migration adds the architectural_analyses table to store PR architecture insights.

Usage:
    python migrations/add_architectural_analyses.py

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
    print("Starting migration: Add architectural_analyses table")
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
        print("\n1. Checking if architectural_analyses table exists...")
        if table_exists(cursor, 'architectural_analyses'):
            print("   ✓ Table already exists. Migration not needed.")
            conn.close()
            return

        # Create the new table
        print("\n2. Creating architectural_analyses table...")
        cursor.execute("""
            CREATE TABLE architectural_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id INTEGER NOT NULL UNIQUE,
                created_at DATETIME NOT NULL,
                components_json TEXT,
                dependencies_diff_json TEXT,
                api_changes_json TEXT,
                schema_changes_json TEXT,
                scope_score VARCHAR(20),
                risk_score VARCHAR(20),
                complexity_score VARCHAR(20),
                component_diagram TEXT,
                dataflow_diagram TEXT,
                dependency_diagram TEXT,
                files_changed INTEGER DEFAULT 0,
                lines_added INTEGER DEFAULT 0,
                lines_removed INTEGER DEFAULT 0,
                FOREIGN KEY (submission_id) REFERENCES submissions (id)
            )
        """)

        # Create index on submission_id for faster lookups
        cursor.execute("""
            CREATE INDEX idx_arch_analysis_submission
            ON architectural_analyses (submission_id)
        """)

        conn.commit()
        print("   ✓ Table created successfully")
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

    response = input("\nThis will add the architectural_analyses table. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Migration cancelled.")
        sys.exit(0)

    run_migration()
    print("\n" + "=" * 60)
