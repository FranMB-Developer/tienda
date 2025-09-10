from django.shortcuts import render
from django.http import HttpResponse
from .utils_scrap import scrap_rango, scrap_rango_precio_omie
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import matplotlib.dates as mdates
from datetime import datetime


def home(request):
    return render(request, "home.html")

# -----------------------------
# Vista para DEMANDA
# -----------------------------
def scrap_demanda_view(request):
    context = {"data": None, "error": None, "fecha_inicio": "", "fecha_fin": "", "total_rows": 0, "titulo": "Scraping de Demanda eléctrica"}

    if request.method == "POST":
        fecha_inicio = request.POST.get("fecha_inicio")
        fecha_fin = request.POST.get("fecha_fin")
        context["fecha_inicio"] = fecha_inicio
        context["fecha_fin"] = fecha_fin

        try:
            df = scrap_rango(fecha_inicio, fecha_fin, url_tipo=1)

            if df.empty:
                context["error"] = "No se encontraron datos en el rango seleccionado."
            else:
                context["total_rows"] = len(df)
                request.session["scrap_data"] = df.to_dict("records")
                request.session["scrap_columns"] = df.columns.tolist()
                request.session["scrap_tipo"] = "demanda"

                if "download_csv" in request.POST:
                    response = HttpResponse(content_type="text/csv")
                    filename = f"Demanda-{fecha_inicio}_{fecha_fin}.csv"
                    response["Content-Disposition"] = f'attachment; filename="{filename}"'
                    df.to_csv(path_or_buf=response, index=False)
                    return response

                context["data"] = df.head(10).to_html(
                    classes="table table-striped table-bordered text-start",
                    index=False,
                    justify="left"
                )

        except Exception as e:
            context["error"] = f"Error en el scraping de demanda: {e}"

    return render(request, "scrap_page.html", context)


# -----------------------------
# Vista para GENERACION
# -----------------------------
def scrap_generacion_view(request):
    context = {
        "data": None,
        "error": None,
        "fecha_inicio": "",
        "fecha_fin": "",
        "total_rows": 0,
        "titulo": "Scraping de Generación eléctrica",
        "tipo_generacion": "todos"  # valor por defecto
    }

    # Columnas por tipo de energía
    renovables_cols = ["Eólica", "Solar fotovoltaica", "Solar térmica", "Biocombustible", "Hidráulica"]
    no_renovables_cols = ["Nuclear", "Carbón", "Ciclo combinado", "Motor diésel", 
                          "Turbina de gas", "Turbina de vapor", "Cogeneración y residuos"]
    
    # Columnas que siempre deben mostrarse
    columnas_fijas = ["Fecha", "Hora"]

    if request.method == "POST":
        fecha_inicio = request.POST.get("fecha_inicio")
        fecha_fin = request.POST.get("fecha_fin")
        tipo_generacion = request.POST.get("tipo_generacion", "todos")
        context["fecha_inicio"] = fecha_inicio
        context["fecha_fin"] = fecha_fin
        context["tipo_generacion"] = tipo_generacion

        try:
            df = scrap_rango(fecha_inicio, fecha_fin, url_tipo=2)

            if df.empty:
                context["error"] = "No se encontraron datos en el rango seleccionado."
            else:


                # Selección de columnas según tipo de energía
                if tipo_generacion == "renovables":
                    cols_a_mostrar = columnas_fijas + [col for col in renovables_cols if col in df.columns]
                elif tipo_generacion == "no_renovables":
                    cols_a_mostrar = columnas_fijas + [col for col in no_renovables_cols if col in df.columns]
                else:  # "todos"
                    cols_a_mostrar = df.columns.tolist()

                df_filtrado = df[cols_a_mostrar]

                context["total_rows"] = len(df_filtrado)
                request.session["scrap_data"] = df_filtrado.to_dict("records")
                request.session["scrap_columns"] = df_filtrado.columns.tolist()
                request.session["scrap_tipo"] = "generacion"

                if "download_csv" in request.POST:
                    response = HttpResponse(content_type="text/csv")
                    filename = f"Generacion-{fecha_inicio}_{fecha_fin}.csv"
                    response["Content-Disposition"] = f'attachment; filename="{filename}"'
                    df_filtrado.to_csv(path_or_buf=response, index=False)
                    return response

                context["data"] = df_filtrado.head(10).to_html(
                    classes="table table-striped table-bordered text-start",
                    index=False,
                    justify="left"
                )

        except Exception as e:
            context["error"] = f"Error en el scraping de generación: {e}"

    return render(request, "scrap_page_generacion.html", context)

