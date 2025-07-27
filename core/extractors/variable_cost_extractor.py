import pandas as pd
from typing import Dict, Any

def extract_variable_costs(df: pd.DataFrame, year: str) -> Dict[str, Any]:
    """
    Extracts variable costs from the given DataFrame for a specific year.
    
    Args:
        df (pd.DataFrame): The DataFrame containing financial data for a year.
        year (str): The year for which to extract data.
        
    Returns:
        Dict[str, Any]: A dictionary containing variable costs,
                        e.g., {'JAN': 1000, 'FEV': 1200, ..., 'ANNUAL': 15000}.
    """
    variable_costs_data = {}
    
    # --- Placeholder for actual extraction logic ---
    # You will need to implement the logic to identify and extract variable costs
    # from your specific Excel sheet structure (df).
    # This might involve:
    # 1. Identifying rows/columns that contain variable cost data.
    # 2. Summing up relevant figures for each month and for the annual total.
    #
    # Example (replace with your actual logic):
    # Assuming 'df' has a column 'Description' and 'Value' and 'Month'
    # For demonstration, let's just return some dummy data
    
    # Dummy data for demonstration
    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    annual_total = 0
    for month in months:
        # Replace with actual extraction from df
        # For example:
        # monthly_cost = df[df['Month'] == month]['Value'].sum()
        monthly_cost = 0 # Placeholder
        variable_costs_data[month] = monthly_cost
        annual_total += monthly_cost
        
    variable_costs_data['ANNUAL'] = annual_total
    
    # --- End of placeholder ---
    
    return variable_costs_data
