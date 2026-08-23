#!/usr/bin/env python
"""Run alembic migrations."""
import sys
import os
import subprocess

# Add the backend directory to the path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

def run_migrations():
    """Run alembic migrations."""
    os.chdir(backend_dir)
    result = subprocess.run([
        sys.executable, "-m", "alembic", "upgrade", "head"
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Migration failed: {result.stderr}")
        return False
    print(result.stdout)
    return True


def create_migration(message: str):
    """Create a new migration."""
    os.chdir(backend_dir)
    result = subprocess.run([
        sys.executable, "-m", "alembic", "revision", "--autogenerate", "-m", message
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Migration creation failed: {result.stderr}")
        return False
    print(result.stdout)
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run or create alembic migrations")
    parser.add_argument("--create", "-c", type=str, help="Create new migration with message")
    parser.add_argument("--run", "-r", action="store_true", help="Run migrations (default)")

    args = parser.parse_args()

    if args.create:
        success = create_migration(args.create)
    else:
        success = run_migrations()

    sys.exit(0 if success else 1)