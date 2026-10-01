from django.test import TestCase

from src.entities.planogram.errors import MaxShelfWidthExceeded, PlanogramDepartmentConflict
from src.entities.planogram.models import Module, Planogram, Shelf, ShelfLevel
from src.entities.planogram.service import PlanogramService
from src.entities.zone.models import Department, Level, Zone


class PlanogramServiceTests(TestCase):
    def setUp(self):
        zone = Zone.objects.create(name="Z", hex_color="#000")
        self.department = Department.objects.create(name="D", orientation="ENTRY", zone=zone)
        self.level = Level.objects.create(name="L", hex_color="#fff", divisions=[], department=self.department)

    def test_creates_nested_structure(self):
        planogram = PlanogramService().create(department_id=self.department.id, name="P", max_module_width=100, modules=[{"sequence": 1, "shelves": [{"sequence": 1, "levels": [{"levelId": self.level.id, "width": 100, "sequence": 1, "expositionType": "SHELF"}]}]}])
        self.assertEqual(Planogram.objects.count(), 1)
        self.assertEqual(Module.objects.count(), 1)
        self.assertEqual(Shelf.objects.count(), 1)
        self.assertEqual(ShelfLevel.objects.count(), 1)
        self.assertEqual(planogram.name, "P")

    def test_rejects_width_above_module_limit_without_writes(self):
        with self.assertRaises(MaxShelfWidthExceeded):
            PlanogramService().create(department_id=self.department.id, name=None, max_module_width=10, modules=[{"sequence": 1, "shelves": [{"sequence": 1, "levels": [{"levelId": self.level.id, "width": 11, "sequence": 1, "expositionType": "SHELF"}]}]}])
        self.assertFalse(Planogram.objects.exists())

    def test_rejects_level_from_another_department(self):
        zone = Zone.objects.create(name="Other", hex_color="#111")
        department = Department.objects.create(name="Other", orientation="ENTRY", zone=zone)
        other = Level.objects.create(name="Other", hex_color="#222", divisions=[], department=department)
        with self.assertRaises(PlanogramDepartmentConflict):
            PlanogramService().create(department_id=self.department.id, name=None, max_module_width=10, modules=[{"sequence": 1, "shelves": [{"sequence": 1, "levels": [{"levelId": other.id, "width": 1, "sequence": 1, "expositionType": "SHELF"}]}]}])

    def test_reorders_shelf_levels_without_duplicate_sequences(self):
        planogram = PlanogramService().create(department_id=self.department.id, name=None, max_module_width=100, modules=[{"sequence": 1, "shelves": [{"sequence": 1, "levels": [{"levelId": self.level.id, "width": 10, "sequence": 1, "expositionType": "SHELF"}]}]}])
        shelf = planogram.modules.get().shelves.get()
        second = ShelfLevel.objects.create(shelf=shelf, level=self.level, width=10, sequence=2, exposition_type="SHELF")
        PlanogramService().update_shelf_level_sequence(second.id, 1)
        self.assertEqual(list(ShelfLevel.objects.filter(shelf=shelf).order_by("sequence").values_list("id", "sequence")), [(second.id, 1), (ShelfLevel.objects.exclude(pk=second.id).get().id, 2)])
