from src.entities.branch.service import BranchService
from .use_case import GetBranchUseCase


def build_use_case():
    return GetBranchUseCase(BranchService())
