"""Security and configuration settings"""

import os
from datetime import datetime
import streamlit as st

# Security settings
REQUIRE_PASSWORD = True
MAX_FILE_SIZE_MB = 50
ALLOWED_FILE_TYPES = ['xlsx', 'xls']
SESSION_TIMEOUT_MINUTES = 30

# Data retention
AUTO_CLEAR_CACHE_HOURS = 24
LOG_USER_ACTIONS = True

# API security
HIDE_API_KEY_INPUT = False  # Set to True in production
USE_ENVIRONMENT_API_KEY = True  # Prefer .env file

# Audit logging
def log_action(action: str, details: str = ""):
    """Log user actions for security audit"""
    if LOG_USER_ACTIONS:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {action}: {details}\n"
        
        with open("audit_log.txt", "a") as f:
            f.write(log_entry)

# Session management
def check_session_timeout():
    """Check if session has timed out"""
    if 'last_activity' in st.session_state:
        last_activity = st.session_state.last_activity
        time_elapsed = (datetime.now() - last_activity).seconds / 60
        
        if time_elapsed > SESSION_TIMEOUT_MINUTES:
            st.session_state.clear()
            st.warning("Sessão expirada por inatividade. Por favor, recarregue a página.")
            st.stop()
    
    st.session_state.last_activity = datetime.now()

# Data sanitization
def sanitize_dataframe(df):
    """Remove any potentially sensitive information"""
    # Add any columns that should be hidden
    sensitive_columns = []
    
    for col in sensitive_columns:
        if col in df.columns:
            df[col] = "***"
    
    return df