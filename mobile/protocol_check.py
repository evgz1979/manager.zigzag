"""Real Python/Swift protocol round trip in an isolated temporary directory."""
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from orders import OrderStore
from mobile_sync import MobileBridge

with tempfile.TemporaryDirectory(prefix="zigzag-phone-protocol-") as temporary:
    base = Path(temporary)
    root = base / "archive"
    relative = "Клиент/Объект/2026-10-18 - Заказ"
    folder = root / relative
    folder.mkdir(parents=True)
    (folder / "Фото.txt").write_text("Документ не меняется")
    store = OrderStore(root, base / "mac-local", {"new": "Новый"}, database_only=False)
    store.add(relative, {"title": "Тест обмена", "note": "Mac", "extra_blocks": {"Задачи": "- [ ] С Mac"}})
    bridge = MobileBridge(store)
    bridge.configure(True)
    bridge.run()
    binary = base / "probe"
    subprocess.run(["swiftc", "-swift-version", "5", "-module-cache-path", str(base / "swift-cache"),
                    str(PROJECT / "mobile/Core.swift"), str(PROJECT / "mobile/ProtocolProbe.swift"), "-o", str(binary)], check=True)
    subprocess.run([str(binary), str(root), "queue"], check=True)
    bridge.run()
    bridge.run()
    subprocess.run([str(binary), str(root), "verify"], check=True)
    assert (folder / "Фото.txt").read_text() == "Документ не меняется"
