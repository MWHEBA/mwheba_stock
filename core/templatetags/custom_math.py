from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
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

@register.filter
def min_value(value, arg):
    """Return the minimum of the value and the argument"""
    try:
        return min(float(value), float(arg))
    except (ValueError, TypeError):
        return value

@register.filter
def over_limit_color(value):
    """Determine the progress bar color based on percentage"""
    try:
        value = float(value)
        if value >= 100:
            return 'danger'
        elif value >= 80:
            return 'warning'
        else:
            return 'success'
    except (ValueError, TypeError):
        return 'secondary'
