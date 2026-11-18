from datetime import date
from decimal import Decimal

from django.contrib.auth.hashers import check_password, make_password
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Rol(models.TextChoices):
    CLIENTE = "CLIENTE", "Cliente"
    ENTRENADOR = "ENTRENADOR", "Entrenador"
    NUTRICIONISTA = "NUTRICIONISTA", "Nutricionista"
    FISIOTERAPEUTA = "FISIOTERAPEUTA", "Fisioterapeuta"
    ADMINISTRADOR = "ADMINISTRADOR", "Administrador"


class Usuario(models.Model):
    numero_identidad = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    telefono = models.CharField(max_length=25, blank=True)
    email = models.EmailField(unique=True)
    contrasena_hash = models.CharField(max_length=128)
    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.CLIENTE)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(default=timezone.now)
    sede = models.ForeignKey("Sede", on_delete=models.SET_NULL, null=True, blank=True, related_name="usuarios")

    class Meta:
        ordering = ["apellido", "nombre"]

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.get_rol_display()})"

    def set_password(self, raw_password):
        self.contrasena_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.contrasena_hash)

    def calcular_edad(self):
        if not self.fecha_nacimiento:
            return None
        hoy = date.today()
        return hoy.year - self.fecha_nacimiento.year - ((hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))


class Sede(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    direccion = models.CharField(max_length=200)
    ciudad = models.CharField(max_length=100)
    telefono = models.CharField(max_length=25, blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ["ciudad", "nombre"]

    def __str__(self):
        return f"{self.nombre} — {self.ciudad}"


class Notificacion(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="notificaciones")
    mensaje = models.CharField(max_length=500)
    fecha_envio = models.DateTimeField(default=timezone.now)
    leida = models.BooleanField(default=False)

    class Meta:
        ordering = ["-fecha_envio"]

    def __str__(self):
        return self.mensaje[:70]


class Cliente(models.Model):
    class Sexo(models.TextChoices):
        MASCULINO = "MASCULINO", "Masculino"
        FEMENINO = "FEMENINO", "Femenino"
        OTRO = "OTRO", "Otro"

    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name="cliente")
    sexo = models.CharField(max_length=12, choices=Sexo.choices, blank=True)
    peso = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    altura = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Metros")
    porcentaje_graso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return str(self.usuario)


class Profesional(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name="profesional")
    especialidad = models.CharField(max_length=120)
    tarjeta_profesional = models.CharField(max_length=80, blank=True)

    def __str__(self):
        return f"{self.usuario.nombre} {self.usuario.apellido} — {self.especialidad}"


class Entrenador(models.Model):
    profesional = models.OneToOneField(Profesional, on_delete=models.CASCADE, related_name="entrenador")

    def __str__(self):
        return f"Entrenador: {self.profesional}"


class Nutricionista(models.Model):
    profesional = models.OneToOneField(Profesional, on_delete=models.CASCADE, related_name="nutricionista")

    def __str__(self):
        return f"Nutricionista: {self.profesional}"


class Fisioterapeuta(models.Model):
    profesional = models.OneToOneField(Profesional, on_delete=models.CASCADE, related_name="fisioterapeuta")

    def __str__(self):
        return f"Fisioterapeuta: {self.profesional}"


class Objetivo(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="objetivos")
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    fecha_objetivo = models.DateField(null=True, blank=True)
    completado = models.BooleanField(default=False)

    def __str__(self):
        return self.nombre


class ProgresoFisico(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="progresos_fisicos")
    fecha = models.DateField(default=date.today)
    peso = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(Decimal("0.1"))])
    altura = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    porcentaje_graso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    notas = models.TextField(blank=True)

    class Meta:
        ordering = ["-fecha"]

    def calcular_imc(self):
        if not self.altura or self.altura <= 0:
            return None
        return (self.peso / (self.altura * self.altura)).quantize(Decimal("0.01"))

    def __str__(self):
        return f"{self.cliente} — {self.fecha}"


class PlanMembresia(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    duracion_dias = models.PositiveSmallIntegerField(default=30)
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Membresia(models.Model):
    """Catálogo de membresías ofrecidas en una sede."""
    class Tipo(models.TextChoices):
        BASICA = "BASICA", "Básica"
        ESTANDAR = "ESTANDAR", "Estándar"
        PREMIUM = "PREMIUM", "Premium"

    tipo = models.CharField(max_length=12, choices=Tipo.choices)
    duracion = models.CharField(max_length=15, choices=[("MENSUAL", "Mensual"), ("TRIMESTRAL", "Trimestral"), ("SEMESTRAL", "Semestral"), ("ANUAL", "Anual")])
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.get_duracion_display()}"


