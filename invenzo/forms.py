from django import forms
from .models import Producto, Usuario

ESTADO_CHOICES = [
    ('activo', 'Activo'),
    ('inactivo', 'Inactivo'),
]

ROL_CHOICES = [
    ('administrador', 'Administrador'),
    ('auxiliar', 'Auxiliar')
]

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'nombre',
            'codigo',
            'categoria',
            'almacen',
            'cantidad',
            'stock_minimo',
            'stock_maximo',
            'precio',
            'descripcion',
            'imagen'  # ← IMPORTANTE
        ]

class FormularioRegistro(forms.Form):
    nombre = forms.CharField(max_length=100)
    email = forms.EmailField()
    contraseña = forms.CharField(widget=forms.PasswordInput)
    confirm = forms.CharField(widget=forms.PasswordInput)
    rol = forms.ChoiceField(choices=ROL_CHOICES, initial='auxiliar')  # ← nuevo campo

    def clean(self):
        datos = self.cleaned_data
        if datos.get('contraseña') != datos.get('confirm'):
            self.add_error('confirm', 'Las contraseñas no coinciden.')



class CategoriaForm(forms.Form):
    nombre = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la categoría'})
    )
    descripcion = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Descripción'})
    )
    productos = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Cantidad de productos'})
    )
    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class UsuarioCreateForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput(), required=True, label="Confirmar contraseña")

    class Meta:
        model = Usuario
        fields = ['nombre', 'email', 'password', 'confirm_password', 'rol', 'foto']
        widgets = {
            'password': forms.PasswordInput(),
        }

    def clean(self):
        cleaned = super().clean()
        p = cleaned.get('password')
        cp = cleaned.get('confirm_password')
        if p and cp and p != cp:
            self.add_error('confirm_password', 'Las contraseñas no coinciden.')
        return cleaned

class UsuarioEditForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nombre', 'email', 'rol', 'foto', 'estado']
