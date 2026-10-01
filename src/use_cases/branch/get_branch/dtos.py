import math
from src.core.compatibility import js_number


def parse_id(value):
    return js_number(value)


def validation_errors(value):
    return ["Tipo inválido para ID da loja"] if math.isnan(value) else []
