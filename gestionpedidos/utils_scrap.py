import pandas as pd
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
import requests
import io

def scrap_tabla(fecha: str, url_tipo: int = 1) -> pd.DataFrame:
    """
    Scraping de una tabla para una fecha concreta (yyyy-mm-dd).
    url_tipo: 1 = demanda, 2 = generacion, 4 = almacenamiento
    El nombre de las columnas se toma de la segunda fila de la tabla.
    """
    url = f"https://demanda.ree.es/visiona/peninsula/nacionalau/tablas/{fecha}/{url_tipo}"

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        if url_tipo == 1:
            table_id = "tabla_evolucion"
        elif url_tipo == 2:
            table_id = "tabla_generacion"
        elif url_tipo == 4:
            table_id = "tabla_almacenamiento"

        else:
            browser.close()
            raise ValueError("url_tipo debe ser 1, 2 o 4")

        page.wait_for_selector(f"table#{table_id}", timeout=60000)

        # Cabeceras: segunda fila de la tabla
        headers_row = page.locator(f"table#{table_id} tr").nth(1)
        headers = headers_row.locator("th").all_inner_texts()
        headers = [h.strip() for h in headers]

        # Filas del tbody
        rows_data = []
        rows = page.locator(f"table#{table_id} tbody tr")
        for i in range(rows.count()):
            cols = rows.nth(i).locator("td").all_inner_texts()
            if cols:
                cols_clean = [c.strip() if c.strip() != "" else "0" for c in cols]
                rows_data.append(cols_clean)

        browser.close()

    if not rows_data:
        return pd.DataFrame()

    df = pd.DataFrame(rows_data, columns=headers)

    # Intentar convertir todas las columnas numéricas
    for col in df.columns[1:]:
        df[col] = (
            df[col].str.replace(".", "", regex=False)
                  .str.replace(",", ".", regex=False)
                  .replace("", "0")
        )
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Si hay columna Hora, convertir
    if "Hora" in df.columns:
        df["Hora"] = pd.to_datetime(df["Hora"], errors="coerce")
        if not df["Hora"].isnull().all():
            df["Fecha"] = df["Hora"].dt.strftime("%d/%m/%Y")
            df["Hora"] = df["Hora"].dt.strftime("%H:%M")
            df = df[["Fecha", "Hora"] + [c for c in df.columns if c not in ["Fecha", "Hora"]]]

    return df


def scrap_rango(fecha_inicio: str, fecha_fin: str, url_tipo: int = 1) -> pd.DataFrame:
    """
    Scrapea todas las fechas entre fecha_inicio y fecha_fin (yyyy-mm-dd)
    y filtra solo las filas dentro del rango exacto.
    """
    start_date = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
    end_date = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

    all_data = []
    day = start_date
    while day <= end_date:
        df_day = scrap_tabla(day.strftime("%Y-%m-%d"), url_tipo=url_tipo)
        if not df_day.empty:
            # Filtrar por Fecha si existe
            if "Fecha" in df_day.columns:
                df_day["Fecha_dt"] = pd.to_datetime(df_day["Fecha"], format="%d/%m/%Y", errors="coerce").dt.date
                mask = (df_day["Fecha_dt"] >= start_date) & (df_day["Fecha_dt"] <= end_date)
                df_day = df_day.loc[mask].drop(columns=["Fecha_dt"])
            if not df_day.empty:
                all_data.append(df_day)
        day += timedelta(days=1)

    if not all_data:
        return pd.DataFrame()

    return pd.concat(all_data, ignore_index=True).reset_index(drop=True)


def scrap_rango_precio_omie(fecha_inicio, fecha_fin):
    """
    Descarga los archivos de OMIE para un rango de fechas y devuelve un DataFrame
    con columnas: Fecha (dd/mm/aaaa), Hora (HH:MM), PrecioZonaEspañola (float).
    """
    df_total = pd.DataFrame()
    fechas = pd.date_range(fecha_inicio, fecha_fin)

    for fecha in fechas:
        fecha_str = fecha.strftime("%Y%m%d")
        url = f"https://www.omie.es/es/file-download?parents=marginalpdbc&filename=marginalpdbc_{fecha_str}.1"
        print(f"\n[DEBUG] Intentando descargar URL: {url}")

        try:
            resp = requests.get(url)
            print(f"[DEBUG] Estado HTTP: {resp.status_code} para fecha {fecha_str}")
            resp.raise_for_status()

            contenido = resp.text.splitlines()
            if contenido and contenido[0].startswith("MARGINALPDBC;"):
                contenido = contenido[1:]
                print(f"[DEBUG] Primera línea 'MARGINALPDBC;' eliminada")

            if not contenido:
                print(f"[DEBUG] No hay datos para la fecha {fecha_str}")
                continue

            df = pd.read_csv(io.StringIO("\n".join(contenido)), sep=';', header=None)

            # Eliminar columnas completamente vacías
            df = df.dropna(axis=1, how='all')

            # Comprobar que hay al menos 6 columnas
            if df.shape[1] < 6:
                print(f"[ERROR] CSV de {fecha_str} tiene menos de 6 columnas, se salta")
                continue

            # Asignar nombres correctos
            df.columns = ["Año", "Mes", "Día", "Periodo", "PrecioZonaPortuguesa", "PrecioZonaEspañola"]

            # Si PrecioZonaEspañola está vacío, usar PrecioZonaPortuguesa
            df["PrecioZonaEspañola"] = df["PrecioZonaEspañola"].fillna(df["PrecioZonaPortuguesa"])

            # Convertir PrecioZonaEspañola a float
            df["PrecioZonaEspañola"] = pd.to_numeric(df["PrecioZonaEspañola"], errors='coerce')

            # Convertir Periodo a entero y crear columna Hora
            df["Periodo"] = pd.to_numeric(df["Periodo"], errors='coerce')
            df = df.dropna(subset=["Periodo"])
            df["Hora"] = df["Periodo"].astype(int).apply(lambda x: f"{x-1:02d}:00")

            # Crear columna Fecha en formato dd/mm/aaaa
            df["Fecha"] = df.apply(lambda row: f"{int(row['Día']):02d}/{int(row['Mes']):02d}/{int(row['Año'])}", axis=1)

            # Seleccionar columnas finales
            df = df[["Fecha", "Hora", "PrecioZonaEspañola"]]

            df_total = pd.concat([df_total, df], ignore_index=True)
            print(f"[DEBUG] Filas acumuladas hasta ahora: {len(df_total)}")

        except Exception as e:
            print(f"[ERROR] No se pudo procesar {fecha_str}: {e}")

    # Ordenar por Fecha y Hora
    if not df_total.empty:
        df_total = df_total.sort_values(["Fecha", "Hora"]).reset_index(drop=True)

    print(f"[DEBUG] DataFrame final listo con {len(df_total)} filas")
    return df_total
