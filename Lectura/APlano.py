# ApiArchivos.py
from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
import io
import re
import json
import csv
import logging
import configparser
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List, Union
import xml.etree.ElementTree as ET

import pandas as pd

try:
    import yaml  # opcional, para YAML
    HAS_YAML = True
except ImportError:
    yaml = None  # type: ignore[assignment]
    HAS_YAML = False


# =============================================================================
# LOGGING
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
class AppError(Exception):
    """Error base de la aplicación."""

class ValidationError(AppError):
    """Entradas inválidas o inconsistentes."""

class UnsupportedFormatError(AppError):
    """Formato no soportado o no reconocible."""

class ReaderError(AppError):
    """Fallo al leer/parsear con un lector específico."""

class MissingDependencyError(AppError):
    """Faltan dependencias opcionales (p. ej. PyYAML)."""


# =============================================================================
# CONSTANTES Y UTILIDADES (compartidas)
# =============================================================================
COMMON_ENCODINGS: tuple[str, ...] = ("utf-8", "latin-1", "cp1252")
CSV_LIKE_SEPS: list[str] = [",", ";", "\t", "|", ":"]

APACHE_LOG_PATTERN = re.compile(
    r'(?P<host>\S+) (?P<ident>\S+) (?P<user>\S+) \[(?P<time>[^\]]+)\] '
    r'"(?P<request>[^"]*)" (?P<status>\d{3}) (?P<size>\S+)(?: '
    r'"(?P<referrer>[^"]*)" "(?P<agent>[^"]*)")?'
)

def _json_to_records(obj: Any) -> List[Dict[str, Any]]:
    # Si es lista de dicts → listo
    if isinstance(obj, list):
        if all(isinstance(it, dict) for it in obj):
            return obj
        return [{"value": it} for it in obj]
    # Si es dict, buscar primera clave con lista de dicts
    if isinstance(obj, dict):
        for _, v in obj.items():
            if isinstance(v, list) and all(isinstance(it, dict) for it in v):
                return v
        # Aplanar dict en una sola fila (serializando anidados)
        flat: Dict[str, Any] = {}
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                flat[k] = json.dumps(v, ensure_ascii=False)
            else:
                flat[k] = v
        return [flat]
    # Fallback genérico
    return [{"value": obj}]


# =============================================================================
# DTOs
# =============================================================================
@dataclass(frozen=True)
class LoadRequest:
    """
    Parámetros de carga.
    path: ruta del archivo a leer
    encoding_hint: codificación sugerida (si la conoces)
    sep_hint: separador sugerido (para CSV/TSV/TXT tabular)
    max_bytes: bytes máximos a muestrear para heurísticas
    allow_yaml: permite leer YAML si hay dependencia instalada
    """
    path: Path | str
    encoding_hint: Optional[str] = None
    sep_hint: Optional[str] = None
    max_bytes: int = 100_000
    allow_yaml: bool = True

    def validate(self) -> None:
        p = Path(self.path)
        if not p.exists():
            raise ValidationError(f"No existe el archivo: {p}")
        if self.max_bytes <= 0:
            raise ValidationError("max_bytes debe ser > 0")


@dataclass(frozen=True)
class LoadResult:
    dataframe: pd.DataFrame
    detected_format: str
    encoding_used: Optional[str]
    sep_used: Optional[str]


@dataclass(frozen=True)
class DetectionContext:
    sample_text: str
    encoding_hint: Optional[str]
    sep_hint: Optional[str]
    detected_format: str


# =============================================================================
# PUERTOS / INTERFACES
# =============================================================================
class TextSampler:
    """Obtiene un fragmento de texto y su encoding probable."""
    def get_sample(self, path: Path, max_bytes: int, encoding_hint: Optional[str]) -> Tuple[str, Optional[str]]:
        if encoding_hint:
            try:
                text = path.read_text(encoding=encoding_hint, errors="strict")
                return text[:max_bytes], encoding_hint
            except UnicodeDecodeError:
                log.warning("Falló lectura con encoding_hint=%s. Se intentarán heurísticas.", encoding_hint)
        data = path.read_bytes()[:max_bytes]
        for enc in COMMON_ENCODINGS:
            try:
                return data.decode(enc), enc
            except UnicodeDecodeError:
                continue
        # último recurso: reemplazos
        return data.decode("utf-8", errors="replace"), "utf-8"


