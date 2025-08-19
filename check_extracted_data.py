#!/usr/bin/env python3
"""
Check what's actually in the extracted data
"""

import json
import streamlit as st

# Check session state
if 'extracted_data' in st.session_state:
    data = st.session_state.extracted_data
    
    # Look for 2024 data
    if 2024 in data:
        year_data = data[2024]
        
        if 'sections' in year_data:
            for section in year_data['sections']:
                if 'FIXOS' in section.get('name', '').upper():
                    print(f"\nFound CUSTOS FIXOS section")
                    print(f"Subcategories: {len(section.get('subcategories', []))}")
                    
                    # List all subcategory names
                    for subcat in section.get('subcategories', []):
                        name = subcat.get('name', '')
                        value = subcat.get('value', 0)
                        items = subcat.get('items', [])
                        print(f"  - {name}: R$ {value:,.2f} ({len(items)} items)")
                        
                        # Check if any travel-related
                        if 'viagens' in name.lower():
                            print(f"    ✅ FOUND VIAGENS!")
                            for item in items:
                                print(f"      • {item.get('name')}: R$ {item.get('value', 0):,.2f}")
        else:
            # Maybe it's a different structure
            print("Data structure:")
            print(json.dumps(year_data, indent=2, default=str)[:1000])
else:
    print("No extracted_data in session state")
    
# Also check the database
from core.database_manager import DatabaseManager
db = DatabaseManager()
stored_data = db.load_shared_financial_data()

if stored_data:
    print("\n\n=== DATA FROM DATABASE ===")
    # Check structure
    for year in [2024]:
        if year in stored_data:
            print(f"\nYear {year} structure:")
            year_data = stored_data[year]
            
            # Print the keys to understand structure
            if isinstance(year_data, dict):
                print(f"Keys: {list(year_data.keys())[:10]}")
                
                # Try to find CUSTOS FIXOS
                if 'CUSTOS FIXOS' in year_data:
                    cf_data = year_data['CUSTOS FIXOS']
                    print(f"CUSTOS FIXOS type: {type(cf_data)}")
                    if isinstance(cf_data, dict):
                        print(f"CUSTOS FIXOS keys: {list(cf_data.keys())[:20]}")
            else:
                print(f"Year data type: {type(year_data)}")