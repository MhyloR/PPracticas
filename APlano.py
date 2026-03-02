from __future__ import annotations
import io
import re
import json
import csv
import configparser
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

import pandas as pd
import xml.etree.ElementTree as ET

try:
    import yaml  # opcional, para YAML
    HAS_YAML = True
except ImportError:
    yaml = None
    HAS_YAML = False


# -------------------------
# Utilidades generales
# -------------------------

COMMON_ENCODINGS = ("utf-8", "latin-1", "cp1252")

def _try_read_text(path: Path, max_bytes: int = 100_000) -> Tuple[str, str]:
    """Lee un fragmento del archivo intentando varias codificaciones. Devuelve (texto, encoding)."""
    data = Path(path).read_bytes()[:max_bytes]
    for enc in COMMON_ENCODINGS:
        try:
            return data.decode(enc), enc
        except UnicodeDecodeError:
            continue
    # último recurso: reemplazar caracteres inválidos
    return data.decode("utf-8", errors="replace"), "utf-8"

def _detect_by_extension(path: Path) -> Optional[str]:
    ext = path.suffix.lower()
    if ext in {".csv"}:
        return "csv"
    if ext in {".tsv"}:
        return "tsv"
    if ext in {".json"}:
        return "json"
    if ext in {".xml"}:
        return "xml"
    if ext in {".yaml", ".yml"}:
        return "yaml"
    if ext in {".ini", ".cfg", ".conf"}:
        return "ini"
    if ext in {".log"}:
        return "log"
    if ext in {".txt"}:
        return "txt"
    return None

CSV_LIKE_SEPS = [",", ";", "\t", "|", ":"]

def _sniff_delimiter(sample: str) -> Optional[str]:
    """Intenta detectar un delimitador probable a partir de un texto de muestra."""
    # Probar csv.Sniffer primero
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters="".join(CSV_LIKE_SEPS))
        return dialect.delimiter
    except Exception:
        pass
    # Heurística: contar separadores por línea y elegir el más consistente
    lines = [ln for ln in sample.splitlines() if ln.strip()]
    lines = lines[:50]  # limitar
    counts = {sep: 0 for sep in CSV_LIKE_SEPS}
    for ln in lines:
        for sep in CSV_LIKE_SEPS:
            counts[sep] += ln.count(sep)
    # Elegir separador con mayor conteo total y que aparezca en varias líneas
    best = max(counts.items(), key=lambda kv: kv[1])
    if best[1] >= 3:  # umbral mínimo
        return best[0]
    return None

def _looks_like_json(sample: str) -> bool:
    s = sample.lstrip()
    return s.startswith("{") or s.startswith("[")

def _looks_like_xml(sample: str) -> bool:
    return sample.lstrip().startswith("<")

def _looks_like_ini(sample: str) -> bool:
    return bool(re.search(r"^\s*\[.+?\]\s*$", sample, flags=re.MULTILINE))

def _looks_like_yaml(sample: str) -> bool:
    # Heurística simple: líneas clave: valor y/o listas con '- '
    k_v = len(re.findall(r"^[\w\-\.]+\s*:\s*.+$", sample, flags=re.MULTILINE))
    dashed = len(re.findall(r"^\s*-\s+.+$", sample, flags=re.MULTILINE))
    return (k_v + dashed) >= 3

APACHE_LOG_PATTERN = re.compile(
    r'(?P<host>\S+) (?P<ident>\S+) (?P<user>\S+) \[(?P<time>[^\]]+)\] '
    r'"(?P<request>[^"]*)" (?P<status>\d{3}) (?P<size>\S+)(?: '
    r'"(?P<referrer>[^"]*)" "(?P<agent>[^"]*)")?'
)

def _looks_like_apache_log(sample: str) -> bool:
    for ln in sample.splitlines()[:10]:
        if APACHE_LOG_PATTERN.search(ln):
            return True
    return False


# -------------------------
# Lectores específicos
# -------------------------