class FormatDetector:
    """Detecta formato por extensión y/o heurísticas de contenido."""

    @staticmethod
    def _detect_by_extension(path: Path) -> Optional[str]:
        ext = path.suffix.lower()
        if ext == ".csv":   return "csv"
        if ext == ".tsv":   return "tsv"
        if ext == ".json":  return "json"
        if ext == ".xml":   return "xml"
        if ext in {".yaml", ".yml"}: return "yaml"
        if ext in {".ini", ".cfg", ".conf"}: return "ini"
        if ext == ".log":   return "log"
        if ext == ".txt":   return "txt"
        return None

    @staticmethod
    def _looks_like_json(sample: str) -> bool:
        s = sample.lstrip()
        return s.startswith("{") or s.startswith("[")

    @staticmethod
    def _looks_like_xml(sample: str) -> bool:
        return sample.lstrip().startswith("<")

    @staticmethod
    def _looks_like_ini(sample: str) -> bool:
        return bool(re.search(r"^\s*\[.+?\]\s*$", sample, flags=re.MULTILINE))

    @staticmethod
    def _looks_like_yaml(sample: str) -> bool:
        # Heurística simple
        k_v = len(re.findall(r"^[\w\-\.\[\]]+\s*:\s*.+$", sample, flags=re.MULTILINE))
        dashed = len(re.findall(r"^\s*-\s+.+$", sample, flags=re.MULTILINE))
        return (k_v + dashed) >= 3

    @staticmethod
    def _looks_like_apache_log(sample: str) -> bool:
        for ln in sample.splitlines()[:10]:
            if APACHE_LOG_PATTERN.search(ln):
                return True
        return False

    @staticmethod
    def sniff_delimiter(sample: str) -> Optional[str]:
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters="".join(CSV_LIKE_SEPS))
            return dialect.delimiter
        except Exception:
            pass
        # Heurística: conteo total por separador
        lines = [ln for ln in sample.splitlines() if ln.strip()][:50]
        counts = {sep: 0 for sep in CSV_LIKE_SEPS}
        for ln in lines:
            for sep in CSV_LIKE_SEPS:
                counts[sep] += ln.count(sep)
        best_sep, best_count = max(counts.items(), key=lambda kv: kv[1])
        return best_sep if best_count >= 3 else None

    def detect(self, path: Path, sample_text: str) -> Tuple[str, Optional[str]]:
        fmt = self._detect_by_extension(path)

        # Si no se reconoció por extensión, usar contenido
        if fmt is None:
            if self._looks_like_json(sample_text):
                fmt = "json"
            elif self._looks_like_xml(sample_text):
                fmt = "xml"
            elif self._looks_like_ini(sample_text):
                fmt = "ini"
            elif self._looks_like_yaml(sample_text):
                fmt = "yaml"
            elif self._looks_like_apache_log(sample_text):
                fmt = "log"
            else:
                sep = self.sniff_delimiter(sample_text)
                fmt = "csv" if (sep and sep != "\t") else ("tsv" if sep == "\t" else "txt")
                return fmt, sep

        # Para formatos tabulares, calcular sep sugerido
        sep_hint = self.sniff_delimiter(sample_text) if fmt in {"csv", "tsv", "txt"} else None
        # Asegurar sep por defecto coherente si viene por extensión
        if fmt == "csv" and not sep_hint:
            sep_hint = ","
        if fmt == "tsv" and not sep_hint:
            sep_hint = "\t"
        return fmt, sep_hint


# =============================================================================
# ESTRATEGIA DE LECTURA (INTERFAZ)
# =============================================================================
class ReaderStrategy:
    """Estrategia de lectura para un formato específico."""
    formats: set[str] = set()

    def read(self, path: Path, ctx: DetectionContext) -> pd.DataFrame:
        raise NotImplementedError


# =============================================================================
# LECTORES CONCRETOS
# =============================================================================
class CsvLikeReader(ReaderStrategy):
    formats = {"csv", "tsv", "txt"}  # txt tabular o fallback a columna única

    def read(self, path: Path, ctx: DetectionContext) -> pd.DataFrame:
        encoding_hint = ctx.encoding_hint
        sep_hint = ctx.sep_hint
        sample = ctx.sample_text

        # Si es txt y no parece tabular, devolver columna "text"
        if ctx.detected_format == "txt":
            guessed_sep = sep_hint or FormatDetector.sniff_delimiter(sample)
            if not guessed_sep:
                lines = [ln for ln in sample.splitlines() if ln.strip()]
                return pd.DataFrame({"text": lines})

        # Intentar combinaciones (encodings/separadores)
        encodings_to_try = (
            [encoding_hint] + [e for e in COMMON_ENCODINGS if e != encoding_hint]
            if encoding_hint else list(COMMON_ENCODINGS)
        )
        seps_to_try = (
            [sep_hint] + [s for s in CSV_LIKE_SEPS if s != sep_hint]
            if sep_hint else CSV_LIKE_SEPS
        )

        errors: list[tuple[Optional[str], Optional[str], str]] = []
        for enc in encodings_to_try:
            for sep in seps_to_try:
                try:
                    return pd.read_csv(path, sep=sep, encoding=enc, engine="python")
                except Exception as ex:
                    errors.append((enc, sep, str(ex)))

        # Último intento: inferencia automática de pandas (Python engine)
        for enc in encodings_to_try:
            try:
                return pd.read_csv(path, sep=None, engine="python", encoding=enc)
            except Exception as ex:
                errors.append((enc, None, str(ex)))

        raise ReaderError(
            f"No fue posible leer como CSV/TSV. Intentos: {len(errors)}. "
            f"Ejemplo de error: {errors[-1] if errors else 'N/A'}"
        )


