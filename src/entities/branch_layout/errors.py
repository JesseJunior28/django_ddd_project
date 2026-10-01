from src.errors.domain_errors import BusinessError


class BranchLayoutNotFound(BusinessError):
    def __init__(self, branch_id): super().__init__(f"Layout da loja com id {branch_id} não foi encontrado.")


class BranchLayoutAlreadyExist(BusinessError):
    def __init__(self, branch_id): super().__init__(f"Já existe um layout para a loja com id {branch_id}.")


class BranchLayoutVersionCodeValidationError(BusinessError):
    def __init__(self, branch_id): super().__init__(f"Erro ao validar código da versão do layout da loja {branch_id}.")


class LayoutElementNotFound(BusinessError):
    def __init__(self, element_id): super().__init__(f"Layout Element com id {element_id} não foi encontrado.")


class ModuleNonMarketingPointConflict(BusinessError):
    def __init__(self): super().__init__("O módulo não é de um planograma de ponto de marketing.")


class ElementNonMarketingPointConflict(BusinessError):
    def __init__(self): super().__init__("Esse módulo só pode ser associado a pontos de marketing.")


class ElementPlanogramDepartmentConflict(BusinessError):
    def __init__(self, planogram_id, department_name): super().__init__(f"Já exite um planograma ({planogram_id}) do departamento {department_name} cadastrado nessa loja.")


class ElementConfigurationModuleConflict(BusinessError):
    def __init__(self, element_id, module_id): super().__init__(f"O módulo com id {module_id} já está configurado no elemento com id {element_id}.")
