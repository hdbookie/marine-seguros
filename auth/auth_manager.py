import streamlit as st
import bcrypt
import jwt
import sqlite3
from datetime import datetime, timedelta
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from typing import Optional, Dict, Tuple
import logging
from config import get_env_var

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthManager:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Use environment variable if available (for Railway volumes)
            data_dir = os.environ.get('DATA_PATH', 'data')
            db_path = os.path.join(data_dir, 'auth.db')
        self.db_path = db_path
        self.secret_key = get_env_var('JWT_SECRET_KEY', secrets.token_urlsafe(32))
        # Set SQLite to handle concurrent access better
        self.init_database()
        self._configure_sqlite()
    
    def _configure_sqlite(self):
        """Configure SQLite for better concurrent access"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        conn.execute("PRAGMA busy_timeout=5000")  # 5 second timeout
        conn.close()
    
    def init_database(self):
        """Initialize authentication database with secure schema"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.execute("PRAGMA busy_timeout=5000")
        cursor = conn.cursor()
        
        # Users table with secure password storage
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                failed_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP
            )
        ''')
        
        # Password reset tokens
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Session tokens for persistence
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Audit log for security
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                success BOOLEAN,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def create_user(self, email: str, username: str, password: str, role: str = 'user') -> bool:
        """Create new user with hashed password"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (email, username, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', (email, username, password_hash, role))
            
            conn.commit()
            conn.close()
            
            self.log_action(None, f"User created: {username}", success=True)
            return True
            
        except sqlite3.IntegrityError:
            self.log_action(None, f"Failed to create user: {username} (already exists)", success=False)
            return False
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and create session"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        cursor = conn.cursor()
        
        try:
            # Check if user exists and is not locked
            cursor.execute('''
                SELECT id, email, username, password_hash, role, failed_attempts, locked_until
                FROM users
                WHERE username = ? AND is_active = 1
            ''', (username,))
            
            user = cursor.fetchone()
            
            if not user:
                self.log_action(None, f"Login attempt for non-existent user: {username}", success=False)
                return None
            
            user_id, email, username, password_hash, role, failed_attempts, locked_until = user
            
            # Check if account is locked
            if locked_until:
                locked_time = datetime.fromisoformat(locked_until)
                if datetime.now() < locked_time:
                    self.log_action(user_id, "Login attempt on locked account", success=False)
                    return None
                else:
                    # Unlock account
                    cursor.execute('''
                        UPDATE users 
                        SET locked_until = NULL, failed_attempts = 0
                        WHERE id = ?
                    ''', (user_id,))
            
            # Verify password
            if not self.verify_password(password, password_hash):
                # Increment failed attempts
                failed_attempts += 1
                if failed_attempts >= 5:
                    # Lock account for 30 minutes
                    locked_until = datetime.now() + timedelta(minutes=30)
                    cursor.execute('''
                        UPDATE users 
                        SET failed_attempts = ?, locked_until = ?
                        WHERE id = ?
                    ''', (failed_attempts, locked_until, user_id))
                else:
                    cursor.execute('''
                        UPDATE users 
                        SET failed_attempts = ?
                        WHERE id = ?
                    ''', (failed_attempts, user_id))
                
                conn.commit()
                self.log_action(user_id, "Failed login attempt", success=False)
                return None
            
            # Success - reset failed attempts and update last login
            cursor.execute('''
                UPDATE users 
                SET failed_attempts = 0, last_login = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
            # Create session token in a separate connection
            session_token = self.create_session(user_id)
            
            self.log_action(user_id, "Successful login", success=True)
            
            return {
                'id': user_id,
                'email': email,
                'username': username,
                'role': role,
                'token': session_token
            }
        finally:
            if conn:
                conn.close()
    
    def create_session(self, user_id: int) -> str:
        """Create JWT session token"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(days=7),
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        
        # Store session in database with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=10.0)
                cursor = conn.cursor()
                
                expires_at = datetime.utcnow() + timedelta(days=7)
                cursor.execute('''
                    INSERT INTO sessions (user_id, token, expires_at)
                    VALUES (?, ?, ?)
                ''', (user_id, token, expires_at))
                
                conn.commit()
                conn.close()
                return token
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    import time
                    time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    raise
        
        return token
    
    def verify_session(self, token: str) -> Optional[Dict]:
        """Verify session token and return user info"""
        try:
            # Decode JWT
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            user_id = payload['user_id']
            
            # Check if session exists in database
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.id, u.email, u.username, u.role
                FROM users u
                JOIN sessions s ON u.id = s.user_id
                WHERE s.token = ? AND s.expires_at > CURRENT_TIMESTAMP
                AND u.is_active = 1
            ''', (token,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    'id': user[0],
                    'email': user[1],
                    'username': user[2],
                    'role': user[3]
                }
            
            return None
            
        except jwt.ExpiredSignatureError:
            logger.info("Expired session token")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid session token")
            return None
    
    def create_reset_token(self, email: str) -> Optional[str]:
        """Create password reset token"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        cursor = conn.cursor()
        
        # Get user
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return None
        
        user_id = user[0]
        
        # Create reset token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=1)
        
        cursor.execute('''
            INSERT INTO reset_tokens (user_id, token, expires_at)
            VALUES (?, ?, ?)
        ''', (user_id, token, expires_at))
        
        conn.commit()
        conn.close()
        
        self.log_action(user_id, "Password reset requested", success=True)
        
        return token
    
    def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using token"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        cursor = conn.cursor()
        
        # Verify token
        cursor.execute('''
            SELECT user_id FROM reset_tokens
            WHERE token = ? AND expires_at > CURRENT_TIMESTAMP AND used = 0
        ''', (token,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False
        
        user_id = result[0]
        password_hash = self.hash_password(new_password)
        
        # Update password
        cursor.execute('''
            UPDATE users SET password_hash = ?, failed_attempts = 0, locked_until = NULL
            WHERE id = ?
        ''', (password_hash, user_id))
        
        # Mark token as used
        cursor.execute('''
            UPDATE reset_tokens SET used = 1 WHERE token = ?
        ''', (token,))
        
        conn.commit()
        conn.close()
        
        self.log_action(user_id, "Password reset completed", success=True)
        
        return True
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> Tuple[bool, str]:
        """Change password for logged-in user"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        cursor = conn.cursor()
        
        # Get current password hash
        cursor.execute('''
            SELECT password_hash FROM users WHERE id = ? AND is_active = 1
        ''', (user_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False, "Usuário não encontrado"
        
        current_hash = result[0]
        
        # Verify current password
        if not bcrypt.checkpw(current_password.encode('utf-8'), current_hash.encode('utf-8')):
            self.log_action(user_id, "Failed password change - incorrect current password", success=False)
            conn.close()
            return False, "Senha atual incorreta"
        
        # Validate new password
        validation_result = self.validate_password(new_password)
        if not validation_result[0]:
            conn.close()
            return False, validation_result[1]
        
        # Hash new password
        new_password_hash = self.hash_password(new_password)
        
        # Update password
        cursor.execute('''
            UPDATE users SET password_hash = ?
            WHERE id = ?
        ''', (new_password_hash, user_id))
        
        conn.commit()
        conn.close()
        
        self.log_action(user_id, "Password changed successfully", success=True)
        
        return True, "Senha alterada com sucesso"
    
    def log_action(self, user_id: Optional[int], action: str, success: bool = True):
        """Log security-relevant actions"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO audit_log (user_id, action, success)
            VALUES (?, ?, ?)
        ''', (user_id, action, success))
        
        conn.commit()
        conn.close()
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user information by ID"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, email, username, role, is_active, created_at, last_login
            FROM users WHERE id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'email': user[1],
                'username': user[2],
                'role': user[3],
                'is_active': user[4],
                'created_at': user[5],
                'last_login': user[6]
            }
        
        return None
    
    def list_users(self) -> list:
        """List all users (admin only)"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, email, username, role, is_active, created_at, last_login
            FROM users
            ORDER BY created_at DESC
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'email': row[1],
                'username': row[2],
                'role': row[3],
                'is_active': row[4],
                'created_at': row[5],
                'last_login': row[6]
            })
        
        conn.close()
        return users
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        """Update user information"""
        allowed_fields = ['email', 'username', 'role', 'is_active']
        updates = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = ?")
                values.append(value)
        
        if not updates:
            return False
        
        values.append(user_id)
        
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        cursor = conn.cursor()
        
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        
        conn.commit()
        conn.close()
        
        return True