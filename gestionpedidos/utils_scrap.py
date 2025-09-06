# utils_scrap.py
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta

def _parse_table_from_html(html):
    """
    Extrae la tabla #tabla_evolucion del HTML y devuelve un DataFrame
    con la columna 'Hora' original parseada a datetime en 'Hora_dt'.
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"id": "tabla_evolucion"})
    if table is None:
        raise RuntimeError("No se encontró la tabla 'tabla_evolucion' en el HTML")

    all_rows = table.find_all("tr")
    if len(all_rows) < 2:
        raise RuntimeError("La tabla no contiene filas suficientes")

    # La segunda fila contiene los nombres de columna reales
    headers = [cell.get_text(strip=True) for cell in all_rows[1].find_all(["th", "td"])]

    # Filas de datos (a partir de la tercera fila)
    data_rows = []
    for tr in all_rows[2:]:
        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        if cells:  # evitar filas vacías
            data_rows.append(cells)

    df = pd.DataFrame(data_rows, columns=headers)

    # Conversión de columnas numéricas (si existen)
    numeric_candidates = ["Real", "Prevista", "Programada"]
    for col in numeric_candidates:
        if col in df.columns:
            # quitamos separador de miles y normalizamos coma decimal
            df[col] = df[col].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Parse de la columna 'Hora' a datetime (columna auxiliar 'Hora_dt')
    if "Hora" not in df.columns:
        raise RuntimeError("La tabla no contiene la columna 'Hora' esperada")
    # pd.to_datetime sin formato explícito es más tolerante si vienen zonas/segundos
    df["Hora_dt"] = pd.to_datetime(df["Hora"], errors="coerce")

    # Eliminamos filas donde no se pudo parsear la hora
    df = df.dropna(subset=["Hora_dt"]).copy()

    return df

def scrap_rango(fecha_inicio, fecha_fin):
    """
    Scrapea todas las páginas entre fecha_inicio y fecha_fin (YYYY-MM-DD, inclusive),
    concatena los resultados y filtra por la fecha (parte fecha de Hora_dt) para que
    sólo queden filas entre fecha_inicio y fecha_fin.
    Devuelve un DataFrame con:
        ['Fecha' (dd/mm/aaaa), 'Hora' (HH:MM), <otras columnas numéricas>...]
    """
    inicio_date = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
    fin_date = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

    if inicio_date > fin_date:
        raise ValueError("fecha_inicio debe ser anterior o igual a fecha_fin")

    collected = []

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()

        # Recorremos día a día
        fecha = inicio_date
        while fecha <= fin_date:
            date_str = fecha.strftime("%Y-%m-%d")
            url = f"https://demanda.ree.es/visiona/peninsula/nacionalau/tablas/{date_str}/1"
            try:
                page.goto(url)
                # esperamos que aparezca la tabla (timeout en ms)
                page.wait_for_selector("#tabla_evolucion", timeout=15000)
                html = page.content()
                df_day = _parse_table_from_html(html)
                collected.append(df_day)
            except Exception as e:
                # imprimimos el error y seguimos con la siguiente fecha
                print(f"⚠️ Error al scrapear {date_str}: {e}")
            fecha = fecha + timedelta(days=1)

        browser.close()

    if not collected:
        return pd.DataFrame()

    # Concatenamos todos los días
    df = pd.concat(collected, ignore_index=True)

    # Filtramos por la parte fecha de Hora_dt: solo filas cuyo date esté en el rango solicitado
    df["Fecha_dt"] = df["Hora_dt"].dt.date
    mask = (df["Fecha_dt"] >= inicio_date) & (df["Fecha_dt"] <= fin_date)
    df = df.loc[mask].copy()

    # Formateamos las columnas finales: Fecha dd/mm/aaaa y Hora HH:MM
    df["Fecha"] = df["Hora_dt"].dt.strftime("%d/%m/%Y")
    df["Hora"] = df["Hora_dt"].dt.strftime("%H:%M")

    # Orden cronológico por Hora_dt (asegura orden correcto entre días)
    df = df.sort_values(by=["Hora_dt"]).reset_index(drop=True)

    # Eliminamos columnas auxiliares y dejamos las importantes
    df = df.drop(columns=["Hora_dt", "Fecha_dt"], errors="ignore")

    # Reordenamos: Fecha, Hora, resto de columnas (si existen)
    cols = df.columns.tolist()
    # sacar Fecha y Hora si están dentro
    if "Fecha" in cols:
        cols.remove("Fecha")
    if "Hora" in cols:
        cols.remove("Hora")
    df = df[["Fecha", "Hora"] + cols]

    return df

def scrap_tabla(fecha):
    """
    Compatibilidad: scrappear un solo día llamando a scrap_rango(fecha, fecha)
    """
    return scrap_rango(fecha, fecha)
