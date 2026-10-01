class PlanogramError(Exception):
    pass


class ModuleNotFound(PlanogramError):
    def __init__(self, value): super().__init__(f"Módulo com id {value} não foi encontrado.")


class ShelfNotFound(PlanogramError):
    def __init__(self, value): super().__init__(f"Prateleira com id {value} não foi encontrada.")


class PlanogramDepartmentConflict(PlanogramError):
    def __init__(self): super().__init__("Todos os níveis devem pertencer ao mesmo planograma.")


class ModuleSequenceConflict(PlanogramError):
    def __init__(self, sequence): super().__init__(f"Já existe um módulo com a sequência {sequence}.")


class ShelfSequenceConflict(PlanogramError):
    def __init__(self, sequence): super().__init__(f"Já existe uma prateleira com a sequência {sequence}.")


class ShelfLevelSequenceConflict(PlanogramError):
    def __init__(self, sequence): super().__init__(f"Já existe um nível na prateleira com a sequência {sequence}.")


class LevelsNotFound(PlanogramError):
    def __init__(self, ids): super().__init__(f"Os níveis com ids {' '.join(map(str, ids))} não foram encontrados.")


class MaxShelfWidthExceeded(PlanogramError):
    def __init__(self, width): super().__init__(f"O tamanho máximo de {width} cm da prateleira foi excedido.")


class PlanogramNotFound(PlanogramError):
    def __init__(self, value): super().__init__(f"O planogram com ID {value} não foi encontrado.")


class ShelfLevelNotFound(PlanogramError):
    def __init__(self, value): super().__init__(f"Nível da prateleira com id {value} não foi encontrado.")


class ShelfLevelExistanceConflict(PlanogramError):
    def __init__(self, value): super().__init__(f"A prateleira com id {value} tem níveis associados e não pode ser deletada.")


class ShelfExistanceConflict(PlanogramError):
    def __init__(self, value): super().__init__(f"O módulo com id {value} tem prateleiras associados e não pode ser deletado.")