# -----------------------------
# Vista para ALMACENAMIENTO
# -----------------------------
def scrap_almacenamiento_view(request):
    context = {"data": None, "error": None, "fecha_inicio": "", "fecha_fin": "", "total_rows": 0, "titulo": "Scraping de Almacenamiento eléctrico"}

    if request.method == "POST":
        fecha_inicio = request.POST.get("fecha_inicio")
        fecha_fin = request.POST.get("fecha_fin")
        context["fecha_inicio"] = fecha_inicio
        context["fecha_fin"] = fecha_fin

        try:
            df = scrap_rango(fecha_inicio, fecha_fin, url_tipo=4)

            if df.empty:
                context["error"] = "No se encontraron datos en el rango seleccionado."
            else:
                context["total_rows"] = len(df)
                request.session["scrap_data"] = df.to_dict("records")
                request.session["scrap_columns"] = df.columns.tolist()
                request.session["scrap_tipo"] = "almacenamiento"

                # Descargar CSV
                if "download_csv" in request.POST:
                    response = HttpResponse(content_type="text/csv")
                    filename = f"Almacenamiento-{fecha_inicio}_{fecha_fin}.csv"
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
            context["error"] = f"Error en el scraping de almacenamiento: {e}"

    return render(request, "scrap_page.html", context)


