import os
from twilio.rest import Client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

# #loading
# load_dotenv()

# Environment variables for sensitive information
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
TO_PHONE_NUMBER = os.getenv('TO_PHONE_NUMBER')

EMAIL_FROM = os.getenv('EMAIL_FROM')
EMAIL_TO = os.getenv('EMAIL_TO')
EMAIL_SUBJECT = 'CO2 Alert'
EMAIL_APP_PASSWORD = os.getenv('EMAIL_APP_PASSWORD')
EMAIL_SERVER = 'smtp.gmail.com'
EMAIL_PORT = 587

# Track the time of the last sent email and SMS
last_email_time = 0
last_sms_time = 0

def send_alert_email(subject, body):
    global last_email_time
    current_time = time.time()

    if current_time - last_email_time > 600:  # 10 minutes
        try:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_FROM
            msg['To'] = EMAIL_TO
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(EMAIL_SERVER, EMAIL_PORT)
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
            server.quit()

            print("Email sent successfully.")
            last_email_time = current_time  # Update the last email time
        except Exception as e:
            print(f"Failed to send email: {e}")

def send_alert_sms(body):
    global last_sms_time
    current_time = time.time()

    if current_time - last_sms_time > 600:  # 10 minutes
        try:
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                body=body,
                from_=TWILIO_PHONE_NUMBER,
                to=TO_PHONE_NUMBER
            )
            print("SMS sent successfully.")
            last_sms_time = current_time  # Update the last SMS time
        except Exception as e:
            print(f"Failed to send SMS: {e}")
