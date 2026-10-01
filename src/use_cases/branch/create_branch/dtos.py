def validation_errors(data):
    if not isinstance(data, dict):
        return ["Erro de validação desconhecido"]

    errors = []
    required = (
        ("id", "ID é obrigatório", "Tipo inválido para ID da loja"),
        ("name", "Nome é obrigatório", "Tipo inválido para nome da loja"),
        ("city", "Cidade é obrigatório", "Tipo inválido para cidade da loja"),
        ("address", "Endereço é obrigatório", "Tipo inválido para endereço da loja"),
        ("ufId", "ID da UF é obrigatório", "Tipo inválido para ID da UF"),
    )
    for field, required_message, type_message in required:
        if data.get(field) is None:
            errors.append(required_message)
        elif field in ("id", "ufId") and type(data[field]) not in (int, float):
            errors.append(type_message)
        elif field not in ("id", "ufId") and not isinstance(data[field], str):
            errors.append(type_message)
    if type(data.get("ufId")) in (int, float):
        if data["ufId"] <= 0:
            errors.append("ufId must be a positive number")
        elif data["ufId"] != int(data["ufId"]):
            errors.append("ufId must be an integer")
    return errors