class JsonReader(ReaderStrategy):
    formats = {"json"}

    def read(self, path: Path, ctx: DetectionContext) -> pd.DataFrame:
        encoding_hint = ctx.encoding_hint
        if encoding_hint:
            text = path.read_text(encoding=encoding_hint)
            enc_used = encoding_hint
        else:
            text, enc_used = TextSampler().get_sample(path, 10_000_000, None)  # leer completo si posible

        try:
            data = json.loads(text)
            return pd.DataFrame.from_records(_json_to_records(data))
        except json.JSONDecodeError:
            # Intentar json lines
            try:
                return pd.read_json(path, lines=True, encoding=enc_used or "utf-8")
            except Exception as ex:
                raise ReaderError(f"JSON inválido o no soportado: {ex}") from ex


class XmlReader(ReaderStrategy):
    formats = {"xml"}

    def read(self, path: Path, ctx: DetectionContext) -> pd.DataFrame:
        # 1) Intentar con pandas.read_xml
        try:
            return pd.read_xml(path)
        except Exception:
            pass

        # 2) Heurística con ElementTree
        text = ctx.sample_text if ctx.sample_text else path.read_text(encoding=ctx.encoding_hint or "utf-8", errors="replace")
        try:
            root = ET.fromstring(text)
        except Exception as ex:
            raise ReaderError(f"XML inválido: {ex}") from ex

        from collections import Counter, defaultdict
        tag_counts = Counter()
        elements_by_tag: Dict[str, list[ET.Element]] = defaultdict(list)
        for elem in root.iter():
            if elem is root:
                continue
            tag_counts[elem.tag] += 1
            elements_by_tag[elem.tag].append(elem)

        if not tag_counts:
            return pd.DataFrame()

        candidate_tag, _ = tag_counts.most_common(1)[0]
        rows: list[Dict[str, Any]] = []
        for el in elements_by_tag[candidate_tag]:
            row: Dict[str, Any] = {}
            # atributos
            for k, v in el.attrib.items():
                row[k] = v
            # hijos directos como columnas
            for child in list(el):
                key = child.tag
                val = (child.text or "").strip() if child.text else ""
                if list(child):  # subhijos → serializar JSON
                    val = json.dumps({c.tag: (c.text or "").strip() for c in child}, ensure_ascii=False)
                row[key] = val
            # texto directo
            if not row and (el.text or "").strip():
                row["value"] = el.text.strip()
            rows.append(row)

        return pd.DataFrame(rows)


class YamlReader(ReaderStrategy):
    formats = {"yaml"}

    def read(self, path: Path, ctx: DetectionContext) -> pd.DataFrame:
        if not HAS_YAML or yaml is None:
            raise MissingDependencyError("PyYAML no está instalado. Instálalo con: pip install pyyaml")
        if ctx.encoding_hint:
            text = path.read_text(encoding=ctx.encoding_hint)
        else:
            text, _ = TextSampler().get_sample(path, 10_000_000, None)
        data = yaml.safe_load(text)
        return pd.DataFrame.from_records(_json_to_records(data))


class IniReader(ReaderStrategy):
    formats = {"ini"}

    def read(self, path: Path, ctx: DetectionContext) -> pd.DataFrame:
        encodings_to_try = (
            [ctx.encoding_hint] + [e for e in COMMON_ENCODINGS if e != ctx.encoding_hint]
            if ctx.encoding_hint else list(COMMON_ENCODINGS)
        )
        parser = configparser.ConfigParser()
        for enc in encodings_to_try:
            try:
                with open(path, "r", encoding=enc) as f:
                    parser.read_file(f)
                break
            except Exception:
                continue
        rows: list[Dict[str, Any]] = []
        for section in parser.sections():
            for option, value in parser.items(section):
                rows.append({"section": section, "option": option, "value": value})
        return pd.DataFrame(rows)


