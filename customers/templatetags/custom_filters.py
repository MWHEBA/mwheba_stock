from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter
def currency(value, symbol='ج.م'):
    """
    Format a number as currency with Egyptian Pound symbol.
    Example: {{ value|currency }}
    """
    try:
        value = float(value)
        formatted = floatformat(value, 2)
        return f"{formatted} {symbol}"
    except (ValueError, TypeError):
        return f"0.00 {symbol}"

@register.filter
def status_badge(status):
    """
    Return appropriate Bootstrap badge class for customer status.
    Example: {{ customer.status|status_badge }}
    """
    status_classes = {
        'active': 'success',
        'inactive': 'warning',
        'blocked': 'danger',
        'pending': 'info',
    }
    return status_classes.get(status, 'secondary')

@register.filter
def yes_no(value):
    """
    Convert boolean to Yes/No in Arabic.
    Example: {{ value|yes_no }}
    """
    if value:
        return 'نعم'
    return 'لا'

@register.filter
def initials(name):
    """
    Get the first letter of a name for avatars.
    Example: {{ customer.name|initials }}
    """
    if not name:
        return 'N/A'
    return name[0].upper()

@register.filter
def credit_status_color(customer):
    """
    Return appropriate color class based on customer credit status.
    Example: {{ customer|credit_status_color }}
    """
    if customer.credit_limit == 0:
        return 'secondary'
    
    if customer.debt > customer.credit_limit:
        return 'danger'
        
    percentage = (customer.debt / customer.credit_limit) * 100
    
    if percentage >= 80:
        return 'warning'
    elif percentage >= 50:
        return 'info'
        
    return 'success'

# Add math operations
@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divide the value by the argument"""
    try:
        arg = float(arg)
        if arg == 0:
            return 0
        return float(value) / arg
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    """Subtract the argument from the value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def add(value, arg):
    """Add the argument to the value"""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, arg):
    """Calculate the percentage"""
    try:
        if float(arg) == 0:
            return 0
        return (float(value) / float(arg)) * 100
    except (ValueError, TypeError):
        return 0
