from .use_case import CreateProductUseCase
from src.entities.product.repository import ProductRepository


def build_use_case() -> CreateProductUseCase:
    repository = ProductRepository()
    return CreateProductUseCase(repository)
