from .views import get_alerts

def alerts(request):
    if request.user.is_authenticated:
        return get_alerts()
    return {}