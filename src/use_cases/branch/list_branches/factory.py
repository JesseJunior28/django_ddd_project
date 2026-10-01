from src.entities.branch.service import BranchService
from .use_case import ListBranchesUseCase


def build_use_case():
    return ListBranchesUseCase(BranchService())
