"""
Hierarchy Consolidator
Consolidates items that appear in different hierarchical positions across years
"""

from typing import Dict, List, Set, Tuple


class HierarchyConsolidator:
    """
    Consolidates hierarchical financial data to handle items that move between categories
    """
    
    # Define known hierarchy relationships
    HIERARCHY_MAPPINGS = {
        'Energia Elétrica': {
            'parent': 'Infraestrutura',
            'category': 'CUSTOS FIXOS'
        },
        'Condomínios': {
            'parent': 'Infraestrutura', 
            'category': 'CUSTOS FIXOS'
        },
        'Advogados': {
            'parent': 'Infraestrutura',
            'category': 'CUSTOS FIXOS'
        },
        'Escritório Contábil': {
            'parent': 'Infraestrutura',
            'category': 'CUSTOS FIXOS'
        },
        'Seguros': {
            'parent': 'Infraestrutura',
            'category': 'CUSTOS FIXOS'
        },
        'Lucro': {
            'parent': 'Distribuição de Lucros',
            'category': 'CUSTOS FIXOS'
        }
    }
    
    # Define subcategory relocations (move entire subcategories between sections)
    SUBCATEGORY_RELOCATIONS = {
        # Empty for now - we'll handle Lucro through HIERARCHY_MAPPINGS instead
    }
    
    def consolidate_year_data(self, year_data: Dict) -> Dict:
        """
        Consolidate hierarchical data for a single year
        
        Args:
            year_data: Dictionary containing year's hierarchical data
            
        Returns:
            Consolidated year data with items properly placed in hierarchy
        """
        if 'sections' not in year_data:
            return year_data
            
        consolidated = year_data.copy()
        sections = consolidated['sections']
        
        # Debug: Print all section names to see what we're working with
        print(f"DEBUG: Found {len(sections)} sections:")
        for idx, section in enumerate(sections):
            print(f"  Section {idx}: {section.get('name', 'NO NAME')} = {section.get('value', 0)}")
            # Also check subcategories
            for subcat in section.get('subcategories', []):
                print(f"    Subcategory: {subcat.get('name', 'NO NAME')} = {subcat.get('value', 0)}")
        
        # Find items that should be moved to their proper hierarchy
        items_to_move = []
        subcategories_to_relocate = []
        
        # Check each section for misplaced subcategories
        for section_idx, section in enumerate(sections):
            section_name = section.get('name', '')
            
            # Check subcategories that should be items under different parents
            for subcat_idx, subcat in enumerate(section.get('subcategories', [])):
                subcat_name = subcat.get('name', '')
                
                # First, check if this subcategory should be relocated to a different section
                for relocation_name, relocation_mapping in self.SUBCATEGORY_RELOCATIONS.items():
                    if self._normalize_name(subcat_name) == self._normalize_name(relocation_name):
                        if self._normalize_name(section_name) == self._normalize_name(relocation_mapping['from_category']):
                            print(f"DEBUG: Found subcategory to relocate: {relocation_name} from {section_name} to {relocation_mapping['to_category']}")
                            subcategories_to_relocate.append({
                                'subcat_name': relocation_name,
                                'section_idx': section_idx,
                                'subcat_idx': subcat_idx,
                                'subcat_data': subcat,
                                'from_category': relocation_mapping['from_category'],
                                'to_category': relocation_mapping['to_category']
                            })
                            break
                else:
                    # If not a relocation, check if this subcategory should actually be an item under a different parent
                    for item_name, mapping in self.HIERARCHY_MAPPINGS.items():
                        if self._normalize_name(subcat_name) == self._normalize_name(item_name):
                            print(f"DEBUG: Found misplaced subcategory to move: {item_name} (currently under {section_name})")
                            # This subcategory should be an item under a different parent
                            items_to_move.append({
                                'item_name': item_name,
                                'section_idx': section_idx,
                                'subcat_idx': subcat_idx,
                                'subcat_data': subcat,
                                'parent_name': mapping['parent'],
                                'category_name': mapping['category'],
                                'is_subcategory': True
                            })
                            break
        
        # Sort items to move by section and subcat index in reverse order
        # This ensures we delete from the end first to preserve indices
        items_to_move.sort(key=lambda x: (x['section_idx'], x.get('subcat_idx', -1)), reverse=True)
        subcategories_to_relocate.sort(key=lambda x: (x['section_idx'], x.get('subcat_idx', -1)), reverse=True)
        
        # First, move items to their proper locations
        for item_info in items_to_move:
            self._move_to_hierarchy(consolidated['sections'], item_info)
        
        # Then, relocate subcategories to different sections
        for relocation_info in subcategories_to_relocate:
            self._relocate_subcategory(consolidated['sections'], relocation_info)
        
        # Remove empty sections
        consolidated['sections'] = [
            s for s in consolidated['sections'] 
            if s.get('value', 0) > 0 or len(s.get('subcategories', [])) > 0
        ]
        
        return consolidated
    
    def _move_to_hierarchy(self, sections: List[Dict], item_info: Dict):
        """
        Move an item to its proper place in the hierarchy
        """
        parent_name = item_info['parent_name']
        category_name = item_info['category_name']
        item_name = item_info['item_name']
        
        # Get the data depending on whether it's a subcategory or section
        if item_info.get('is_subcategory'):
            item_data = item_info['subcat_data']
        else:
            item_data = item_info.get('section_data', {})
        
        # Find the target category section
        target_section = None
        for section in sections:
            if self._normalize_name(section.get('name', '')) == self._normalize_name(category_name):
                target_section = section
                break
        
        # Create category section if it doesn't exist
        if not target_section:
            target_section = {
                'name': category_name,
                'value': 0,
                'subcategories': []
            }
            sections.append(target_section)
        
        # Find or create the parent subcategory
        parent_subcat = None
        for subcat in target_section.get('subcategories', []):
            if self._normalize_name(subcat.get('name', '')) == self._normalize_name(parent_name):
                parent_subcat = subcat
                break
        
        if not parent_subcat:
            parent_subcat = {
                'name': parent_name,
                'value': 0,
                'items': []
            }
            if 'subcategories' not in target_section:
                target_section['subcategories'] = []
            target_section['subcategories'].append(parent_subcat)
        
        # Check if item already exists in the parent
        item_exists = False
        for existing_item in parent_subcat.get('items', []):
            if self._normalize_name(existing_item.get('name', '')) == self._normalize_name(item_name):
                # Update existing item value
                existing_item['value'] = existing_item.get('value', 0) + item_data.get('value', 0)
                item_exists = True
                break
        
        if not item_exists:
            # Add the item to the parent subcategory
            new_item = {
                'name': item_name,
                'value': item_data.get('value', 0)
            }
            
            # Copy monthly data if available
            if 'monthly' in item_data:
                new_item['monthly'] = item_data['monthly']
            
            if 'items' not in parent_subcat:
                parent_subcat['items'] = []
            parent_subcat['items'].append(new_item)
        
        # Update parent subcategory value
        parent_subcat['value'] = sum(
            item.get('value', 0) for item in parent_subcat.get('items', [])
        )
        
        # Update section value
        target_section['value'] = sum(
            subcat.get('value', 0) for subcat in target_section.get('subcategories', [])
        )
        
        # Remove the original item from its incorrect location
        if item_info.get('is_subcategory'):
            # Remove from subcategories list
            section_idx = item_info['section_idx']
            subcat_idx = item_info['subcat_idx']
            if section_idx < len(sections):
                section = sections[section_idx]
                if 'subcategories' in section and subcat_idx < len(section['subcategories']):
                    # Remove the subcategory
                    del section['subcategories'][subcat_idx]
                    # Update section value
                    section['value'] = sum(
                        sc.get('value', 0) for sc in section.get('subcategories', [])
                    )
        else:
            # Remove standalone section
            section_idx = item_info['section_idx']
            if section_idx < len(sections):
                # Mark for removal by setting value to 0 and clearing subcategories
                sections[section_idx]['value'] = 0
                sections[section_idx]['subcategories'] = []
    
    def _relocate_subcategory(self, sections: List[Dict], relocation_info: Dict):
        """
        Relocate a subcategory from one section to another
        """
        subcat_name = relocation_info['subcat_name']
        to_category = relocation_info['to_category']
        subcat_data = relocation_info['subcat_data']
        
        # Find or create the target section
        target_section = None
        for section in sections:
            if self._normalize_name(section.get('name', '')) == self._normalize_name(to_category):
                target_section = section
                break
        
        if not target_section:
            # Create target section if it doesn't exist
            target_section = {
                'name': to_category,
                'value': 0,
                'subcategories': []
            }
            sections.append(target_section)
        
        # Add the subcategory to the target section
        if 'subcategories' not in target_section:
            target_section['subcategories'] = []
        
        # Check if subcategory already exists in target
        existing_subcat = None
        for existing in target_section['subcategories']:
            if self._normalize_name(existing.get('name', '')) == self._normalize_name(subcat_name):
                existing_subcat = existing
                break
        
        if existing_subcat:
            # Merge with existing subcategory
            existing_subcat['value'] = existing_subcat.get('value', 0) + subcat_data.get('value', 0)
            # Merge monthly data if available
            if 'monthly' in subcat_data and 'monthly' in existing_subcat:
                for month, value in subcat_data['monthly'].items():
                    existing_subcat['monthly'][month] = existing_subcat['monthly'].get(month, 0) + value
            elif 'monthly' in subcat_data:
                existing_subcat['monthly'] = subcat_data['monthly'].copy()
        else:
            # Add new subcategory
            new_subcat = subcat_data.copy()
            new_subcat['name'] = subcat_name  # Ensure consistent naming
            target_section['subcategories'].append(new_subcat)
        
        # Update target section value
        target_section['value'] = sum(
            subcat.get('value', 0) for subcat in target_section.get('subcategories', [])
        )
        
        # Remove the subcategory from original location
        section_idx = relocation_info['section_idx']
        subcat_idx = relocation_info['subcat_idx']
        if section_idx < len(sections):
            original_section = sections[section_idx]
            if 'subcategories' in original_section and subcat_idx < len(original_section['subcategories']):
                # Remove the subcategory
                del original_section['subcategories'][subcat_idx]
                # Update original section value
                original_section['value'] = sum(
                    sc.get('value', 0) for sc in original_section.get('subcategories', [])
                )
    
    def _normalize_name(self, name: str) -> str:
        """
        Normalize a name for comparison
        """
        return name.strip().upper().replace('_', ' ')
    
    def consolidate_multiple_years(self, financial_data: Dict) -> Dict:
        """
        Consolidate hierarchical data across multiple years
        
        Args:
            financial_data: Dictionary with years as keys
            
        Returns:
            Consolidated financial data
        """
        consolidated_data = {}
        
        for year, year_data in financial_data.items():
            if isinstance(year_data, dict):
                consolidated_data[year] = self.consolidate_year_data(year_data)
            else:
                consolidated_data[year] = year_data
        
        return consolidated_data