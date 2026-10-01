import logging

from src.core.either import right, wrong
from src.errors.domain_errors import PersistenceError

from .errors import IndustryAlreadyExistConflict, IndustryNotFoundError, IndustryWithBrandConflict
from .repository import IndustryRepository

logger = logging.getLogger(__name__)


class IndustryService:
    def __init__(self, repository=None):
        self.repository = repository or IndustryRepository()

    @staticmethod
    def entity(industry):
        return {
            "id": industry.id,
            "name": industry.name,
            "brands": [
                {"id": brand.id, "name": brand.name, "industryId": brand.industry_id}
                for brand in industry.brands.all()
            ],
        }

    def list_industries(self, name=None):
        return {"results": [self.entity(industry) for industry in self.repository.get(name)]}

    def create_industry(self, data):
        if self.repository.get_by_name(data["name"]):
            return wrong(IndustryAlreadyExistConflict(data["name"]))
        try:
            return right(self.entity(self.repository.create(data["name"], data["brands"])))
        except Exception:
            logger.exception("IndustryService.create_industry failed")
            return wrong(PersistenceError())

    def update_industry(self, data):
        industry = self.repository.get_by_id(data.get("id"))
        if not industry:
            return wrong(IndustryNotFoundError(data.get("id")))
        duplicate = self.repository.get_by_name(data["name"])
        if duplicate and duplicate.id != industry.id:
            return wrong(IndustryAlreadyExistConflict(data["name"]))
        try:
            return right(self.entity(self.repository.update(industry, data["name"], data["brandsToAdd"])))
        except Exception:
            logger.exception("IndustryService.update_industry failed")
            return wrong(PersistenceError())

    def delete_industry(self, industry_id):
        industry = self.repository.get_by_id(industry_id)
        if not industry:
            return wrong(IndustryNotFoundError(industry_id))
        try:
            self.repository.delete(industry)
            return right(None)
        except Exception:
            logger.exception("IndustryService.delete_industry failed")
            return wrong(PersistenceError())
