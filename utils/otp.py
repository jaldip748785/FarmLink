import os
import random
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import session


def generate_otp_code():
    """Generate a random 6-digit OTP code."""
    return str(random.randint(100000, 999999))


def send_real_email_otp(target_email, code):
    """
    Optional SMTP Real Email sending function.
    Reads SMTP settings from environment variables if set.
    """
    if not target_email or "@" not in target_email:
        return False, "Invalid email address."

    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER") or os.getenv("MAIL_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD") or os.getenv("MAIL_PASSWORD")

    if not smtp_user or not smtp_pass:
        return False, "SMTP credentials not configured."

    try:
        msg = MIMEMultipart()
        msg["From"] = f"FarmLink Security <{smtp_user}>"
        msg["To"] = target_email
        msg["Subject"] = f"{code} is your FarmLink Confirmation Code"

        body = f"""Hello,

Your FarmLink 6-digit confirmation code is: {code}

This code is valid for 10 minutes. Please enter it to complete your verification.

Best regards,
FarmLink Security Team
"""
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        return True, "Email sent successfully."
    except Exception as e:
        print("SMTP Email Error:", e)
        return False, str(e)


def create_otp_session(purpose, target, extra_data=None):
    """
    Store OTP code and metadata in Flask session.
    purpose: 'registration' or 'login'
    target: email address or mobile number
    extra_data: dict containing pending user registration data or user_id
    """
    code = generate_otp_code()
    expires_at = time.time() + 600  # 10 minutes validity

    session['otp_code'] = code
    session['otp_target'] = target
    session['otp_purpose'] = purpose
    session['otp_expires_at'] = expires_at
    if extra_data:
        session['otp_data'] = extra_data

    # Log to server console for testing/debugging
    print(f"\n==========================================")
    print(f"[OTP CONFIRMATION CODE SENT]")
    print(f"Target: {target}")
    print(f"Purpose: {purpose}")
    print(f"Code: {code}")
    print(f"==========================================\n")

    # Try sending real email if SMTP is configured
    if target and "@" in target:
        send_real_email_otp(target, code)

    return code


def check_otp_code(submitted_code):
    """
    Verify submitted OTP code against session data.
    Returns (success: bool, error_message: str or None)
    """
    if not submitted_code:
        return False, "Please enter the 6-digit confirmation code."

    stored_code = session.get('otp_code')
    expires_at = session.get('otp_expires_at')

    if not stored_code or not expires_at:
        return False, "Verification session expired. Please request a new code."

    if time.time() > expires_at:
        session.pop('otp_code', None)
        return False, "Confirmation code has expired. Please resend a new code."

    if str(submitted_code).strip() != str(stored_code).strip():
        return False, "Invalid confirmation code. Please check the code and try again."

    return True, None


def clear_otp_session():
    """Clear OTP session variables."""
    session.pop('otp_code', None)
    session.pop('otp_target', None)
    session.pop('otp_purpose', None)
    session.pop('otp_expires_at', None)
    session.pop('otp_data', None)