def _read_csv_like(path: Path, encoding_hint: Optional[str], sep_hint: Optional[str]) -> pd.DataFrame:
    # pandas infiere compresión por extensión (gz, bz2, zip, xz)
    encodings_to_try = [encoding_hint] + [e for e in COMMON_ENCODINGS if e != encoding_hint] if encoding_hint else list(COMMON_ENCODINGS)
    seps_to_try = [sep_hint] + [s for s in CSV_LIKE_SEPS if s != sep_hint] if sep_hint else CSV_LIKE_SEPS
    errors = []
    for enc in encodings_to_try:
        for sep in seps_to_try:
            try:
                return pd.read_csv(path, sep=sep, encoding=enc, engine="python")
            except Exception as ex:
                errors.append((enc, sep, str(ex)))
    # Último intento: dejar que pandas infiera con sep=None (solo Python engine)
    for enc in encodings_to_try:
        try:
            return pd.read_csv(path, sep=None, engine="python", encoding=enc)
        except Exception as ex:
            errors.append((enc, "auto", str(ex)))
    raise RuntimeError(f"No fue posible leer como CSV/TSV. Intentos: {len(errors)}. Ejemplo de error: {errors[-1] if errors else 'N/A'}")

def _json_to_records(obj: Any) -> List[Dict[str, Any]]:
    # Si es lista de dicts → listo
    if isinstance(obj, list):
        if all(isinstance(it, dict) for it in obj):
            return obj
        # lista de valores -> envolver
        return [{"value": it} for it in obj]
    # Si es dict, buscar la primera clave que sea lista de dicts
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, list) and all(isinstance(it, dict) for it in v):
                return v
        # Sin listas de dicts -> aplanar dict en una sola fila
        flat = {}
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                flat[k] = json.dumps(v, ensure_ascii=False)
            else:
                flat[k] = v
        return [flat]
    # Cualquier otro → fila única
    return [{"value": obj}]

def _read_json(path: Path, encoding_hint: Optional[str]) -> pd.DataFrame:
    text, enc = _try_read_text(path) if encoding_hint is None else (Path(path).read_text(encoding=encoding_hint), encoding_hint)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as ex:
        # pandas también puede leer JSON línea por línea (jsonlines)
        try:
            return pd.read_json(path, lines=True, encoding=enc)
        except Exception:
            raise ex
    records = _json_to_records(data)
    return pd.DataFrame.from_records(records)

def _read_xml(path: Path, encoding_hint: Optional[str]) -> pd.DataFrame:
    # 1) Intentar con pandas.read_xml (si lxml/etree lo permite)
    try:
        return pd.read_xml(path)  # pandas intentará inferir estructura
    except Exception:
        pass
    # 2) Heurística con ElementTree: elegir el tag más repetido como "fila"
    text, _ = _try_read_text(path)
    root = ET.fromstring(text)
    # Contar ocurrencias por etiqueta (ignorando root)
    from collections import Counter, defaultdict
    tag_counts = Counter()
    elements_by_tag = defaultdict(list)
    for elem in root.iter():
        if elem is root:
            continue
        tag_counts[elem.tag] += 1
        elements_by_tag[elem.tag].append(elem)
    if not tag_counts:
        # XML vacío o trivial
        return pd.DataFrame()
    candidate_tag, _ = tag_counts.most_common(1)[0]
    rows = []
    for el in elements_by_tag[candidate_tag]:
        row = {}
        # atributos
        for k, v in el.attrib.items():
            row[k] = v
        # hijos directos como columnas
        for child in list(el):
            key = child.tag
            val = (child.text or "").strip() if child.text else ""
            # si el hijo tiene subhijos, serializar JSON
            if list(child):
                val = json.dumps({c.tag: (c.text or "").strip() for c in child}, ensure_ascii=False)
            row[key] = val
        # texto directo del elemento
        if not row and (el.text or "").strip():
            row["value"] = el.text.strip()
        rows.append(row)
    return pd.DataFrame(rows)

def _read_yaml(path: Path, encoding_hint: Optional[str]) -> pd.DataFrame:
    if not HAS_YAML or yaml is None:
        raise ImportError("PyYAML no está instalado. Instálalo con: pip install pyyaml")
    text, enc = _try_read_text(path) if encoding_hint is None else (Path(path).read_text(encoding=encoding_hint), encoding_hint)
    data = yaml.safe_load(text)
    records = _json_to_records(data)
    return pd.DataFrame.from_records(records)

