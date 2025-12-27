#!/usr/bin/env python
from app import app, db, Inquiry

# Create a test inquiry
test_inquiry = Inquiry(
    name='Test User',
    email='test@example.com',
    phone='9876543210',
    city='Mumbai',
    business_info='Test Business'
)

with app.app_context():
    try:
        db.session.add(test_inquiry)
        db.session.commit()
        print(f"✓ Successfully saved inquiry: {test_inquiry.name}")
        print(f"✓ Inquiry ID: {test_inquiry.id}")
        
        # Verify it was saved
        saved = Inquiry.query.get(test_inquiry.id)
        print(f"✓ Verified saved inquiry: {saved.name} ({saved.email})")
    except Exception as e:
        print(f"✗ Error: {e}")
        db.session.rollback()
