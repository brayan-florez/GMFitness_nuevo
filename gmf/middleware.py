from .models import Usuario


class UsuarioActualMiddleware:
    """Expone request.usuario para vistas y plantillas de la sesión propia."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario_id = request.session.get("usuario_id")
        request.usuario = Usuario.objects.filter(pk=usuario_id, activo=True).first() if usuario_id else None
        return self.get_response(request)
