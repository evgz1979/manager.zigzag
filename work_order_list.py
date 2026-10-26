"""Orders of the favorite supplier sections, shown together in #work."""
from pathlib import Path

from event_folder_undo import guard_database
from folder_structure import dated, is_work_root, is_print_section
from object_orders import ObjectOrders, LOCK, canonical
import work_orders


class WorkOrderList(ObjectOrders):
    scope_kind = "work_orders_scope"
    folder_kind = "work_order_folder"

    def path(self, relative):
        relative = canonical(self.store.path(relative))
        if len(Path(relative).parts) != 1 or not is_work_root(relative):
            raise ValueError("Выбери корень # work")
        guard_database(self.store.database, relative, include_children=True)
        return relative

    def sections(self, relative):
        records = work_orders.read_supplier_favorites(self.store, relative)
        return sorted((row for row in records.values() if row["is_favorite"] is True and not is_print_section(row["path"])),
                      key=lambda row: (row["position"], row["path"]))

    def allowed_paths(self, relative, inactive=(), show_inactive=False):
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
            self.save_catalog(relative, found, errors)

    def read(self, relative, **kwargs):
        result = super().read(relative, **kwargs)
        with self.store.connect() as db:
            groups = [{"key": row["path"], "label": Path(row["path"]).name.lstrip("#").strip(),
                       "color": work_orders.supplier_color(db, row["path"])} for row in self.sections(result["path"])]
        colors = {row["key"]: row["color"] for row in groups}
        for order in result["orders"]:
            order["work_supplier"] = work_orders.supplier_name(order["path"])
            order["work_supplier_color"] = colors.get(canonical(Path(order["path"]).parent.as_posix()))
        result["groups"] = groups + [{"key": result["path"], "label": "Заказы производства", "color": None}]
        return result
