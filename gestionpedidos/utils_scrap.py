# utils_scrap.py
import pandas as pd
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright


def scrap_tabla(fecha: str) -> pd.DataFrame:
    """
    Scraping de la tabla de demanda para una fecha concreta (yyyy-mm-dd).
    Devuelve columnas: Fecha (dd/mm/aaaa), Hora (HH:MM), Real, Prevista, Programada
    """
    url = f"https://demanda.ree.es/visiona/peninsula/nacionalau/tablas/{fecha}/1"

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_selector("table#tabla_evolucion", timeout=60000)

        # ✅ Cabeceras fijas conocidas
        headers = ["Hora", "Real", "Prevista", "Programada"]

        # ✅ Filas del tbody
        rows_data = []
        rows = page.locator("table#tabla_evolucion tbody tr")
        for i in range(rows.count()):
            cols = rows.nth(i).locator("td").all_inner_texts()
            if cols:
                rows_data.append([c.strip() for c in cols])

        browser.close()

    if not rows_data:
        return pd.DataFrame()

    df = pd.DataFrame(rows_data, columns=headers)

    # Conversión de columnas numéricas
    for col in ["Real", "Prevista", "Programada"]:
        df[col] = (
            df[col]
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .replace("", None)
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Convertimos Hora y separamos Fecha
    df["Hora"] = pd.to_datetime(df["Hora"], errors="coerce")
    if df["Hora"].isnull().all():
        return pd.DataFrame()

    df["Fecha"] = df["Hora"].dt.strftime("%d/%m/%Y")
    df["Hora"] = df["Hora"].dt.strftime("%H:%M")

    return df[["Fecha", "Hora", "Real", "Prevista", "Programada"]]


def scrap_rango(fecha_inicio: str, fecha_fin: str) -> pd.DataFrame:
    """
    Scrapea todas las fechas entre fecha_inicio y fecha_fin (formato yyyy-mm-dd).
    Filtra para quedarse solo con filas dentro del rango exacto de fechas.
    """
    start_date = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
    end_date = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

    all_data = []
    day = start_date
    while day <= end_date:
        df_day = scrap_tabla(day.strftime("%Y-%m-%d"))
        if not df_day.empty:
            # Convertimos la columna Fecha a tipo date para filtrar
            df_day["Fecha_dt"] = pd.to_datetime(
                df_day["Fecha"], format="%d/%m/%Y", errors="coerce"
            ).dt.date

            mask = (df_day["Fecha_dt"] >= start_date) & (df_day["Fecha_dt"] <= end_date)
            df_day = df_day.loc[mask].drop(columns=["Fecha_dt"])

            if not df_day.empty:
                all_data.append(df_day)
        day += timedelta(days=1)

    if not all_data:
        return pd.DataFrame()

    return pd.concat(all_data, ignore_index=True).reset_index(drop=True)


