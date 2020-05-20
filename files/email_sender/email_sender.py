import os
import smtplib
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class EmailSender:

    def __init__(self, username=None, password=None):

        self.username = username if username is not None else os.environ["EMAIL_USERNAME"]
        self.password = password if password is not None else os.environ["EMAIL_PASSWORD"]

    def send_email(self, receiver_email, subject_name, attachment_fullpath):

        subject_name = str.replace(subject_name, ' ', '-')

        message = MIMEMultipart()
        message["From"]    = self.username
        message["To"]      = receiver_email
        message["Subject"] = f"Report - {subject_name}"

        body = "This is an automatically sent email"
        message.attach(MIMEText(body, "plain"))


        with open(attachment_fullpath, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        encoders.encode_base64(part)

        part.add_header(
            "Content-Disposition",
            f"attachment; filename= report-{subject_name}.pdf"
        )

        message.attach(part)
        text = message.as_string()

        print("sending email")
        port = 465  # For SSL
        # Create a secure SSL context
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(self.username, self.password)
            server.sendmail(self.username, receiver_email, text)