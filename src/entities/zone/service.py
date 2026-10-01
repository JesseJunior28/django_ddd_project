from src.core.either import right, wrong
from .models import Zone, Department, Level
from .errors import *


class ZoneService:
    @staticmethod
    def zone(zone):
        return {"id": zone.id, "name": zone.name, "hexColor": zone.hex_color,
                "isMarketingZone": zone.is_marketing_zone,
                "departments": [{"id": d.id, "name": d.name, "orientation": d.orientation, "zoneId": d.zone_id} for d in zone.departments.all()]}
    @staticmethod
    def department(value):
        return {"id": value.id, "name": value.name, "orientation": value.orientation, "zoneId": value.zone_id, "zoneName": value.zone.name}
    @staticmethod
    def level(value):
        return {"id": value.id, "name": value.name, **({"label": value.label} if value.label is not None else {}), "hexColor": value.hex_color, "divisions": value.divisions, "departmentId": value.department_id}
    def list_zones(self): return {"results": [self.zone(x) for x in Zone.objects.prefetch_related("departments").order_by("name")]}
    def list_departments(self): return {"results": [self.department(x) for x in Department.objects.select_related("zone").order_by("name")]}
    def list_levels(self, department_id): return {"results": [self.level(x) for x in Level.objects.filter(department_id=department_id).order_by("name")]}
    def create_zone(self, data):
        if Zone.objects.filter(name=data["name"]).exists(): return wrong(ZoneNameConflict())
        zone = Zone.objects.create(name=data["name"], hex_color=data["hexColor"])
        return right(self.zone(Zone.objects.prefetch_related("departments").get(pk=zone.id)))
    def update_zone(self, data):
        zone = Zone.objects.prefetch_related("departments").filter(pk=data.get("id")).first()
        if not zone: return wrong(ZoneNotFoundError(data.get("id")))
        if data.get("name") and Zone.objects.filter(name=data["name"]).exclude(pk=zone.id).exists(): return wrong(ZoneNameConflict())
        if "name" in data: zone.name = data["name"]
        if "hexColor" in data: zone.hex_color = data["hexColor"]
        zone.save()
        return right(self.zone(Zone.objects.prefetch_related("departments").get(pk=zone.id)))
    def delete_zone(self, value):
        zone = Zone.objects.filter(pk=value).first()
        if not zone: return wrong(ZoneNotFoundError(value))
        if zone.departments.exists(): return wrong(ZoneWithDepartmentsConflict())
        zone.delete(); return right(None)
    def create_department(self, data):
        zone = Zone.objects.filter(pk=data.get("zoneId")).first()
        if not zone: return wrong(ZoneNotFoundError(data.get("zoneId")))
        if Department.objects.filter(name=data["name"]).exists(): return wrong(DepartmentNameConflict())
        value = Department.objects.create(name=data["name"], orientation=data["orientation"], zone=zone)
        return right(self.department(Department.objects.select_related("zone").get(pk=value.id)))
    def update_department(self, data):
        value = Department.objects.select_related("zone").filter(pk=data.get("id")).first()
        if not value: return wrong(DepartmentNotFoundError(data.get("id")))
        if data.get("name") and Department.objects.filter(name=data["name"]).exclude(pk=value.id).exists(): return wrong(DepartmentNameConflict())
        if "zoneId" in data:
            zone = Zone.objects.filter(pk=data["zoneId"]).first()
            if not zone: return wrong(ZoneNotFoundError(data["zoneId"]))
            value.zone = zone
        for source, dest in (("name", "name"), ("orientation", "orientation")):
            if source in data: setattr(value, dest, data[source])
        value.save(); return right(self.department(Department.objects.select_related("zone").get(pk=value.id)))
    def delete_department(self, value):
        department = Department.objects.filter(pk=value).first()
        if not department: return wrong(DepartmentNotFoundError(value))
        if department.levels.exists(): return wrong(DepartmentWithLevelsConflict())
        department.delete(); return right(None)
    def create_level(self, data):
        department = Department.objects.filter(pk=data.get("departmentId")).first()
        if not department: return wrong(DepartmentNotFoundError(data.get("departmentId")))
        if Level.objects.filter(name=data["name"], department=department).exists(): return wrong(LevelNameConflict())
        value = Level.objects.create(name=data["name"], label=data.get("label"), hex_color=data["hexColor"], divisions=data["divisions"], department=department)
        return right(self.level(value))
    def update_level(self, data):
        value = Level.objects.filter(pk=data.get("id")).first()
        if not value: return wrong(LevelNotFound(data.get("id")))
        if "departmentId" in data:
            department = Department.objects.filter(pk=data["departmentId"]).first()
            if not department: return wrong(DepartmentNotFoundError(data["departmentId"]))
            value.department = department
        if data.get("name") and Level.objects.filter(name=data["name"], department=value.department).exclude(pk=value.id).exists(): return wrong(LevelNameConflict())
        for source, dest in (("name", "name"), ("label", "label"), ("hexColor", "hex_color"), ("divisions", "divisions")):
            if source in data: setattr(value, dest, data[source])
        value.save(); return right(self.level(value))
    def delete_level(self, value):
        level = Level.objects.filter(pk=value).first()
        if not level: return wrong(LevelNotFound(value))
        level.delete(); return right(None)
