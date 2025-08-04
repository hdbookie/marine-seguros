"""
Debug tool to verify if extractors are working correctly
"""

import streamlit as st
import pandas as pd
from core.unified_extractor import UnifiedFinancialExtractor
from utils import format_currency
import json
import tempfile
import os

def render_debug_extractors_tab():
    st.title("🔍 Debug Extractor Results")
    
    # File uploader
    uploaded_file = st.file_uploader("Upload Excel file to debug", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        # Process the file
        extractor = UnifiedFinancialExtractor()
        
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        try:
            # Extract data
            year_data = extractor.extract_from_excel(tmp_file_path)
        except Exception as e:
            st.error(f"Error extracting data: {str(e)}")
            year_data = None
        finally:
            # Clean up temp file
            os.unlink(tmp_file_path)
        
        if year_data and len(year_data) > 0:
            year = list(year_data.keys())[0]
            data = year_data[year]
            
            st.success(f"✅ Successfully extracted data for year {year}")
            
            # Show summary of extracted categories
            st.header("📊 Summary of Extracted Categories")
            
            categories = [
                'revenue', 'variable_costs', 'fixed_costs', 'non_operational_costs',
                'taxes', 'commissions', 'administrative_expenses', 'marketing_expenses',
                'financial_expenses', 'operational_costs', 'net_profit', 'gross_profit'
            ]
            
            summary_data = []
            for cat in categories:
                if cat in data:
                    if isinstance(data[cat], dict):
                        annual = data[cat].get('annual', 0)
                        line_items = len(data[cat].get('line_items', {}))
                        summary_data.append({
                            'Category': cat,
                            'Annual Total': format_currency(annual),
                            'Line Items': line_items,
                            'Has Monthly Data': 'monthly' in data[cat] and bool(data[cat]['monthly'])
                        })
                    else:
                        summary_data.append({
                            'Category': cat,
                            'Annual Total': format_currency(data[cat]) if data[cat] else 'N/A',
                            'Line Items': 0,
                            'Has Monthly Data': False
                        })
            
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)
            
            # Check for double counting
            st.header("🔍 Double Counting Check")
            
            # Check if sum of sub-components equals main categories
            if all(cat in data and isinstance(data[cat], dict) for cat in ['variable_costs', 'taxes', 'commissions']):
                var_costs_total = data['variable_costs'].get('annual', 0)
                taxes_total = data['taxes'].get('annual', 0)
                commissions_total = data['commissions'].get('annual', 0)
                
                st.write(f"**Variable Costs Total**: {format_currency(var_costs_total)}")
                st.write(f"**Taxes Total**: {format_currency(taxes_total)}")
                st.write(f"**Commissions Total**: {format_currency(commissions_total)}")
                st.write(f"**Sum of Components**: {format_currency(taxes_total + commissions_total)}")
                
                if abs(var_costs_total - (taxes_total + commissions_total)) > 1:
                    st.warning(f"⚠️ Variable costs ({format_currency(var_costs_total)}) doesn't match sum of components ({format_currency(taxes_total + commissions_total)})")
                else:
                    st.success("✅ Variable costs matches sum of its components")
            
            # Show detailed view of each category
            st.header("📋 Detailed Category View")
            
            selected_category = st.selectbox("Select category to inspect", categories)
            
            if selected_category in data and isinstance(data[selected_category], dict):
                cat_data = data[selected_category]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Annual Total", format_currency(cat_data.get('annual', 0)))
                with col2:
                    st.metric("Line Items", len(cat_data.get('line_items', {})))
                
                # Show line items
                if 'line_items' in cat_data and cat_data['line_items']:
                    st.subheader("Line Items")
                    
                    line_items_data = []
                    for item_key, item_data in cat_data['line_items'].items():
                        if isinstance(item_data, dict):
                            line_items_data.append({
                                'Item': item_data.get('label', item_key),
                                'Annual Value': format_currency(item_data.get('annual', 0)),
                                'Has Sub-items': 'sub_items' in item_data and bool(item_data['sub_items']),
                                'Sub-items Count': len(item_data.get('sub_items', {}))
                            })
                    
                    if line_items_data:
                        line_items_df = pd.DataFrame(line_items_data)
                        st.dataframe(line_items_df, use_container_width=True)
                        
                        # Show sub-items if any
                        items_with_subitems = [item for item in line_items_data if item['Has Sub-items']]
                        if items_with_subitems:
                            st.subheader("Sub-items Detail")
                            
                            for item in items_with_subitems:
                                with st.expander(f"{item['Item']} ({item['Sub-items Count']} sub-items)"):
                                    # Find the item in the original data
                                    for item_key, item_data in cat_data['line_items'].items():
                                        if isinstance(item_data, dict) and item_data.get('label', item_key) == item['Item']:
                                            if 'sub_items' in item_data:
                                                sub_items_data = []
                                                for sub_key, sub_data in item_data['sub_items'].items():
                                                    if isinstance(sub_data, dict):
                                                        sub_items_data.append({
                                                            'Sub-item': sub_data.get('label', sub_key),
                                                            'Value': format_currency(sub_data.get('annual', 0))
                                                        })
                                                
                                                if sub_items_data:
                                                    sub_df = pd.DataFrame(sub_items_data)
                                                    st.dataframe(sub_df, use_container_width=True)
                
                # Show monthly data
                if 'monthly' in cat_data and cat_data['monthly']:
                    st.subheader("Monthly Breakdown")
                    monthly_data = []
                    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                             'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
                    
                    for month in months:
                        if month in cat_data['monthly']:
                            monthly_data.append({
                                'Month': month,
                                'Value': format_currency(cat_data['monthly'][month])
                            })
                    
                    if monthly_data:
                        monthly_df = pd.DataFrame(monthly_data)
                        st.dataframe(monthly_df, use_container_width=True)
            
            # Show universal data if available
            if 'universal_data' in data and data['universal_data']:
                st.header("🌐 Universal Line Items Extraction")
                
                universal = data['universal_data']
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Line Items", len(universal.get('all_line_items', [])))
                with col2:
                    st.metric("Categorized Items", sum(len(items) for items in universal.get('categorized_items', {}).values()))
                with col3:
                    st.metric("Uncategorized Items", len(universal.get('uncategorized_items', {})))
                
                # Show all line items in a table
                if st.checkbox("📋 Show All Line Items"):
                    all_items = universal.get('all_line_items', [])
                    if all_items:
                        items_df = pd.DataFrame([
                            {
                                'Label': item['label'],
                                'Parent': item.get('parent', ''),
                                'Category': item.get('category', 'uncategorized'),
                                'Section': item.get('section', ''),
                                'Annual': format_currency(item['annual']),
                                'Is Sub-item': '✓' if item.get('is_sub_item') else ''
                            }
                            for item in all_items
                        ])
                        st.dataframe(items_df, use_container_width=True, height=400)
            
            # Show raw JSON for debugging
            with st.expander("🔧 View Raw JSON Data"):
                st.json(data)
        
        else:
            st.error("❌ Failed to extract data from the uploaded file")

