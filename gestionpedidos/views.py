from django.shortcuts import render
from django.http import HttpResponse
from gestionpedidos.models import Articulos
from gestionpedidos.forms import ArticuloForm, BorrarArticuloForm
from .utils_scrap import scrap_rango
import pandas as pd
import io

# Create your views here.
def home(request):
    return render(request, 'home.html')

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
            articulo = mi_formulario.cleaned_data
            Articulos.objects.create(nombre=articulo['nombre'], precio=articulo['precio'], seccion=articulo['seccion'])
            return HttpResponse(f"Artículo guardado: {articulo['nombre']}, Precio: {articulo['precio']}, Sección: {articulo['seccion']} <a href='/'>Volver al inicio</a>")
    else:
        mi_formulario = ArticuloForm()

    return render(request, 'formulario_articulo.html', {'formulario':mi_formulario})

def borrar_articulo(request):
    if request.method == 'POST':
        mi_formulario = BorrarArticuloForm(request.POST)
        if mi_formulario.is_valid():
            nombre_articulo = mi_formulario.cleaned_data['nombre']
            try:
                articulo = Articulos.objects.get(nombre=nombre_articulo)
                articulo.delete()
                return HttpResponse(f"Artículo '{nombre_articulo}' borrado correctamente.")
            except Articulos.DoesNotExist:
                return HttpResponse(f"Artículo '{nombre_articulo}' no encontrado.")
    else:
        mi_formulario = BorrarArticuloForm()
    return render(request, 'borrar_articulo.html', {'formulario': mi_formulario})

def scrap_view(request):
    df_html = None
    fecha_inicio = None
    fecha_fin = None

    if request.method == "POST":
        fecha_inicio = request.POST.get("fecha_inicio")
        fecha_fin = request.POST.get("fecha_fin")
        download = request.POST.get("download")

        if fecha_inicio and fecha_fin:
            try:
                df = scrap_rango(fecha_inicio, fecha_fin)

                if df.empty:
                    df_html = "<p>No se encontraron datos en el rango seleccionado.</p>"
                elif download:  # descargar CSV
                    buffer = io.StringIO()
                    df.to_csv(buffer, index=False, encoding="utf-8")
                    buffer.seek(0)
                    response = HttpResponse(
                        buffer,
                        content_type='text/csv'
                    )
                    response['Content-Disposition'] = (
                        f'attachment; filename="Demanda-{fecha_inicio}_a_{fecha_fin}.csv"'
                    )
                    return response
                else:  # mostrar en HTML
                    df_html = df.to_html(classes="table table-striped", index=False)
            except Exception as e:
                df_html = f"<p>Error al scrapear: {e}</p>"

    return render(
        request,
        "scrap_page.html",
        {"df_html": df_html, "fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
    )