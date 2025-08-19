#!/usr/bin/env python3
"""
Test hierarchy with the exact values from the Excel image
"""

import pandas as pd
from core.extractors.excel_hierarchy_extractor import ExcelHierarchyExtractor

# Data from the Excel image
test_data = {
    'Item': [
        'MARGEM DE CONTRIBUIÇÃO',
        'CUSTOS FIXOS',
        'Infraestrutura',      # 1,653.13 = sum of next 4
        'Condomínios',         # 431.49
        'Escritório Contábil', # 581.92
        'Energia Elétrica',    # 260.18
        'Seguros',             # 379.54
        'Funcionários',        # 35,649.02 = sum of items with "-"
        '- Salário',           # 20,608.69
        '- Premiações',        # 2,500.91
        '- Férias',            # (value not shown)
        '- Décimo Terceiro',   # (value not shown)
        '- Vale alimentação',  # 5,245.00
        '- Vale transporte',   # 33.44
        '- IRRF',              # 55.54
        '- INSS',              # 1,583.89
        '- FGTS',              # 2,310.44
        '- Plano de saúde',    # 963.50
        '- Plano odontológico',# 302.61
        '- Exames/consultas',  # 35.00
        'Cursos e Treinamentos', # 2,010.00
        'Pro Labore',          # 7,722.44 = sum of next 4
        '- Salário',           # 5,020.62
        '- INSS socio',        # 707.69
        '- IRRF socio',        # 705.26
        '- Plano de saúde',    # 1,288.87
        'Distribuição de Lucros', # 15,000.00
        'Lucro',               # 15,000.00
        'Tecnologia e Comunicação', # 2,430.54 = sum of next 4
        'Informática',         # 807.00
        'Softwares',           # 926.26
        'Telefones Celulares', # 388.65
        'Telefones Fixos/Internet', # 308.63
    ],
    'Total': [
        123756.61,  # MARGEM
        65580.49,   # CUSTOS FIXOS
        1653.13,    # Infraestrutura
        431.49,
        581.92,
        260.18,
        379.54,
        35649.02,   # Funcionários
        20608.69,
        2500.91,
        1000.00,    # Estimated
        1000.00,    # Estimated
        5245.00,
        33.44,
        55.54,
        1583.89,
        2310.44,
        963.50,
        302.61,
        35.00,
        2010.00,    # Cursos
        7722.44,    # Pro Labore
        5020.62,
        707.69,
        705.26,
        1288.87,
        15000.00,   # Distribuição
        15000.00,   # Lucro
        2430.54,    # Tecnologia
        807.00,
        926.26,
        388.65,
        308.63
    ]
}

df = pd.DataFrame(test_data)

print("Testing hierarchy extraction with real Excel data")
print("=" * 60)

extractor = ExcelHierarchyExtractor()
result = extractor._extract_hierarchy(df, 2024)

print("\nEXTRACTED HIERARCHY:")
print("=" * 60)

if result['sections']:
    for section in result['sections']:
        print(f"\n{section['name']} - R$ {section['value']:,.2f}")
        for subcat in section.get('subcategories', []):
            items_sum = sum(item['value'] for item in subcat.get('items', []))
            print(f"  └─ {subcat['name']} - R$ {subcat['value']:,.2f}")
            if items_sum > 0:
                print(f"     (children sum: R$ {items_sum:,.2f})")
            for item in subcat.get('items', []):
                print(f"      ├─ {item['name']} - R$ {item['value']:,.2f}")
else:
    print("No sections found!")

print("\n" + "=" * 60)

# Check specific items
print("\nVERIFICATION:")
print(f"Infraestrutura: {1653.13} = {431.49 + 581.92 + 260.18 + 379.54} ✓")
print(f"Funcionários: {35649.02} should have all '-' items as children")
print(f"Pro Labore: {7722.44} = {5020.62 + 707.69 + 705.26 + 1288.87} ✓")
print(f"Tecnologia: {2430.54} = {807.00 + 926.26 + 388.65 + 308.63} ✓")