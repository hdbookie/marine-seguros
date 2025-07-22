import streamlit as st
from direct_extractor import DirectDataExtractor
import pandas as pd

st.title("Test Data Extraction")

if st.button("Extract All Data"):
    extractor = DirectDataExtractor()
    
    files = [
        'Análise de Resultado Financeiro 2018_2023.xlsx',
        'Resultado Financeiro - 2024.xlsx', 
        'Resultado Financeiro - 2025.xlsx'
    ]
    
    all_data = {}
    
    for file in files:
        st.write(f"Processing: {file}")
        data = extractor.extract_from_excel(file)
        
        for year, year_data in data.items():
            all_data[year] = year_data
            revenue = year_data.get('revenue', {}).get('ANNUAL', 0)
            st.success(f"✅ {year}: R$ {revenue:,.2f}")
    
    st.write(f"**Total years found: {len(all_data)}**")
    st.write(f"Years: {sorted(all_data.keys())}")
    
    # Create a simple dataframe
    df_data = []
    for year in sorted(all_data.keys()):
        revenue = all_data[year].get('revenue', {}).get('ANNUAL', 0)
        df_data.append({
            'Year': year,
            'Revenue': revenue
        })
    
    df = pd.DataFrame(df_data)
    st.dataframe(df)
    
    # Simple line chart
    st.line_chart(df.set_index('Year'))