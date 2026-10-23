def texto_excel(valor):
    """Un texto que empiece por = + - @ lo toma Excel como fórmula (inyección de fórmulas): se antepone una comilla."""
    if isinstance(valor, str) and valor[:1] in ('=', '+', '-', '@', '\t', '\r'):
        return "'" + valor
    return valor
