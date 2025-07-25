import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Email configuration from environment variables
        self.smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_user = os.environ.get('SMTP_USER')
        self.smtp_password = os.environ.get('SMTP_PASSWORD')
        self.from_email = os.environ.get('FROM_EMAIL', self.smtp_user)
        self.app_url = os.environ.get('APP_URL', 'http://localhost:8501')
    
    def send_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Send password reset email"""
        if not self.smtp_user or not self.smtp_password:
            logger.error("Email configuration missing. Set SMTP_USER and SMTP_PASSWORD environment variables.")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'Marine Seguros - Recuperação de Senha'
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Create the body of the message
            reset_url = f"{self.app_url}?reset_token={reset_token}"
            
            text = f"""
            Olá,
            
            Você solicitou a recuperação de senha para sua conta no Marine Seguros.
            
            Para criar uma nova senha, acesse o link abaixo:
            {reset_url}
            
            Este link é válido por 1 hora.
            
            Se você não solicitou esta recuperação, ignore este email.
            
            Atenciosamente,
            Equipe Marine Seguros
            """
            
            html = f"""
            <html>
              <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                  <h2 style="color: #2563eb;">Marine Seguros - Recuperação de Senha</h2>
                  
                  <p>Olá,</p>
                  
                  <p>Você solicitou a recuperação de senha para sua conta no Marine Seguros.</p>
                  
                  <p>Para criar uma nova senha, clique no botão abaixo:</p>
                  
                  <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" style="background-color: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                      Criar Nova Senha
                    </a>
                  </div>
                  
                  <p style="color: #666; font-size: 14px;">Este link é válido por 1 hora.</p>
                  
                  <p style="color: #666; font-size: 14px;">Se você não solicitou esta recuperação, ignore este email.</p>
                  
                  <hr style="border: 1px solid #eee; margin: 30px 0;">
                  
                  <p style="color: #999; font-size: 12px;">
                    Atenciosamente,<br>
                    Equipe Marine Seguros
                  </p>
                </div>
              </body>
            </html>
            """
            
            # Record the MIME types of both parts
            part1 = MIMEText(text, 'plain')
            part2 = MIMEText(html, 'html')
            
            # Attach parts into message container
            msg.attach(part1)
            msg.attach(part2)
            
            # Send the message via SMTP server
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Password reset email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def send_welcome_email(self, to_email: str, username: str) -> bool:
        """Send welcome email to new user"""
        if not self.smtp_user or not self.smtp_password:
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'Bem-vindo ao Marine Seguros'
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            text = f"""
            Olá {username},
            
            Bem-vindo ao Marine Seguros!
            
            Sua conta foi criada com sucesso. Você já pode fazer login e acessar o sistema.
            
            Acesse: {self.app_url}
            
            Atenciosamente,
            Equipe Marine Seguros
            """
            
            html = f"""
            <html>
              <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                  <h2 style="color: #2563eb;">Bem-vindo ao Marine Seguros!</h2>
                  
                  <p>Olá {username},</p>
                  
                  <p>Sua conta foi criada com sucesso. Você já pode fazer login e acessar o sistema.</p>
                  
                  <div style="text-align: center; margin: 30px 0;">
                    <a href="{self.app_url}" style="background-color: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                      Acessar Sistema
                    </a>
                  </div>
                  
                  <hr style="border: 1px solid #eee; margin: 30px 0;">
                  
                  <p style="color: #999; font-size: 12px;">
                    Atenciosamente,<br>
                    Equipe Marine Seguros
                  </p>
                </div>
              </body>
            </html>
            """
            
            part1 = MIMEText(text, 'plain')
            part2 = MIMEText(html, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email: {e}")
            return False