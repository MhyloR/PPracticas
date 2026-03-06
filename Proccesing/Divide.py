# ApiSeparacion.py
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Tuple, Optional
import pandas as pd

# =============================================================================
# LOGGING (opcional)
# =============================================================================
def setup_logging(level: int | str = logging.INFO) -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        )

log = logging.getLogger(__name__)


# =============================================================================
# ERRORES
# =============================================================================
class SeparacionError(Exception):
    """Error base para separación."""


class ValidationError(SeparacionError):
    """Entradas inválidas."""


# =============================================================================
# DTOs
# =============================================================================
@dataclass(frozen=True)
class SeparacionRequest:
    """
    archivo: DataFrame fuente
    (El parámetro `columnas` del original no se usa para seleccionar; se valida desde el DF real)
    """
    archivo: pd.DataFrame
    # Nota: selección y renombrado son interactivos; no se pasan aquí.

    def validate(self) -> None:
        if not isinstance(self.archivo, pd.DataFrame):
            raise ValidationError(f"Se esperaba DataFrame, recibido: {type(self.archivo)}")
        if self.archivo.empty:
            raise ValidationError("El DataFrame está vacío")


@dataclass(frozen=True)
class SeparacionResult:
    df_general: pd.DataFrame  # 2 columnas (X, Y) tras renombrado
    df_atributos: pd.DataFrame  # resto de columnas


# =============================================================================
# COMPONENTES (responsabilidades únicas)
# =============================================================================
class ColumnChooser:
    """Encapsula la interacción para escoger X e Y desde las columnas del DataFrame."""

    def choose_x(self, columnas_validas: list[str]) -> str:
        while True:
            var_x = input("Variable eje X: ").strip()
            if var_x in columnas_validas:
                return var_x
            print(f"Columna no encontrada. Disponibles: {columnas_validas}")

    def choose_y(self, columnas_validas: list[str], var_x: str) -> str:
        while True:
            var_y = input("Variable eje Y: ").strip()
            if var_y == var_x:
                print("La variable Y no puede ser igual a X")
                continue
            if var_y in columnas_validas:
                return var_y
            print(f"Columna no encontrada. Disponibles: {columnas_validas}")


class TimeConverter:
    """Convierte la columna X a datetime replicando la lógica del original."""

    def to_datetime_like_original(self, df: pd.DataFrame, col_x: str) -> None:
        # Intento estricto con formato '%Y-%m-%d %H:%M:%S'
        try:
            df[col_x] = pd.to_datetime(df[col_x], format='%Y-%m-%d %H:%M:%S')
        except Exception:
            # Flexible, coercitivo
            df[col_x] = pd.to_datetime(df[col_x], errors='coerce', dayfirst=False)


class Renamer:
    """Gestión de renombrado interactivo SOLO para X e Y con validaciones."""

    def interactive_rename_xy(self, var_x: str, var_y: str) -> tuple[str, str]:
        print("\n=== Renombrar columnas de df_general (solo X e Y) ===")
        print(f"Nombre actual de X: {var_x}")
        nuevo_x = input("Nuevo nombre para X (Enter para conservar): ").strip()
        if not nuevo_x:
            nuevo_x = var_x

        print(f"Nombre actual de Y: {var_y}")
        nuevo_y = input("Nuevo nombre para Y (Enter para conservar): ").strip()
        if not nuevo_y:
            nuevo_y = var_y

        self._validate_new_names(nuevo_x, nuevo_y)
        return nuevo_x, nuevo_y

    def _validate_new_names(self, nuevo_x: str, nuevo_y: str) -> None:
        if not nuevo_x:
            raise ValidationError("El nombre para X no puede ser vacío.")
        if not nuevo_y:
            raise ValidationError("El nombre para Y no puede ser vacío.")
        if nuevo_x == nuevo_y:
            raise ValidationError("Los nombres de X e Y no pueden ser iguales.")


# =============================================================================
# SERVICIO (caso de uso)
# =============================================================================
class SeparacionService:
    """
    Caso de uso que reproduce exactamente el comportamiento original:
    - Selección interactiva de X e Y
    - df_general = archivo[[X, Y]].copy()
    - Convertir X a datetime (estricto y luego flexible/Coerce)
    - df_atributos = archivo.drop([X, Y])
    - Renombrado interactivo de X e Y
    """

    def __init__(
        self,
        chooser: Optional[ColumnChooser] = None,
        converter: Optional[TimeConverter] = None,
        renamer: Optional[Renamer] = None,
    ) -> None:
        self.chooser = chooser or ColumnChooser()
        self.converter = converter or TimeConverter()
        self.renamer = renamer or Renamer()

    def ejecutar(self, req: SeparacionRequest) -> SeparacionResult:
        req.validate()

        # Columnas válidas desde el DF real
        columnas_validas = list(req.archivo.columns)

        # Selección interactiva de X e Y
        var_x = self.chooser.choose_x(columnas_validas)
        var_y = self.chooser.choose_y(columnas_validas, var_x)

        # Construcción de df_general y df_atributos
        df_general = req.archivo[[var_x, var_y]].copy()
        self.converter.to_datetime_like_original(df_general, var_x)

        df_atributos = req.archivo.drop([var_x, var_y], axis=1).copy()

        # Renombrado interactivo de SOLO X e Y
        nuevo_x, nuevo_y = self.renamer.interactive_rename_xy(var_x, var_y)
        df_general.rename(columns={var_x: nuevo_x, var_y: nuevo_y}, inplace=True)

        # Validaciones finales (mismas garantías lógicas del original)
        assert isinstance(df_general, pd.DataFrame), "df_general no es DataFrame"
        assert isinstance(df_atributos, pd.DataFrame), "df_atributos no es DataFrame"
        assert df_general.shape[1] == 2, f"df_general debe tener 2 columnas, tiene {df_general.shape[1]}"

        return SeparacionResult(df_general=df_general, df_atributos=df_atributos)


# =============================================================================
# FACHADA (compatibilidad con tu función original)
# =============================================================================
def Separacion(columnas, archivo: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fachada con la MISMA firma y comportamiento observable que tu función original.
    Ignora 'columnas' para la selección (como en el original), validando desde el DF real.
    """
    service = SeparacionService()
    result = service.ejecutar(SeparacionRequest(archivo=archivo))
    return result.df_general, result.df_atributos


# =============================================================================
# EJEMPLO DE USO (opcional)
# =============================================================================
if __name__ == "__main__":
    setup_logging()
    demo = pd.DataFrame({
        "fecha": ["2024-01-01 12:00:00", "2024-01-02 13:30:25"],
        "valor": [10.5, 20.3],
        "categoria": ["A", "B"],
        "otra": [1, 2],
    })
    # Ejecuta y responde por consola como tu versión original:
    df_g, df_attr = Separacion(columnas=list(demo.columns), archivo=demo)
    print("\n[Salida] df_general:")
    print(df_g.head())
    print("\n[Salida] df_atributos:")
    print(df_attr.head())