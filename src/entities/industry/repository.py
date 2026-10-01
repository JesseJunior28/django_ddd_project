from django.db.models import F, Q

from src.entities.branch.repository import PrismaContains

from .models import Industry


class IndustryRepository:
    def get(self, name=None):
        query = Industry.objects.prefetch_related("brands")
        if name:
            query = query.filter(Q(PrismaContains(F("name"), name)))
        return list(query.order_by("name")[:50])

    def get_by_id(self, industry_id):
        return Industry.objects.prefetch_related("brands").filter(id=industry_id).first()

    def get_by_name(self, name):
        return Industry.objects.filter(name=name).first()

    def create(self, name, brands):
        industry = Industry.objects.create(name=name)
        industry.brands.bulk_create([industry.brands.model(name=value, industry=industry) for value in brands])
        return self.get_by_id(industry.id)

    def update(self, industry, name, brands_to_add):
        industry.name = name
        industry.save(update_fields=["name"])
        industry.brands.bulk_create([industry.brands.model(name=value, industry=industry) for value in brands_to_add])
        return self.get_by_id(industry.id)

    def delete(self, industry):
        industry.delete()
