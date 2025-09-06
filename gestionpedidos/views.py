from django.shortcuts import render
from django.http import HttpResponse
from gestionpedidos.models import Articulos
from gestionpedidos.forms import ArticuloForm, BorrarArticuloForm
from .utils_scrap import scrap_rango
import pandas as pd
import io
from datetime import datetime
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
    df_html = None
    error_msg = None
    fecha_inicio, fecha_fin = "", ""
    total_rows = None
    chart_base64 = None

    if request.method == "POST":
        fecha_inicio = request.POST.get("fecha_inicio")
        fecha_fin = request.POST.get("fecha_fin")
        download = request.POST.get("download")

        try:
            # 1) Scrap y filtrado con tu función existente
            df = scrap_rango(fecha_inicio, fecha_fin)

            if df.empty:
                error_msg = "No se encontraron datos en el rango seleccionado."
            else:
                # 2) CSV si se pulsa descargar
                if download:
                    csv_buffer = io.StringIO()
                    df.to_csv(csv_buffer, index=False)
                    response = HttpResponse(csv_buffer.getvalue(), content_type="text/csv")
                    response["Content-Disposition"] = f'attachment; filename="Demanda-{fecha_inicio}_a_{fecha_fin}.csv"'
                    return response

                # 3) Tabla con primeras 10 filas
                total_rows = len(df)
                df_head = df.head(10)
                df_html = df_head.to_html(classes="table table-striped", index=False)

                # 4) Gráfica usando solo los datos filtrados en scrap_table_range
                df_plot = df.copy()
                df_plot["FechaHora_dt"] = pd.to_datetime(df_plot["Fecha"] + " " + df_plot["Hora"], format="%d/%m/%Y %H:%M", errors="coerce")

                # Filtrar de nuevo por seguridad (opcional)
                start_dt = pd.to_datetime(fecha_inicio, format="%Y-%m-%d")
                end_dt = pd.to_datetime(fecha_fin, format="%Y-%m-%d") + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                df_plot = df_plot.loc[(df_plot["FechaHora_dt"] >= start_dt) & (df_plot["FechaHora_dt"] <= end_dt)]
                df_plot = df_plot.sort_values("FechaHora_dt")

                if not df_plot.empty:
                    fig, ax = plt.subplots(figsize=(12, 5))
                    ax.bar(df_plot["FechaHora_dt"], df_plot["Real"], color="steelblue", label="Real (MW)")

                    # Eje X: cada 6 horas, mostrar día + hora
                    ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
                    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m\n%H:%M"))

                    ax.set_xlabel("Fecha y hora")
                    ax.set_ylabel("Potencia (MW)")
                    ax.set_title(f"Demanda real {fecha_inicio} a {fecha_fin}")
                    ax.legend()

                    plt.xticks(rotation=0, ha="center", fontsize=8)
                    plt.tight_layout()

                    buf = io.BytesIO()
                    fig.savefig(buf, format="png")
                    buf.seek(0)
                    chart_base64 = base64.b64encode(buf.read()).decode("utf-8")
                    plt.close(fig)
                else:
                    chart_base64 = None

        except Exception as e:
            error_msg = f"Error en el scraping: {e}"



    return render(request, "scrap_page.html", {
        "df_html": df_html,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "error_msg": error_msg,
        "total_rows": total_rows,
        "chart_base64": chart_base64,
    })