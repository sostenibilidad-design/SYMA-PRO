from django import template

register = template.Library()

@register.filter
def cop(valor):
    try:
        valor = float(valor)
        return f"{valor:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return valor
