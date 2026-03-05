# -*- coding: utf-8 -*-
from __future__ import annotations
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Optional, Tuple, Dict, Any

# =========================
# Helpers internos
# =========================

def _parse_col_fecha(
    df: pd.DataFrame,
    x_col: str,
    *,
    date_format: Optional[str],
    dayfirst: bool,
    strict_parse: bool,
    sintetizar_si_no_hay_fecha: bool,
    sintetico_origen: str
) -> Tuple[pd.DataFrame, str]:
    """
    Devuelve (df_con_fecha_parseada, nombre_col_fecha).
    Si x_col no existe, intenta con la primera columna.
    Si no puede parsear y se permite sintetizar, crea una secuencia diaria.
    """
    if df is None or df.empty:
        return df, x_col

    tmp = df.copy()
    errors_mode = "raise" if strict_parse else "coerce"

    if x_col in tmp.columns:
        col = x_col
    else:
        col = tmp.columns[0]  # fallback a primera columna

    try:
        tmp[col] = pd.to_datetime(tmp[col], format=date_format, dayfirst=dayfirst, errors=errors_mode)
    except Exception as e:
        if not sintetizar_si_no_hay_fecha:
            raise ValueError(
                f"No existe '{x_col}' o no se pudo parsear la columna '{col}' como fecha: {e}\n"
                "Sugerencia: indica 'x_col' correcto o provee 'date_format' adecuado; "
                "si quieres inventar fechas, activa sintetizar_si_no_hay_fecha=True."
            )
        # Sintetizar fechas (no recomendado salvo debugging)
        tmp = tmp.reset_index(drop=True)
        base = pd.to_datetime(sintetico_origen)
        tmp[col] = base + pd.to_timedelta(np.arange(len(tmp)), unit="D")

    # Quitar NAs en la fecha
    tmp = tmp.dropna(subset=[col])

    return tmp, col


def _obtener_cols_valor(
    df: pd.DataFrame,
    fecha_col_name: str,
    y_cols: Optional[List[str]]
) -> List[str]:
    """Determina columnas 'valor' automáticamente si y_cols es None."""
    if y_cols is None:
        if "valor" in df.columns:
            return ["valor"]
        # Todas las numéricas excepto la fecha
        return [c for c in df.columns if c != fecha_col_name and pd.api.types.is_numeric_dtype(df[c])]
    else:
        return [c for c in y_cols if c in df.columns and c != fecha_col_name]


def _normalizar_minmax_por_serie(largo: pd.DataFrame) -> pd.DataFrame:
    """Normaliza valor a [0,1] por serie (min-max). Si rango=0, pone 0."""
    def _scale(g: pd.DataFrame) -> pd.DataFrame:
        vmin, vmax = g["valor"].min(), g["valor"].max()
        rng = vmax - vmin
        if rng == 0 or not np.isfinite(rng):
            g["valor"] = 0.0
        else:
            g["valor"] = (g["valor"] - vmin) / rng
        return g
    return largo.groupby("serie", group_keys=False).apply(_scale)


# =========================
# Núcleo de preparación
# =========================

