from src.use_cases.auth.login.dtos import EMAIL


def validation_errors(data):
    if not isinstance(data, dict):
        return ["Erro de validação desconhecido"]
    email = data.get("email")
    if email is None or email == "":
        return ["Email é obrigatório"]
    if not isinstance(email, str):
        return ["Tipo inválido para email do usuário"]
    if not EMAIL.fullmatch(email):
        return ["Email inválido"]
    return []
