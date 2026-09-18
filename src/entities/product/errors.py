from src.errors import ConflictError, NotFoundError


class ProductNotFoundError(NotFoundError):
    def __init__(self, product_id: int | None = None, ean: str | None = None):
        if product_id is not None:
            message = f"Produto com ID {product_id} não encontrado."
        elif ean:
            message = f"Produto com EAN {ean} não encontrado."
        else:
            message = "Produto não encontrado."
        super().__init__("Product", message)


class DuplicateProductEanError(ConflictError):
    def __init__(self, ean: str):
        super().__init__(f"Já existe um produto com o EAN {ean}.")
