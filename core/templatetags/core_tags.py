from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Template filter to get an item from a dictionary."""
    if dictionary is None:
        return None
    return dictionary.get(key)
