"""Count direct Inbox files without opening documents or walking subfolders."""
import os
from pathlib import Path
import unicodedata


def snapshot(root):
    root = Path(root)
    try:
        with os.scandir(root) as entries:
            folders = [entry.name for entry in entries
                       if entry.name.startswith('#')
                       and unicodedata.normalize('NFC', entry.name[1:]).casefold().strip() == 'inbox'
                       and entry.is_dir(follow_symlinks=False)]
        if not folders:
            return {'path': '', 'count': 0, 'error': ''}
        if len(folders) != 1:
            return {'path': '', 'count': None, 'error': 'Найдено несколько папок #inbox'}
        name = folders[0]
        with os.scandir(root / name) as entries:
            count = sum(1 for entry in entries
                        if not entry.name.startswith('.') and entry.is_file(follow_symlinks=False))
        return {'path': name, 'count': count, 'error': ''}
    except OSError:
        return {'path': '', 'count': None, 'error': 'Не удалось проверить папку #inbox. Повторим автоматически'}
