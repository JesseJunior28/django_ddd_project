from django.db import IntegrityError, transaction
from django.db.models import Q

from src.middlewares.auth import AuthenticatedController
from src.entities.industry.models import Brand
from src.entities.product.models import Product
from src.services.storage.local import LocalProductStorage


class ProductContractView(AuthenticatedController):
    authorized_roles = ("ADMIN",)

    def post(self, request):
        fields = request.data
        required = ("name", "sku", "ean", "brandId", "isRelease", "isNews", "width", "height")
        if any(not fields.get(field) for field in required) or "primaryImageUrl" not in request.FILES:
            return self.bad_request({"name": "InputValidationError", "message": "Erro de validação"})
        try:
            sku, brand_id = int(fields["sku"]), int(fields["brandId"])
            width, height = float(fields["width"]), float(fields["height"])
            length = float(fields["length"]) if fields.get("length") else None
        except (TypeError, ValueError):
            return self.bad_request({"name": "InputValidationError", "message": "Erro de validação"})
        brand = Brand.objects.filter(pk=brand_id).first()
        if not brand:
            return self.not_found({"name": "BrandNotFoundError", "message": f"Marca com ID {brand_id} não foi encontrado."})
        if Product.objects.filter(ean=fields["ean"]).exists():
            return self.conflict({"name": "EanProductAlreadyExistConflict", "message": f"Já existe um produto cadastrado com este ean {fields['ean']}."})
        storage = LocalProductStorage()
        names = []
        try:
            with transaction.atomic():
                # Remove posições vazias antes de associar as URLs resultantes.
                for key in ("primaryImageUrl", "secondaryImageUrl", "tertiaryImageUrl"):
                    if request.FILES.get(key):
                        names.append(storage.save(request.FILES[key]))
                product = Product.objects.create(sku=sku, ean=fields["ean"], name=fields["name"], brand=brand,
                    primary_image_url=names[0], secondary_image_url=names[1] if len(names) > 1 else None, tertiary_image_url=names[2] if len(names) > 2 else None, family=fields.get("family") or None,
                    is_release=fields.get("isRelease") == "true", is_news=fields.get("isNews") == "true", width=width, height=height, length=length)
        except ValueError as error:
            for name in names:
                if name: storage.delete(name)
            return self.bad_request({"name": "InputValidationError", "message": str(error)})
        except IntegrityError:
            for name in names:
                if name: storage.delete(name)
            return self.conflict({"name": "EanProductAlreadyExistConflict", "message": f"Já existe um produto cadastrado com este ean {fields['ean']}."})
        return self.created({"id": product.id, "sku": product.sku, "ean": product.ean, "brandId": product.brand_id, "name": product.name,
                             "primaryImageUrl": product.primary_image_url, **({"secondaryImageUrl": product.secondary_image_url} if product.secondary_image_url else {}),
                             **({"tertiaryImageUrl": product.tertiary_image_url} if product.tertiary_image_url else {}), **({"family": product.family} if product.family else {}),
                             "isActive": product.is_active, "isRelease": product.is_release, "isNews": product.is_news, "width": product.width, "height": product.height,
                             **({"length": product.length} if product.length is not None else {}), "createdAt": product.created_at, "updatedAt": product.updated_at,
                             "brand": {"id": brand.id, "name": brand.name, "industryId": brand.industry_id, "industryName": brand.industry.name}, "expositionsDetails": []})

    def get(self, request):
        query = request.query_params.get("queryString")
        try:
            page_number = int(request.query_params.get("pageNumber", 1))
            page_size = int(request.query_params.get("pageSize", 10))
        except ValueError:
            return self.bad_request({"name": "InputValidationError", "message": "Erro de validação"})
        products = Product.objects.select_related("brand__industry")
        if query:
            condition = Q(name__icontains=query) | Q(ean__icontains=query)
            if len(query) <= 7:
                try:
                    condition |= Q(sku=int(query))
                except ValueError:
                    pass
            products = products.filter(condition)
        sort = request.query_params.get("sort")
        if sort:
            fields = []
            for value in sort.split(","):
                field, _, direction = value.partition(":")
                if field not in ("name", "createdAt") or direction not in ("asc", "desc"):
                    return self.bad_request({"name": "InputValidationError", "message": "Parâmetro de ordenação inválido"})
                fields.append(("-" if direction == "desc" else "") + {"createdAt": "created_at"}.get(field, field))
            products = products.order_by(*fields)
        else:
            products = products.order_by("name")
        total = products.count()
        offset = (page_number - 1) * page_size
        return self.ok({"totalPages": -(-total // page_size), "results": [self._entity(product) for product in products[offset:offset + page_size]]})

    def put(self, request):
        fields = request.data
        try:
            product_id = int(fields.get("id"))
        except (TypeError, ValueError):
            return self.bad_request({"name": "InputValidationError", "message": "Erro de validação"})
        product = Product.objects.select_related("brand__industry").filter(pk=product_id).first()
        if not product:
            return self.not_found({"name": "ProductNotFoundError", "message": f"Produto com ID {product_id} não foi encontrado."})
        storage = LocalProductStorage()
        names = [None, None, None]
        try:
            for index, key in enumerate(("primaryImageUrl", "secondaryImageUrl", "tertiaryImageUrl")):
                if request.FILES.get(key):
                    names[index] = storage.save(request.FILES[key])
        except ValueError as error:
            for name in names:
                if name: storage.delete(name)
            return self.bad_request({"name": "InputValidationError", "message": str(error)})
        for attr, value in zip(("primary_image_url", "secondary_image_url", "tertiary_image_url"), names):
            if value:
                setattr(product, attr, value)
        for field, attr, cast in (("width", "width", float), ("height", "height", float), ("length", "length", float)):
            if fields.get(field):
                try:
                    setattr(product, attr, cast(fields[field]))
                except (TypeError, ValueError):
                    return self.bad_request({"name": "InputValidationError", "message": "Erro de validação"})
        if fields.get("family"):
            product.family = fields["family"]
        product.is_active = fields.get("isActive") == "true"
        product.is_release = fields.get("isRelease") == "true"
        product.is_news = fields.get("isNews") == "true"
        product.save()
        return self.ok(self._entity(product))

    @staticmethod
    def _entity(product):
        brand = product.brand
        expositions = []
        for detail in product.expositions_details.select_related("level__department").order_by("id"):
            level, department = detail.level, detail.level.department
            expositions.append({"id": detail.id, "productId": detail.product_id, "levelId": detail.level_id,
                "ranking": detail.ranking, "priority": detail.priority, "forefront": detail.forefront,
                "minStock": detail.min_stock, "fixedSide": detail.fixed_side,
                "isExtraExposition": detail.is_extra_exposition,
                "level": {"id": level.id, "name": level.name, "hexColor": level.hex_color,
                    "departmentId": level.department_id, "divisions": level.divisions,
                    "department": {"id": department.id, "name": department.name,
                        "orientation": department.orientation, "zoneId": department.zone_id}}})
        return {"id": product.id, "sku": product.sku, "ean": product.ean, "primaryImageUrl": product.primary_image_url,
                **({"secondaryImageUrl": product.secondary_image_url} if product.secondary_image_url else {}), **({"tertiaryImageUrl": product.tertiary_image_url} if product.tertiary_image_url else {}),
                "name": product.name, **({"family": product.family} if product.family else {}), "isActive": product.is_active, "isRelease": product.is_release,
                "isNews": product.is_news, "width": product.width, "height": product.height, **({"length": product.length} if product.length is not None else {}),
                "createdAt": product.created_at, "updatedAt": product.updated_at, "brandId": product.brand_id,
                "brand": {"id": brand.id, "name": brand.name, "industryId": brand.industry_id, "industryName": brand.industry.name}, "expositionsDetails": expositions}
