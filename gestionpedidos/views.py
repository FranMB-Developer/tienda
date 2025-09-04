from django.shortcuts import render
from django.http import HttpResponse
from gestionpedidos.models import Articulos
from gestionpedidos.forms import ArticuloForm

# Create your views here.
def busqueda_productos(request):
    return render(request, 'busqueda_productos.html')

def buscar(request):
    if request.GET['prd']:
        #mensaje = "Artículo buscado: %r" % request.GET['prd']
        producto = request.GET['prd']
        articulos= Articulos.objects.filter(nombre__icontains=producto)
        return render(request, 'resultados_busqueda.html', {'articulos':articulos, 'query':producto})
    else:
        mensaje = "No se ha realizado ninguna búsqueda."
    return HttpResponse(mensaje)

def formulario_articulo(request):
    if request.method == 'POST':
        mi_formulario = ArticuloForm(request.POST)
        if mi_formulario.is_valid():
            articulo = mi_formulario.save()
            return HttpResponse(f"Artículo guardado: {articulo.nombre}, Precio: {articulo.precio}, Sección: {articulo.seccion}")
    else:
        mi_formulario = ArticuloForm()

    return render(request, 'formulario_articulo.html', {'formulario':mi_formulario})