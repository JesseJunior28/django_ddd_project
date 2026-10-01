def validation_errors(data):
    if not isinstance(data, dict): return ["Erro de validação desconhecido"]
    errors = []
    if data.get("id") is None: errors.append("ID é obrigatório")
    elif type(data["id"]) not in (int, float): errors.append("Tipo inválido para ID da loja")
    for field, message in (("name", "Tipo inválido para nome da loja"), ("city", "Tipo inválido para cidade da loja"), ("address", "Tipo inválido para endereço da loja")):
        if field in data and not isinstance(data[field], str): errors.append(message if data[field] is not None else f"{field} cannot be null")
    if "ufId" in data:
        value = data["ufId"]
        if type(value) not in (int, float): errors.append("Tipo inválido para ID da UF")
        elif value <= 0: errors.append("ufId must be a positive number")
        elif value != int(value): errors.append("ufId must be an integer")
    return errors
