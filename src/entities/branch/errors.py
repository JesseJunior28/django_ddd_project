from src.errors.domain_errors import BusinessError


class BranchNotFoundError(BusinessError):
    def __init__(self, branch_id):
        value = int(branch_id) if isinstance(branch_id, float) and branch_id.is_integer() else branch_id
        super().__init__(f"Loja com ID {value} não foi encontrada.")
