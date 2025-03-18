from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def mul(value, arg):
    """مضاعفة القيمة بالمعامل"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """قسمة القيمة على المعامل"""
    try:
        arg = float(arg)
        if arg == 0:
            return 0
        return float(value) / arg
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    """طرح القيمة من المعامل"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def add(value, arg):
    """إضافة القيمتين"""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, arg):
    """حساب النسبة المئوية"""
    try:
        if float(arg) == 0:
            return 0
        return (float(value) / float(arg)) * 100
    except (ValueError, TypeError):
        return 0

@register.filter
def min_value(value, arg):
    """إرجاع القيمة الأصغر"""
    try:
        return min(float(value), float(arg))
    except (ValueError, TypeError):
        return value

@register.filter
def over_limit_color(value):
    """تحدد لون الشريط التقدمي حسب النسبة المئوية"""
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