# -----------------------------
# Vista para mostrar gráficas
# -----------------------------
def scrap_view_graph(request):
    """
    Reutilizable para generar gráficos según los datos en sesión.
    Demanda → scrap_graph_demanda.html con estadísticas.
    Generación y almacenamiento → scrap_graph.html con gráfico.
    """
    data = request.session.get("scrap_data")
    columns = request.session.get("scrap_columns")
    tipo = request.session.get("scrap_tipo", "demanda")

    if not data or not columns:
        return render(request, "scrap_page.html", {"error": "No hay datos para visualizar."})

    df = pd.DataFrame(data, columns=columns)

    if "Fecha" not in df.columns or "Hora" not in df.columns:
        return render(request, "scrap_page.html", {"error": "No se pueden generar gráficos sin columnas Fecha y Hora."})

    # Construir columna FechaHora
    df["FechaHora"] = pd.to_datetime(df["Fecha"] + " " + df["Hora"], format="%d/%m/%Y %H:%M")
    df = df.sort_values("FechaHora")

    # --- DEMANDA ---
    if tipo == "demanda":
        fig, ax = plt.subplots(figsize=(12, 5))
        if "Real" in df.columns:
            ax.bar(df["FechaHora"], df["Real"], color="skyblue", label="Real")
        if "Prevista" in df.columns:
            ax.plot(df["FechaHora"], df["Prevista"], color="green", marker="o", label="Prevista")
        if "Programada" in df.columns:
            ax.plot(df["FechaHora"], df["Programada"], color="red", marker="o", label="Programada")

        # Configuración eje X
        start = df["FechaHora"].iloc[0].replace(hour=0, minute=0)
        end = df["FechaHora"].iloc[-1].replace(hour=23, minute=55)
        rango_dias = (end.date() - start.date()).days + 1
        freq = "3H" if rango_dias <= 3 else "12H"
        ax.set_xlim(start, end)
        ax.set_xticks(pd.date_range(start=start, end=end, freq=freq))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m-%Y %H:%M"))

        ax.set_xlabel("Tiempo")
        ax.set_ylabel("Potencia (MW)")
        ax.legend()
        fig.autofmt_xdate(rotation=45)

        # Guardar gráfico
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format="png")
        buf.seek(0)
        graph_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        buf.close()
        plt.close(fig)

        # Calcular estadísticas
        stats = {}
        if "Real" in df.columns:
            max_val = df["Real"].max()
            min_val = df["Real"].min()
            mean_val = df["Real"].mean()

            stats = {
                "max_val": round(max_val, 2),
                "hora_max": df.loc[df["Real"].idxmax(), "FechaHora"].strftime("%d-%m-%Y %H:%M"),
                "min_val": round(min_val, 2),
                "hora_min": df.loc[df["Real"].idxmin(), "FechaHora"].strftime("%d-%m-%Y %H:%M"),
                "mean_val": round(mean_val, 2),
            }

        return render(request, "scrap_graph_demanda.html", {"graph": graph_base64, "stats": stats})

    # --- GENERACIÓN ---
    elif tipo == "generacion":
        # Usar directamente las columnas seleccionadas por el usuario
        # excluyendo 'Fecha', 'Hora' y 'FechaHora' si ya existen
        columnas_a_graficar = [col for col in df.columns if col not in ["Fecha", "Hora", "FechaHora"]]

        # Asegurarse de que las columnas existan en el DataFrame
        for col in columnas_a_graficar:
            if col not in df.columns:
                df[col] = 0

        fig, ax = plt.subplots(figsize=(12, 5))
        bottom = pd.Series([0] * len(df))
        for col in columnas_a_graficar:
            ax.bar(df["FechaHora"], df[col], bottom=bottom, label=col)
            bottom += df[col]

        start = df["FechaHora"].iloc[0].replace(hour=0, minute=0)
        end = df["FechaHora"].iloc[-1].replace(hour=23, minute=55)
        rango_dias = (end.date() - start.date()).days + 1
        freq = "3H" if rango_dias <= 3 else "12H"
        ax.set_xlim(start, end)
        ax.set_xticks(pd.date_range(start=start, end=end, freq=freq))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m-%Y %H:%M"))

        ax.set_xlabel("Tiempo")
        ax.set_ylabel("Potencia (MW)")
        ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
        fig.autofmt_xdate(rotation=45)


    # --- ALMACENAMIENTO ---
    elif tipo == "almacenamiento":
        cols = ["Turbinación bombeo", "Consumo bombeo", "Entrega de baterías", "Carga de baterías"]
        for col in cols:
            if col not in df.columns:
                df[col] = 0

        fig, ax = plt.subplots(figsize=(12, 5))
        for col in cols:
            ax.bar(df["FechaHora"], df[col], label=col, alpha=0.7)

        start = df["FechaHora"].iloc[0].replace(hour=0, minute=0)
        end = df["FechaHora"].iloc[-1].replace(hour=23, minute=55)
        rango_dias = (end.date() - start.date()).days + 1
        freq = "3H" if rango_dias <= 3 else "12H"
        ax.set_xlim(start, end)
        ax.set_xticks(pd.date_range(start=start, end=end, freq=freq))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m-%Y %H:%M"))

        ax.set_xlabel("Tiempo")
        ax.set_ylabel("Potencia (MW)")
        ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
        fig.autofmt_xdate(rotation=45)

    # --- Generar gráfico en memoria y renderizar ---
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    buf.seek(0)
    graph_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    buf.close()
    plt.close(fig)

    return render(request, "scrap_graph.html", {"graph": graph_base64})


