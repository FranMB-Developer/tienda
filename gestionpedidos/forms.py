from django import forms
from gestionpedidos.models import Articulos

class ArticuloForm(forms.ModelForm):
    class Meta:
        model = Articulos
        fields = ['nombre', 'precio', 'seccion']

