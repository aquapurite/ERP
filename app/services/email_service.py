import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending transactional emails via Gmail SMTP."""

    def __init__(
        self,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_password: str = "",
        from_email: str = "",
        from_name: str = "Aquapurite ERP"
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email or smtp_user
        self.from_name = from_name

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email using Gmail SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body of the email
            text_content: Plain text body (optional fallback)

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.smtp_user or not self.smtp_password:
            logger.warning("Email not configured. SMTP credentials missing.")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email

            # Add plain text version
            if text_content:
                part1 = MIMEText(text_content, 'plain')
                msg.attach(part1)

            # Add HTML version
            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)

            # Connect and send with timeout
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to_email, msg.as_string())

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP Authentication failed. Check email credentials.")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return False
        except TimeoutError:
            logger.error("SMTP connection timed out")
            return False
        except OSError as e:
            logger.error(f"Network error sending email: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        reset_url: str,
        user_name: str = "User"
    ) -> bool:
        """
        Send a password reset email.

        Args:
            to_email: User's email address
            reset_token: The password reset token
            reset_url: Full URL to reset password page
            user_name: User's name for personalization

        Returns:
            True if email sent successfully, False otherwise
        """
        subject = "Reset Your Password - Aquapurite ERP"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #1a56db; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background: #f9f9f9; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #1a56db; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .token-box {{ background: #e5e7eb; padding: 15px; border-radius: 5px; font-family: monospace; word-break: break-all; margin: 15px 0; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Aquapurite ERP</h1>
                </div>
                <div class="content">
                    <h2>Password Reset Request</h2>
                    <p>Hello {user_name},</p>
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>

                    <p style="text-align: center;">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </p>

                    <p>Or copy and paste this link in your browser:</p>
                    <p style="word-break: break-all; color: #1a56db;">{reset_url}</p>

                    <p><strong>Your reset token:</strong></p>
                    <div class="token-box">{reset_token}</div>

                    <p>This link will expire in <strong>1 hour</strong>.</p>

                    <p>If you didn't request this password reset, please ignore this email or contact support if you have concerns.</p>

                    <p>Best regards,<br>Aquapurite ERP Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from Aquapurite Private Limited's ERP System.</p>
                    <p>Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Password Reset Request

        Hello {user_name},

        We received a request to reset your password.

        Click this link to reset your password:
        {reset_url}

        Or use this token: {reset_token}

        This link will expire in 1 hour.

        If you didn't request this password reset, please ignore this email.

        Best regards,
        Aquapurite ERP Team
        """

        return self.send_email(to_email, subject, html_content, text_content)


# Create a default instance (will be configured via environment variables)
def get_email_service() -> EmailService:
    """Get configured email service instance."""
    from app.config import settings

    return EmailService(
        smtp_host=getattr(settings, 'SMTP_HOST', 'smtp.gmail.com'),
        smtp_port=getattr(settings, 'SMTP_PORT', 587),
        smtp_user=getattr(settings, 'SMTP_USER', ''),
        smtp_password=getattr(settings, 'SMTP_PASSWORD', ''),
        from_email=getattr(settings, 'SMTP_FROM_EMAIL', ''),
        from_name=getattr(settings, 'SMTP_FROM_NAME', 'Aquapurite ERP')
    )
