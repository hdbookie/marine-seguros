"""
Debug script to compare hierarchy structure between different views
Helps identify categorization discrepancies
"""

import streamlit as st
import json
from core.database_manager import DatabaseManager
from core.extractors.excel_hierarchy_extractor import ExcelHierarchyExtractor

def analyze_hierarchy(data):
    """Analyze and flatten hierarchy structure"""
    analysis = {
        'sections': {},
        'all_items': [],
        'orphaned_items': [],
        'total_value': 0
    }
    
    for year, year_data in data.items():
        if not isinstance(year_data, dict) or 'sections' not in year_data:
            continue
            
        for section in year_data.get('sections', []):
            section_name = section.get('name', 'Unknown')
            
            if section_name not in analysis['sections']:
                analysis['sections'][section_name] = {
                    'subcategories': {},
                    'standalone_items': [],
                    'total': 0
                }
            
            # Process subcategories
            for subcat in section.get('subcategories', []):
                subcat_name = subcat.get('name', 'Unknown')
                subcat_value = subcat.get('value', 0)
                items = subcat.get('items', [])
                
                if subcat_name not in analysis['sections'][section_name]['subcategories']:
                    analysis['sections'][section_name]['subcategories'][subcat_name] = {
                        'value': 0,
                        'items': [],
                        'has_children': len(items) > 0
                    }
                
                analysis['sections'][section_name]['subcategories'][subcat_name]['value'] += subcat_value
                
                # Add items
                for item in items:
                    item_info = {
                        'name': item.get('name', 'Unknown'),
                        'value': item.get('value', 0),
                        'parent': subcat_name,
                        'section': section_name,
                        'year': year
                    }
                    analysis['sections'][section_name]['subcategories'][subcat_name]['items'].append(item_info)
                    analysis['all_items'].append(item_info)
                
                # If no items, this might be a standalone item miscategorized as subcategory
                if len(items) == 0:
                    analysis['sections'][section_name]['standalone_items'].append({
                        'name': subcat_name,
                        'value': subcat_value,
                        'year': year
                    })
                
                analysis['sections'][section_name]['total'] += subcat_value
            
            analysis['total_value'] += section.get('value', 0)
    
    return analysis

def compare_views():
    """Compare data between different visualization views"""
    
    st.title("🔍 Hierarchy Comparison Debug Tool")
    
    # Load data
    db = DatabaseManager()
    financial_data = db.load_shared_financial_data()
    
    if not financial_data:
        st.error("No data available. Please upload data first.")
        return
    
    # Analyze hierarchy
    analysis = analyze_hierarchy(financial_data)
    
    # Display analysis
    st.header("📊 Data Structure Analysis")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Sections", len(analysis['sections']))
    with col2:
        total_subcats = sum(len(s['subcategories']) for s in analysis['sections'].values())
        st.metric("Total Subcategories", total_subcats)
    with col3:
        st.metric("Total Items", len(analysis['all_items']))
    
    # Show potential issues
    st.header("⚠️ Potential Issues")
    
    # Find subcategories without children
    standalone_subcats = []
    for section_name, section_data in analysis['sections'].items():
        for subcat_name, subcat_data in section_data['subcategories'].items():
            if not subcat_data['has_children']:
                standalone_subcats.append({
                    'Section': section_name,
                    'Subcategory': subcat_name,
                    'Value': subcat_data['value'],
                    'Status': 'No children - might be miscategorized'
                })
    
    if standalone_subcats:
        st.warning(f"Found {len(standalone_subcats)} subcategories without children (might be items miscategorized as subcategories)")
        st.dataframe(standalone_subcats)
    
    # Detailed breakdown
    st.header("📋 Detailed Hierarchy Breakdown")
    
    for section_name, section_data in analysis['sections'].items():
        with st.expander(f"📁 {section_name} (Total: R$ {section_data['total']:,.2f})"):
            
            # Subcategories with children
            parent_subcats = {k: v for k, v in section_data['subcategories'].items() if v['has_children']}
            if parent_subcats:
                st.markdown("**Parent Subcategories (with children):**")
                for subcat_name, subcat_data in parent_subcats.items():
                    st.markdown(f"  • **{subcat_name}**: R$ {subcat_data['value']:,.2f} ({len(subcat_data['items'])} items)")
                    for item in subcat_data['items'][:5]:  # Show first 5 items
                        st.markdown(f"    - {item['name']}: R$ {item['value']:,.2f}")
                    if len(subcat_data['items']) > 5:
                        st.markdown(f"    ... and {len(subcat_data['items']) - 5} more items")
            
            # Standalone subcategories (no children)
            standalone = {k: v for k, v in section_data['subcategories'].items() if not v['has_children']}
            if standalone:
                st.markdown("**Standalone Items (no children - possibly miscategorized):**")
                for subcat_name, subcat_data in standalone.items():
                    st.markdown(f"  • {subcat_name}: R$ {subcat_data['value']:,.2f} ⚠️")
    
    # Check for specific items
    st.header("🔎 Specific Item Check")
    
    # Check for known problematic items
    problematic_items = ['Combustível', 'Alimentacao', 'Hotel', 'Estacionamento/pedagio', 'Aluguel veículo/ taxi']
    
    st.info("Checking for items that should be under 'Viagens e Deslocamentos':")
    
    for item_name in problematic_items:
        found = False
        for section_name, section_data in analysis['sections'].items():
            # Check in subcategories
            if item_name in section_data['subcategories']:
                st.warning(f"  • '{item_name}' found as SUBCATEGORY in {section_name} - Should be ITEM under Viagens e Deslocamentos")
                found = True
            # Check in items
            for subcat_name, subcat_data in section_data['subcategories'].items():
                for item in subcat_data['items']:
                    if item_name.lower() in item['name'].lower():
                        st.success(f"  • '{item_name}' correctly found as ITEM under {subcat_name} in {section_name}")
                        found = True
                        break
        
        if not found:
            st.error(f"  • '{item_name}' NOT FOUND in hierarchy")
    
    # Export for debugging
    if st.button("📥 Export Full Analysis to JSON"):
        # Convert to JSON-serializable format
        export_data = {
            'sections': analysis['sections'],
            'total_items': len(analysis['all_items']),
            'standalone_subcategories': standalone_subcats
        }
        
        with open('hierarchy_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        st.success("Analysis exported to hierarchy_analysis.json")

if __name__ == "__main__":
    # Run as standalone script
    st.set_page_config(page_title="Hierarchy Debug", layout="wide")
    compare_views()