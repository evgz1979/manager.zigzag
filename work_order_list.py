"""Production order tables in #work and individual supplier sections."""
from pathlib import Path

from event_folder_undo import guard_database
from folder_structure import dated, is_work_root, is_supplier_root, is_print_section, in_freza
from object_orders import ObjectOrders, LOCK, canonical
import work_orders


def supplier_scope(relative):
    parts = Path(relative).parts
    return not is_print_section(relative) and not in_freza(relative) and (
        (len(parts) == 1 and is_supplier_root(parts[0])) or
        (len(parts) == 2 and is_work_root(parts[0]) and not dated(parts[1]) and not parts[1].startswith(".")))


class WorkOrderList(ObjectOrders):
    scope_kind = "work_orders_scope"
    folder_kind = "work_order_folder"

    def path(self, relative):
        relative = canonical(self.store.path(relative))
        if not (len(Path(relative).parts) == 1 and is_work_root(relative)) and not supplier_scope(relative):
            raise ValueError("Выбери корень # work или раздел поставщика")
        guard_database(self.store.database, relative, include_children=True)
        return relative

    def sections(self, relative):
        if supplier_scope(relative):
            return [{"path": relative}]
        records = work_orders.read_supplier_favorites(self.store, relative)
        return sorted((row for row in records.values() if row["is_favorite"] is True and not is_print_section(row["path"])),
                      key=lambda row: (work_orders.is_etc_section(row["path"]), row["position"], row["path"]))

    def allowed_paths(self, relative, inactive=(), show_inactive=False):
        if supplier_scope(relative):
            return lambda path: (canonical(Path(path).parent.as_posix()) == relative and
                                 not Path(path).name.startswith((".", "#")))
        sections = {row["path"] for row in self.sections(relative)}
        def allowed(path):
            path = canonical(path)
            parts = Path(path).parts
            if not parts or parts[0] != relative or parts[-1].startswith((".", "#")):
                return False
            return (len(parts) == 2 and dated(parts[1])) or (len(parts) == 3 and Path(path).parent.as_posix() in sections)
        return allowed

    def refresh(self, relative):
        source = self.store.path(relative)
        relative = self.path(source)
        target = self.store.target(source)
        allowed = self.allowed_paths(relative)
        with LOCK:
            found, errors = set(), []
            sections = {row["path"] for row in self.sections(relative)}
            try:
                children = list(target.iterdir())
                if len(children) > 20000:
                    raise ValueError("Слишком много папок производства; показан сохранённый список")
                for child in children:
                    if child.name.startswith(".") or child.is_symlink() or not child.is_dir():
                        continue
                    path = child.relative_to(self.store.root).as_posix()
                    if allowed(path):
                        found.add(canonical(path))
                    elif canonical(path) in sections:
                        try:
                            orders = list(child.iterdir())
                            if len(orders) + len(found) > 20000:
                                raise ValueError("Слишком много заказов производства; показан сохранённый список")
                            for order in orders:
                                order_path = order.relative_to(self.store.root).as_posix()
                                if allowed(order_path) and not order.is_symlink() and order.is_dir():
                                    found.add(canonical(order_path))
                        except (OSError, ValueError) as error:
                            errors.append(str(error))
            except (OSError, ValueError) as error:
                errors.append(str(error))
            self.save_catalog(relative, found, errors, allowed=allowed)

    def read(self, relative, **kwargs):
        result = super().read(relative, **kwargs)
        with self.store.connect() as db:
            groups = [{"key": row["path"], "label": Path(row["path"]).name.lstrip("#").strip(),
                       "color": work_orders.supplier_color(db, row["path"])} for row in self.sections(result["path"])]
        colors = {row["key"]: row["color"] for row in groups}
        for order in result["orders"]:
            order["work_supplier"] = work_orders.supplier_name(order["path"])
            order["work_supplier_color"] = colors.get(canonical(Path(order["path"]).parent.as_posix()))
        result["groups"] = groups if supplier_scope(result["path"]) else groups + [
            {"key": result["path"], "label": "Заказы производства", "color": None}]
        return result
