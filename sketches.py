"""Direct CDR sketches, embedded thumbnails and readable per-file relevance."""
import hashlib
import io
import json
from pathlib import Path
import plistlib
import re
import struct
import subprocess
import tempfile
import unicodedata
import zipfile
import zlib

from event_relevance import LABELS

BLOCK = "Актуальность эскизов"
MAX_PREVIEW = 8 * 1024 * 1024
PNG = b"\x89PNG\r\n\x1a\n"


def cdr_folder(name):
    return name.startswith("#") and name[1:].strip().casefold() == "cdr"


def sketch_name(name):
    normalized = unicodedata.normalize("NFC", name).casefold()
    backup = re.match(r"^(?:резервная[ _-]+копия|автосохранение|автоматическая[ _-]+копия|backup(?:[ _-]+of)?|auto[ _-]?backup|autosave)(?:[ _.-]|$)", normalized)
    return (not name.startswith((".", "~")) and Path(name).suffix.casefold() == ".cdr"
            and not backup and not re.search(r"(?:[ _.-](?:backup|bak|autosave))\.cdr$", normalized))


def folder_path(relative):
    path = Path(relative)
    if (path.is_absolute() or len(path.parts) < 3 or any(part.startswith(".") for part in path.parts)
            or not cdr_folder(path.parent.name) or not sketch_name(path.name)):
        raise ValueError("Выберите эскиз CDR непосредственно в #cdr заказа")
    return path.parent.as_posix()


def read(blocks):
    result = {}
    for line in blocks.get(BLOCK, "").splitlines():
        if not line.strip():
            continue
        try:
            filename, end = json.JSONDecoder().raw_decode(line)
            tail = line[end:]
            state = next((key for key, label in LABELS.items() if tail == ": " + label), None)
            if not isinstance(filename, str) or Path(filename).name != filename or not sketch_name(filename) or state is None:
                return None
            filename = unicodedata.normalize("NFC", filename)
            if filename in result:
                return None
            result[filename] = state
        except (ValueError, TypeError):
            return None
    return result


def write(blocks, filename, value):
    if not isinstance(value, str) or value not in LABELS:
        raise ValueError("Выберите актуальность эскиза")
    states = read(blocks)
    if states is None:
        raise ValueError(f"Раздел [{BLOCK}] содержит неизвестный текст; он сохранён без замены. Проверьте !.txt в #cdr")
    states[unicodedata.normalize("NFC", filename)] = value
    body = "\n".join(json.dumps(name, ensure_ascii=False) + ": " + LABELS[state] for name, state in states.items())
    return {**blocks, BLOCK: body}


def info(record, filename, error=""):
    states = read(record["extra_blocks"]) if record else None
    return {"value": states.get(unicodedata.normalize("NFC", filename), "none") if states is not None else None,
            "revision": record["revision"] if record else None,
            "sync_pending": record["sync_pending"] if record else False,
            "sync_error": record["sync_error"] if record else "",
            "error": error or (f"Проверьте раздел [{BLOCK}] в !.txt папки #cdr" if record and states is None else "")}


def group_info(record):
    result = info(record, "")
    result.pop("value")
    result["states"] = read(record["extra_blocks"])
    return result


