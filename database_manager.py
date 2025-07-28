import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import streamlit as st
from pathlib import Path
import pandas as pd

class DatabaseManager:
    """SQLite-based persistence for dashboard data"""
    
    def __init__(self, db_path: str = "data/dashboard.db"):
        self.db_path = db_path
        Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Table for shared financial data (all users access this)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shared_financial_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    year TEXT NOT NULL UNIQUE,
                    data TEXT NOT NULL,
                    uploaded_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table for upload history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS upload_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    email TEXT,
                    files TEXT NOT NULL,
                    upload_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table for file storage (for production persistence)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS uploaded_files (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_data BLOB NOT NULL,
                    file_size INTEGER,
                    uploaded_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Legacy table for backward compatibility
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS financial_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    year TEXT NOT NULL UNIQUE,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table for filter states
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS filter_state (
                    id INTEGER PRIMARY KEY,
                    selected_years TEXT,
                    selected_months TEXT,
                    other_filters TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table for analysis cache
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_cache (
                    id INTEGER PRIMARY KEY,
                    analysis_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table for user preferences
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def save_shared_financial_data(self, year: str, data: Dict[str, Any], username: str = None) -> bool:
        """Save financial data to shared storage accessible by all users"""
        try:
            # Convert numpy types to Python native types
            clean_data = self._serialize_for_json(data)
            data_json = json.dumps(clean_data, ensure_ascii=False)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO shared_financial_data 
                    (year, data, uploaded_by, updated_at) 
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (str(year), data_json, username))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving shared financial data for year {year}: {e}")
            return False
    
    def save_financial_data(self, year: str, data: Dict[str, Any]) -> bool:
        """Save financial data for a specific year"""
        try:
            # Validate data before saving
            if not self._validate_financial_data(data):
                st.warning(f"⚠️ Dados inválidos para o ano {year}, pulando...")
                return False
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Serialize the data with proper handling
                serialized_data = self._serialize_for_json(data)
                json_data = json.dumps(serialized_data, ensure_ascii=False)
                
                cursor.execute("""
                    INSERT OR REPLACE INTO financial_data (year, data, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (year, json_data))
                
                conn.commit()
                pass  # Saved financial data
                return True
        except Exception as e:
            st.error(f"Error saving financial data for {year}: {str(e)}")
            return False
    
    def _serialize_for_json(self, obj):
        """Recursively serialize an object for JSON storage"""
        import datetime
        import pandas as pd
        import numpy as np
        
        try:
            # Handle None first
            if obj is None:
                return None
            
            # Check for pandas NA values
            if pd.isna(obj):
                return None
            
            # Handle numpy arrays BEFORE checking for other types
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            
            # Handle numpy scalar types
            if isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            
            # Handle DataFrame
            if hasattr(obj, 'to_dict') and hasattr(obj, 'columns'):  # DataFrame
                # Convert DataFrame to a serializable format
                try:
                    df_dict = obj.to_dict('records')
                    serialized_records = [self._serialize_for_json(record) for record in df_dict]
                    return {
                        '__dataframe__': True,
                        'data': serialized_records,
                        'columns': list(obj.columns),
                        'dtypes': {col: str(dtype) for col, dtype in obj.dtypes.items()}
                    }
                except:
                    # If DataFrame serialization fails, convert to dict
                    return self._serialize_for_json(obj.to_dict())
            
            # Handle datetime objects (including Timestamp)
            elif isinstance(obj, (datetime.datetime, datetime.date, pd.Timestamp)):
                return obj.isoformat()
            elif hasattr(obj, 'isoformat'):
                return obj.isoformat()
            
            # Handle collections
            elif isinstance(obj, dict):
                result = {}
                for k, v in obj.items():
                    # Ensure keys are strings
                    key_str = str(k) if not isinstance(k, str) else k
                    result[key_str] = self._serialize_for_json(v)
                return result
            elif isinstance(obj, (list, tuple)):
                return [self._serialize_for_json(item) for item in obj]
            elif isinstance(obj, (set, frozenset)):
                return [self._serialize_for_json(item) for item in obj]
            
            # Handle basic types
            elif isinstance(obj, (str, int, float, bool)):
                return obj
            
            # Fallback - convert to string
            else:
                return str(obj)
                
        except Exception as e:
            # Don't print in production - just handle silently
            # Return a safe fallback value
            try:
                return str(obj)
            except:
                return None
    
    def _validate_financial_data(self, data: Dict[str, Any]) -> bool:
        """Validate financial data structure and content"""
        if not isinstance(data, dict):
            return False
            return False
        
        # Check data structure
        
        # Check if it's flexible extractor data (has line_items)
        if 'line_items' in data:
            print(f"Detected flexible extractor data format")
            # Validate flexible extractor format
            if not isinstance(data['line_items'], dict):
                return False
                return False
            if len(data['line_items']) == 0:
                return False
                return False
            # Flexible data validation passed
            return True
        
        # Check for standard extractor required fields
        required_fields = ['revenue', 'costs']
        for field in required_fields:
            if field not in data:
                pass
                return False
            
            # Check if field has data
            if not isinstance(data[field], dict) or len(data[field]) == 0:
                pass
                return False
        
        # Validate revenue data
        revenue_data = data.get('revenue', {})
        if not revenue_data:
            pass
            return False
        
        # Check if we have at least some data (either monthly or annual)
        monthly_data_count = sum(1 for k in revenue_data.keys() 
                                if k in ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                                         'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ'])
        
        has_annual = 'ANNUAL' in revenue_data
        
        # Accept data if it has either monthly data OR annual totals
        if monthly_data_count < 3 and not has_annual:
            pass
            return False
        
        # Validate numeric values
        for key, value in revenue_data.items():
            if value is not None and not isinstance(value, (int, float)):
                pass
                return False
        
        # Check for zero revenue - don't save years with no activity
        annual_revenue = revenue_data.get('ANNUAL', 0) if has_annual else 0
        monthly_revenue_sum = sum(revenue_data.get(month, 0) for month in ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ'] if isinstance(revenue_data.get(month, 0), (int, float)))
        
        # Skip years with zero revenue
        if annual_revenue == 0 and monthly_revenue_sum == 0:
            year = data.get('year', 'Unknown')
            pass
            return False
        
        return True
    
    def load_shared_financial_data(self) -> Dict[str, Any]:
        """Load all shared financial data accessible by all users"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT year, data FROM shared_financial_data 
                    ORDER BY year
                """)
                
                financial_data = {}
                for row in cursor.fetchall():
                    year = row[0]
                    data = json.loads(row[1])
                    
                    # Ensure year is an integer if it's a valid year
                    try:
                        year_int = int(year)
                        if 2000 <= year_int <= 2100:
                            financial_data[year_int] = data
                        else:
                            financial_data[year] = data
                    except ValueError:
                        financial_data[year] = data
                
                return financial_data
        except Exception as e:
            print(f"Error loading shared financial data: {e}")
            return {}
    
    def save_upload_history(self, username: str, email: str, files: List[str], upload_type: str = "financial_data") -> bool:
        """Save upload history for tracking who uploaded what"""
        try:
            files_json = json.dumps(files, ensure_ascii=False)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO upload_history 
                    (username, email, files, upload_type) 
                    VALUES (?, ?, ?, ?)
                """, (username, email, files_json, upload_type))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving upload history: {e}")
            return False
    
    def get_upload_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent upload history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT username, email, files, upload_type, created_at 
                    FROM upload_history 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
                
                history = []
                for row in cursor.fetchall():
                    history.append({
                        'username': row[0],
                        'email': row[1],
                        'files': json.loads(row[2]),
                        'upload_type': row[3],
                        'created_at': row[4]
                    })
                
                return history
        except Exception as e:
            print(f"Error loading upload history: {e}")
            return []
    
    def get_last_upload_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the last upload"""
        history = self.get_upload_history(limit=1)
        return history[0] if history else None
    
    def load_all_financial_data(self) -> Dict[str, Any]:
        """Load all financial data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT year, data FROM financial_data
                    ORDER BY year
                """)
                
                result = {}
                for row in cursor.fetchall():
                    year, json_data = row
                    result[year] = json.loads(json_data)
                
                return result
        except Exception as e:
            st.error(f"Error loading financial data: {str(e)}")
            return {}
    
    def save_filter_state(self, selected_years: List[str], selected_months: List[str], 
                         other_filters: Dict[str, Any] = None) -> bool:
        """Save current filter state"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Convert numpy types to Python native types for JSON serialization
                years_list = [int(year) if hasattr(year, 'item') else year for year in selected_years]
                months_list = [str(month) for month in selected_months]
                
                cursor.execute("""
                    INSERT OR REPLACE INTO filter_state 
                    (id, selected_years, selected_months, other_filters, updated_at)
                    VALUES (1, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    json.dumps(years_list),
                    json.dumps(months_list),
                    json.dumps(other_filters or {})
                ))
                
                conn.commit()
                return True
        except Exception as e:
            st.error(f"Error saving filter state: {str(e)}")
            return False
    
    def load_filter_state(self) -> Optional[Dict[str, Any]]:
        """Load saved filter state"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT selected_years, selected_months, other_filters
                    FROM filter_state WHERE id = 1
                """)
                
                row = cursor.fetchone()
                if row:
                    return {
                        'selected_years': json.loads(row[0]),
                        'selected_months': json.loads(row[1]),
                        'other_filters': json.loads(row[2])
                    }
                return None
        except Exception as e:
            st.error(f"Error loading filter state: {str(e)}")
            return None
    
    def save_analysis_cache(self, analysis_data: Any) -> bool:
        """Save analysis results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Use the same serialization method as save_financial_data
                try:
                    serialized_data = self._serialize_for_json(analysis_data)
                    json_data = json.dumps(serialized_data, ensure_ascii=False)
                except Exception as serialize_error:
                    print(f"Serialization error details: {str(serialize_error)}")
                    print(f"Data structure causing error: {type(analysis_data)}")
                    if hasattr(analysis_data, 'keys'):
                        print(f"Data keys: {list(analysis_data.keys())}")
                    
                    # Try a more aggressive approach
                    def force_serialize(obj):
                        import datetime
                        import pandas as pd
                        import numpy as np
                        
                        if isinstance(obj, pd.DataFrame):
                            # Properly serialize DataFrame
                            return {
                                '__dataframe__': True,
                                'data': obj.to_dict('records'),
                                'columns': list(obj.columns),
                                'dtypes': {col: str(dtype) for col, dtype in obj.dtypes.items()}
                            }
                        elif isinstance(obj, (datetime.datetime, datetime.date, pd.Timestamp)):
                            return obj.isoformat()
                        elif hasattr(obj, 'isoformat'):
                            return obj.isoformat()
                        elif isinstance(obj, (np.integer, np.int64)):
                            return int(obj)
                        elif isinstance(obj, (np.floating, np.float64)):
                            return float(obj)
                        elif pd.isna(obj):
                            return None
                        elif isinstance(obj, (set, frozenset)):
                            return list(obj)
                        elif isinstance(obj, list):
                            # Properly serialize lists
                            return [force_serialize(item) for item in obj]
                        elif isinstance(obj, dict):
                            # Properly serialize dicts
                            return {k: force_serialize(v) for k, v in obj.items()}
                        else:
                            return str(obj)
                    
                    json_data = json.dumps(analysis_data, ensure_ascii=False, default=force_serialize)
                
                cursor.execute("""
                    INSERT OR REPLACE INTO analysis_cache 
                    (id, analysis_data, updated_at)
                    VALUES (1, ?, CURRENT_TIMESTAMP)
                """, (json_data,))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving analysis cache: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    
    def load_analysis_cache(self) -> Optional[Any]:
        """Load cached analysis results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT analysis_data FROM analysis_cache WHERE id = 1
                """)
                
                row = cursor.fetchone()
                if row:
                    data = json.loads(row[0])
                    
                    # Reconstruct DataFrames from JSON data
                    def deserialize_value(value):
                        if isinstance(value, dict):
                            if value.get('__dataframe__') == True:
                                # This was a DataFrame, reconstruct it
                                try:
                                    df = pd.DataFrame(value['data'], columns=value['columns'])
                                    return df
                                except Exception as e:
                                    pass  # Error reconstructing DataFrame
                                    # Return None or empty DataFrame instead of corrupted data
                                    return pd.DataFrame()
                            else:
                                # Recursively handle nested dictionaries
                                return {k: deserialize_value(v) for k, v in value.items()}
                        elif isinstance(value, list):
                            # Handle lists
                            return [deserialize_value(item) for item in value]
                        else:
                            # If value is a string that looks like it was a DataFrame converted to string
                            if isinstance(value, str) and value.startswith('<') and 'DataFrame' in value:
                                pass  # Found DataFrame converted to string
                                # Return empty DataFrame instead of the string
                                return pd.DataFrame()
                            # If value is a string that looks like it was a list converted to string
                            elif isinstance(value, str) and value.startswith('[{') and value.endswith('}]'):
                                pass  # Found list that was converted to string
                                try:
                                    # Try to parse it back to a list
                                    import ast
                                    return ast.literal_eval(value)
                                except:
                                    # If parsing fails, return empty list
                                    return []
                            return value
                    
                    reconstructed_data = deserialize_value(data)
                    return reconstructed_data
                return None
        except Exception as e:
            st.error(f"Error loading analysis cache: {str(e)}")
            return None
    
    def save_preference(self, key: str, value: Any) -> bool:
        """Save a user preference"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                json_value = json.dumps(value, ensure_ascii=False)
                
                cursor.execute("""
                    INSERT OR REPLACE INTO user_preferences 
                    (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (key, json_value))
                
                conn.commit()
                return True
        except Exception as e:
            st.error(f"Error saving preference: {str(e)}")
            return False
    
    def load_preference(self, key: str, default=None) -> Any:
        """Load a user preference"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT value FROM user_preferences WHERE key = ?
                """, (key,))
                
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
                return default
        except Exception as e:
            st.error(f"Error loading preference: {str(e)}")
            return default
    
    def clear_all_data(self) -> bool:
        """Clear all data from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM financial_data")
                cursor.execute("DELETE FROM filter_state")
                cursor.execute("DELETE FROM analysis_cache")
                cursor.execute("DELETE FROM user_preferences")
                cursor.execute("DELETE FROM shared_financial_data")
                cursor.execute("DELETE FROM upload_history")
                
                conn.commit()
                return True
        except Exception as e:
            st.error(f"Error clearing data: {str(e)}")
            return False
    
    def get_data_stats(self) -> Dict[str, Any]:
        """Get statistics about stored data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Financial data stats
                cursor.execute("SELECT COUNT(*), MAX(updated_at) FROM financial_data")
                count, last_update = cursor.fetchone()
                stats['financial_data'] = {
                    'count': count,
                    'last_update': last_update
                }
                
                # Filter state stats
                cursor.execute("SELECT updated_at FROM filter_state WHERE id = 1")
                row = cursor.fetchone()
                stats['filter_state'] = {
                    'last_update': row[0] if row else None
                }
                
                # Analysis cache stats
                cursor.execute("SELECT updated_at FROM analysis_cache WHERE id = 1")
                row = cursor.fetchone()
                stats['analysis_cache'] = {
                    'last_update': row[0] if row else None
                }
                
                return stats
        except Exception as e:
            st.error(f"Error getting data stats: {str(e)}")
            return {}
    
    def auto_save_state(self, session_state) -> None:
        """Automatically save all relevant session state data to shared storage"""
        try:
            saved_count = 0
            username = session_state.user.get('username', 'Unknown') if hasattr(session_state, 'user') and session_state.user else 'System'
            
            # Save financial data to shared storage
            if hasattr(session_state, 'extracted_data') and session_state.extracted_data:
                print(f"Attempting to save {len(session_state.extracted_data)} years of data to shared storage...")
                
                # Track uploaded files for history
                uploaded_files = []
                if hasattr(session_state, 'uploaded_files'):
                    # Handle both list of strings and list of file objects
                    if isinstance(session_state.uploaded_files, list):
                        for f in session_state.uploaded_files:
                            if isinstance(f, str):
                                uploaded_files.append(f)
                            elif hasattr(f, 'name'):
                                uploaded_files.append(f.name)
                            elif isinstance(f, dict) and 'nome' in f:
                                uploaded_files.append(f['nome'])
                
                for year, data in session_state.extracted_data.items():
                    # Ensure year is string for consistency
                    year_str = str(year)
                    # Clean the data before saving
                    clean_data = self._serialize_for_json(data)
                    if self.save_shared_financial_data(year_str, clean_data, username):
                        saved_count += 1
                    else:
                        pass  # Failed to save data
                
                # Save upload history if we have uploaded files
                if uploaded_files and saved_count > 0:
                    user_email = session_state.user.get('email', '') if hasattr(session_state, 'user') and session_state.user else ''
                    self.save_upload_history(username, user_email, uploaded_files)
                
                pass  # Saved data to shared storage
            else:
                pass  # No extracted_data found
            
            # Save filter state
            if hasattr(session_state, 'selected_years') and hasattr(session_state, 'selected_months'):
                if self.save_filter_state(
                    session_state.selected_years,
                    session_state.selected_months
                ):
                    pass  # Saved filter state
            
            # Save complete analyzed data cache
            cache_data = {}
            
            # Save processed_data if available
            if hasattr(session_state, 'processed_data') and session_state.processed_data:
                cache_data['processed_data'] = session_state.processed_data
                
            # Save monthly_data if available
            if hasattr(session_state, 'monthly_data') and session_state.monthly_data is not None:
                cache_data['monthly_data'] = session_state.monthly_data
                
            # Save flexible_data if available
            if hasattr(session_state, 'flexible_data') and session_state.flexible_data:
                cache_data['flexible_data'] = session_state.flexible_data
                
            # Save comparative analysis if available
            if hasattr(session_state, 'comparative_analysis') and session_state.comparative_analysis:
                cache_data['comparative_analysis'] = session_state.comparative_analysis
                
            # Save gemini insights if available
            if hasattr(session_state, 'gemini_insights') and session_state.gemini_insights:
                cache_data['gemini_insights'] = session_state.gemini_insights
            
            if cache_data:
                if self.save_analysis_cache(cache_data):
                    pass  # Saved analysis cache
                    
        except Exception as e:
            # Don't show error to user for auto-save failures
            pass  # Auto-save error
            import traceback
            traceback.print_exc()
    
    def auto_load_state(self, session_state) -> bool:
        """Automatically load all saved data into session state"""
        try:
            data_loaded = False
            
            # Load shared financial data - ALWAYS overwrite if data exists in DB
            financial_data = self.load_shared_financial_data()
            if financial_data:
                # Force overwrite even if session_state has empty dict
                session_state.extracted_data = financial_data
                data_loaded = True
                pass  # Loaded shared financial data
            
            # Load filter state
            filter_state = self.load_filter_state()
            if filter_state:
                # Force overwrite
                session_state.selected_years = filter_state.get('selected_years', [])
                session_state.selected_months = filter_state.get('selected_months', [])
                data_loaded = True
                pass  # Loaded filter state
            
            # Load complete analysis cache
            analysis_cache = self.load_analysis_cache()
            if analysis_cache:
                # Load all cached data types
                if 'processed_data' in analysis_cache:
                    session_state.processed_data = analysis_cache['processed_data']
                    pass  # Loaded processed_data
                    
                if 'monthly_data' in analysis_cache:
                    session_state.monthly_data = analysis_cache['monthly_data']
                    pass  # Loaded monthly_data
                    
                if 'flexible_data' in analysis_cache:
                    session_state.flexible_data = analysis_cache['flexible_data']
                    pass  # Loaded flexible_data
                    
                if 'comparative_analysis' in analysis_cache:
                    session_state.comparative_analysis = analysis_cache['comparative_analysis']
                    pass  # Loaded comparative_analysis
                    
                if 'gemini_insights' in analysis_cache:
                    session_state.gemini_insights = analysis_cache['gemini_insights']
                    pass  # Loaded gemini_insights
                    
                data_loaded = True
                pass  # Loaded analysis cache
            
            # If we have financial data but no filters selected, select all by default
            if financial_data and not hasattr(session_state, 'selected_years'):
                session_state.selected_years = list(financial_data.keys())
                session_state.selected_months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                                               'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
            elif financial_data and hasattr(session_state, 'selected_years') and not session_state.selected_years:
                session_state.selected_years = list(financial_data.keys())
                session_state.selected_months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                                               'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
            
            return data_loaded
        except Exception as e:
            print(f"Auto-load error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def clear_session_data(self):
        """Clear all cached data from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Clear analysis cache
                cursor.execute("DELETE FROM analysis_cache")
                
                # Clear filter state
                cursor.execute("DELETE FROM filter_state")
                
                # Optionally clear financial data (uncomment if needed)
                # cursor.execute("DELETE FROM financial_data")
                
                conn.commit()
                print("Session data cleared from database")
                return True
        except Exception as e:
            print(f"Error clearing session data: {str(e)}")
            return False
    
    def save_file_to_db(self, file_id: str, filename: str, file_data: bytes, username: str = None) -> bool:
        """Save uploaded file to database for persistence"""
        try:
            file_size = len(file_data)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO uploaded_files 
                    (id, filename, file_data, file_size, uploaded_by) 
                    VALUES (?, ?, ?, ?, ?)
                """, (file_id, filename, file_data, file_size, username))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving file {filename} to database: {e}")
            return False
    
    def get_file_from_db(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve uploaded file from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT filename, file_data, file_size, uploaded_by, created_at 
                    FROM uploaded_files 
                    WHERE id = ?
                """, (file_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'filename': row[0],
                        'file_data': row[1],
                        'file_size': row[2],
                        'uploaded_by': row[3],
                        'created_at': row[4]
                    }
                return None
        except Exception as e:
            print(f"Error retrieving file {file_id} from database: {e}")
            return None
    
    def list_files_in_db(self) -> List[Dict[str, Any]]:
        """List all files stored in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, filename, file_size, uploaded_by, created_at 
                    FROM uploaded_files 
                    ORDER BY created_at DESC
                """)
                
                files = []
                for row in cursor.fetchall():
                    files.append({
                        'id': row[0],
                        'filename': row[1],
                        'file_size': row[2],
                        'uploaded_by': row[3],
                        'created_at': row[4]
                    })
                
                return files
        except Exception as e:
            print(f"Error listing files from database: {e}")
            return []
    
    def delete_file_from_db(self, file_id: str) -> bool:
        """Delete a file from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM uploaded_files WHERE id = ?", (file_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting file {file_id} from database: {e}")
            return False