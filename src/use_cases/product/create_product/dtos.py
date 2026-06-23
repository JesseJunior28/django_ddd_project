from dataclasses import dataclass


@dataclass
class CreateProductInput:
    ean: str
    name: str
    width: float
    height: float
    length: float
    is_active: bool = True


@dataclass
class CreateProductOutput:
    id: int
    ean: str
    name: str
