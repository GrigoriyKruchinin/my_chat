import smtplib
from celery import shared_task
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings


@shared_task
def send_email(to_email, subject, message):
    msg = MIMEMultipart()
    msg["From"] = settings.SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(message, "plain"))

    with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
