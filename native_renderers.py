"""Сборка Swift-помощников с постоянным путём кеша между релизами."""
import hashlib
import subprocess
import tempfile
from pathlib import Path


def build(source, data_dir, name, timeout):
    source = Path(source).resolve()
    data_dir = Path(data_dir).resolve()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:20]
    binary = data_dir / "native-renderers" / f"{name}-{digest}"
    if not binary.is_file():
        binary.parent.mkdir(parents=True, exist_ok=True)
        # Прежний кеш содержит абсолютные пути через data разных релизов.
        cache = data_dir / "swift-cache-v2"
        with tempfile.TemporaryDirectory(prefix=f".{name}-", dir=binary.parent) as temporary:
            output = Path(temporary) / name
            subprocess.run(["/usr/bin/swiftc", "-O", "-module-cache-path", str(cache),
                            str(source), "-o", str(output)], check=True, capture_output=True, timeout=timeout)
            output.replace(binary)
    return binary
