from .models import Product


class ProductRepository:
    """Encapsula o acesso a dados da entidade Product."""

    def create(self, ean: str, name: str, width: float, height: float, length: float, is_active: bool = True) -> Product:
        return Product.objects.create(
            ean=ean, name=name, width=width, height=height, length=length, is_active=is_active,
        )

    def find_by_id(self, id: int) -> Product | None:
        return Product.objects.filter(id=id).first()

    def find_by_ean(self, ean: str) -> Product | None:
        return Product.objects.filter(ean=ean).first()

    def list_all(self):
        return Product.objects.all()

    def update(self, id: int, **fields) -> Product | None:
        product = self.find_by_id(id)
        if not product:
            return None
        for key, value in fields.items():
            setattr(product, key, value)
        product.save()
        return product

    def delete(self, id: int) -> bool:
        deleted, _ = Product.objects.filter(id=id).delete()
        return deleted > 0
