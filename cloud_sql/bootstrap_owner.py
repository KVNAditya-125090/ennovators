"""
Cloud SQL - first Owner.
Creates the Owner Manager account when no Owner exists yet, with a random temporary password that must be changed at
the first sign-in. The password is written to the file named by --password-file and never printed, so it can be moved
into Secret Manager.

    python -m cloud_sql.bootstrap_owner --email you@example.com --name "Your Name" --password-file out.txt
"""

import argparse
import secrets
import string
import sys

from cloud_sql import db
from cloud_sql.schema import ensure_schema
from cloud_sql.services.maas import cloud_sql_maas

def _password() -> str:
    letters = string.ascii_letters + string.digits
    while True:
        value = "".join(secrets.choice(letters) for _ in range(18))
        if any(c.islower() for c in value) and any(c.isupper() for c in value) and any(c.isdigit() for c in value):
            return value

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--password-file", required=True)
    args = parser.parse_args()

    ensure_schema()
    if db.one("SELECT 1 AS found FROM users WHERE role LIKE 'Owner%'"):
        print("An Owner already exists: nothing was changed.")
        return 1
    password = _password()
    user = cloud_sql_maas.create_account(args.name, args.email, "Owner / Manager", "Owner", password, must_change_password=True)
    with open(args.password_file, "w", encoding="utf-8") as out:
        out.write(password)
    print(f"Owner created: {user['email']} (user id {user['user_id']}). The temporary password is in {args.password_file}.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
