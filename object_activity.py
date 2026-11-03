"""Object visibility using the shared SQLite activity index and legacy marker compatibility."""
import os
from pathlib import Path

from client_activity import ClientActivity
from folder_structure import folder_role

BLOCK = "Активность объекта"


# Объединяет операции модуля: индекс неактивности объектов на основе механизма активности клиента.
# Основные операции: matches, refresh.
class ObjectActivity(ClientActivity):
    table = "object_activity"
    block = BLOCK
    entity = "объекта"

    # Проверяет соответствие папки роли индексируемой сущности.
    # Возвращает `folder_role(self.root, path)['folderKind'] == 'object'`.
    def matches(self, path):
        return folder_role(self.root, path)["folderKind"] == "object"

    # Обновляет индекс из разрешённого источника данных.
    # Передаёт работу `os.walk`, `Path`, `name.startswith`.
    def refresh(self):
        # Только контейнеры и карточки объектов; в заказы, #… и ссылки не входим.
        # Сохраняет ошибку обхода, не выдавая неполный результат за полный.
        # Передаёт работу `print`.
        def on_error(error):
            print(f"Активность объектов: {error}", flush=True)

        for current, dirs, _ in os.walk(self.root, followlinks=False, onerror=on_error):
            parent = Path(current)
            allowed = []
            for name in dirs:
                folder = parent / name
                if name.startswith((".", "#")) or folder.is_symlink():
                    continue
                path = folder.relative_to(self.root).as_posix()
                try:
                    kind = folder_role(self.root, path)["folderKind"]
                    if kind not in {"root", "client", "catalog_group", "object", "year", "group"}:
                        continue
                    allowed.append(name)
                    if kind == "object":
                        self.read(path)
                except (OSError, ValueError) as error:
                    self.error(path, error)
            dirs[:] = allowed
