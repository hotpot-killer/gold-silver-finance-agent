import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from .base import BaseNotifier

logger = logging.getLogger(__name__)

class EmailNotifier(BaseNotifier):
    """邮件通知"""
    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        to_emails: List[str]
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
        
    def send(self, title: str, content: str) -> bool:
        """发送邮件通知"""
        try:
            msg = MIMEMultipart()
            msg['Subject'] = title
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            
            text_part = MIMEText(content, 'html')
            msg.attach(text_part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.from_email, self.to_emails, msg.as_string())
                
            logger.info("Email notification sent successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
