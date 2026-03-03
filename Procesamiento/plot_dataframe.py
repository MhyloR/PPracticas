# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Optional, Union

def preparar_largo_desde_lista(
    dfs: List[pd.DataFrame],
    x_col: str = "fecha",
    y_cols: Optional[List[str]] = None,   # si None: intenta ['valor'] o detecta numéricas
    label_col: Optional[str] = None,      # si None: se creará un label por DF (DF1, DF2,...)
    max_series: int = 5
) -> pd.DataFrame:
    """
    Convierte una lista de DataFrames a un DF "largo" con columnas: [fecha, valor, serie].
    - Si y_cols tiene varias columnas, cada una se vuelve una serie separada por DF.
    - Si label_col existe, se usa como nombre de serie; si no, se crea TIPO DF{i}/col.
    - Limita a `max_series` series (para evitar saturación visual).
    """
    largos = []
    serie_count = 0

    for i, df in enumerate(dfs, start=1):
        if df is None or df.empty:
            continue
        tmp = df.copy()

        # Asegurar x_col como datetime si existe
        if x_col in tmp.columns:
            tmp[x_col] = pd.to_datetime(tmp[x_col], errors="coerce")
            tmp = tmp.dropna(subset=[x_col]).sort_values(x_col)
        else:
            # Si no hay x_col, usamos un índice numérico convertido a fechas relativas
            # (no ideal para calendario, pero permite graficar).
            tmp = tmp.reset_index(drop=True)
            tmp[x_col] = pd.to_datetime(np.arange(len(tmp)), unit="D", origin="2025-01-01")

        # Determinar columnas de valor
        if y_cols is None:
            if "valor" in tmp.columns:
                cols_val = ["valor"]
            else:
                cols_val = [c for c in tmp.columns if c != x_col and pd.api.types.is_numeric_dtype(tmp[c])]
        else:
            cols_val = [c for c in y_cols if c in tmp.columns and c != x_col]

        if not cols_val:
            continue

        # Armar "largo": (fecha, valor, serie)
        if label_col and (label_col in tmp.columns):
            # Una serie por unique(label) por cada columna en cols_val
            for col in cols_val:
                sub = tmp[[x_col, col, label_col]].dropna()
                if sub.empty: 
                    continue
                sub = sub.rename(columns={x_col: "fecha", col: "valor", label_col: "serie"})
                # 1 serie por valor único en 'serie'
                for s in sub["serie"].unique():
                    parte = sub[sub["serie"] == s][["fecha", "valor"]].copy()
                    parte["serie"] = str(s)
                    largos.append(parte)
                    serie_count += 1
                    if serie_count >= max_series:
                        break
                if serie_count >= max_series:
                    break
        else:
            # Sin label: crea una serie por cada col de valor y por cada DF
            for col in cols_val:
                sub = tmp[[x_col, col]].dropna()
                if sub.empty:
                    continue
                parte = sub.rename(columns={x_col: "fecha", col: "valor"})
                parte["serie"] = f"DF{i}/{col}"
                largos.append(parte[["fecha", "valor", "serie"]])
                serie_count += 1
                if serie_count >= max_series:
                    break

        if serie_count >= max_series:
            break

    if not largos:
        raise ValueError("No se encontraron series válidas para graficar.")

    largo = pd.concat(largos, ignore_index=True)
    # Agregar seguridad por si hay duplicados por fecha/serie
    largo = (
        largo.groupby(["fecha", "serie"], as_index=False)["valor"]
        .mean()
        .sort_values("fecha")
    )
    return largo


def plot_series_desde_lista(
    dfs: List[pd.DataFrame],
    x_col: str = "fecha",
    y_cols: Optional[List[str]] = None,
    label_col: Optional[str] = None,
    titulo: str = "Comparación de series",
    unidad: str = "",
    normalizar: bool = False,
    apilado: bool = False,  # True=área apilada, False=líneas superpuestas
    max_series: int = 5,
    figsize=(12, 6)
):
    """
    Lee una lista de DataFrames y grafica hasta 5 series en una sola figura (plt/sns).
    - apilado=True: área apilada (stackplot).
    - apilado=False: líneas superpuestas.
    - normalizar=True: normaliza cada serie a [0,1].
    Muestra inmediatamente (no guarda).
    """
    sns.set(style="whitegrid")
    largo = preparar_largo_desde_lista(
        dfs, x_col=x_col, y_cols=y_cols, label_col=label_col, max_series=max_series
    )

    # Normalizar si aplica (por serie)
    if normalizar:
        largo["valor"] = largo.groupby("serie")["valor"].transform(
            lambda s: (s - s.min()) / (s.max() - s.min()) if s.max() != s.min() else 0.0
        )

    fig, ax = plt.subplots(figsize=figsize)

    if apilado:
        # Pivot para stackplot (área apilada)
        piv = largo.pivot(index="fecha", columns="serie", values="valor").sort_index().fillna(0.0)
        x = piv.index
        ys = piv.values.T  # shape: (n_series, n_points)
        labels = piv.columns.tolist()
        ax.stackplot(x, ys, labels=labels, alpha=0.85)
    else:
        # Líneas superpuestas
        for serie, sub in largo.groupby("serie"):
            sub = sub.sort_values("fecha")
            ax.plot(sub["fecha"], sub["valor"], label=str(serie), linewidth=2)

    # Títulos y ejes
    ax.set_title(titulo + (" (normalizado)" if normalizar else ""), fontsize=15)
    ax.set_xlabel("Tiempo")
    ax.set_ylabel(f"Valor {unidad}".strip())
    ax.legend(ncol=2, frameon=True, fontsize=9)
    fig.autofmt_xdate()
    plt.tight_layout()
    plt.show()
