from functools import wraps

from django.contrib import messages
from django.db import models as django_models
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from . import models
from .forms import LoginForm, RegistroForm, UsuarioAdminForm, model_form


ADMIN = {"ADMINISTRADOR"}
ROLES = {
    "sedes": ADMIN,
    "usuarios": ADMIN,
    "clientes": ADMIN | {"ENTRENADOR", "NUTRICIONISTA", "FISIOTERAPEUTA"},
    "profesionales": ADMIN,
    "objetivos": {"CLIENTE", "ADMINISTRADOR"},
    "progreso-fisico": {"CLIENTE", "ENTRENADOR", "ADMINISTRADOR"},
    "membresias": ADMIN | {"CLIENTE"},
    "planes": ADMIN,
    "suscripciones": {"CLIENTE", "ADMINISTRADOR"},
    "pagos": {"CLIENTE", "ADMINISTRADOR"},
    "facturas": {"CLIENTE", "ADMINISTRADOR"},
    "disponibilidades": {"FISIOTERAPEUTA", "ADMINISTRADOR"},
    "citas": {"CLIENTE", "FISIOTERAPEUTA", "ADMINISTRADOR"},
    "rutinas": {"CLIENTE", "ENTRENADOR", "ADMINISTRADOR"},
    "ejercicios": {"ENTRENADOR", "ADMINISTRADOR"},
    "asignaciones-rutina": {"CLIENTE", "ENTRENADOR", "ADMINISTRADOR"},
    "progreso-ejercicio": {"CLIENTE", "ENTRENADOR", "ADMINISTRADOR"},
    "dietas": {"CLIENTE", "NUTRICIONISTA", "ADMINISTRADOR"},
    "alimentos": {"NUTRICIONISTA", "ADMINISTRADOR"},
    "asignaciones-dieta": {"CLIENTE", "NUTRICIONISTA", "ADMINISTRADOR"},
    "notificaciones": {"CLIENTE", "ENTRENADOR", "NUTRICIONISTA", "FISIOTERAPEUTA", "ADMINISTRADOR"},
}
CATALOGO = {
    "sedes": (models.Sede, "Sedes"),
    "usuarios": (models.Usuario, "Usuarios"),
    "clientes": (models.Cliente, "Clientes"),
    "profesionales": (models.Profesional, "Profesionales"),
    "objetivos": (models.Objetivo, "Objetivos"),
    "progreso-fisico": (models.ProgresoFisico, "Progreso físico"),
    "membresias": (models.Membresia, "Membresías"),
    "planes": (models.PlanMembresia, "Planes de membresía"),
    "suscripciones": (models.Suscripcion, "Suscripciones"),
    "pagos": (models.Pago, "Pagos"),
    "facturas": (models.Factura, "Facturas"),
    "disponibilidades": (models.Disponibilidad, "Disponibilidad de fisioterapia"),
    "citas": (models.Cita, "Citas"),
    "rutinas": (models.Rutina, "Rutinas"),
    "ejercicios": (models.Ejercicio, "Ejercicios"),
    "asignaciones-rutina": (models.AsignacionRutina, "Asignaciones de rutina"),
    "progreso-ejercicio": (models.ProgresoEjercicio, "Progreso de ejercicio"),
    "dietas": (models.Dieta, "Dietas"),
    "alimentos": (models.Alimento, "Alimentos"),
    "asignaciones-dieta": (models.AsignacionDieta, "Asignaciones de dieta"),
    "notificaciones": (models.Notificacion, "Notificaciones"),
}


def login_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not getattr(request, "usuario", None):
            return redirect("login")
        return view(request, *args, **kwargs)
    return wrapped


def role_required(allowed):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(request, *args, **kwargs):
            if request.usuario.rol not in allowed:
                messages.error(request, "No tienes permiso para acceder a esa sección.")
                return redirect("panel")
            return view(request, *args, **kwargs)
        return wrapped
    return decorator


