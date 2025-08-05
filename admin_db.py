"""Temporary admin database management - DELETE AFTER USE"""
import streamlit as st
import sqlite3
import os
from auth import AuthManager

st.set_page_config(page_title="Admin DB", page_icon="🔒")

# Security check - must have admin token in URL
if st.query_params.get('token') != os.environ.get('JWT_SECRET_KEY', '')[:8]:
    st.error("Unauthorized")
    st.stop()

st.title("🔒 Database Admin")

auth_manager = AuthManager()

# Show current users
conn = sqlite3.connect(auth_manager.db_path)
cursor = conn.cursor()

cursor.execute("SELECT email, username, email_verified FROM users")
users = cursor.fetchall()

st.write(f"Current users: {len(users)}")
for user in users:
    st.write(f"- {user[0]} ({user[1]}) - Verified: {bool(user[2])}")

if st.button("🗑️ DELETE ALL USERS", type="primary"):
    cursor.execute("DELETE FROM users")
    conn.commit()
    st.success("✅ All users deleted!")
    st.rerun()

conn.close()