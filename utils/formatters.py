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


def format_time_difference(time_diff):
    """
    Format a time difference in a human-readable way in Portuguese.
    
    Args:
        time_diff: A timedelta object
        
    Returns:
        A formatted string like "há 2 dias", "há 3 horas", "há 45 minutos", or "agora mesmo"
    """
    total_seconds = int(time_diff.total_seconds())
    
    # Less than 1 minute
    if total_seconds < 60:
        return "agora mesmo"
    
    # Minutes (1-59)
    minutes = total_seconds // 60
    if minutes < 60:
        if minutes == 1:
            return "há 1 minuto"
        return f"há {minutes} minutos"
    
    # Hours (1-23)
    hours = minutes // 60
    if hours < 24:
        if hours == 1:
            return "há 1 hora"
        return f"há {hours} horas"
    
    # Days
    days = hours // 24
    if days == 1:
        return "há 1 dia"
    return f"há {days} dias"