def login(request):
    if request.usuario:
        return redirect("panel")
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        usuario = models.Usuario.objects.filter(email__iexact=form.cleaned_data["email"], activo=True).first()
        if usuario and usuario.check_password(form.cleaned_data["contrasena"]):
            request.session.cycle_key()
            request.session["usuario_id"] = usuario.pk
            models.Notificacion.objects.create(usuario=usuario, mensaje="Inicio de sesión correcto.")
            return redirect("panel")
        messages.error(request, "Correo o contraseña incorrectos.")
    return render(request, "gmf/login.html", {"form": form})


def registro(request):
    if request.usuario:
        return redirect("panel")
    form = RegistroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        usuario = form.save()
        request.session["usuario_id"] = usuario.pk
        messages.success(request, "Tu cuenta está lista.")
        return redirect("panel")
    return render(request, "gmf/registro.html", {"form": form})


@require_POST
def logout(request):
    request.session.flush()
    return redirect("login")


@login_required
def panel(request):
    user = request.usuario
    cliente = getattr(user, "cliente", None)
    counts = {}
    if cliente:
        counts = {
            "citas": cliente.citas.exclude(estado="CANCELADA").count(),
            "suscripciones": cliente.suscripciones.count(),
            "rutinas": cliente.asignaciones_rutina.filter(estado="ACTIVA").count(),
            "dietas": cliente.asignaciones_dieta.filter(estado="ACTIVA").count(),
        }
    elif user.rol == "ADMINISTRADOR":
        counts = {"usuarios": models.Usuario.objects.count(), "clientes": models.Cliente.objects.count(), "citas": models.Cita.objects.exclude(estado="CANCELADA").count(), "pagos": models.Pago.objects.filter(estado="PENDIENTE").count()}
    return render(request, "gmf/panel.html", {"counts": counts, "secciones": menu_for(user), "notificaciones": user.notificaciones.filter(leida=False)[:5]})


@login_required
def perfil(request):
    form = model_form(models.Usuario, exclude=["contrasena_hash", "rol", "activo", "fecha_registro"])(request.POST or None, instance=request.usuario)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Perfil actualizado.")
        return redirect("perfil")
    return render(request, "gmf/perfil.html", {"form": form})


@login_required
def marcar_notificacion(request, pk):
    notificacion = get_object_or_404(models.Notificacion, pk=pk, usuario=request.usuario)
    notificacion.leida = True
    notificacion.save(update_fields=["leida"])
    return redirect("panel")


def menu_for(user):
    result = []
    for key, (_, title) in CATALOGO.items():
        if user.rol in ROLES[key]:
            result.append({"key": key, "title": title})
    return result


def _professional_for(user, role):
    prof = getattr(user, "profesional", None)
    if not prof:
        return None
    return {"ENTRENADOR": getattr(prof, "entrenador", None), "NUTRICIONISTA": getattr(prof, "nutricionista", None), "FISIOTERAPEUTA": getattr(prof, "fisioterapeuta", None)}.get(role)


def scoped_queryset(request, key, model):
    qs = model.objects.all()
    user = request.usuario
    if user.rol == "ADMINISTRADOR":
        return qs
    if key == "clientes":
        return qs if user.rol in {"ENTRENADOR", "NUTRICIONISTA", "FISIOTERAPEUTA"} else qs.filter(usuario=user)
    if key in {"objetivos", "progreso-fisico"}:
        return qs.filter(cliente__usuario=user) if user.rol == "CLIENTE" else qs
    if key == "profesionales":
        return qs.filter(usuario=user)
    if key in {"suscripciones", "citas"}:
        return qs.filter(cliente__usuario=user) if user.rol == "CLIENTE" else (qs.filter(fisioterapeuta__profesional__usuario=user) if key == "citas" else qs)
    if key == "pagos":
        return qs.filter(suscripcion__cliente__usuario=user)
    if key == "facturas":
        return qs.filter(pago__suscripcion__cliente__usuario=user)
    if key in {"disponibilidades"}:
        return qs.filter(fisioterapeuta__profesional__usuario=user)
    if key in {"rutinas", "dietas"}:
        return qs.filter(Q(autor=user) | Q(visibilidad="PUBLICA"))
    if key == "asignaciones-rutina":
        if user.rol == "CLIENTE": return qs.filter(cliente__usuario=user)
        trainer = _professional_for(user, "ENTRENADOR")
        return qs.filter(entrenador=trainer)
    if key == "asignaciones-dieta":
        if user.rol == "CLIENTE": return qs.filter(cliente__usuario=user)
        nutritionist = _professional_for(user, "NUTRICIONISTA")
        return qs.filter(nutricionista=nutritionist)
    if key == "progreso-ejercicio":
        return qs.filter(asignacion__cliente__usuario=user) if user.rol == "CLIENTE" else qs.filter(asignacion__entrenador=_professional_for(user, "ENTRENADOR"))
    if key == "notificaciones":
        return qs.filter(usuario=user)
    if key == "usuarios":
        return qs.filter(pk=user.pk)
    if key == "membresias":
        return qs.filter(activa=True)
    return qs


