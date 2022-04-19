from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    result = value * arg
    return round(result, 2)

@register.filter
def total_ammount(value):
    return sum(round(d.price * d.quantity, 2) for d in value)