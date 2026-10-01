import logging
from datetime import timezone

from .repository import BranchRepository
from .errors import BranchNotFoundError
from src.core.either import right, wrong
from src.errors.domain_errors import PersistenceError

logger = logging.getLogger(__name__)


class BranchService:
    def __init__(self, repository=None):
        self.repository = repository or BranchRepository()

    def get_branch_by_id(self, branch_id):
        branch = self.repository.find_by_id(branch_id)
        return right(self.map_to_entity(branch)) if branch else wrong(BranchNotFoundError(branch_id))

    def create_branch(self, data):
        try:
            return right(self.map_to_entity(self.repository.create_from_contract(data)))
        except Exception:
            logger.exception("BranchService.create_branch failed")
            return wrong(PersistenceError())

    def get_branches(self, query, page_size, page_number):
        try:
            return [self.map_to_entity(branch) for branch in self.repository.get(query, page_size, page_number)]
        except Exception:
            logger.warning("BranchService.get_branches failed")
            return []

    def count_branches(self, query):
        # Erros de persistência precisam atravessar este fluxo sem serem mascarados.
        return self.repository.count_branches(query)

    def update_branch(self, branch_id, data):
        if not self.repository.find_by_id(branch_id):
            return wrong(BranchNotFoundError(branch_id))
        try:
            return right(self.map_to_entity(self.repository.update(branch_id, **data)))
        except Exception:
            logger.exception("BranchService.update_branch failed")
            return wrong(PersistenceError())

    def delete_branch(self, branch_id):
        if not self.repository.find_by_id(branch_id):
            return wrong(BranchNotFoundError(branch_id))
        try:
            self.repository.delete(branch_id)
            return right(None)
        except Exception:
            logger.exception("BranchService.delete_branch failed")
            return wrong(PersistenceError())

    @staticmethod
    def map_to_entity(branch):
        def date(value):
            return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        return {"id": branch.id, "name": branch.name, "city": branch.city,
                "address": branch.address, "uf": branch.uf, "hasLayout": False,
                "createdAt": date(branch.created_at), "updatedAt": date(branch.updated_at)}
