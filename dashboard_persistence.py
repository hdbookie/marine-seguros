import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import streamlit as st

class DashboardPersistence:
    """Handle persistence of dashboard data and state"""
    
    def __init__(self):
        self.storage_path = Path("data/dashboard_state")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Files for different types of data
        self.extracted_data_file = self.storage_path / "extracted_data.json"
        self.filter_state_file = self.storage_path / "filter_state.json"
        self.analysis_cache_file = self.storage_path / "analysis_cache.json"
        self.session_state_file = self.storage_path / "session_state.json"
    
    def save_extracted_data(self, data: Dict[str, Any]) -> bool:
        """Save extracted financial data"""
        try:
            # Convert data to JSON-serializable format
            serializable_data = self._make_serializable(data)
            
            with open(self.extracted_data_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'data': serializable_data,
                    'timestamp': datetime.now().isoformat(),
                    'version': '1.0'
                }, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            st.error(f"Error saving extracted data: {str(e)}")
            return False
    
    def load_extracted_data(self) -> Optional[Dict[str, Any]]:
        """Load previously saved extracted data"""
        try:
            if self.extracted_data_file.exists():
                with open(self.extracted_data_file, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                    return saved_data.get('data', {})
            return None
        except Exception as e:
            st.error(f"Error loading extracted data: {str(e)}")
            return None
    
    def save_filter_state(self, selected_years: list, selected_months: list, 
                         other_filters: Dict[str, Any]) -> bool:
        """Save current filter selections"""
        try:
            filter_data = {
                'selected_years': selected_years,
                'selected_months': selected_months,
                'other_filters': other_filters,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.filter_state_file, 'w', encoding='utf-8') as f:
                json.dump(filter_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            st.error(f"Error saving filter state: {str(e)}")
            return False
    
    def load_filter_state(self) -> Optional[Dict[str, Any]]:
        """Load previously saved filter state"""
        try:
            if self.filter_state_file.exists():
                with open(self.filter_state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            st.error(f"Error loading filter state: {str(e)}")
            return None
    
    def save_analysis_cache(self, analysis_data: Any) -> bool:
        """Save comparative analysis results"""
        try:
            serializable_data = self._make_serializable(analysis_data)
            
            with open(self.analysis_cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'analysis': serializable_data,
                    'timestamp': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            st.error(f"Error saving analysis cache: {str(e)}")
            return False
    
    def load_analysis_cache(self) -> Optional[Any]:
        """Load cached analysis results"""
        try:
            if self.analysis_cache_file.exists():
                with open(self.analysis_cache_file, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                    return saved_data.get('analysis')
            return None
        except Exception as e:
            st.error(f"Error loading analysis cache: {str(e)}")
            return None
    
    def save_session_state(self, state_dict: Dict[str, Any]) -> bool:
        """Save complete session state"""
        try:
            # Filter out non-serializable objects
            safe_state = {}
            for key, value in state_dict.items():
                if key not in ['filter_system', 'chat_assistant', 'charts', 'month_analytics']:
                    safe_state[key] = self._make_serializable(value)
            
            with open(self.session_state_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'state': safe_state,
                    'timestamp': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            st.error(f"Error saving session state: {str(e)}")
            return False
    
    def load_session_state(self) -> Optional[Dict[str, Any]]:
        """Load complete session state"""
        try:
            if self.session_state_file.exists():
                with open(self.session_state_file, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                    return saved_data.get('state', {})
            return None
        except Exception as e:
            st.error(f"Error loading session state: {str(e)}")
            return None
    
    def clear_all_data(self) -> bool:
        """Clear all persisted data"""
        try:
            for file_path in [self.extracted_data_file, self.filter_state_file, 
                            self.analysis_cache_file, self.session_state_file]:
                if file_path.exists():
                    file_path.unlink()
            return True
        except Exception as e:
            st.error(f"Error clearing persisted data: {str(e)}")
            return False
    
    def get_data_age(self) -> Dict[str, Optional[float]]:
        """Get age of persisted data in hours"""
        ages = {}
        current_time = datetime.now()
        
        for name, file_path in [
            ('extracted_data', self.extracted_data_file),
            ('filter_state', self.filter_state_file),
            ('analysis_cache', self.analysis_cache_file),
            ('session_state', self.session_state_file)
        ]:
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        timestamp = datetime.fromisoformat(data.get('timestamp', ''))
                        age_hours = (current_time - timestamp).total_seconds() / 3600
                        ages[name] = age_hours
                except:
                    ages[name] = None
            else:
                ages[name] = None
        
        return ages
    
    def _make_serializable(self, obj: Any) -> Any:
        """Convert object to JSON-serializable format"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, tuple):
            return list(obj)
        elif isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        else:
            # Convert other types to string
            return str(obj)
    
    def auto_save(self, session_state) -> None:
        """Automatically save all relevant session state data"""
        try:
            # Save extracted data if available
            if hasattr(session_state, 'extracted_data') and session_state.extracted_data:
                self.save_extracted_data(session_state.extracted_data)
            
            # Save filter state
            if hasattr(session_state, 'selected_years') and hasattr(session_state, 'selected_months'):
                other_filters = {}
                # Add any other filter states here
                self.save_filter_state(
                    session_state.selected_years,
                    session_state.selected_months,
                    other_filters
                )
            
            # Save analysis cache if available
            if hasattr(session_state, 'comparative_analysis') and session_state.comparative_analysis:
                self.save_analysis_cache(session_state.comparative_analysis)
                
        except Exception as e:
            # Don't show error to user for auto-save failures
            print(f"Auto-save error: {str(e)}")
    
    def auto_load(self, session_state) -> bool:
        """Automatically load all saved data into session state"""
        try:
            data_loaded = False
            
            # Load extracted data - check if empty or doesn't exist
            extracted_data = self.load_extracted_data()
            if extracted_data and (not hasattr(session_state, 'extracted_data') or not session_state.extracted_data):
                session_state.extracted_data = extracted_data
                data_loaded = True
            
            # Load filter state
            filter_state = self.load_filter_state()
            if filter_state:
                if not hasattr(session_state, 'selected_years') or not session_state.selected_years:
                    session_state.selected_years = filter_state.get('selected_years', [])
                if not hasattr(session_state, 'selected_months') or not session_state.selected_months:
                    session_state.selected_months = filter_state.get('selected_months', [])
                data_loaded = True
            
            # Load analysis cache
            analysis_cache = self.load_analysis_cache()
            if analysis_cache and (not hasattr(session_state, 'comparative_analysis') or not session_state.comparative_analysis):
                session_state.comparative_analysis = analysis_cache
                data_loaded = True
            
            return data_loaded
        except Exception as e:
            print(f"Auto-load error: {str(e)}")
            return False