def _read_ini(path: Path, encoding_hint: Optional[str]) -> pd.DataFrame:
    encodings_to_try = [encoding_hint] + [e for e in COMMON_ENCODINGS if e != encoding_hint] if encoding_hint else list(COMMON_ENCODINGS)
    parser = configparser.ConfigParser()
    for enc in encodings_to_try:
        try:
            with open(path, "r", encoding=enc) as f:
                parser.read_file(f)
            break
        except Exception:
            continue
    rows = []
    for section in parser.sections():
        for option, value in parser.items(section):
            rows.append({"section": section, "option": option, "value": value})
    return pd.DataFrame(rows)

def _read_log(path: Path, encoding_hint: Optional[str]) -> pd.DataFrame:
    text, enc = _try_read_text(path) if encoding_hint is None else (Path(path).read_text(encoding=encoding_hint), encoding_hint)
    lines = [ln for ln in text.splitlines() if ln.strip()]
    # Intentar Apache/Nginx common/combined
    matches = [APACHE_LOG_PATTERN.search(ln) for ln in lines]
    if any(m is not None for m in matches):
        records = []
        for m in matches:
            if not m:
                continue
            rec = m.groupdict()
            # convertir size a int si aplica
            if rec.get("size") and rec["size"].isdigit():
                rec["size"] = int(rec["size"])
            records.append(rec)
        return pd.DataFrame(records)
    # Heurística: intentar key=value
    kv_pattern = re.compile(r"(\b[\w\.-]+)=(\"[^\"]*\"|\S+)")
    kv_records = []
    for ln in lines:
        pairs = dict((k, v.strip('"')) for k, v in kv_pattern.findall(ln))
        if pairs:
            kv_records.append(pairs)
    if kv_records:
        return pd.DataFrame(kv_records)
    # Fallback: una columna con el texto
    return pd.DataFrame({"line": lines})

# -------------------------
# Cargador principal
# -------------------------

def load_to_dataframe(path: str | Path) -> pd.DataFrame:
    """
    Detecta el formato del archivo y lo carga como DataFrame.
    Devuelve solo el DataFrame.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    sample_text, enc = _try_read_text(path)
    fmt = _detect_by_extension(path)

    # Si no se determinó por extensión, usar heurísticas de contenido
    if fmt is None:
        if _looks_like_json(sample_text):
            fmt = "json"
        elif _looks_like_xml(sample_text):
            fmt = "xml"
        elif _looks_like_ini(sample_text):
            fmt = "ini"
        elif _looks_like_yaml(sample_text):
            fmt = "yaml"
        elif _looks_like_apache_log(sample_text):
            fmt = "log"
        else:
            # ¿Tabular?
            sep = _sniff_delimiter(sample_text)
            if sep:
                fmt = "csv" if sep != "\t" else "tsv"
            else:
                fmt = "txt"

    # Lectura por formato
    sep_hint = _sniff_delimiter(sample_text) if fmt in {"csv", "tsv", "txt"} else None

    if fmt in {"csv", "tsv"}:
        df = _read_csv_like(path, enc, sep_hint or ("," if fmt == "csv" else "\t"))
    elif fmt == "json":
        df = _read_json(path, enc)
    elif fmt == "xml":
        df = _read_xml(path, enc)
    elif fmt == "yaml":
        df = _read_yaml(path, enc)
    elif fmt == "ini":
        df = _read_ini(path, enc)
    elif fmt == "log":
        df = _read_log(path, enc)
    elif fmt == "txt":
        # Intentar tabular; si no, columna única
        if sep_hint:
            df = _read_csv_like(path, enc, sep_hint)
        else:
            lines = [ln for ln in sample_text.splitlines() if ln.strip()]
            df = pd.DataFrame({"text": lines})
    else:
        raise ValueError(f"Formato no soportado o no reconocido: {fmt}")

    return df