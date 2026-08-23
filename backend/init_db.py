#!/usr/bin/env python
"""Initialize database with all tables using alembic migrations."""
import sys
import os
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def init_db():
    """Run alembic migrations to create/update database tables."""
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print("Running database migrations...")

    # Check if alembic is initialized, if not initialize it
    alembic_dir = os.path.join(backend_dir, 'alembic')
    if not os.path.exists(alembic_dir):
        print("Initializing alembic...")
        result = subprocess.run([
            sys.executable, "-m", "alembic", "init", "alembic"
        ], cwd=backend_dir, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Alembic init failed: {result.stderr}")
            return False

    # Run migrations
    result = subprocess.run([
        sys.executable, "-m", "alembic", "upgrade", "head"
    ], cwd=backend_dir, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Migration failed: {result.stderr}")
        return False

    print(result.stdout)
    print("Database migrations completed successfully!")
    return True


if __name__ == "__main__":
    success = init_db()
    sys.exit(0 if success else 1)