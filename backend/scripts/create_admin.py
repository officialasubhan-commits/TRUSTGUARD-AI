"""
TrustGuard AI — Initial Administrator Account Provisioning CLI.
Safely provisions an administrator account with Argon2id password hashing.
Can be executed interactively or via CLI arguments.

Usage:
    python scripts/create_admin.py --username admin --email admin@trustguard.ai
    python scripts/create_admin.py (prompts for inputs securely)
"""

import argparse
import asyncio
import getpass
import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

from app.core.admin_security import hash_admin_password
from app.database.connection import init_database
from app.database.repositories.admin_repo import get_admin_repository


async def main():
    parser = argparse.ArgumentParser(description="Provision a TrustGuard AI Administrator Account")
    parser.add_argument("--username", help="Administrator username (minimum 3 characters)")
    parser.add_argument("--password", help="Administrator password (minimum 8 characters)")
    parser.add_argument("--email", help="Administrator email address")
    parser.add_argument("--full-name", help="Administrator display name")
    parser.add_argument("--role", default="super_admin", choices=["super_admin", "security_analyst", "moderator"])
    args = parser.parse_args()

    print("=" * 60)
    print("TrustGuard AI — Administrator Account Provisioning")
    print("=" * 60)

    username = args.username
    if not username:
        username = input("Enter Admin Username: ").strip()
    if len(username) < 3:
        print("[ERROR] Username must be at least 3 characters.")
        sys.exit(1)

    password = args.password
    if not password:
        password = getpass.getpass("Enter Admin Password (min 8 characters): ")
        confirm_password = getpass.getpass("Confirm Admin Password: ")
        if password != confirm_password:
            print("[ERROR] Passwords do not match.")
            sys.exit(1)
    
    if len(password) < 8:
        print("[ERROR] Password must be at least 8 characters.")
        sys.exit(1)

    email = args.email or (input("Enter Admin Email (optional): ").strip() or None)
    full_name = args.full_name or (input("Enter Full Name (optional): ").strip() or None)
    role = args.role

    # Initialize connection
    init_database()
    repo = get_admin_repository()

    # Check if admin already exists
    existing = await repo.get_admin_by_username(username)
    if existing:
        print(f"[ERROR] Administrator with username '{username}' already exists.")
        sys.exit(1)

    print("\nHashing password using Argon2id...")
    password_hash = hash_admin_password(password)

    print(f"Creating administrator '{username}' with role '{role}'...")
    admin = await repo.create_admin_user(
        username=username,
        password_hash=password_hash,
        email=email,
        full_name=full_name,
        role=role,
    )

    # Log initial provisioning event
    await repo.log_audit_event(
        action="ADMIN_PROVISIONED",
        admin_username=username,
        admin_id=admin.id,
        target_resource=f"admin:{admin.id}",
        outcome="SUCCESS",
        details={"provisioned_via": "CLI_SCRIPT", "role": role},
    )

    print("=" * 60)
    print(f"[SUCCESS] Administrator Account Created!")
    print(f"  ID:       {admin.id}")
    print(f"  Username: {admin.username}")
    print(f"  Role:     {admin.role}")
    print(f"  Login at: http://localhost:5173/admin/login")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

