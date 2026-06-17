from flask_mail import Message
from flask import current_app
from app import mail

def send_reference_email(recipient, reference_no, track_url):
    if not current_app.config.get("MAIL_USERNAME"):
        return False, "Mail not configured."
    msg = Message(
        subject=f"Case Reference: {reference_no}",
        recipients=[recipient],
        body=f"Your case has been recorded.\n\nReference Number: {reference_no}\nTrack here: {track_url}"
    )
    mail.send(msg)
    return True, "Email sent."