class LogReader(ReaderStrategy):
    formats = {"log"}

    def read(self, path: Path, ctx: DetectionContext) -> pd.DataFrame:
        text = ctx.sample_text if ctx.sample_text else path.read_text(encoding=ctx.encoding_hint or "utf-8", errors="replace")
        lines = [ln for ln in text.splitlines() if ln.strip()]

        # Apache/Nginx (common/combined)
        matches = [APACHE_LOG_PATTERN.search(ln) for ln in lines]
        if any(m is not None for m in matches):
            records: list[Dict[str, Any]] = []
            for m in matches:
                if not m:
                    continue
                rec = m.groupdict()
                if rec.get("size") and str(rec["size"]).isdigit():
                    rec["size"] = int(rec["size"])
                records.append(rec)
            return pd.DataFrame(records)

        # key=value
        kv_pattern = re.compile(r"(\b[\w\.-]+)=(\"[^\"]*\"|\S+)")
        kv_records: list[Dict[str, Any]] = []
        for ln in lines:
            pairs = dict((k, v.strip('"')) for k, v in kv_pattern.findall(ln))
            if pairs:
                kv_records.append(pairs)
        if kv_records:
            return pd.DataFrame(kv_records)

        # Fallback: una columna
        return pd.DataFrame({"line": lines})


class TxtReader(ReaderStrategy):
    formats = {"txt"}

    def read(self, path: Path, ctx: DetectionContext) -> pd.DataFrame:
        # Se delega a CsvLikeReader si hay separador; si no, columna única
        guessed_sep = ctx.sep_hint or FormatDetector.sniff_delimiter(ctx.sample_text)
        if guessed_sep:
            return CsvLikeReader().read(path, ctx)
        lines = [ln for ln in ctx.sample_text.splitlines() if ln.strip()]
        return pd.DataFrame({"text": lines})


# =============================================================================
# REGISTRO DE ESTRATEGIAS
# =============================================================================
class ReaderRegistry:
    def __init__(self) -> None:
        self._strategies: Dict[str, ReaderStrategy] = {}
        self.register(CsvLikeReader())
        self.register(JsonReader())
        self.register(XmlReader())
        self.register(YamlReader())
        self.register(IniReader())
        self.register(LogReader())
        self.register(TxtReader())

    def register(self, strategy: ReaderStrategy) -> None:
        for fmt in strategy.formats:
            self._strategies[fmt] = strategy

    def get(self, fmt: str) -> ReaderStrategy:
        try:
            return self._strategies[fmt]
        except KeyError as e:
            raise UnsupportedFormatError(f"No hay lector para formato: {fmt}") from e


# =============================================================================
# SERVICIO (CASO DE USO)
# =============================================================================
class DataFrameLoader:
    """
    Orquesta:
    - Muestreo de texto + encoding
    - Detección de formato y separador
    - Delegación al lector adecuado
    """

    def __init__(self, registry: Optional[ReaderRegistry] = None) -> None:
        self.sampler = TextSampler()
        self.detector = FormatDetector()
        self.registry = registry or ReaderRegistry()

    def load(self, req: LoadRequest) -> LoadResult:
        req.validate()
        path = Path(req.path)

        sample_text, enc = self.sampler.get_sample(path, req.max_bytes, req.encoding_hint)
        fmt, sep_hint = self.detector.detect(path, sample_text)

        if fmt == "yaml" and not req.allow_yaml:
            raise UnsupportedFormatError("YAML no permitido por configuración (allow_yaml=False).")

        ctx = DetectionContext(
            sample_text=sample_text,
            encoding_hint=enc,
            sep_hint=req.sep_hint or sep_hint,
            detected_format=fmt,
        )

        reader = self.registry.get(fmt)
        df = reader.read(path, ctx)

        # Si fue TXT sin separador → df ya es columna única
        # Si fue CSV/TSV → se intentó leer con varias combinaciones
        return LoadResult(
            dataframe=df,
            detected_format=fmt,
            encoding_used=enc,
            sep_used=ctx.sep_hint,
        )


# =============================================================================
# FACADES / COMPATIBILIDAD
# =============================================================================
def load_to_dataframe(path: str | Path) -> pd.DataFrame:
    """
    API procedural para compatibilidad con tu código existente.
    Detecta el formato y devuelve únicamente el DataFrame.
    """
    loader = DataFrameLoader()
    result = loader.load(LoadRequest(path=path))
    return result.dataframe
