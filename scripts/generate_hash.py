from werkzeug.security import generate_password_hash
import sys

if len(sys.argv) > 1:
    password = sys.argv[1]
    print(f"Password: {password}")
    print(f"Hash: {generate_password_hash(password)}")
else:
    print("Usage: python scripts/generate_hash.py <password>")
    print("Example: python scripts/generate_hash.py admin123")
