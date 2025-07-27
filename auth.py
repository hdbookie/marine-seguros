"""
Simple authentication module for Marine Seguros
"""

import streamlit as st
import hashlib
import json
import os
from datetime import datetime


def init_auth():
    """Initialize authentication state"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'users' not in st.session_state:
        st.session_state.users = load_users()


def load_users():
    """Load users from file or create default"""
    users_file = "data/users.json"
    
    # Default users
    default_users = {
        "admin": {
            "password": hash_password("admin123"),
            "role": "admin",
            "name": "Administrator"
        },
        "user": {
            "password": hash_password("user123"),
            "role": "user",
            "name": "User"
        }
    }
    
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r') as f:
                return json.load(f)
        except:
            return default_users
    
    return default_users


def save_users(users):
    """Save users to file"""
    users_file = "data/users.json"
    os.makedirs("data", exist_ok=True)
    
    with open(users_file, 'w') as f:
        json.dump(users, f, indent=2)


def hash_password(password):
    """Hash a password"""
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate(username, password):
    """Authenticate a user"""
    users = st.session_state.users
    
    if username in users:
        if users[username]["password"] == hash_password(password):
            return {
                "username": username,
                "role": users[username]["role"],
                "name": users[username]["name"]
            }
    
    return None


def require_auth():
    """Check if user is authenticated"""
    return st.session_state.user is not None


def show_login_page():
    """Show login page"""
    st.title("🔐 Marine Seguros - Login")
    
    with st.container():
        st.markdown("### Please login to continue")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", type="primary")
            
            if submitted:
                user = authenticate(username, password)
                if user:
                    st.session_state.user = user
                    st.success(f"Welcome, {user['name']}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        # Show default credentials hint
        with st.expander("ℹ️ Demo Credentials"):
            st.info("""
            **Admin Access:**
            - Username: admin
            - Password: admin123
            
            **User Access:**
            - Username: user
            - Password: user123
            """)


def show_user_menu():
    """Show user menu in sidebar"""
    if st.session_state.user:
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**👤 {st.session_state.user['name']}**")
        st.sidebar.caption(f"Role: {st.session_state.user['role'].title()}")
        
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()


def show_admin_panel():
    """Show admin panel in sidebar"""
    if st.session_state.user and st.session_state.user['role'] == 'admin':
        with st.sidebar.expander("👨‍💼 Admin Panel"):
            st.markdown("### User Management")
            
            # Add new user
            st.markdown("**Add New User**")
            new_username = st.text_input("Username", key="new_username")
            new_password = st.text_input("Password", key="new_password", type="password")
            new_name = st.text_input("Full Name", key="new_name")
            new_role = st.selectbox("Role", ["user", "admin"], key="new_role")
            
            if st.button("➕ Add User"):
                if new_username and new_password and new_name:
                    users = st.session_state.users
                    if new_username not in users:
                        users[new_username] = {
                            "password": hash_password(new_password),
                            "role": new_role,
                            "name": new_name
                        }
                        save_users(users)
                        st.session_state.users = users
                        st.success(f"User '{new_username}' added successfully!")
                    else:
                        st.error("Username already exists")
                else:
                    st.error("Please fill all fields")
            
            # List users
            st.markdown("**Current Users**")
            users = st.session_state.users
            for username, user_data in users.items():
                st.text(f"• {username} ({user_data['role']})")