def _form_for(request, key, model, instance=None):
    if key == "usuarios":
        return UsuarioAdminForm(request.POST or None, instance=instance)
    exclude = []
    if key in {"rutinas", "dietas"} and request.usuario.rol != "ADMINISTRADOR":
        exclude.append("autor")
    if key == "objetivos" and request.usuario.rol == "CLIENTE": exclude.append("cliente")
    if key == "progreso-fisico" and request.usuario.rol == "CLIENTE": exclude.append("cliente")
    if key == "asignaciones-rutina" and request.usuario.rol == "ENTRENADOR": exclude.append("entrenador")
    if key == "asignaciones-dieta" and request.usuario.rol == "NUTRICIONISTA": exclude.append("nutricionista")
    if key == "notificaciones" and request.usuario.rol != "ADMINISTRADOR": exclude.append("usuario")
    if key == "pagos" and request.usuario.rol != "ADMINISTRADOR":
        exclude.extend(["estado", "monto"])
    if key == "suscripciones" and request.usuario.rol == "CLIENTE":
        exclude.extend(["cliente", "estado", "precio_contratado", "fecha_fin"])
    form = model_form(model, exclude=exclude or None)(request.POST or None, instance=instance)
    if key == "suscripciones" and request.usuario.rol == "CLIENTE":
        form.fields["membresia"].queryset = models.Membresia.objects.filter(activa=True)
    if key == "pagos" and request.usuario.rol == "CLIENTE":
        form.fields["suscripcion"].queryset = models.Suscripcion.objects.filter(cliente__usuario=request.usuario)
    if key == "progreso-ejercicio" and request.usuario.rol == "CLIENTE":
        form.fields["asignacion"].queryset = models.AsignacionRutina.objects.filter(cliente__usuario=request.usuario, estado=models.AsignacionRutina.Estado.ACTIVA)
    return form


def _set_owner(request, key, obj):
    user = request.usuario
    cliente = getattr(user, "cliente", None)
    if key in {"rutinas", "dietas"} and not obj.autor_id:
        obj.autor = user
    if key in {"objetivos", "progreso-fisico"} and user.rol == "CLIENTE":
        obj.cliente = cliente
    if key == "asignaciones-rutina":
        if user.rol == "CLIENTE": obj.cliente = cliente
        if user.rol == "ENTRENADOR": obj.entrenador = _professional_for(user, "ENTRENADOR")
    if key == "asignaciones-dieta":
        if user.rol == "CLIENTE": obj.cliente = cliente
        if user.rol == "NUTRICIONISTA": obj.nutricionista = _professional_for(user, "NUTRICIONISTA")
    if key == "progreso-ejercicio" and user.rol == "CLIENTE":
        obj.asignacion = get_object_or_404(models.AsignacionRutina, pk=request.POST.get("asignacion"), cliente=cliente)
    if key == "notificaciones" and user.rol != "ADMINISTRADOR":
        obj.usuario = user
    if key == "citas" and user.rol == "CLIENTE": obj.cliente = cliente
    if key == "citas" and user.rol == "FISIOTERAPEUTA": obj.fisioterapeuta = _professional_for(user, "FISIOTERAPEUTA")
    if key == "disponibilidades": obj.fisioterapeuta = _professional_for(user, "FISIOTERAPEUTA")
    if key == "suscripciones" and user.rol == "CLIENTE":
        obj.cliente = cliente
        obj.precio_contratado = obj.membresia.precio
        dias = {"MENSUAL": 30, "TRIMESTRAL": 90, "SEMESTRAL": 180, "ANUAL": 365}.get(obj.membresia.duracion, 30)
        from datetime import timedelta
        obj.fecha_fin = obj.fecha_inicio + timedelta(days=dias)
        obj.estado = models.Suscripcion.Estado.VENCIDA
    if key == "pagos" and user.rol == "CLIENTE":
        obj.monto = obj.suscripcion.precio_contratado
        obj.estado = models.Pago.Estado.PENDIENTE
    return obj


