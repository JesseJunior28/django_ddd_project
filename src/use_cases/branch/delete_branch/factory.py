from src.entities.branch.service import BranchService
from .use_case import DeleteBranchUseCase
def build_use_case(): return DeleteBranchUseCase(BranchService())
