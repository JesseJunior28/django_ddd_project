import re

# Aceita e-mails válidos inclusive em domínios locais sem ponto.
EMAIL = re.compile(r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@"
                   r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
                   r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$")


def validation_errors(data):
    if not isinstance(data, dict):
        return ["Erro de validação desconhecido"]
    errors = []
    email, password = data.get("email"), data.get("password")
    if email is None or email == "":
        errors.append("Email é obrigatório")
    elif not isinstance(email, str):
        errors.append("Tipo inválido para email do usuário")
    elif not EMAIL.fullmatch(email):
        errors.append("Email inválido")
    if password is None:
        errors.append("Senha é obrigatório")
    elif not isinstance(password, str):
        errors.append("Tipo inválido para senha do usuário")
    else:
        # O limite considera unidades UTF-16 para tratar caracteres fora do BMP.
        if len(password.encode("utf-16-le", errors="surrogatepass")) // 2 < 6:
            errors.append("A senha deve ter mais de 6 caracteres")
        if password == "":
            errors.append("Senha é obrigatório")
    return errors