class Suscripcion(models.Model):
    class Estado(models.TextChoices):
        ACTIVA = "ACTIVA", "Activa"
        VENCIDA = "VENCIDA", "Vencida"
        CANCELADA = "CANCELADA", "Cancelada"

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="suscripciones")
    membresia = models.ForeignKey(Membresia, on_delete=models.PROTECT, related_name="suscripciones")
    plan = models.ForeignKey(PlanMembresia, on_delete=models.SET_NULL, null=True, blank=True, related_name="suscripciones")
    fecha_inicio = models.DateField(default=date.today)
    fecha_fin = models.DateField()
    precio_contratado = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.VENCIDA)

    def verificar_vigencia(self):
        return self.estado == self.Estado.ACTIVA and self.fecha_inicio <= date.today() <= self.fecha_fin

    def calcular_dias_restantes(self):
        return max((self.fecha_fin - date.today()).days, 0)

    def __str__(self):
        return f"{self.cliente} — {self.membresia}"


class Pago(models.Model):
    class Metodo(models.TextChoices):
        EFECTIVO = "EFECTIVO", "Efectivo"
        TARJETA = "TARJETA", "Tarjeta"
        TRANSFERENCIA = "TRANSFERENCIA", "Transferencia"
        PSE = "PSE", "PSE"

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        APROBADO = "APROBADO", "Aprobado"
        RECHAZADO = "RECHAZADO", "Rechazado"
        REEMBOLSADO = "REEMBOLSADO", "Reembolsado"

    suscripcion = models.ForeignKey(Suscripcion, on_delete=models.PROTECT, related_name="pagos")
    monto = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    fecha = models.DateTimeField(default=timezone.now)
    metodo_pago = models.CharField(max_length=15, choices=Metodo.choices)
    referencia = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PENDIENTE)
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return f"Pago {self.pk} — ${self.monto} ({self.get_estado_display()})"


class Factura(models.Model):
    class Estado(models.TextChoices):
        EMITIDA = "EMITIDA", "Emitida"
        ANULADA = "ANULADA", "Anulada"

    pago = models.OneToOneField(Pago, on_delete=models.PROTECT, related_name="factura")
    detalle_factura = models.CharField(max_length=255)
    fecha_factura = models.DateTimeField(default=timezone.now)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    impuestos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=8, choices=Estado.choices, default=Estado.EMITIDA)

    def __str__(self):
        return f"Factura {self.pk} — {self.total}"


class Disponibilidad(models.Model):
    fisioterapeuta = models.ForeignKey(Fisioterapeuta, on_delete=models.CASCADE, related_name="disponibilidades")
    inicio = models.DateTimeField()
    fin = models.DateTimeField()
    disponible = models.BooleanField(default=True)

    class Meta:
        ordering = ["inicio"]

    def __str__(self):
        return f"{self.fisioterapeuta} — {self.inicio:%Y-%m-%d %H:%M}"


class Cita(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        CONFIRMADA = "CONFIRMADA", "Confirmada"
        CANCELADA = "CANCELADA", "Cancelada"
        COMPLETADA = "COMPLETADA", "Completada"

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="citas")
    fisioterapeuta = models.ForeignKey(Fisioterapeuta, on_delete=models.PROTECT, related_name="citas")
    disponibilidad = models.ForeignKey(Disponibilidad, on_delete=models.PROTECT, null=True, blank=True, related_name="citas")
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PENDIENTE)
    motivo = models.CharField(max_length=160)
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ["-fecha_inicio"]

    def __str__(self):
        return f"Cita {self.cliente} — {self.fecha_inicio:%Y-%m-%d %H:%M}"


class Rutina(models.Model):
    class Visibilidad(models.TextChoices):
        PRIVADA = "PRIVADA", "Privada"
        PUBLICA = "PUBLICA", "Pública"

    autor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="rutinas")
    nombre = models.CharField(max_length=120)
    objetivo = models.CharField(max_length=160)
    descripcion = models.TextField(blank=True)
    visibilidad = models.CharField(max_length=8, choices=Visibilidad.choices, default=Visibilidad.PRIVADA)

    def __str__(self):
        return self.nombre


