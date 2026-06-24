from dataclasses import dataclass

@dataclass
class DomainError(Exception):
    message: str

@dataclass
class ProductNotFoundError(DomainError):
    def __init__(self, product_id: int= None, ean: str = None):
        if product_id:
            self.message = f"Produto com ID {product_id} não encontrado."
        elif ean:
            self.message = f"Produto com EAN {ean} não encontrado."
        else:
            self.message = f"Produto não encontrado."

@dataclass
class DuplicateProductEanError(DomainError):
    def __init__(self, ean: str):
        self.message = f"Um produto com EAN {ean} que já existe."

