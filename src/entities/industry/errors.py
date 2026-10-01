from src.errors.domain_errors import BusinessError


class IndustryAlreadyExistConflict(BusinessError):
    def __init__(self, name):
        super().__init__(f"Já existe uma indústria cadastrada com o nome {name}")


class IndustryNotFoundError(BusinessError):
    def __init__(self, industry_id):
        super().__init__(f"Industria com ID {industry_id} não foi encontrada.")


class IndustryWithBrandConflict(BusinessError):
    def __init__(self):
        super().__init__("Existe marca associada a esta industria.")
