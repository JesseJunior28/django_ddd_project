from django.db import transaction
from django.db.models import F
from rest_framework.response import Response

from src.entities.product.models import Product, ProductExpositionDetail
from src.entities.zone.models import Level
from src.middlewares.auth import AuthenticatedController
from .contract_view import ProductContractView


class ProductExpositionView(AuthenticatedController):
    authorized_roles = ("ADMIN",)

    def post(self, request):
        data = request.data
        if "levelExpositions" in data:
            return self._import(request)
        required = ("productId", "levelId", "ranking", "priority", "forefront", "minStock", "fixedSide")
        if any(key not in data for key in required):
            return self.bad_request({"name": "InputValidationError", "message": "Erro de validação"})
        try:
            product_id, level_id, ranking, priority, forefront, min_stock = (int(data[key]) for key in ("productId", "levelId", "ranking", "priority", "forefront", "minStock"))
        except (TypeError, ValueError):
            return self.bad_request({"name": "InputValidationError", "message": "Erro de validação"})
        fixed_side = data["fixedSide"]
        if fixed_side not in ProductExpositionDetail.FixedSide.values:
            return self.bad_request({"name": "InputValidationError", "message": "Lado fixo inválido"})
        product = Product.objects.filter(pk=product_id).first()
        if not product:
            return self.not_found({"name": "ProductNotFoundError", "message": f"Produto com ID {product_id} não foi encontrado."})
        level = Level.objects.select_related("department").filter(pk=level_id).first()
        if not level:
            return self.not_found({"name": "LevelNotFound", "message": f"Nível com ID {level_id} não foi encontrado."})
        if (fixed_side == "HEIGHT" and not product.secondary_image_url) or (fixed_side == "LENGTH" and not product.tertiary_image_url):
            return self.conflict({"name": "ProductFixedSideImageConflict", "message": "Não foi possível adicionar a exposição do produto, pois ele não tem uma imagem secundária ou terciária cadastrada."})
        if ProductExpositionDetail.objects.filter(product_id=product_id, level_id=level_id).exists():
            return self.conflict({"name": "ProductExpositionAlreadyExistError", "message": "Já existe uma exposição para este produto no nível especificado."})
        with transaction.atomic():
            ProductExpositionDetail.objects.filter(level_id=level_id, ranking__gte=ranking).update(ranking=F("ranking") + 1)
            detail = ProductExpositionDetail.objects.create(product=product, level=level, ranking=ranking, priority=priority, forefront=forefront, min_stock=min_stock, fixed_side=fixed_side, is_extra_exposition=data.get("isExtraExposition", False) is True)
            self._normalize(level_id)
            detail.refresh_from_db()
        return self.created(self._detail(detail, with_level=True))

    def _import(self, request):
        data = request.data
        try:
            level_id = int(data.get("levelId"))
        except (TypeError, ValueError):
            return self.bad_request({"name": "InputValidationError", "message": "Erro de validação"})
        rows = data.get("levelExpositions")
        if not isinstance(rows, list) or not rows:
            return self.bad_request({"name": "InputValidationError", "message": "É necessário ao menos uma exposição na planilha"})
        if not Level.objects.filter(pk=level_id).exists():
            return self.not_found({"name": "LevelNotFound", "message": f"Nível com ID {level_id} não foi encontrado."})
        products, used_products, used_positions = [], set(), set()
        for row in rows:
            try:
                sku, ean = int(row["sku"]), row["ean"]
                ranking, priority, forefront = int(row["ranking"]), int(row["priority"]), int(row["forefront"])
            except (KeyError, TypeError, ValueError):
                return self.bad_request({"name": "InputValidationError", "message": "Erro de validação"})
            product = Product.objects.filter(sku=sku, ean=ean).first()
            if not product:
                return Response({"name": "ImportLevelExpositionProductsNotFount", "message": "Existem produtos que não foram encontrados para a importação!", "errorResponseData": [row]}, status=422)
            if product.id in used_products:
                return Response({"name": "ImportLevelExpositionDuplicatedError", "message": "Existem produtos duplicados na planilha.", "errorResponseData": [row]}, status=422)
            if (ranking, priority) in used_positions:
                return Response({"name": "ImportLevelExpositionRankingConflict", "message": "Existem produtos com ranking e prioridade duplicados.", "errorResponseData": [row]}, status=422)
            used_products.add(product.id)
            used_positions.add((ranking, priority))
            products.append((product, ranking, priority, forefront))
        with transaction.atomic():
            ProductExpositionDetail.objects.filter(level_id=level_id).delete()
            ProductExpositionDetail.objects.bulk_create([ProductExpositionDetail(product=product, level_id=level_id, ranking=ranking, priority=priority, forefront=forefront, min_stock=1, fixed_side="WIDTH") for product, ranking, priority, forefront in products])
        details = ProductExpositionDetail.objects.filter(level_id=level_id).select_related("product__brand__industry").order_by("ranking", "priority")
        results = []
        for detail in details:
            product = ProductContractView._entity(detail.product)
            product["expositionsDetails"] = self._detail(detail)
            results.append(product)
        return self.ok({"results": results})

    def get(self, request, level_id):
        level = Level.objects.filter(pk=level_id).first()
        if not level:
            return self.not_found({"name": "LevelNotFound", "message": f"Nível com ID {level_id} não foi encontrado."})
        details = ProductExpositionDetail.objects.filter(level_id=level_id).select_related("product__brand__industry").order_by("ranking", "priority")
        results = []
        for detail in details:
            product = ProductContractView._entity(detail.product)
            product["expositionsDetails"] = self._detail(detail)
            results.append(product)
        return self.ok({"results": results})

    def put(self, request):
        data = request.data
        try:
            detail = ProductExpositionDetail.objects.select_related("level__department").get(pk=int(data.get("id")))
        except (TypeError, ValueError):
            return self.bad_request({"name": "InputValidationError", "message": "Erro de validação"})
        except ProductExpositionDetail.DoesNotExist:
            identifier = data.get("id")
            return self.not_found({"name": "ProductExpositionDetailsNotFoundError", "message": f"Detalhes da exposição com ID {identifier} não foi encontrado."})
        for key, attribute, cast in (("forefront", "forefront", int), ("minStock", "min_stock", int)):
            if key in data:
                try:
                    setattr(detail, attribute, cast(data[key]))
                except (TypeError, ValueError):
                    return self.bad_request({"name": "InputValidationError", "message": "Erro de validação"})
        if "fixedSide" in data:
            if data["fixedSide"] not in ProductExpositionDetail.FixedSide.values:
                return self.bad_request({"name": "InputValidationError", "message": "Lado fixo inválido"})
            detail.fixed_side = data["fixedSide"]
        if "isExtraExposition" in data:
            detail.is_extra_exposition = data["isExtraExposition"]
        detail.save()
        return self.ok(self._detail(detail))

    def delete(self, request, detail_id):
        try:
            detail = ProductExpositionDetail.objects.get(pk=detail_id)
        except ProductExpositionDetail.DoesNotExist:
            return self.not_found({"name": "ProductExpositionDetailsNotFoundError", "message": f"Detalhes da exposição com ID {detail_id} não foi encontrado."})
        with transaction.atomic():
            level_id = detail.level_id
            detail.delete()
            self._normalize(level_id)
        return self.no_content()

    def patch(self, request):
        data = request.data
        try:
            detail = ProductExpositionDetail.objects.get(pk=int(data.get("expositionId")))
            ranking = int(data.get("ranking"))
        except (TypeError, ValueError):
            return self.bad_request({"name": "InputValidationError", "message": "Erro de validação"})
        except ProductExpositionDetail.DoesNotExist:
            return self.not_found({"name": "ProductExpositionDetailsNotFoundError", "message": f"Detalhes da exposição com ID {data.get('expositionId')} não foi encontrado."})
        if data.get("priority") is not None and data.get("swapRanking") is True:
            return self.bad_request({"name": "InputValidationError", "message": "priority e swapRanking não podem ser enviados juntos"})
        with transaction.atomic():
            if data.get("priority") is not None:
                try:
                    new_priority = int(data["priority"])
                except (TypeError, ValueError):
                    return self.bad_request({"name": "InputValidationError", "message": "Erro de validação"})
                if detail.ranking == ranking:
                    ProductExpositionDetail.objects.filter(level_id=detail.level_id, ranking=ranking, priority__gte=new_priority).exclude(pk=detail.pk).update(priority=F("priority") + 1)
                detail.ranking, detail.priority = ranking, new_priority
            elif detail.ranking != ranking:
                if data.get("swapRanking") is True:
                    ProductExpositionDetail.objects.filter(level_id=detail.level_id, ranking=ranking).exclude(pk=detail.pk).update(ranking=detail.ranking)
                else:
                    priority = ProductExpositionDetail.objects.filter(level_id=detail.level_id, ranking=ranking).exclude(pk=detail.pk).count() + 1
                    detail.priority = priority
                detail.ranking = ranking
            detail.save()
            self._normalize(detail.level_id)
        details = ProductExpositionDetail.objects.filter(level_id=detail.level_id).select_related("product__brand__industry").order_by("ranking", "priority")
        results = []
        for item in details:
            product = ProductContractView._entity(item.product)
            product["expositionsDetails"] = self._detail(item)
            results.append(product)
        return self.ok({"results": results})

    @staticmethod
    def _normalize(level_id):
        details = list(ProductExpositionDetail.objects.filter(level_id=level_id).order_by("ranking", "priority", "id"))
        ranking, priority, prior_ranking = 1, 1, details[0].ranking if details else None
        for detail in details:
            if detail.ranking != prior_ranking:
                ranking += 1
                priority = 1
                prior_ranking = detail.ranking
            if detail.ranking != ranking or detail.priority != priority:
                ProductExpositionDetail.objects.filter(pk=detail.pk).update(ranking=ranking, priority=priority)
            priority += 1

    @staticmethod
    def _detail(detail, with_level=False):
        response = {"id": detail.id, "productId": detail.product_id, "levelId": detail.level_id, "ranking": detail.ranking, "priority": detail.priority, "forefront": detail.forefront, "minStock": detail.min_stock, "fixedSide": detail.fixed_side, "isExtraExposition": detail.is_extra_exposition}
        if with_level:
            level = detail.level
            response["level"] = {"id": level.id, "name": level.name, **({"label": level.label} if level.label else {}), "hexColor": level.hex_color, "divisions": level.divisions, "departmentId": level.department_id,
                                 "department": {"id": level.department.id, "name": level.department.name, "orientation": level.department.orientation, "zoneId": level.department.zone_id}}
        return response