def embedded_preview(target, *, allow_bmp=False):
    """Read saved Corel thumbnails; never extract archive paths to disk."""
    try:
        with zipfile.ZipFile(target) as archive:
            entries = {entry.filename.casefold(): entry for entry in archive.infolist()}
            for name in ("previews/thumbnail.png", "previews/page1.png"):
                entry = entries.get(name)
                if not entry or not 24 <= entry.file_size <= MAX_PREVIEW or entry.flag_bits & 1:
                    continue
                with archive.open(entry) as stream:
                    raw = stream.read(MAX_PREVIEW + 1)
                if not 24 <= len(raw) <= MAX_PREVIEW or raw[:8] != PNG or raw[12:16] != b"IHDR":
                    continue
                width, height = struct.unpack(">II", raw[16:24])
                if width and height and width <= 16384 and height <= 16384 and width * height <= 40_000_000:
                    return raw
            if allow_bmp:
                for name in ("metadata/thumbnails/thumbnail.bmp", "metadata/thumbnails/page1.bmp"):
                    entry = entries.get(name)
                    if not entry or not 24 <= entry.file_size <= MAX_PREVIEW or entry.flag_bits & 1:
                        continue
                    with archive.open(entry) as stream:
                        raw = stream.read(MAX_PREVIEW + 1)
                    if not 24 <= len(raw) <= MAX_PREVIEW:
                        continue
                    # Recent Corel files also put PNG bytes under .bmp names.
                    if raw[:8] == PNG and raw[12:16] == b'IHDR':
                        width, height = struct.unpack('>II', raw[16:24])
                        if 0 < width <= 16384 and 0 < height <= 16384 and width * height <= 40_000_000:
                            return raw
                    if len(raw) < 54 or raw[:2] != b'BM':
                        continue
                    header = struct.unpack_from('<I', raw, 14)[0]
                    width, height = struct.unpack_from('<ii', raw, 18)
                    if header >= 40 and 0 < width <= 16384 and 0 < abs(height) <= 16384 and width * abs(height) <= 40_000_000:
                        return raw
    except (zipfile.BadZipFile, KeyError, RuntimeError, EOFError, NotImplementedError, zlib.error) as error:
        raise ValueError("Встроенное превью CDR недоступно") from error
    raise ValueError("В CDR нет доступного встроенного превью" if allow_bmp else "В CDR нет доступного встроенного PNG-превью")


def fingerprint(target):
    stat = target.stat()
    return hashlib.sha256(f"{target}:{stat.st_dev}:{stat.st_ino}:{stat.st_size}:{stat.st_mtime_ns}:{stat.st_ctime_ns}".encode()).hexdigest()


def preview(target, data_dir, *, read_bytes=None, allow_bmp=False):
    digest = fingerprint(target)
    cache = Path(data_dir) / "sketch-previews"
    cached = cache / (digest + ".png")
    if cached.is_file():
        return cached
    source = io.BytesIO(read_bytes(target, max_bytes=20 * 1024 * 1024)) if read_bytes else target
    raw = embedded_preview(source, allow_bmp=allow_bmp)
    if fingerprint(target) != digest:
        raise ValueError("Эскиз изменился во время чтения. Обнови страницу")
    cache.mkdir(parents=True, exist_ok=True)
    if raw[:2] == b'BM':
        with tempfile.TemporaryDirectory(prefix='.sketch-bmp-', dir=cache) as staging:
            source, converted = Path(staging) / 'preview.bmp', Path(staging) / 'preview.png'
            source.write_bytes(raw)
            try:
                subprocess.run(['/usr/bin/sips', '-s', 'format', 'png', str(source), '--out', str(converted)],
                               check=True, timeout=15, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                raw = converted.read_bytes()
            except (OSError, subprocess.SubprocessError) as error:
                raise ValueError('Не удалось показать встроенное превью CDR. Открой оригинал на Mac') from error
    with tempfile.NamedTemporaryFile(prefix=".sketch-", suffix=".png", dir=cache, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(raw)
    try:
        temporary.replace(cached)
    finally:
        temporary.unlink(missing_ok=True)
    return cached


def corel_app():
    candidates = []
    for root in (Path("/Applications"), Path.home() / "Applications"):
        for pattern in ("CorelDRAW*.app", "CorelDRAW Graphics Suite/CorelDRAW*.app", "CorelDRAW Graphics Suite/*/CorelDRAW*.app"):
            for app in root.glob(pattern):
                try:
                    data = plistlib.loads((app / "Contents/Info.plist").read_bytes())
                    if data.get("CFBundleIdentifier", "").casefold().endswith(".coreldraw"):
                        version = tuple(int(part) for part in re.findall(r"\d+", data.get("CFBundleShortVersionString", "0")))
                        candidates.append((version, str(app)))
                except (OSError, ValueError):
                    continue
    if not candidates:
        raise ValueError("CorelDRAW не найден на рабочем Mac M4")
    return max(candidates)[1]


def open_corel(target):
    try:
        subprocess.run(["/usr/bin/open", "-a", corel_app(), str(target)], check=True, capture_output=True, timeout=15)
    except (subprocess.SubprocessError, OSError) as error:
        raise ValueError("Не удалось открыть эскиз в CorelDRAW на M4") from error
