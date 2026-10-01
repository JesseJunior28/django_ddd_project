from src.errors.domain_errors import BusinessError


class ZoneNameConflict(BusinessError):
    def __init__(self): super().__init__("Já existe um setor com esse nome.")
class ZoneNotFoundError(BusinessError):
    def __init__(self, value): super().__init__(f"Zona com ID {value} não foi encontrada.")
class ZoneWithDepartmentsConflict(BusinessError):
    def __init__(self): super().__init__("Existem departamentos associados ao setor.")
class DepartmentNameConflict(BusinessError):
    def __init__(self): super().__init__("Já existe um departamento com esse nome nesse setor.")
class DepartmentNotFoundError(BusinessError):
    def __init__(self, value): super().__init__(f"Departmento com ID {value} não foi encontrado.")
class DepartmentWithLevelsConflict(BusinessError):
    def __init__(self): super().__init__("Existem níveis associados ao departamento.")
class LevelNameConflict(BusinessError):
    def __init__(self): super().__init__("Já existe um nível com esse nome nesse departamento.")
class LevelNotFound(BusinessError):
    def __init__(self, value): super().__init__(f"Nível com ID {value} não foi encontrado.")