# -----------------------------
# Vista principal de precios
# -----------------------------
def scrap_precio_view(request):
    context = {
        "data": None,
        "error": None,
        "fecha_inicio": "",
        "fecha_fin": "",
        "total_rows": 0,
        "titulo": "Scraping de Precios OMIE"
    }

    if request.method == "POST":
        fecha_inicio = request.POST.get("fecha_inicio")
        fecha_fin = request.POST.get("fecha_fin")
        context["fecha_inicio"] = fecha_inicio
        context["fecha_fin"] = fecha_fin

        # Validación de fechas
        if not fecha_inicio or not fecha_fin:
            context["error"] = "Por favor, selecciona fecha de inicio y fin."
            return render(request, "scrap_page_precio.html", context)
        try:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
        except ValueError:
            context["error"] = "Formato de fecha no válido."
            return render(request, "scrap_page_precio.html", context)
        if fecha_fin_dt < fecha_inicio_dt:
            context["error"] = "La fecha fin no puede ser anterior a la fecha inicio."
            return render(request, "scrap_page_precio.html", context)

        try:
            df = scrap_rango_precio_omie(fecha_inicio, fecha_fin)

            if df.empty:
                context["error"] = "No se encontraron datos en el rango seleccionado."
            else:
                context["total_rows"] = len(df)

                # Guardar solo columnas necesarias en sesión (sin Timestamp)
                request.session["scrap_data_precio"] = df[["Fecha", "Hora", "PrecioZonaEspañola"]].to_dict("records")

                # Mostrar tabla en la página
                context["data"] = df[["Fecha", "Hora", "PrecioZonaEspañola"]].to_dict("records")

                # Descargar CSV
                if "download_csv" in request.POST:
                    response = HttpResponse(content_type="text/csv")
                    filename = f"Precios_{fecha_inicio}_{fecha_fin}.csv"
                    response["Content-Disposition"] = f'attachment; filename="{filename}"'
                    df.to_csv(path_or_buf=response, index=False, sep=';')
                    return response

        except Exception as e:
            context["error"] = f"Error en el scraping de precios: {e}"

    return render(request, "scrap_page_precio.html", context)


# -----------------------------
# Vista para mostrar gráfico
# -----------------------------
def scrap_graph_precio_view(request):
    data = request.session.get("scrap_data_precio")

    if not data:
        return render(request, "scrap_page_precio.html", {"error": "No hay datos para visualizar."})

    df = pd.DataFrame(data)
    df["FechaHora"] = pd.to_datetime(df["Fecha"] + " " + df["Hora"], format="%d/%m/%Y %H:%M")
    df = df.sort_values("FechaHora")

    # Estadísticas
    max_val = df["PrecioZonaEspañola"].max()
    min_val = df["PrecioZonaEspañola"].min()
    mean_val = df["PrecioZonaEspañola"].mean()
    stats = {
        "max_val": round(max_val, 2),
        "hora_max": df.loc[df["PrecioZonaEspañola"].idxmax(), "FechaHora"].strftime("%d/%m/%Y %H:%M"),
        "min_val": round(min_val, 2),
        "hora_min": df.loc[df["PrecioZonaEspañola"].idxmin(), "FechaHora"].strftime("%d/%m/%Y %H:%M"),
        "mean_val": round(mean_val, 2),
    }

    # Gráfico
    fig, ax = plt.subplots(figsize=(12,5))
    ax.plot(df["FechaHora"], df["PrecioZonaEspañola"], color="blue", marker="o", linestyle="-")

    start = df["FechaHora"].iloc[0].replace(hour=0, minute=0)
    end = df["FechaHora"].iloc[-1].replace(hour=23, minute=55)
    rango_dias = (end.date() - start.date()).days + 1
    freq = "3H" if rango_dias <= 3 else "12H"
    ax.set_xlim(start, end)
    ax.set_xticks(pd.date_range(start=start, end=end, freq=freq))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m-%Y %H:%M"))

    ax.set_xlabel("Tiempo")
    ax.set_ylabel("Precio Zona Española (€/MWh)")
    ax.set_title("Precio OMIE")
    fig.autofmt_xdate(rotation=45)

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    buf.seek(0)
    graph_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    buf.close()
    plt.close(fig)

    return render(request, "scrap_graph_precio.html", {"graph": graph_base64, "stats": stats})
