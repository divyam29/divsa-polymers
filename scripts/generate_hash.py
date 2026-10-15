"""Generate an admin password hash without exposing the password in argv/logs."""
from getpass import getpass
from werkzeug.security import generate_password_hash

if __name__ == '__main__':
    password = getpass('Admin password (at least 12 characters): ')
    if len(password) < 12:
        raise SystemExit('Use a password of at least 12 characters.')
    if password != getpass('Confirm password: '):
        raise SystemExit('Passwords do not match.')
    # Some macOS Python builds lack hashlib.scrypt. PBKDF2 works on those
    # builds and is also supported by the app's password-hash validation.
    print(generate_password_hash(password, method='pbkdf2:sha256:1000000'))
