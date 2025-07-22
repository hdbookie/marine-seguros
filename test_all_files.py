from direct_extractor import DirectDataExtractor

# Test all three files
extractor = DirectDataExtractor()

files = [
    'Análise de Resultado Financeiro 2018_2023.xlsx',
    'Resultado Financeiro - 2024.xlsx',
    'Resultado Financeiro - 2025.xlsx'
]

all_data = {}

for file in files:
    print(f"\n{'='*50}")
    print(f"Processing: {file}")
    print('='*50)
    
    data = extractor.extract_from_excel(file)
    print(f"Years found: {sorted(data.keys())}")
    
    for year, year_data in sorted(data.items()):
        all_data[year] = year_data
        revenue = year_data.get('revenue', {}).get('ANNUAL', 0)
        print(f"  {year}: Revenue = R$ {revenue:,.2f}")

print(f"\n{'='*50}")
print(f"TOTAL YEARS EXTRACTED: {sorted(all_data.keys())}")
print(f"Total count: {len(all_data)} years")
print('='*50)