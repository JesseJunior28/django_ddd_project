from src.entities.branch.service import BranchService
from .use_case import UpdateBranchUseCase
def build_use_case(): return UpdateBranchUseCase(BranchService())
