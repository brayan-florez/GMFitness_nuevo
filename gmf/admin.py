from django.contrib import admin
from django.db.models import Sum

from .models import (
    Usuario, Sede, Notificacion, Cliente, Profesional, Entrenador, Nutricionista,
    Fisioterapeuta, Objetivo, ProgresoFisico, PlanMembresia, Membresia,
    Suscripcion, Pago, Factura, Disponibilidad, Cita, Rutina, Ejercicio,
    RutinaEjercicio, AsignacionRutina, ProgresoEjercicio, Dieta, Alimento,
    DietaAlimento, AsignacionDieta,
)


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("numero_identidad", "nombre", "apellido", "email", "rol", "sede", "activo")
    list_filter = ("rol", "activo", "sede")
    search_fields = ("numero_identidad", "nombre", "apellido", "email")


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("usuario", "sexo", "peso", "altura")
    search_fields = ("usuario__nombre", "usuario__apellido", "usuario__email")


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ("id", "suscripcion", "monto", "metodo_pago", "estado", "fecha")
    list_filter = ("estado", "metodo_pago")
    actions = ("aprobar_pagos",)

    @admin.action(description="Aprobar pagos seleccionados")
    def aprobar_pagos(self, request, queryset):
        for pago in queryset.select_related("suscripcion"):
            pago.estado = Pago.Estado.APROBADO
            pago.save(update_fields=["estado"])
            Factura.objects.get_or_create(
                pago=pago,
                defaults={"detalle_factura": f"Pago de membresía {pago.suscripcion.membresia}", "subtotal": pago.monto, "impuestos": 0, "total": pago.monto},
            )
            suscripcion = pago.suscripcion
            if suscripcion.pagos.filter(estado=Pago.Estado.APROBADO).aggregate(total=Sum("monto"))["total"] >= suscripcion.precio_contratado:
                suscripcion.estado = suscripcion.Estado.ACTIVA
                suscripcion.save(update_fields=["estado"])
        self.message_user(request, "Pagos aprobados; se generaron las facturas correspondientes.")


for model in [
    Sede, Notificacion, Profesional, Entrenador, Nutricionista, Fisioterapeuta,
    Objetivo, ProgresoFisico, PlanMembresia, Membresia, Suscripcion, Factura,
    Disponibilidad, Cita, Rutina, Ejercicio, RutinaEjercicio,
    AsignacionRutina, ProgresoEjercicio, Dieta, Alimento, DietaAlimento,
    AsignacionDieta,
]:
    admin.site.register(model)
