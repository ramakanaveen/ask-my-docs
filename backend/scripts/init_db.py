#!/usr/bin/env python3
"""
Database Initialization Script (Python)

This script initializes the PostgreSQL database for Ask My Docs:
- Creates database and user
- Enables PGVector extension
- Runs Alembic migrations

Usage:
    python scripts/init_db.py
"""

import os
import subprocess
import sys
from pathlib import Path

try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("Error: psycopg2 is not installed")
    print("Please install it: pip install psycopg2-binary")
    sys.exit(1)


# Colors for output
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'


def print_colored(message: str, color: str = Colors.NC):
    """Print colored message."""
    print(f"{color}{message}{Colors.NC}")


def main():
    """Main initialization function."""

    # Configuration from environment
    db_name = os.getenv('DB_NAME', 'askmydocs')
    db_user = os.getenv('DB_USER', 'askmydocs')
    db_password = os.getenv('DB_PASSWORD', 'password')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    postgres_user = os.getenv('POSTGRES_USER', 'postgres')
    postgres_password = os.getenv('POSTGRES_PASSWORD', None)

    print_colored("=" * 40, Colors.GREEN)
    print_colored("Ask My Docs - Database Initialization", Colors.GREEN)
    print_colored("=" * 40, Colors.GREEN)
    print()

    # Connect to PostgreSQL
    print_colored("→ Connecting to PostgreSQL...", Colors.YELLOW)
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=postgres_user,
            password=postgres_password,
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        print_colored("✓ Connected to PostgreSQL", Colors.GREEN)
        print()
    except Exception as e:
        print_colored(f"✗ Cannot connect to PostgreSQL: {e}", Colors.RED)
        print_colored("  Please ensure PostgreSQL is running and credentials are correct.", Colors.RED)
        sys.exit(1)

    # Drop database if exists
    print_colored(f"→ Checking if database '{db_name}' exists...", Colors.YELLOW)
    try:
        cursor.execute(
            sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"),
            [db_name]
        )
        if cursor.fetchone():
            print_colored(f"  Database '{db_name}' exists. Dropping it...", Colors.YELLOW)
            cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db_name)))
            print_colored("✓ Dropped existing database", Colors.GREEN)
        else:
            print_colored(f"  Database '{db_name}' does not exist", Colors.GREEN)
    except Exception as e:
        print_colored(f"Warning: {e}", Colors.YELLOW)
    print()

    # Drop user if exists
    print_colored(f"→ Checking if user '{db_user}' exists...", Colors.YELLOW)
    try:
        cursor.execute(
            sql.SQL("SELECT 1 FROM pg_roles WHERE rolname = %s"),
            [db_user]
        )
        if cursor.fetchone():
            print_colored(f"  User '{db_user}' exists. Dropping it...", Colors.YELLOW)
            cursor.execute(sql.SQL("DROP USER IF EXISTS {}").format(sql.Identifier(db_user)))
            print_colored("✓ Dropped existing user", Colors.GREEN)
        else:
            print_colored(f"  User '{db_user}' does not exist", Colors.GREEN)
    except Exception as e:
        print_colored(f"Warning: {e}", Colors.YELLOW)
    print()

    # Create user
    print_colored(f"→ Creating user '{db_user}'...", Colors.YELLOW)
    try:
        cursor.execute(
            sql.SQL("CREATE USER {} WITH PASSWORD %s").format(sql.Identifier(db_user)),
            [db_password]
        )
        cursor.execute(
            sql.SQL("ALTER USER {} WITH SUPERUSER").format(sql.Identifier(db_user))
        )
        print_colored("✓ User created", Colors.GREEN)
    except Exception as e:
        print_colored(f"✗ Failed to create user: {e}", Colors.RED)
        sys.exit(1)
    print()

    # Create database
    print_colored(f"→ Creating database '{db_name}'...", Colors.YELLOW)
    try:
        cursor.execute(
            sql.SQL("CREATE DATABASE {} OWNER {}").format(
                sql.Identifier(db_name),
                sql.Identifier(db_user)
            )
        )
        cursor.execute(
            sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
                sql.Identifier(db_name),
                sql.Identifier(db_user)
            )
        )
        print_colored("✓ Database created", Colors.GREEN)
    except Exception as e:
        print_colored(f"✗ Failed to create database: {e}", Colors.RED)
        sys.exit(1)
    print()

    # Close connection to postgres database
    cursor.close()
    conn.close()

    # Connect to new database to enable PGVector
    print_colored("→ Enabling PGVector extension...", Colors.YELLOW)
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=postgres_user,
            password=postgres_password,
            database=db_name
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cursor.close()
        conn.close()
        print_colored("✓ PGVector extension enabled", Colors.GREEN)
    except Exception as e:
        print_colored(f"✗ Failed to enable PGVector: {e}", Colors.RED)
        sys.exit(1)
    print()

    # Update .env file
    backend_dir = Path(__file__).parent.parent
    env_file = backend_dir / '.env'
    env_example = backend_dir / '.env.example'

    if not env_file.exists():
        print_colored("→ No .env file found. Creating from .env.example...", Colors.YELLOW)
        if env_example.exists():
            # Copy .env.example to .env
            with open(env_example, 'r') as f:
                content = f.read()

            # Update DATABASE_URL
            database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                if line.startswith('DATABASE_URL='):
                    new_lines.append(f'DATABASE_URL={database_url}')
                else:
                    new_lines.append(line)

            with open(env_file, 'w') as f:
                f.write('\n'.join(new_lines))

            print_colored("✓ Created .env file", Colors.GREEN)
        else:
            print_colored("Warning: .env.example not found", Colors.YELLOW)
        print()

    # Run Alembic migrations
    print_colored("→ Running database migrations...", Colors.YELLOW)
    try:
        os.chdir(backend_dir)
        result = subprocess.run(
            ['alembic', 'upgrade', 'head'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_colored("✓ Migrations completed", Colors.GREEN)
        else:
            print_colored(f"✗ Migration failed: {result.stderr}", Colors.RED)
            sys.exit(1)
    except Exception as e:
        print_colored(f"✗ Failed to run migrations: {e}", Colors.RED)
        sys.exit(1)
    print()

    # Display summary
    print_colored("=" * 40, Colors.GREEN)
    print_colored("✓ Database initialization complete!", Colors.GREEN)
    print_colored("=" * 40, Colors.GREEN)
    print()
    print("Database Details:")
    print(f"  Host:     {db_host}")
    print(f"  Port:     {db_port}")
    print(f"  Database: {db_name}")
    print(f"  User:     {db_user}")
    print(f"  Password: {db_password}")
    print()
    print("Connection String:")
    print(f"  postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")
    print()
    print_colored("Next steps:", Colors.YELLOW)
    print("  1. Update your .env file with the correct API keys")
    print("  2. Run the backend: uvicorn app.main:app --reload")
    print()


if __name__ == '__main__':
    main()
