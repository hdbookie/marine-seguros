import pandas as pd
from typing import Dict
from .base_hierarchical_extractor import BaseHierarchicalExtractor


class CommissionExtractor(BaseHierarchicalExtractor):
    def __init__(self):
        super().__init__()
        self.patterns = ["REPASSE COMISSÃO", "REPASSE COMISSAO"]

    def extract(self, df: pd.DataFrame) -> Dict:
        # Use the base class hierarchical extraction with commission-specific patterns
        return self.extract_hierarchical_items(df, self.patterns)