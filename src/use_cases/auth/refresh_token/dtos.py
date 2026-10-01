def validation_errors(data):
    if not isinstance(data, dict):
        return ["Erro de validação desconhecido"]
    token = data.get("refreshToken")
    if token is None or token == "":
        return ["O refresh token é obrigatório"]
    if not isinstance(token, str):
        return ["Tipo inválido para refresh token"]
    return []
