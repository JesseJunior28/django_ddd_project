from django.db.models import Q

from src.entities.product.models import BaseProduct
from src.middlewares.auth import AuthenticatedController


class BaseProductView(AuthenticatedController):
    authorized_roles = ("ADMIN",)

    def get(self, request):
        if request.path.endswith("get-total-base-products"):
            return self.ok({"totalBaseProducts": BaseProduct.objects.count()})
        query = request.query_params.get("queryString")
        try:
            page_number = int(request.query_params.get("pageNumber", 1))
            page_size = int(request.query_params.get("pageSize", 10))
        except ValueError:
            return self.bad_request({"name": "InputValidationError", "message": "Erro de validação"})
        products = BaseProduct.objects.select_related("brand__industry")
        if query:
            filter_query = Q(name__icontains=query) | Q(ean__icontains=query)
            if len(query) <= 7:
                try:
                    filter_query |= Q(sku=int(query))
                except ValueError:
                    pass
            products = products.filter(filter_query)
        total = products.count()
        offset = (page_number - 1) * page_size
        return self.ok({"totalPages": -(-total // page_size), "results": [self._entity(item) for item in products[offset:offset + page_size]]})

    @staticmethod
    def _entity(product):
        response = {"id": product.id, "sku": product.sku, "ean": product.ean, "name": product.name,
                    **({"family": product.family} if product.family else {}), **({"width": product.width} if product.width else {}),
                    **({"height": product.height} if product.height else {}), **({"length": product.length} if product.length else {}), "createdAt": product.created_at}
        if product.brand_id:
            response["brandId"] = product.brand_id
            response["brand"] = {"id": product.brand_id, "name": product.brand.name, "industryId": product.brand.industry_id, "industryName": product.brand.industry.name}
        return response
