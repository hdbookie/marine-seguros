#!/usr/bin/env python3
"""Debug what's being passed to the UI"""

import streamlit as st
from core.extractors.excel_hierarchy_extractor import ExcelHierarchyExtractor
from core.gerenciador_arquivos import GerenciadorArquivos
import os

st.set_page_config(page_title="Debug UI", layout="wide")
st.title("Debug Micro Analysis V2 Display")

# Initialize file manager like the app does
if 'file_manager' not in st.session_state:
    st.session_state.file_manager = GerenciadorArquivos('data/arquivos_enviados')

# Show what files are available
file_paths = st.session_state.file_manager.obter_caminhos_arquivos()
st.write("Files available:", file_paths)

if file_paths:
    # Extract using Excel hierarchy extractor
    excel_extractor = ExcelHierarchyExtractor()
    excel_hierarchy_data = {}
    
    for file_path in file_paths:
        st.write(f"Processing: {file_path}")
        extracted = excel_extractor.extract_from_excel(file_path)
        excel_hierarchy_data.update(extracted)
    
    st.write("Years extracted:", list(excel_hierarchy_data.keys()))
    
    # Check 2024 data
    if 2024 in excel_hierarchy_data:
        year_data = excel_hierarchy_data[2024]
        
        st.header("2024 Data Structure")
        st.write(f"Sections: {len(year_data.get('sections', []))}")
        
        # Show first section details
        if year_data.get('sections'):
            first_section = year_data['sections'][0]
            st.write(f"First section: {first_section['name']}")
            st.write(f"Value: {first_section['value']}")
            st.write(f"Subcategories: {len(first_section.get('subcategories', []))}")
            
            # Check CUSTOS FIXOS
            for section in year_data['sections']:
                if section['name'] == 'CUSTOS FIXOS':
                    st.header("CUSTOS FIXOS Details")
                    st.write(f"Total value: R$ {section['value']:,.2f}")
                    st.write(f"Number of subcategories: {len(section.get('subcategories', []))}")
                    
                    # Show first few subcategories
                    for i, subcat in enumerate(section['subcategories'][:5]):
                        st.write(f"{i+1}. {subcat['name']}: R$ {subcat['value']:,.2f} ({len(subcat.get('items', []))} items)")
                        if subcat.get('items'):
                            for j, item in enumerate(subcat['items'][:2]):
                                st.write(f"   - {item['name']}: R$ {item['value']:,.2f}")
        
        # Show the data that would be passed to render_native_hierarchy_tab
        st.header("Data passed to render_native_hierarchy_tab:")
        st.json({
            'years': list(excel_hierarchy_data.keys()),
            '2024_sections': len(year_data.get('sections', [])),
            '2024_calculations': len(year_data.get('calculations', {}))
        })
else:
    st.error("No files found!")