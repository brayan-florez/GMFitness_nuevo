# GMFitness

Aplicación de gestión de gimnasio creada con Django. El proyecto mantiene la estructura usada por `sena`: un proyecto Django (`config`) y una app principal (`gmf`) que contiene modelos, vistas, formularios, rutas y plantillas.

## Módulos

La app principal incluye usuarios y roles, sedes, clientes y profesionales, objetivos y progreso, membresías y suscripciones, pagos y facturas, disponibilidad y citas, rutinas y ejercicios, dietas y alimentos, asignaciones y notificaciones.

Las cuentas de cliente se crean en la página de registro. Las cuentas del equipo se crean desde la administración o con el comando de administración. Las contraseñas se almacenan con los hashers de Django. La aprobación de un pago genera una factura interna y activa la suscripción cuando el acumulado aprobado cubre el precio contratado; no se conecta a una pasarela de pago externa.

## Instalación local

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py crear_administrador
python manage.py runserver
```

Abre `http://127.0.0.1:8000/`. La base de datos inicial usa SQLite, como el proyecto de referencia.
