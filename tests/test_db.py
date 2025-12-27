#!/usr/bin/env python
import os
import sys
from app import app, db, Inquiry

print("Testing database connection...")
print(f"DEBUG: {app.debug}")
print(f"DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

try:
    with app.app_context():
        # Test query
        inquiries = Inquiry.query.all()
        print(f"✓ Database connection successful!")
        print(f"✓ Total inquiries in DB: {len(inquiries)}")
        for inquiry in inquiries:
            print(f"  - {inquiry.name} ({inquiry.email})")
except Exception as e:
    print(f"✗ Database error: {e}")
    sys.exit(1)