def preparar_largo_desde_lista(
    dfs: List[pd.DataFrame],
    x_col: str = "fecha",
    y_cols: Optional[List[str]] = None,
    label_col: Optional[str] = None,
    max_series: int = 5,
    sintetizar_si_no_hay_fecha: bool = False,
    sintetico_origen: str = "1970-01-01",
    date_format: Optional[str] = None,
    dayfirst: bool = False,
    strict_parse: bool = True,
    *,
    verbose: bool = True,
    retornar_diag: bool = False
) -> pd.DataFrame | Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Convierte una lista de DataFrames a formato largo [fecha, valor, serie].
    - Si no encuentra x_col, usa la PRIMERA COLUMNA como fecha (sin inventar, salvo que se autorice).
    - Limita a max_series para evitar saturación.
    - Si label_col existe en el DF, conserva el comportamiento original: para cada col de valor, 
      se agregan registros bajo el MISMO nombre de serie proveniente de label_col (potencial colisión intencional).
    Retorna:
      - largo o (largo, diag) si retornar_diag=True.
    """
    largos: List[pd.DataFrame] = []
    serie_count = 0

    for i, df in enumerate(dfs, start=1):
        if df is None or df.empty:
            continue

        tmp, fecha_col_name = _parse_col_fecha(
            df, x_col,
            date_format=date_format,
            dayfirst=dayfirst,
            strict_parse=strict_parse,
            sintetizar_si_no_hay_fecha=sintetizar_si_no_hay_fecha,
            sintetico_origen=sintetico_origen
        )

        cols_val = _obtener_cols_valor(tmp, fecha_col_name, y_cols)
        if not cols_val:
            continue

        # -------- Rama con label_col ----------
        if label_col and (label_col in tmp.columns):
            # Conservamos semántica original: cada columna de valor se vuelca bajo el mismo nombre de serie=label
            # Esto colapsa múltiples columnas en la misma etiqueta; es intencional por compatibilidad.
            for col in cols_val:
                sub = tmp[[fecha_col_name, col, label_col]].dropna(subset=[fecha_col_name, col, label_col])
                if sub.empty:
                    continue
                sub = sub.rename(columns={fecha_col_name: "fecha", col: "valor", label_col: "serie"})
                # Cast a string para estabilidad en leyendas
                sub["serie"] = sub["serie"].astype(str)
                largos.append(sub[["fecha", "valor", "serie"]])
                serie_count += sub["serie"].nunique()
                if serie_count >= max_series:
                    break
        else:
            # Sin label_col: cada columna de valor es una serie distinta
            for col in cols_val:
                sub = tmp[[fecha_col_name, col]].dropna(subset=[fecha_col_name, col])
                if sub.empty:
                    continue
                parte = sub.rename(columns={fecha_col_name: "fecha", col: "valor"})
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

    # Agregado por duplicados exactos (fecha, serie)
    largo = (largo
             .groupby(["fecha", "serie"], as_index=False, sort=False)["valor"].mean()
             .sort_values("fecha"))

    # Diagnóstico (opcional)
    diag = (largo.groupby("serie")["fecha"]
            .agg(fecha_min="min", fecha_max="max", n="count")
            .reset_index())

    if verbose:
        try:
            with pd.option_context("display.max_rows", None, "display.width", 120):
                print("Diagnóstico de fechas por serie:")
                print(diag.to_string(index=False))
        except Exception:
            print("Diagnóstico de fechas por serie:")
            print(diag)

    return (largo, diag) if retornar_diag else largo


# =========================
# Visualizaciones
# =========================

def _plot_lineas_desde_largo(
    largo: pd.DataFrame,
    *,
    titulo: str = "Comparación de series",
    unidad: str = "",
    normalizar: bool = False,
    figsize: Tuple[int, int] = (12, 6)
) -> Tuple[plt.Figure, plt.Axes]:
    """Dibuja líneas superpuestas desde un DF largo estándar."""
    sns.set(style="whitegrid")

    data = largo.copy()
    if normalizar:
        data = _normalizar_minmax_por_serie(data)

    fig, ax = plt.subplots(figsize=figsize)

    for serie, sub in data.groupby("serie", sort=False):
        sub = sub.sort_values("fecha")
        ax.plot(sub["fecha"], sub["valor"], label=str(serie), linewidth=2)

    xmin, xmax = data["fecha"].min(), data["fecha"].max()
    ax.set_xlim(left=xmin, right=xmax)

    ax.set_title(titulo + (" (normalizado)" if normalizar else ""), fontsize=15)
    ax.set_xlabel("Tiempo")
    ax.set_ylabel(f"Valor {unidad}".strip())
    ax.legend(ncol=2, frameon=True, fontsize=9)
    fig.autofmt_xdate()
    plt.tight_layout()
    return fig, ax


def plot_series_desde_lista(
    dfs: List[pd.DataFrame],
    x_col: str = "fecha",
    y_cols: Optional[List[str]] = None,
    label_col: Optional[str] = None,
    titulo: str = "Comparación de series",
    unidad: str = "",
    normalizar: bool = False,
    apilado: bool = False,
    max_series: int = 5,
    figsize: Tuple[int, int] = (12, 6),
    sintetizar_si_no_hay_fecha: bool = False,
    sintetico_origen: str = "1970-01-01",
    date_format: Optional[str] = None,
    dayfirst: bool = False,
    strict_parse: bool = True,
    *,
    verbose: bool = True,
    retornar_diag: bool = False
) -> Tuple[plt.Figure, plt.Axes, pd.DataFrame, Optional[pd.DataFrame]]:
    """
    Lee lista de DFs, prepara largo y grafica (líneas o área apilada).
    Devuelve (fig, ax, largo, diag_opcional).
    """
    largo, diag = preparar_largo_desde_lista(
        dfs, x_col=x_col, y_cols=y_cols, label_col=label_col, max_series=max_series,
        sintetizar_si_no_hay_fecha=sintetizar_si_no_hay_fecha,
        sintetico_origen=sintetico_origen,
        date_format=date_format,
        dayfirst=dayfirst,
        strict_parse=strict_parse,
        verbose=verbose,
        retornar_diag=True
    )

    sns.set(style="whitegrid")
    fig, ax = plt.subplots(figsize=figsize)

    data = largo.copy()
    if apilado:
        # Área apilada (normalizar=True NO hace stacking porcentual; conserva magnitudes)
        piv = data.pivot(index="fecha", columns="serie", values="valor").sort_index().fillna(0.0)
        if normalizar:
            # Normalización min-max por serie (columna)
            piv = (piv - piv.min()) / (piv.max() - piv.min()).replace({0.0: np.nan}).fillna(0.0)
        x = piv.index
        ys = piv.values.T
        labels = list(piv.columns.astype(str))
        ax.stackplot(x, *ys, labels=labels, alpha=0.85)
    else:
        # Líneas superpuestas
        if normalizar:
            data = _normalizar_minmax_por_serie(data)
        for serie, sub in data.groupby("serie", sort=False):
            sub = sub.sort_values("fecha")
            ax.plot(sub["fecha"], sub["valor"], label=str(serie), linewidth=2)

    xmin, xmax = data["fecha"].min(), data["fecha"].max()
    ax.set_xlim(left=xmin, right=xmax)

    ax.set_title(titulo + (" (normalizado)" if normalizar else ""), fontsize=15)
    ax.set_xlabel("Tiempo")
    ax.set_ylabel(f"Valor {unidad}".strip())
    ax.legend(ncol=2, frameon=True, fontsize=9)
    fig.autofmt_xdate()
    plt.tight_layout()

    if retornar_diag:
        return fig, ax, largo, diag
    return fig, ax, largo, None


def _plot_boxplot_mensual_desde_largo(
    largo: pd.DataFrame,
    unidad: str = "",
    titulo: str = "Distribución mensual (boxplot) de valores",
    showfliers: bool = False,
    figsize: Tuple[int, int] = (12, 5)
) -> Tuple[plt.Figure, plt.Axes]:
    """Boxplot por mes a partir de 'fecha' y 'valor'."""
    df = largo.copy().dropna(subset=["fecha", "valor"])
    if df.empty:
        raise ValueError("No hay datos para boxplot mensual.")
    df["Mes"] = pd.to_datetime(df["fecha"]).dt.to_period("M").dt.to_timestamp()

    orden = sorted(df["Mes"].dropna().unique().tolist())
    fig, ax = plt.subplots(figsize=figsize)
    sns.boxplot(ax=ax, data=df, x="Mes", y="valor", order=orden, whis=1.5, showfliers=showfliers)
    for label in ax.get_xticklabels():
        label.set_rotation(90)
    ax.set_title(titulo)
    ax.set_xlabel("Mes")
    ax.set_ylabel(f"Valor {unidad}".strip())
    plt.tight_layout()
    return fig, ax


def plot_inteligente(
    dfs: List[pd.DataFrame],
    x_col: str = "fecha",
    y_cols: Optional[List[str]] = None,
    label_col: Optional[str] = None,
    titulo: str = "Visualización inteligente",
    unidad: str = "",
    normalizar: bool = False,
    apilado: bool = False,
    max_series: int = 5,
    figsize: Tuple[int, int] = (12, 6),
    sintetizar_si_no_hay_fecha: bool = False,
    sintetico_origen: str = "1970-01-01",
    date_format: Optional[str] = None,
    dayfirst: bool = False,
    strict_parse: bool = True,
    mostrar: Optional[List[str]] = None,
    *,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Orquesta automáticamente:
      - Si hay UNA sola fecha ⇒ usa plot_series_desde_lista (líneas o apilado).
      - Si hay MÚLTIPLES fechas ⇒ genera en orden: 'lineas' y/o 'boxplot'.
    Retorna dict con handlers: {'largo', 'diag', 'lineas', 'apilado', 'boxplot'} según corresponda.
    """
    largo, diag = preparar_largo_desde_lista(
        dfs,
        x_col=x_col,
        y_cols=y_cols,
        label_col=label_col,
        max_series=max_series,
        sintetizar_si_no_hay_fecha=sintetizar_si_no_hay_fecha,
        sintetico_origen=sintetico_origen,
        date_format=date_format,
        dayfirst=dayfirst,
        strict_parse=strict_parse,
        verbose=verbose,
        retornar_diag=True
    )

    n_fechas = largo["fecha"].nunique(dropna=True)
    if verbose:
        print(f"Fechas únicas detectadas: {n_fechas}")

    resultados: Dict[str, Any] = {"largo": largo, "diag": diag}

    if n_fechas <= 1:
        if verbose:
            print("Caso detectado: una sola fecha. Usando plot_series_desde_lista()...")
        fig, ax, _, _ = plot_series_desde_lista(
            dfs=dfs,
            x_col=x_col,
            y_cols=y_cols,
            label_col=label_col,
            titulo=titulo,
            unidad=unidad,
            normalizar=normalizar,
            apilado=apilado,
            max_series=max_series,
            figsize=figsize,
            sintetizar_si_no_hay_fecha=sintetizar_si_no_hay_fecha,
            sintetico_origen=sintetico_origen,
            date_format=date_format,
            dayfirst=dayfirst,
            strict_parse=strict_parse,
            verbose=verbose,
            retornar_diag=False
        )
        resultados["apilado" if apilado else "lineas"] = (fig, ax)
        return resultados

    # Múltiples fechas
    if not mostrar:
        mostrar = ["lineas", "boxplot"]

    if "lineas" in mostrar:
        fig_l, ax_l = _plot_lineas_desde_largo(
            largo=largo,
            titulo="Líneas por serie (superpuestas)",
            unidad=unidad,
            normalizar=normalizar,
            figsize=figsize
        )
        resultados["lineas"] = (fig_l, ax_l)

    if "boxplot" in mostrar:
        fig_b, ax_b = _plot_boxplot_mensual_desde_largo(
            largo=largo,
            unidad=unidad,
            titulo="Distribución mensual (boxplot) de valores",
            showfliers=False,
            figsize=(figsize[0], max(5, int(figsize[1]*0.8)))
        )
        resultados["boxplot"] = (fig_b, ax_b)

    return resultados