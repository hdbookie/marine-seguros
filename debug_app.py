import streamlit as st
import pandas as pd
from direct_extractor import DirectDataExtractor
from financial_processor import FinancialProcessor
import os

st.title("Debug Financial Data Loading")

# Check which files exist
st.header("1. File Check")
files = [
    'Análise de Resultado Financeiro 2018_2023.xlsx',
    'Resultado Financeiro - 2024.xlsx',
    'Resultado Financeiro - 2025.xlsx'
]

for file in files:
    if os.path.exists(file):
        st.success(f"✅ {file} exists")
    else:
        st.error(f"❌ {file} NOT FOUND")

# Load with financial processor
st.header("2. Financial Processor Load")
if st.button("Load with Financial Processor"):
    processor = FinancialProcessor()
    
    st.write("Loading Excel files...")
    excel_data = processor.load_excel_files(files)
    
    st.write("Excel data keys:", list(excel_data.keys()))
    
    for file, sheets in excel_data.items():
        st.write(f"\n**{file}:**")
        st.write(f"  Sheets: {list(sheets.keys()) if isinstance(sheets, dict) else 'Not a dict'}")

# Direct extraction test
st.header("3. Direct Extraction Test")
if st.button("Test Direct Extraction"):
    extractor = DirectDataExtractor()
    
    for file in files:
        st.write(f"\n**Processing {file}:**")
        if os.path.exists(file):
            data = extractor.extract_from_excel(file)
            st.write(f"Years found: {sorted(data.keys())}")
            for year, year_data in sorted(data.items()):
                revenue = year_data.get('revenue', {}).get('ANNUAL', 0)
                st.write(f"  {year}: R$ {revenue:,.2f}")
        else:
            st.error(f"File not found!")

# Load and consolidate
st.header("4. Full Pipeline Test")
if st.button("Test Full Pipeline"):
    processor = FinancialProcessor()
    
    # Load files
    st.write("Loading files...")
    excel_data = processor.load_excel_files(files)
    
    # Check what was loaded
    st.write("\nLoaded files:")
    for file in excel_data:
        st.write(f"- {file}")
    
    # Consolidate
    st.write("\nConsolidating data...")
    consolidated_df = processor.consolidate_all_years(excel_data)
    
    st.write(f"\nConsolidated DataFrame shape: {consolidated_df.shape}")
    st.write("Years in consolidated data:", sorted(consolidated_df['year'].unique()) if 'year' in consolidated_df.columns else "No year column")
    
    st.dataframe(consolidated_df)