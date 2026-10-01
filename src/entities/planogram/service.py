from django.db import transaction

from src.entities.zone.models import Department, Level

from .errors import (LevelsNotFound, MaxShelfWidthExceeded, ModuleSequenceConflict,
                     ModuleNotFound, PlanogramDepartmentConflict, ShelfLevelSequenceConflict,
                     ShelfLevelExistanceConflict, ShelfLevelNotFound, ShelfExistanceConflict,
                     ShelfNotFound, ShelfSequenceConflict)
from .models import Module, Planogram, Shelf, ShelfLevel


class PlanogramService:
    """Domain creation rules shared by the v0.5 HTTP adapters."""

    def create(self, *, department_id, name, max_module_width, modules):
        department = Department.objects.filter(pk=department_id).first()
        if not department:
            return None
        self._validate_sequences(modules)
        level_ids = [level["levelId"] for module in modules for shelf in module["shelves"] for level in shelf["levels"]]
        levels = {level.id: level for level in Level.objects.filter(pk__in=level_ids)}
        missing = [level_id for level_id in level_ids if level_id not in levels]
        if missing:
            raise LevelsNotFound(missing)
        if any(level.department_id != department_id for level in levels.values()):
            raise PlanogramDepartmentConflict()
        for module in modules:
            for shelf in module["shelves"]:
                if sum(level["width"] for level in shelf["levels"]) > max_module_width:
                    raise MaxShelfWidthExceeded(max_module_width)

        with transaction.atomic():
            planogram = Planogram.objects.create(name=name, department=department)
            for module_data in modules:
                module = Module.objects.create(planogram=planogram, sequence=module_data["sequence"], width=max_module_width)
                for shelf_data in module_data["shelves"]:
                    shelf = Shelf.objects.create(module=module, sequence=shelf_data["sequence"])
                    ShelfLevel.objects.bulk_create([
                        ShelfLevel(shelf=shelf, level=levels[level_data["levelId"]], width=level_data["width"],
                                   sequence=level_data["sequence"], exposition_type=level_data["expositionType"])
                        for level_data in shelf_data["levels"]
                    ])
        return planogram

    def create_module(self, planogram_id, width):
        planogram = Planogram.objects.filter(pk=planogram_id).first()
        if not planogram:
            return None
        with transaction.atomic():
            planogram = Planogram.objects.select_for_update().get(pk=planogram_id)
            Module.objects.create(planogram=planogram, width=width, sequence=Module.objects.filter(planogram=planogram).count() + 1)
        return planogram

    def create_shelf(self, module_id):
        module = Module.objects.filter(pk=module_id).first()
        if not module:
            raise ModuleNotFound(module_id)
        with transaction.atomic():
            module = Module.objects.select_for_update().get(pk=module_id)
            Shelf.objects.create(module=module, sequence=Shelf.objects.filter(module=module).count() + 1)
        return module

    def add_shelf_level(self, shelf_id, level_id, width, exposition_type):
        shelf = Shelf.objects.select_related("module__planogram").filter(pk=shelf_id).first()
        if not shelf:
            raise ShelfNotFound(shelf_id)
        level = Level.objects.filter(pk=level_id).first()
        if not level:
            raise LevelsNotFound([level_id])
        if level.department_id != shelf.module.planogram.department_id:
            raise PlanogramDepartmentConflict()
        if sum(shelf.levels.values_list("width", flat=True)) + width > shelf.module.width:
            raise MaxShelfWidthExceeded(shelf.module.width)
        with transaction.atomic():
            shelf = Shelf.objects.select_for_update().get(pk=shelf_id)
            if sum(shelf.levels.values_list("width", flat=True)) + width > shelf.module.width:
                raise MaxShelfWidthExceeded(shelf.module.width)
            ShelfLevel.objects.create(shelf=shelf, level=level, width=width, exposition_type=exposition_type,
                                      sequence=shelf.levels.count() + 1)
        return shelf

    def delete_shelf_level(self, shelf_level_id):
        detail = ShelfLevel.objects.select_related("shelf").filter(pk=shelf_level_id).first()
        if not detail:
            return None
        with transaction.atomic():
            shelf = Shelf.objects.select_for_update().get(pk=detail.shelf_id)
            ShelfLevel.objects.filter(pk=detail.pk).delete()
            self.normalize_sequences(ShelfLevel.objects.select_for_update().filter(shelf=shelf))
        return shelf

    def update_shelf_level_sequence(self, shelf_level_id, sequence):
        detail = ShelfLevel.objects.select_related("shelf").filter(pk=shelf_level_id).first()
        if not detail:
            raise ShelfLevelNotFound(shelf_level_id)
        with transaction.atomic():
            shelf = Shelf.objects.select_for_update().get(pk=detail.shelf_id)
            siblings = list(ShelfLevel.objects.select_for_update().filter(shelf=shelf).exclude(pk=detail.pk).order_by("sequence", "id"))
            position = max(0, min(sequence - 1, len(siblings)))
            siblings.insert(position, detail)
            for item in siblings:
                ShelfLevel.objects.filter(pk=item.pk).update(sequence=-item.pk)
            for index, item in enumerate(siblings, start=1):
                ShelfLevel.objects.filter(pk=item.pk).update(sequence=index)
        return shelf

    def delete_module(self, module_id):
        module = Module.objects.filter(pk=module_id).first()
        if not module:
            raise ModuleNotFound(module_id)
        if module.shelves.exists():
            raise ShelfExistanceConflict(module_id)
        with transaction.atomic():
            planogram = Planogram.objects.select_for_update().get(pk=module.planogram_id)
            Module.objects.filter(pk=module_id).delete()
            self.normalize_sequences(Module.objects.select_for_update().filter(planogram=planogram))
        return planogram

    def delete_shelf(self, shelf_id):
        shelf = Shelf.objects.filter(pk=shelf_id).first()
        if not shelf:
            raise ShelfNotFound(shelf_id)
        if shelf.levels.exists():
            raise ShelfLevelExistanceConflict(shelf_id)
        with transaction.atomic():
            module = Module.objects.select_for_update().get(pk=shelf.module_id)
            Shelf.objects.filter(pk=shelf_id).delete()
            self.normalize_sequences(Shelf.objects.select_for_update().filter(module=module))
        return module

    def update_module_sequence(self, module_id, sequence):
        module = Module.objects.filter(pk=module_id).first()
        if not module:
            raise ModuleNotFound(module_id)
        with transaction.atomic():
            planogram = Planogram.objects.select_for_update().get(pk=module.planogram_id)
            self._move(Module.objects.select_for_update().filter(planogram=planogram), module_id, sequence)
        return planogram

    def update_shelf_sequence(self, shelf_id, sequence):
        shelf = Shelf.objects.filter(pk=shelf_id).first()
        if not shelf:
            raise ShelfNotFound(shelf_id)
        with transaction.atomic():
            module = Module.objects.select_for_update().get(pk=shelf.module_id)
            self._move(Shelf.objects.select_for_update().filter(module=module), shelf_id, sequence)
        return module

    def update_shelf_level(self, shelf_level_id, width=None, exposition_type=None):
        detail = ShelfLevel.objects.select_related("shelf__module").filter(pk=shelf_level_id).first()
        if not detail:
            raise ShelfLevelNotFound(shelf_level_id)
        if width is not None:
            total = sum(detail.shelf.levels.exclude(pk=detail.pk).values_list("width", flat=True))
            if total + width > detail.shelf.module.width:
                raise MaxShelfWidthExceeded(detail.shelf.module.width)
        values = {}
        if width is not None:
            values["width"] = width
        if exposition_type is not None:
            values["exposition_type"] = exposition_type
        if values:
            ShelfLevel.objects.filter(pk=detail.pk).update(**values)
        return ShelfLevel.objects.select_related("level").get(pk=detail.pk)

    def update_planogram_name(self, planogram_id, name):
        planogram = Planogram.objects.filter(pk=planogram_id).first()
        if not planogram:
            return None
        Planogram.objects.filter(pk=planogram_id).update(name=name)
        return planogram

    def update_planogram_status(self, planogram_id, is_active):
        planogram = Planogram.objects.filter(pk=planogram_id).first()
        if not planogram:
            return None
        Planogram.objects.filter(pk=planogram_id).update(is_active=is_active)
        return planogram

    @staticmethod
    def _move(queryset, item_id, sequence):
        items = list(queryset.order_by("sequence", "id"))
        target = next(item for item in items if item.pk == item_id)
        items.remove(target)
        items.insert(max(0, min(sequence - 1, len(items))), target)
        for item in items:
            type(item).objects.filter(pk=item.pk).update(sequence=-item.pk)
        for position, item in enumerate(items, start=1):
            type(item).objects.filter(pk=item.pk).update(sequence=position)

    @staticmethod
    def _validate_sequences(modules):
        def unique(items, error):
            sequences = [item["sequence"] for item in items]
            if len(sequences) != len(set(sequences)):
                for sequence in sequences:
                    if sequences.count(sequence) > 1:
                        raise error(sequence)

        unique(modules, ModuleSequenceConflict)
        for module in modules:
            unique(module["shelves"], ShelfSequenceConflict)
            for shelf in module["shelves"]:
                unique(shelf["levels"], ShelfLevelSequenceConflict)

    @staticmethod
    def normalize_sequences(queryset):
        """Renumber a locked sibling queryset from one, preserving its order."""
        items = list(queryset.order_by("sequence", "id"))
        for item in items:
            type(item).objects.filter(pk=item.pk).update(sequence=-item.pk)
        for position, item in enumerate(items, start=1):
            type(item).objects.filter(pk=item.pk).update(sequence=position)
