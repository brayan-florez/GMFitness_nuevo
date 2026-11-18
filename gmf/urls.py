from django.urls import path

from . import views

urlpatterns = [
    path("", views.login, name="login"),
    path("registro/", views.registro, name="registro"),
    path("salir/", views.logout, name="logout"),
    path("panel/", views.panel, name="panel"),
    path("perfil/", views.perfil, name="perfil"),
    path("notificaciones/<int:pk>/leida/", views.marcar_notificacion, name="marcar_notificacion"),
    path("<slug:key>/", views.catalogo, name="catalogo"),
    path("<slug:key>/nuevo/", views.editar, name="crear"),
    path("<slug:key>/<int:pk>/editar/", views.editar, name="editar"),
    path("<slug:key>/<int:pk>/eliminar/", views.eliminar, name="eliminar"),
]
