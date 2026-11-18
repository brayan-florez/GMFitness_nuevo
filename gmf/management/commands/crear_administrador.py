from getpass import getpass

from django.core.management.base import BaseCommand, CommandError

from gmf.models import Rol, Usuario


class Command(BaseCommand):
    help = "Crea una cuenta de administrador para GMFitness."

    def handle(self, *args, **options):
        email = input("Correo electrónico: ").strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise CommandError("Ya existe una cuenta con ese correo.")
        identidad = input("Número de identidad: ").strip()
        nombre = input("Nombre: ").strip()
        apellido = input("Apellido: ").strip()
        password = getpass("Contraseña (mínimo 8 caracteres): ")
        confirm = getpass("Confirma la contraseña: ")
        if len(password) < 8 or password != confirm:
            raise CommandError("La contraseña debe tener al menos 8 caracteres y coincidir con su confirmación.")
        usuario = Usuario(numero_identidad=identidad, nombre=nombre, apellido=apellido, email=email, rol=Rol.ADMINISTRADOR)
        usuario.set_password(password)
        usuario.save()
        self.stdout.write(self.style.SUCCESS(f"Administrador {email} creado."))