class Ejercicio(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    musculo = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


class RutinaEjercicio(models.Model):
    rutina = models.ForeignKey(Rutina, on_delete=models.CASCADE, related_name="ejercicios")
    ejercicio = models.ForeignKey(Ejercicio, on_delete=models.PROTECT, related_name="en_rutinas")
    orden = models.PositiveSmallIntegerField(default=1)
    series = models.PositiveSmallIntegerField(default=3)
    repeticiones = models.PositiveSmallIntegerField(default=10)
    descanso_segundos = models.PositiveSmallIntegerField(default=60)
    intensidad = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ["orden"]
        unique_together = [("rutina", "orden")]

    def __str__(self):
        return f"{self.orden}. {self.ejercicio}"


class AsignacionRutina(models.Model):
    class Estado(models.TextChoices):
        ACTIVA = "ACTIVA", "Activa"
        PAUSADA = "PAUSADA", "Pausada"
        FINALIZADA = "FINALIZADA", "Finalizada"
        CANCELADA = "CANCELADA", "Cancelada"

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="asignaciones_rutina")
    entrenador = models.ForeignKey(Entrenador, on_delete=models.SET_NULL, null=True, blank=True, related_name="asignaciones")
    rutina = models.ForeignKey(Rutina, on_delete=models.PROTECT, related_name="asignaciones")
    fecha_asignacion = models.DateField(default=date.today)
    fecha_inicio = models.DateField(default=date.today)
    fecha_fin = models.DateField(null=True, blank=True)
    dias_por_semana = models.PositiveSmallIntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(7)])
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.ACTIVA)

    def __str__(self):
        return f"{self.cliente} — {self.rutina}"


class ProgresoEjercicio(models.Model):
    asignacion = models.ForeignKey(AsignacionRutina, on_delete=models.CASCADE, related_name="progresos")
    ejercicio = models.ForeignKey(Ejercicio, on_delete=models.PROTECT, related_name="progresos")
    fecha = models.DateField(default=date.today)
    series_realizadas = models.PositiveSmallIntegerField(default=0)
    repeticiones_realizadas = models.PositiveSmallIntegerField(default=0)
    carga_kg = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    intensidad = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def calcular_volumen(self):
        return self.series_realizadas * self.repeticiones_realizadas * self.carga_kg

    def __str__(self):
        return f"{self.ejercicio} — {self.fecha}"


class Dieta(models.Model):
    class Visibilidad(models.TextChoices):
        PRIVADA = "PRIVADA", "Privada"
        PUBLICA = "PUBLICA", "Pública"

    autor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="dietas")
    nombre = models.CharField(max_length=120)
    objetivo = models.CharField(max_length=160)
    descripcion = models.TextField(blank=True)
    visibilidad = models.CharField(max_length=8, choices=Visibilidad.choices, default=Visibilidad.PRIVADA)

    def __str__(self):
        return self.nombre


class Alimento(models.Model):
    codigo_barras = models.CharField(max_length=40, blank=True, unique=True, null=True)
    nombre = models.CharField(max_length=120, unique=True)
    porcion_gramos = models.DecimalField(max_digits=7, decimal_places=2, default=100)
    proteinas = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    grasas = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    carbohidratos = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    kcal = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    def __str__(self):
        return self.nombre


class DietaAlimento(models.Model):
    class Comida(models.TextChoices):
        DESAYUNO = "DESAYUNO", "Desayuno"
        MEDIA_MANANA = "MEDIA_MANANA", "Media mañana"
        ALMUERZO = "ALMUERZO", "Almuerzo"
        ALGO = "ALGO", "Algo"
        CENA = "CENA", "Cena"

    dieta = models.ForeignKey(Dieta, on_delete=models.CASCADE, related_name="alimentos")
    alimento = models.ForeignKey(Alimento, on_delete=models.PROTECT, related_name="dietas")
    cantidad_gramos = models.DecimalField(max_digits=7, decimal_places=2, validators=[MinValueValidator(Decimal("0.1"))])
    comida = models.CharField(max_length=15, choices=Comida.choices)

    def __str__(self):
        return f"{self.alimento} — {self.get_comida_display()}"


class AsignacionDieta(models.Model):
    class Estado(models.TextChoices):
        ACTIVA = "ACTIVA", "Activa"
        PAUSADA = "PAUSADA", "Pausada"
        FINALIZADA = "FINALIZADA", "Finalizada"
        CANCELADA = "CANCELADA", "Cancelada"

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="asignaciones_dieta")
    nutricionista = models.ForeignKey(Nutricionista, on_delete=models.SET_NULL, null=True, blank=True, related_name="asignaciones")
    dieta = models.ForeignKey(Dieta, on_delete=models.PROTECT, related_name="asignaciones")
    fecha_asignacion = models.DateField(default=date.today)
    fecha_inicio = models.DateField(default=date.today)
    fecha_fin = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.ACTIVA)

    def __str__(self):
        return f"{self.cliente} — {self.dieta}"
