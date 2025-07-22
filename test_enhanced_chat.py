#!/usr/bin/env python3
"""Test the enhanced AI chat assistant chart generation"""

import os
import sys
from pathlib import Path

# Add the project directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Mock Streamlit session state
class MockSessionState:
    def __init__(self):
        self.chat_history = []
        self.last_processed_message = None
        self._data = {
            'chat_history': [],
            'last_processed_message': None
        }
    
    def __contains__(self, key):
        return key in self._data
    
    def __getattr__(self, key):
        return self._data.get(key)
    
    def __setattr__(self, key, value):
        if key.startswith('_'):
            super().__setattr__(key, value)
        else:
            self._data[key] = value

# Create mock streamlit
class MockStreamlit:
    session_state = MockSessionState()

# Replace streamlit import
sys.modules['streamlit'] = MockStreamlit

from ai_chat_assistant import AIChatAssistant
import json

def test_chart_parsing():
    """Test the chart requirements parsing"""
    
    # Initialize with a dummy API key (won't actually call Gemini in test)
    assistant = AIChatAssistant("dummy_key")
    
    # Test data
    test_data = {
        '2022': {
            'revenue': {'ANNUAL': 1000000, 'JAN': 80000, 'FEV': 85000},
            'costs': {'ANNUAL': 600000, 'JAN': 50000, 'FEV': 52000},
            'fixed_costs': 100000,
            'operational_costs': 50000,
            'margins': {'ANNUAL': 25}
        },
        '2023': {
            'revenue': {'ANNUAL': 1200000, 'JAN': 95000, 'FEV': 100000},
            'costs': {'ANNUAL': 700000, 'JAN': 58000, 'FEV': 60000},
            'fixed_costs': 120000,
            'operational_costs': 60000,
            'margins': {'ANNUAL': 28}
        },
        '2024': {
            'revenue': {'ANNUAL': 1400000, 'JAN': 110000, 'FEV': 115000},
            'costs': {'ANNUAL': 800000, 'JAN': 65000, 'FEV': 68000},
            'fixed_costs': 140000,
            'operational_costs': 70000,
            'margins': {'ANNUAL': 30}
        }
    }
    
    # Test queries
    test_queries = [
        "Show me a pie chart of expenses for 2024",
        "Create a waterfall chart showing how we get from revenue to profit",
        "Plot revenue vs costs as a scatter plot",
        "Show me a heatmap of monthly revenue",
        "Compare all cost types as a stacked bar chart",
        "Show the distribution of monthly revenue as a box plot",
        "Create an area chart of revenue and costs over time",
        "Compare revenue and costs side by side for the last 3 years"
    ]
    
    print("=== Testing Chart Requirements Parsing ===\n")
    
    for query in test_queries:
        print(f"Query: {query}")
        
        # Check if needs chart
        needs_chart = assistant._check_if_needs_chart(query)
        print(f"Needs chart: {needs_chart}")
        
        if needs_chart:
            # Test auto chart type selection
            # Simulate what would happen without actual AI call
            if "pie" in query.lower():
                chart_type = "pie"
            elif "waterfall" in query.lower():
                chart_type = "waterfall"
            elif "scatter" in query.lower():
                chart_type = "scatter"
            elif "heatmap" in query.lower():
                chart_type = "heatmap"
            elif "stacked bar" in query.lower():
                chart_type = "stacked_bar"
            elif "box plot" in query.lower():
                chart_type = "box"
            elif "area" in query.lower():
                chart_type = "area"
            else:
                chart_type = "bar"
            
            print(f"Detected chart type: {chart_type}")
        
        print("-" * 50)
    
    # Test metric value extraction
    print("\n=== Testing Metric Value Extraction ===\n")
    
    year_data = test_data['2024']
    metrics = ['revenue', 'costs', 'variable_costs', 'fixed_costs', 'operational_costs']
    
    for metric in metrics:
        value = assistant._get_metric_value(year_data, metric)
        print(f"{metric}: R$ {value:,.2f}")
    
    # Test metric name translation
    print("\n=== Testing Metric Name Translation ===\n")
    
    for metric in metrics:
        translated = assistant._translate_metric_name(metric)
        print(f"{metric} -> {translated}")

def test_chart_generation():
    """Test actual chart generation (without real AI calls)"""
    
    print("\n=== Testing Chart Generation ===\n")
    
    # This would require mocking the Gemini API response
    # For now, just verify the methods exist
    
    assistant = AIChatAssistant("dummy_key")
    
    chart_methods = [
        '_create_pie_chart',
        '_create_waterfall_chart',
        '_create_heatmap',
        '_create_scatter_plot',
        '_create_stacked_bar_chart',
        '_create_box_plot',
        '_create_area_chart',
        '_create_bar_chart',
        '_create_enhanced_line_chart'
    ]
    
    for method_name in chart_methods:
        if hasattr(assistant, method_name):
            print(f"✓ {method_name} exists")
        else:
            print(f"✗ {method_name} missing")

if __name__ == "__main__":
    print("Testing Enhanced AI Chat Assistant...\n")
    
    test_chart_parsing()
    test_chart_generation()
    
    print("\n✅ Test completed!")