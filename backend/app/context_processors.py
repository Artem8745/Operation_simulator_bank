def api_prefix(request):
    """
    Контекстный процессор для добавления префикса API во все шаблоны
    """
    return {
        'API_PREFIX': '/api'
    }