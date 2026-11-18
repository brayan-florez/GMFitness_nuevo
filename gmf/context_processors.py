def navigation(request):
    user = getattr(request, "usuario", None)
    if user is None:
        return {"secciones": []}
    from .views import menu_for
    return {"secciones": menu_for(user)}
