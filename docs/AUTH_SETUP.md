# Authentication Setup Guide

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` and configure:
   - `JWT_SECRET_KEY`: Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - Email settings (for password reset - optional)

3. **Run the app:**
   ```bash
   streamlit run app.py
   ```

4. **First user becomes admin:**
   - Register the first account
   - It will automatically be assigned admin role
   - Subsequent users will be regular users

## Features

### Security
- ✅ Bcrypt password hashing
- ✅ JWT session tokens
- ✅ Account lockout after 5 failed attempts (30 min)
- ✅ Secure password reset via email
- ✅ Audit logging of all security events
- ✅ Role-based access control

### User Roles
- **Admin**: Can upload/delete files, manage users
- **User**: Can view data and use analytics features

### Admin Features
- View all users
- Change user roles
- Activate/deactivate accounts
- Reset user passwords
- View audit logs

## Email Configuration (Optional)

For password reset functionality, configure email in `.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Use app password, not regular password
FROM_EMAIL=noreply@marineseguros.com
APP_URL=https://your-deployed-app.com
```

### Gmail App Password
1. Enable 2-factor authentication
2. Go to Google Account settings
3. Security → 2-Step Verification → App passwords
4. Generate app password for "Mail"

## Database

Authentication data is stored in `data/auth.db` (SQLite):
- Users table
- Sessions table
- Password reset tokens
- Audit log

## Deployment

### Streamlit Community Cloud
1. Add secrets in app settings:
   ```toml
   JWT_SECRET_KEY = "your-secret-key"
   SMTP_USER = "your-email@gmail.com"
   SMTP_PASSWORD = "your-app-password"
   ```

### Other Platforms
- Set environment variables as per platform documentation
- Ensure `data/` directory is writable for SQLite

## Troubleshooting

- **"Account locked"**: Wait 30 minutes or have admin reset
- **Email not sending**: Check SMTP settings and app password
- **Session expired**: Login again (sessions last 7 days)

## Security Best Practices

1. Use strong JWT secret key
2. Enable email for password recovery
3. Regularly review audit logs
4. Use HTTPS in production
5. Keep dependencies updated