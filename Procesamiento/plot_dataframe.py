# -*- coding: utf-8 -*-
"""
Graficador de series temporales con múltiples vistas
- Primera columna: fechas/tiempos
- Segunda columna: valores numéricos
Crea: línea, barras, área, dispersión, boxplot por mes y heatmap temporal.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# =========================
# Parámetros de entrada
# =========================
# Opción A: leer desde CSV (descomenta y pone tu ruta)
CSV_PATH = None  # p.ej.: r"datos/serie.csv"

# Opción B: si ya tienes un DataFrame en memoria llamado `df`,
# deja CSV_PATH=None y el script usará `df` directamente.
# Se espera que df tenga dos columnas: [fecha, valor]

# =========================
# Funciones utilitarias
# =========================

def cargar_datos(csv_path=None, df=None):
    """
    Carga datos ya sea desde CSV o usa un DataFrame dado.
    Asume: 1ra columna = fecha/tiempo, 2da columna = valor.
    """
    if csv_path is not None:
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"No se encontró el archivo: {csv_path}")
        tmp = pd.read_csv(csv_path)
    else:
        if df is None:
            raise ValueError("Proporciona CSV_PATH o un DataFrame `df` con dos columnas.")
        tmp = df.copy()

    if tmp.shape[1] < 2:
        raise ValueError("Se requieren al menos 2 columnas: tiempo y valor.")

    # Renombrar de forma estándar
    tmp = tmp.iloc[:, :2].copy()
    tmp.columns = ["fecha", "valor"]

    # Parse de fechas
    tmp["fecha"] = pd.to_datetime(tmp["fecha"], errors="coerce")
    # Limpiar filas con fecha no válida
    tmp = tmp.dropna(subset=["fecha"])
    # Convertir valor a numérico
    tmp["valor"] = pd.to_numeric(tmp["valor"], errors="coerce")
    tmp = tmp.dropna(subset=["valor"])

    # Ordenar por tiempo
    tmp = tmp.sort_values("fecha").reset_index(drop=True)

    return tmp


def hay_componente_hora(series_fechas: pd.Series) -> bool:
    """
    Retorna True si hay componente horario (no todos los tiempos están a medianoche).
    """
    # Si la parte de hora/min/seg no es todo cero, asumimos que hay componente horario
    return not ((series_fechas.dt.hour == 0) &
                (series_fechas.dt.minute == 0) &
                (series_fechas.dt.second == 0)).all()


def preparar_dimensiones_temporales(df: pd.DataFrame):
    """
    Agrega columnas auxiliares de tiempo: año, mes, día de semana, hora.
    """
    out = df.copy()
    out["anio"] = out["fecha"].dt.year
    out["mes"] = out["fecha"].dt.month
    out["mes_nombre"] = out["fecha"].dt.month_name(locale="es_ES").str.capitalize() \
                        if hasattr(out["fecha"].dt, "month_name") else out["mes"].astype(str)
    out["dow"] = out["fecha"].dt.dayofweek  # 0=Lunes
    out["dow_nombre"] = out["fecha"].dt.day_name(locale="es_ES").str.capitalize() \
                        if hasattr(out["fecha"].dt, "day_name") else out["dow"].astype(str)
    out["hora"] = out["fecha"].dt.hour
    return out


def plot_todos(df: pd.DataFrame, titulo_base: str = "Serie temporal"):
    """
    Genera todas las gráficas: línea, barras, área, dispersión,
    boxplot por mes, heatmap temporal (dow×hora o año×mes).
    """
    # Configuración general
    sns.set(style="whitegrid")
    plt.rcParams["axes.titlesize"] = 12
    plt.rcParams["axes.labelsize"] = 10

    # -------- 1) LÍNEA --------
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["fecha"], df["valor"], color="#1f77b4", linewidth=1.8)
    ax.set_title(f"{titulo_base} - Línea")
    ax.set_xlabel("Tiempo")
    ax.set_ylabel("Valor")
    fig.autofmt_xdate()
    plt.tight_layout()

    # -------- 2) BARRAS --------
    # Útil cuando la frecuencia es discreta (mes, día, etc.)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(df["fecha"], df["valor"], color="#2ca02c", width=0.8)
    ax.set_title(f"{titulo_base} - Barras")
    ax.set_xlabel("Tiempo")
    ax.set_ylabel("Valor")
    fig.autofmt_xdate()
    plt.tight_layout()

    # -------- 3) ÁREA --------
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.fill_between(df["fecha"], df["valor"], step="pre", alpha=0.3, color="#ff7f0e")
    ax.plot(df["fecha"], df["valor"], color="#ff7f0e", linewidth=1.5)
    ax.set_title(f"{titulo_base} - Área")
    ax.set_xlabel("Tiempo")
    ax.set_ylabel("Valor")
    fig.autofmt_xdate()
    plt.tight_layout()

    # -------- 4) DISPERSIÓN --------
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.scatter(df["fecha"], df["valor"], s=20, alpha=0.7, color="#9467bd")
    ax.set_title(f"{titulo_base} - Dispersión")
    ax.set_xlabel("Tiempo")
    ax.set_ylabel("Valor")
    fig.autofmt_xdate()
    plt.tight_layout()

    # Preparar columnas temporales
    dft = preparar_dimensiones_temporales(df)

    # -------- 5) BOXPLOT POR MES (agregado por mes) --------
    # Si hay múltiples observaciones por mes, esto muestra distribución.
    fig, ax = plt.subplots(figsize=(10, 4))
    order_meses = [1,2,3,4,5,6,7,8,9,10,11,12]
    sns.boxplot(
        data=dft,
        x="mes",
        y="valor",
        order=order_meses,
        ax=ax,
        color="#8c564b"
    )
    ax.set_title(f"{titulo_base} - Boxplot por mes")
    ax.set_xlabel("Mes")
    ax.set_ylabel("Valor")
    ax.set_xticklabels([ "Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic" ])
    plt.tight_layout()

    # -------- 6) HEATMAP TEMPORAL --------
    # Si hay componente horario, usamos DíaSemana×Hora; si no, Año×Mes.
    if hay_componente_hora(df["fecha"]):
        # Promedio por (día de semana, hora)
        piv = dft.pivot_table(index="dow", columns="hora", values="valor", aggfunc="mean")
        # Reordenar días L->D
        piv = piv.reindex([0,1,2,3,4,5,6])
        fig, ax = plt.subplots(figsize=(12, 4))
        sns.heatmap(piv, cmap="YlOrRd", ax=ax, cbar_kws={"label": "Valor medio"})
        ax.set_title(f"{titulo_base} - Heatmap (Día de semana × Hora)")
        ax.set_xlabel("Hora del día")
        ax.set_ylabel("Día de la semana")
        ax.set_yticklabels(["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"], rotation=0)
        plt.tight_layout()
    else:
        # Promedio por (año, mes)
        piv = dft.pivot_table(index="anio", columns="mes", values="valor", aggfunc="mean")
        # Asegurar 12 columnas (1-12)
        piv = piv.reindex(columns=range(1,13))
        fig, ax = plt.subplots(figsize=(12, 4))
        sns.heatmap(piv, cmap="YlGnBu", ax=ax, cbar_kws={"label": "Valor medio"})
        ax.set_title(f"{titulo_base} - Heatmap (Año × Mes)")
        ax.set_xlabel("Mes")
        ax.set_ylabel("Año")
        ax.set_xticklabels([ "Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic" ], rotation=0)
        plt.tight_layout()

    plt.show()


