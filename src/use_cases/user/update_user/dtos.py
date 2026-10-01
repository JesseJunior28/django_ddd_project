def validation_errors(data):
    if not isinstance(data, dict):
        return ["Erro de validação desconhecido"]
    errors = []
    fields = [("id", (int, float), "Tipo inválido para o campo id"),
              ("name", (str,), "Tipo inválido para nome do usuário"),
              ("itecUser", (int, float), "Tipo inválido para código itec"),
              ("role", (str,), "Tipo inválido para campo role"),
              ("isActive", (bool,), "Tipo inválido para campo ativo/inativo")]
    for key, types, message in fields:
        if key == "id" and data.get(key) is None:
            errors.append("Id do usuário é obrigatório")
        elif key in data:
            value = data[key]
            if value is None:
                errors.append(f"{key} cannot be null")
            elif type(value) not in types:
                errors.append(message)
            elif key == "itecUser":
                if value < 0:
                    errors.append("O código itec não pode ser menor que 0")
                if value > 9999:
                    errors.append("O código itec não pode ser maior que 9999")
    return errors
