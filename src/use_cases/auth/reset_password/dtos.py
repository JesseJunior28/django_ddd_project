def validation_errors(data):
    if not isinstance(data, dict):
        return ["Erro de validação desconhecido"]
    errors = []
    token, password = data.get("token"), data.get("password")
    if token is None or token == "":
        errors.append("Token é obrigatório")
    elif not isinstance(token, str):
        errors.append("Tipo inválido para o token")
    if password is None:
        errors.append("Senha é obrigatório")
    elif not isinstance(password, str):
        errors.append("Tipo inválido para senha do usuário")
    else:
        if len(password.encode("utf-16-le", errors="surrogatepass")) // 2 < 6:
            errors.append("A senha deve ter mais de 6 caracteres")
        if password == "":
            errors.append("Senha é obrigatório")
    return errors
