#!/usr/bin/env python3
"""Test Streamlit rendering of hierarchy"""

import streamlit as st
from core.extractors.excel_hierarchy_extractor import ExcelHierarchyExtractor
from utils import format_currency

st.set_page_config(page_title="Test Hierarchy View", layout="wide")
st.title("Test Hierarchy Display")

# Extract data
file_path = "data/arquivos_enviados/Análise de Resultado Financeiro 2018_2024 - Atualizada.xlsx"
extractor = ExcelHierarchyExtractor()
result = extractor.extract_from_excel(file_path)

if 2024 in result:
    year_data = result[2024]
    
    st.header("📂 Estrutura Hierárquica - 2024")
    
    # Show raw structure
    with st.expander("Debug: Raw Structure", expanded=False):
        st.json({
            'sections_count': len(year_data['sections']),
            'sections': [
                {
                    'name': s['name'],
                    'value': s['value'],
                    'subcategories_count': len(s.get('subcategories', [])),
                    'first_subcategories': [
                        {
                            'name': sc['name'],
                            'value': sc['value'],
                            'items_count': len(sc.get('items', []))
                        }
                        for sc in s.get('subcategories', [])[:3]
                    ]
                }
                for s in year_data['sections']
            ]
        })
    
    # Render hierarchy
    st.markdown("### Hierarchical View")
    
    for section in year_data['sections']:
        # Level 1: Main Section
        with st.expander(
            f"**{section['name']}** - {format_currency(section.get('value', 0))}",
            expanded=True
        ):
            # Level 2: Subcategories
            for subcat in section.get('subcategories', []):
                # Check if subcategory has items
                has_items = len(subcat.get('items', [])) > 0
                
                if has_items:
                    # Parent subcategory with children
                    st.markdown(
                        f"\n**└── {subcat['name']}** - "
                        f"{format_currency(subcat.get('value', 0))}"
                    )
                    
                    # Show item count
                    st.caption(f"   ({len(subcat['items'])} items)")
                    
                    # Level 3: Items
                    items = subcat.get('items', [])
                    for i, item in enumerate(items[:5]):  # Show first 5
                        prefix = "    └──" if i == len(items) - 1 else "    ├──"
                        st.markdown(
                            f"{prefix} {item['name']} - {format_currency(item.get('value', 0))}"
                        )
                    
                    if len(items) > 5:
                        st.caption(f"    ... and {len(items) - 5} more items")
                else:
                    # Standalone subcategory
                    st.markdown(
                        f"├── {subcat['name']} - {format_currency(subcat.get('value', 0))}"
                    )
    
    # Show calculations
    if year_data.get('calculations'):
        st.markdown("---")
        st.markdown("### 📊 Calculations")
        
        cols = st.columns(3)
        for i, (calc_name, calc_data) in enumerate(list(year_data['calculations'].items())[:6]):
            with cols[i % 3]:
                st.metric(
                    label=calc_name,
                    value=format_currency(calc_data.get('value', 0))
                )
else:
    st.error("No 2024 data found!")