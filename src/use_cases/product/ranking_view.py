from src.entities.product.models import Product, ProductExpositionDetail
from src.entities.zone.models import Level
from src.middlewares.auth import AuthenticatedController


class ProductRankingView(AuthenticatedController):
    authorized_roles = ("ADMIN",)

    def get(self, request):
        try:
            level_id = int(request.query_params.get("levelId"))
            product_id = int(request.query_params.get("productId"))
        except (TypeError, ValueError):
            return self.bad_request({"name": "InputValidationError", "message": "Erro de validação"})
        if not Level.objects.filter(pk=level_id).exists():
            return self.not_found({"name": "LevelNotFound", "message": f"Nível com ID {level_id} não foi encontrado."})
        product = Product.objects.filter(pk=product_id).first()
        if not product:
            return self.not_found({"name": "ProductNotFoundError", "message": f"Produto com ID {product_id} não foi encontrado."})
        details = ProductExpositionDetail.objects.filter(level_id=level_id)
        last = details.order_by("-ranking", "-priority").first()
        if not last:
            return self.ok({"ranking": 1, "priority": 1})
        if not product.family:
            return self.ok({"ranking": last.ranking + 1, "priority": 1})
        same_family = details.filter(product__family=product.family).order_by("-ranking", "-priority").first()
        return self.ok({"ranking": (same_family.ranking if same_family else last.ranking) + 1, "priority": 1})
