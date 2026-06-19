from .use_case import CreateBranchUseCase
from src.entities.branch.repository import BranchRepository


def build_use_case() -> CreateBranchUseCase:
    repository = BranchRepository()
    return CreateBranchUseCase(repository)
