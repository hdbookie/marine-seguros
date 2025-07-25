# Email Configuration Guide

## Why Email is Important

When users sign up, they provide their email address. The system uses email for:
- Welcome emails when users register
- Password reset links
- Account notifications

## Gmail Setup (Recommended)

### Step 1: Enable 2-Factor Authentication
1. Go to your Google Account settings
2. Security → 2-Step Verification → Turn on

### Step 2: Generate App Password
1. Go to https://myaccount.google.com/security
2. Under "2-Step Verification", click "App passwords"
3. Select "Mail" and your device
4. Copy the 16-character password

### Step 3: Update .env File
```env
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx  # Your 16-character app password
```

## Alternative Email Providers

### Outlook/Hotmail
```env
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=your-email@outlook.com
SMTP_PASSWORD=your-password
```

### Yahoo
```env
SMTP_HOST=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USER=your-email@yahoo.com
SMTP_PASSWORD=your-app-password
```

## Testing Email

Run this command to test your email configuration:
```python
from auth.email_service import EmailService
email = EmailService()
# Check if configuration is loaded
print(f"SMTP User: {email.smtp_user}")
print(f"SMTP Host: {email.smtp_host}")
```

## What Happens Without Email?

If email is not configured:
- Users can still register and login
- Password reset won't work
- No welcome emails will be sent
- The app will show a warning but continue working

## Security Notes

- Never commit your .env file to git
- Use app passwords, not your regular email password
- Consider using a dedicated email account for the app