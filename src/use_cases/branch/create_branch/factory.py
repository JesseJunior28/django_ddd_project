from .use_case import CreateBranchUseCase
from src.entities.branch.service import BranchService


def build_use_case() -> CreateBranchUseCase:
    return CreateBranchUseCase(BranchService())
