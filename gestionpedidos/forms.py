from django import forms
from gestionpedidos.models import Articulos

class ArticuloForm(forms.ModelForm):
    class Meta:
        model = Articulos
        fields = ['nombre', 'precio', 'seccion']

class BorrarArticuloForm(forms.Form):
    nombre = forms.CharField(max_length=30, label='Nombre del Artículo a Borrar')


