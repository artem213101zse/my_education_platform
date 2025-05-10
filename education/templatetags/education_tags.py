from django import template

register = template.Library()

@register.filter
def lookup(value, key):
    return value.get(key) if isinstance(value, dict) else None

@register.filter
def div(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0


@register.filter
def times(number):
    return range(number)

from django import template
@register.filter
def get_item(dictionary, key):
    return dictionary.get(str(key))