from django import template
register = template.Library()

@register.filter(is_safe=False)
def length_is(value, arg):
    """Return a boolean of whether the value's length is the argument."""
    "The length_is template filter is deprecated in favor of the length template "
    "filter and the == operator within an {% if %} tag."
    
    try:
        return len(value) == int(arg)
    except (ValueError, TypeError):
        return ""