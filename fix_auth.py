#!/usr/bin/env python3
"""Fix authentication database using AuthManager"""

from auth.auth_manager import AuthManager

# Initialize auth manager
auth = AuthManager('auth.db')

# Register the admin user
try:
    success, message = auth.create_user(
        email='hdbooks15@gmail.com',
        username='hdbooks15',
        password='Hdb2016!!',
        role='admin'
    )
    if success:
        print(f"Admin user created successfully: {message}")
    else:
        print(f"User creation failed: {message}")
except Exception as e:
    print(f"Error: {e}")
    
# Verify the user can login
user = auth.authenticate('hdbooks15@gmail.com', 'Hdb2016!!')
if user:
    print(f"Login test successful for: {user['email']}")
else:
    print("Login test failed")