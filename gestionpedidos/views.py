from django.shortcuts import render
from django.http import HttpResponse
from gestionpedidos.models import Articulos
from gestionpedidos.forms import ArticuloForm, BorrarArticuloForm
from .utils_scrap import scrap_rango
import pandas as pd
import io
import base64
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

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
    context = {"data": None, "error": None, "fecha_inicio": "", "fecha_fin": "", "total_rows": 0}

    if request.method == "POST":
        fecha_inicio = request.POST.get("fecha_inicio")
        fecha_fin = request.POST.get("fecha_fin")
        context["fecha_inicio"] = fecha_inicio
        context["fecha_fin"] = fecha_fin

        try:
            df = scrap_rango(fecha_inicio, fecha_fin)

            if df.empty:
                context["error"] = "No se encontraron datos en el rango seleccionado."
            else:
                context["total_rows"] = len(df)
                request.session["scrap_data"] = df.to_dict("records")
                request.session["scrap_columns"] = df.columns.tolist()

                if "download_csv" in request.POST:
                    response = HttpResponse(content_type="text/csv")
                    filename = f"Demanda-{fecha_inicio}_{fecha_fin}.csv"
                    response["Content-Disposition"] = f'attachment; filename="{filename}"'
                    df.to_csv(path_or_buf=response, index=False)
                    return response

                # Mostrar solo 10 primeras filas
                context["data"] = df.head(10).to_html(
                    classes="table table-striped table-bordered text-start",
                    index=False,
                    justify="left"
                )

        except Exception as e:
            context["error"] = f"Error en el scraping: {e}"

    return render(request, "scrap_page.html", context)

def scrap_view_graph(request):
    # Recuperamos datos de la sesión
    data = request.session.get("scrap_data")
    columns = request.session.get("scrap_columns")

    if not data or not columns:
        return render(request, "scrap_page.html", {"error": "No hay datos para visualizar."})

    df = pd.DataFrame(data, columns=columns)

    # Convertimos Fecha + Hora a datetime
    df["FechaHora"] = pd.to_datetime(df["Fecha"] + " " + df["Hora"], format="%d/%m/%Y %H:%M")

    # Ordenamos por FechaHora
    df = df.sort_values("FechaHora")

    # Generar gráfico
    fig, ax = plt.subplots(figsize=(12,5))
    ax.bar(df["FechaHora"], df["Real"], color="skyblue", label="Real")
    ax.plot(df["FechaHora"], df["Prevista"], color="green", marker='o', label="Prevista")
    ax.plot(df["FechaHora"], df["Programada"], color="red", marker='o', label="Programada")

    # Formateamos eje X con intervalos de 12 horas
    start = df["FechaHora"].iloc[0].replace(hour=0, minute=0)
    end = df["FechaHora"].iloc[-1].replace(hour=23, minute=55)
    ax.set_xlim(start, end)
    ax.set_xticks(pd.date_range(start=start, end=end, freq="12H"))
    ax.set_xlabel("Tiempo")
    ax.set_ylabel("Potencia (MW)")
    ax.legend()
    fig.autofmt_xdate(rotation=45)

    # Guardamos gráfico en memoria para mostrar en template
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    buf.seek(0)
    graph_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    buf.close()
    plt.close(fig)

    return render(request, "scrap_graph.html", {"graph": graph_base64})

def scrap_generacion(request):
    return HttpResponse("Página de información sobre generación eléctrica. (Contenido pendiente)")

def scrap_almacenamiento(request):
    return HttpResponse("Página de información sobre almacenamiento eléctrico. (Contenido pendiente)")

def scrap_precio(request):
    return HttpResponse("Página de información sobre precios eléctricos. (Contenido pendiente)")
