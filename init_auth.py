#!/usr/bin/env python3
"""Initialize authentication database"""

import sqlite3
import bcrypt
from datetime import datetime

# Create database connection
conn = sqlite3.connect('auth.db')
cursor = conn.cursor()

# Create users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
)
''')

# Create default admin user
username = 'hdbooks15'
email = 'hdbooks15@gmail.com'
password = 'Hdb2016!!'

# Hash the password
hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Check if user exists
cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
if not cursor.fetchone():
    # Insert user
    cursor.execute('''
        INSERT INTO users (username, email, password, role, created_at, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (username, email, hashed_password, 'admin', datetime.now(), 1))
    print(f"Created admin user: {email}")
else:
    print(f"User already exists: {email}")

# Commit and close
conn.commit()
conn.close()

print("Authentication database initialized successfully!")