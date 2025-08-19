#!/usr/bin/env python3
"""
Test the Excel hierarchy extraction
"""

import pandas as pd
from core.extractors.excel_hierarchy_extractor import ExcelHierarchyExtractor

# Create test data that mimics the Excel structure
test_data = {
    'Item': [
        'CUSTOS FIXOS',
        'Infraestrutura',  # This should be Level 2 parent
        'Condomínios',     # These should be Level 3 children
        'Escritório Contábil',
        'Advogados', 
        'Energia Elétrica',
        'Seguros',
        'Funcionários',    # This should be Level 2 parent
        '- Salário',       # These should be Level 3 children
        '- Salário Comercial',
        '- Premiações',
        '- Férias',
        '- Vale alimentação',
        '- FGTS',
        'Pro Labore',      # This should be Level 2 parent
        '- Salário',
        '- INSS socio',
        'CUSTOS VARIÁVEIS',
        'Simples nacional',
        'Repasse Comissão',
        '- Maria do Seguro',
        '- Willian'
    ],
    'Total': [
        1000000,  # CUSTOS FIXOS total
        53500,    # Infraestrutura = sum of next 5
        18100,    # Condomínios
        9300,     # Escritório Contábil
        11400,    # Advogados
        4300,     # Energia Elétrica
        10400,    # Seguros
        836700,   # Funcionários = sum of its children
        295800,   # Salário
        52500,    # Salário Comercial
        61700,    # Premiações
        34100,    # Férias
        112800,   # Vale alimentação
        20700,    # FGTS
        87000,    # Pro Labore
        54000,    # Salário
        8000,     # INSS socio
        200000,   # CUSTOS VARIÁVEIS
        39000,    # Simples nacional
        12000,    # Repasse Comissão
        8000,     # Maria
        4000      # Willian
    ]
}

# Create DataFrame
df = pd.DataFrame(test_data)

# Test extraction
print("Testing Excel Hierarchy Extraction")
print("=" * 50)

extractor = ExcelHierarchyExtractor()
result = extractor._extract_hierarchy(df, 2024)

print("\n" + "=" * 50)
print("EXTRACTION RESULTS:")
print("=" * 50)

if result['sections']:
    for section in result['sections']:
        print(f"\n{section['name']} (Level 1) - R$ {section['value']:,.2f}")
        for subcat in section.get('subcategories', []):
            print(f"  └── {subcat['name']} (Level 2) - R$ {subcat['value']:,.2f}")
            for item in subcat.get('items', []):
                print(f"      ├── {item['name']} (Level 3) - R$ {item['value']:,.2f}")
else:
    print("No sections extracted!")

print("\n" + "=" * 50)
print("TEST COMPLETE")