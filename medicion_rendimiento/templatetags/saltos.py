from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def con_saltos(valor):
    """Muestra un texto guardado con «<br>» como separador: escapa todo el HTML y deja pasar solo los saltos de línea."""
    if valor is None:
        return ''
    partes = str(valor).replace('<br />', '<br>').split('<br>')
    return mark_safe('<br>'.join(conditional_escape(parte) for parte in partes))  # nosec B308 B703
