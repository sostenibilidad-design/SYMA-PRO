from django import template

register = template.Library()


@register.filter
def alcanzo(paso_actual, minimo):
    """True si el registro ya llegó al paso `minimo`: {{ paso_actual|alcanzo:3 }}."""
    try:
        return int(paso_actual) >= int(minimo)
    except (TypeError, ValueError):
        return False
