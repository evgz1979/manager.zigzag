"""Manual calendar placement, independent of dates, deadlines and finances."""
import json

CALENDAR_LAYOUT_VERSION = 1
COMPACT_BLOCK = "Мелкий заказ календаря"


# Читает строгую отметку мелкого заказа из дополнительных блоков.
# Разбирает JSON; вызывающий код должен учитывать ошибки или неизвестный формат.
def read_compact(blocks):
    if COMPACT_BLOCK not in blocks:
        return False
    try:
        value = json.loads(blocks[COMPACT_BLOCK])
        if (not isinstance(value, dict) or set(value) != {"version", "enabled"}
                or type(value["version"]) is not int or value["version"] != 1
                or type(value["enabled"]) is not bool):
            return None
        return value["enabled"]
    except (ValueError, TypeError):
        return None


# Сериализует известную отметку мелкого заказа без замены неизвестного формата.
# При недопустимом состоянии возбуждает ValueError.
def write_compact(blocks, enabled):
    if type(enabled) is not bool:
        raise ValueError("Укажи состояние отметки «Мелкий заказ»")
    if read_compact(blocks) is None:
        raise ValueError("Неизвестная отметка «Мелкий заказ» сохранена без изменений")
    return {**blocks, COMPACT_BLOCK: json.dumps({"version": 1, "enabled": enabled}, ensure_ascii=False)}


# Фиксирует в настройках базы использование несовместимого со старым кодом формата.
# Работает с таблицами metadata_settings.
def mark_contract(db):
    from local_metadata import schema
    schema(db)
    db.execute("INSERT INTO metadata_settings VALUES ('calendar_layout','1') ON CONFLICT(key) DO UPDATE SET value=excluded.value")
