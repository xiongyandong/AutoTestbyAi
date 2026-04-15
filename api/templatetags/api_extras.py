from django import template

register = template.Library()


@register.filter
def lookup(obj, key):
    """从字典中取值，用于模板中动态键访问"""
    if isinstance(obj, dict):
        return obj.get(key)
    return None
