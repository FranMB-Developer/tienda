# utils_scrap.py
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta

def scrap_tabla(fecha):
    """
    Scrapea los datos de un único día (fecha en formato YYYY-MM-DD).
    Devuelve un DataFrame con las columnas ['Hora', 'Real', 'Prevista', 'Programada'].
    """
    url = f"https://demanda.ree.es/visiona/peninsula/nacionalau/tablas/{fecha}/1"

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector("#tabla_evolucion")
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"id": "tabla_evolucion"})
    all_rows = table.find_all("tr")

    # Cabeceras reales (segunda fila)
    column_headers = [cell.get_text(strip=True) for cell in all_rows[1].find_all(["th","td"])]

    # Filas de datos
    data_rows = []
    for tr in all_rows[2:]:
        cells = [td.get_text(strip=True) for td in tr.find_all(["td","th"])]
        data_rows.append(cells)

    df = pd.DataFrame(data_rows, columns=column_headers)

    # Limpieza
    for col in ["Real", "Prevista", "Programada"]:
        df[col] = df[col].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df["Hora"] = pd.to_datetime(df["Hora"], format="%Y-%m-%d %H:%M")
    df["Fecha"] = fecha  # añadimos la fecha como columna auxiliar

    return df

def scrap_rango(fecha_inicio, fecha_fin):
    """
    Scrapea datos desde fecha_inicio hasta fecha_fin (ambas inclusive).
    """
    inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fin = datetime.strptime(fecha_fin, "%Y-%m-%d")

    todos = []
    fecha = inicio
    while fecha <= fin:
        try:
            df = scrap_tabla(fecha.strftime("%Y-%m-%d"))
            todos.append(df)
        except Exception as e:
            print(f"⚠️ Error en {fecha.date()}: {e}")
        fecha += timedelta(days=1)

    if todos:
        return pd.concat(todos, ignore_index=True)
    else:
        return pd.DataFrame()
