from django import forms
from django.core.exceptions import ValidationError
from django.forms import modelform_factory

from .models import Usuario, Cliente, Profesional, Entrenador, Nutricionista, Fisioterapeuta, Rol


class LoginForm(forms.Form):
    email = forms.EmailField(label="Correo electrónico")
    contrasena = forms.CharField(label="Contraseña", widget=forms.PasswordInput)


class RegistroForm(forms.ModelForm):
    contrasena = forms.CharField(label="Contraseña", min_length=8, widget=forms.PasswordInput)
    confirmar_contrasena = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput)

    class Meta:
        model = Usuario
        fields = ["numero_identidad", "nombre", "apellido", "fecha_nacimiento", "telefono", "email"]
        labels = {"numero_identidad": "Número de identidad", "fecha_nacimiento": "Fecha de nacimiento", "telefono": "Teléfono"}
        widgets = {"fecha_nacimiento": forms.DateInput(attrs={"type": "date"})}

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("contrasena") != cleaned.get("confirmar_contrasena"):
            self.add_error("confirmar_contrasena", "Las contraseñas no coinciden.")
        return cleaned

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.rol = Rol.CLIENTE
        usuario.set_password(self.cleaned_data["contrasena"])
        if commit:
            usuario.save()
            Cliente.objects.create(usuario=usuario)
        return usuario


class UsuarioAdminForm(forms.ModelForm):
    contrasena = forms.CharField(label="Contraseña inicial", min_length=8, widget=forms.PasswordInput, required=False)

    class Meta:
        model = Usuario
        fields = ["numero_identidad", "nombre", "apellido", "fecha_nacimiento", "telefono", "email", "rol", "activo", "sede"]
        widgets = {"fecha_nacimiento": forms.DateInput(attrs={"type": "date"})}

    def clean(self):
        cleaned = super().clean()
        if not self.instance.pk and not cleaned.get("contrasena"):
            self.add_error("contrasena", "Escribe una contraseña inicial.")
        return cleaned

    def save(self, commit=True):
        usuario = super().save(commit=False)
        if self.cleaned_data.get("contrasena"):
            usuario.set_password(self.cleaned_data["contrasena"])
        elif not usuario.pk:
            raise ValidationError("Asigna una contraseña inicial.")
        if commit:
            usuario.save()
            if usuario.rol == Rol.CLIENTE:
                Cliente.objects.get_or_create(usuario=usuario)
            elif usuario.rol in {Rol.ENTRENADOR, Rol.NUTRICIONISTA, Rol.FISIOTERAPEUTA}:
                profesional, _ = Profesional.objects.get_or_create(usuario=usuario, defaults={"especialidad": usuario.get_rol_display()})
                {Rol.ENTRENADOR: Entrenador, Rol.NUTRICIONISTA: Nutricionista, Rol.FISIOTERAPEUTA: Fisioterapeuta}[usuario.rol].objects.get_or_create(profesional=profesional)
        return usuario


def model_form(model, fields="__all__", exclude=None):
    return modelform_factory(model, fields=fields, exclude=exclude, formfield_callback=_style_field)


def _style_field(model_field):
    field = model_field.formfield()
    if field is None:
        return None
    widget = field.widget
    widget.attrs["class"] = "field-input"
    if isinstance(widget, forms.DateInput):
        widget.attrs.setdefault("type", "date")
    if isinstance(widget, forms.DateTimeInput):
        widget.attrs.setdefault("type", "datetime-local")
    return field