@role_required(set().union(*ROLES.values()))
def catalogo(request, key):
    if key not in CATALOGO:
        return redirect("panel")
    if request.usuario.rol not in ROLES[key]:
        messages.error(request, "No tienes permiso para acceder a esa sección.")
        return redirect("panel")
    model, title = CATALOGO[key]
    query = scoped_queryset(request, key, model).select_related()
    search = request.GET.get("q", "").strip()
    if search:
        fields = [f.name for f in model._meta.fields if isinstance(f, (django_models.CharField, django_models.EmailField, django_models.TextField))]
        condition = Q()
        for field in fields:
            condition |= Q(**{f"{field}__icontains": search})
        if condition: query = query.filter(condition)
    return render(request, "gmf/catalogo.html", {"items": query[:200], "title": title, "key": key, "search": search, "solo_lectura": key == "facturas" or (key == "membresias" and request.usuario.rol != "ADMINISTRADOR")})


@role_required(set().union(*ROLES.values()))
def editar(request, key, pk=None):
    if key not in CATALOGO or request.usuario.rol not in ROLES.get(key, set()):
        messages.error(request, "No tienes permiso para esa acción.")
        return redirect("panel")
    if key == "facturas" or (key == "membresias" and request.usuario.rol != "ADMINISTRADOR") or (key == "pagos" and request.usuario.rol != "ADMINISTRADOR" and pk):
        messages.error(request, "Este registro es de consulta o solo puede editarlo un administrador.")
        return redirect("catalogo", key=key)
    model, title = CATALOGO[key]
    instance = get_object_or_404(scoped_queryset(request, key, model), pk=pk) if pk else None
    form = _form_for(request, key, model, instance)
    if request.method == "POST" and form.is_valid():
        if key == "usuarios":
            obj = form.save()
        else:
            obj = _set_owner(request, key, form.save(commit=False))
            obj.save()
            form.save_m2m()
        if key == "pagos" and obj.estado == models.Pago.Estado.APROBADO:
            from django.db.models import Sum
            from django.utils import timezone
            models.Factura.objects.get_or_create(pago=obj, defaults={"detalle_factura": f"Pago de membresía {obj.suscripcion.membresia}", "subtotal": obj.monto, "impuestos": 0, "total": obj.monto})
            paid = obj.suscripcion.pagos.filter(estado=models.Pago.Estado.APROBADO).aggregate(total=Sum("monto"))["total"] or 0
            if paid >= obj.suscripcion.precio_contratado:
                obj.suscripcion.estado = models.Suscripcion.Estado.ACTIVA
                obj.suscripcion.fecha_inicio = timezone.localdate()
                obj.suscripcion.save(update_fields=["estado", "fecha_inicio"])
        messages.success(request, f"{title[:-1] if title.endswith('s') else title} guardado correctamente.")
        return redirect("catalogo", key=key)
    return render(request, "gmf/formulario.html", {"form": form, "title": title, "key": key, "instance": instance})


@require_POST
@role_required(set().union(*ROLES.values()))
def eliminar(request, key, pk):
    if key not in CATALOGO or request.usuario.rol not in ROLES.get(key, set()):
        messages.error(request, "No tienes permiso para esa acción.")
        return redirect("panel")
    model, title = CATALOGO[key]
    obj = get_object_or_404(scoped_queryset(request, key, model), pk=pk)
    obj.delete()
    messages.success(request, "Registro eliminado.")
    return redirect("catalogo", key=key)
