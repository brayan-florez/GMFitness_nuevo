import builtins

from django import template

register = template.Library()


@register.filter
def getattr(obj, name):
    try:
        value = builtins.getattr(obj, name)
        return value() if callable(value) else value
    except Exception:
        return "—"


@register.filter
def display_fields(obj):
    result = []
    for field in obj._meta.fields:
        if field.name in {"id", "contrasena_hash"}:
            continue
        result.append((field.verbose_name.capitalize(), builtins.getattr(obj, field.name)))
    return result
