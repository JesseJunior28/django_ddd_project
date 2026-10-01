from src.use_cases.auth.login.dtos import EMAIL


def validation_errors(data):
    if not isinstance(data, dict):
        return ["Erro de validação desconhecido"]
    errors = []
    for key, required, invalid in (
        ("name", "Nome é obrigatório", "Tipo inválido para nome do usuário"),
        ("email", "Email é obrigatório", "Tipo inválido para email do usuário"),
        ("password", "Senha é obrigatório", "Tipo inválido para senha do usuário"),
    ):
        value = data.get(key)
        if value is None:
            errors.append(required)
        elif not isinstance(value, str):
            errors.append(invalid)
        else:
            if key == "password" and len(value.encode("utf-16-le", errors="surrogatepass")) // 2 < 6:
                errors.append("Deve ter mais de 6 caracteres")
            if value == "":
                errors.append(required)
            elif key == "email" and not EMAIL.fullmatch(value):
                errors.append("Email inválido")
    if "itecUser" in data:
        value = data["itecUser"]
        if value is None:
            errors.append("itecUser cannot be null")
        elif type(value) not in (int, float):
            errors.append("Tipo inválido para código itec")
        elif value < 0:
            errors.append("O código não pode ser menor que 0")
        elif value > 9999:
            errors.append("O código itec não pode ser maior que 9999")
    return errors
