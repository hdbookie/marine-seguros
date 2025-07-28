"""Formatting utility functions"""

def format_currency(value):
    """Format a number as Brazilian currency"""
    if value is None or value == 0:
        return "R$ 0,00"
    
    # Handle negative values
    negative = value < 0
    value = abs(value)
    
    # Format with thousands separator and 2 decimal places
    if value >= 1_000_000:
        formatted = f"R$ {value/1_000_000:,.2f}M".replace(",", ".")
    elif value >= 1_000:
        formatted = f"R$ {value/1_000:,.1f}K".replace(",", ".")
    else:
        formatted = f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    return f"-{formatted}" if negative else formatted


def format_percentage(value, decimal_places=1):
    """Format a number as percentage"""
    if value is None:
        return "0%"
    return f"{value:.{decimal_places}f}%"


def format_number(value, decimal_places=0):
    """Format a number with thousand separators"""
    if value is None:
        return "0"
    return f"{value:,.{decimal_places}f}".replace(",", ".")