import threading
import smtplib
from email.mime.text import MIMEText
from flask import current_app

def send_inquiry_email(inquiry):
    app = current_app._get_current_object()
    host = app.config.get('EMAIL_HOST')
    port = app.config.get('EMAIL_PORT', 587)
    username = app.config.get('EMAIL_USERNAME')
    password = app.config.get('EMAIL_PASSWORD')
    use_tls = app.config.get('EMAIL_USE_TLS', True)
    from_email = app.config.get('EMAIL_FROM') or username
    to_email = app.config.get('EMAIL_TO_ADMIN', 'divyamjain29@gmail.com')

    if not host or not from_email or not to_email:
        app.logger.warning('Email not sent - missing SMTP configuration')
        return

    subject = f"New inquiry from {inquiry.get('name', 'Unknown')}"
    lines = [
        f"Name: {inquiry.get('name', 'N/A')}",
        f"Email: {inquiry.get('email', 'N/A')}",
        f"Phone: {inquiry.get('phone', 'N/A')}",
        f"City: {inquiry.get('city', 'N/A')}",
        f"Business: {inquiry.get('business_info', 'N/A')}",
        f"Quantity: {inquiry.get('quantity_required', 'N/A')}",
        f"Product ID: {inquiry.get('product_id', 'N/A')}",
    ]
    body = '\n'.join(lines)

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    try:
        # Synchronous for Vercel
        server = smtplib.SMTP(host, port, timeout=10)
        if use_tls: server.starttls()
        if username and password: server.login(username, password)
        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
        app.logger.info('Inquiry email sent')
    except Exception as e:
        app.logger.error(f'Failed to send email: {e}')
