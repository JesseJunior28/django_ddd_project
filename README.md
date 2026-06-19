# Django DDD — Arquitetura Domain-Driven Design

Projeto Django com arquitetura DDD, espelhando a estrutura do projeto TypeScript (Prisma + Express).

**Stack:** Django 5.2 LTS · Django REST Framework · PostgreSQL 16 · Docker

## Subindo o projeto com Docker (recomendado)

```bash
# 1. Copiar o arquivo de variáveis de ambiente
cp .env.example .env

# 2. Subir os containers (Django + Postgres)
docker compose up --build

# A API estará em http://localhost:8000
```

Isso já roda as migrations automaticamente antes de subir o servidor. Para rodar comandos dentro do container (como o gerador de use cases):

```bash
docker compose exec web python manage.py make_usecase
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py makemigrations
```

Para parar:
```bash
docker compose down          # mantém os dados do Postgres
docker compose down -v       # remove também o volume do banco
```

## Subindo sem Docker (ambiente local)

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

# Configure um Postgres local e ajuste o .env, ou troque temporariamente
# DB_ENGINE para django.db.backends.sqlite3 em settings.py / .env

python manage.py migrate
python manage.py runserver
```

## Estrutura

```
src/
├── core/
│   ├── either.py        # Either monad (right/wrong) — equivalente ao @core/either
│   ├── use_case.py      # Classe base UseCase — equivalente ao @core/use-case
│   └── controller.py    # Classe base Controller (APIView DRF) — equivalente ao @core/controller
│
├── errors/
│   └── domain_errors.py # ApplicationError, BusinessError, InputValidationError, etc.
│
├── entities/             # Modelos Django por domínio (equivalente ao schema.prisma)
│   └── branch/
│       ├── apps.py        # registra o domínio como app Django
│       ├── models.py      # equivalente ao `model Branch { ... }` do schema.prisma
│       ├── repository.py  # acesso a dados (create, find_by_id, list_all...)
│       └── migrations/    # geradas via `makemigrations` (equivalente ao prisma migrate)
│
├── services/             # Serviços de infraestrutura (email, hash, storage, token...)
│
├── use_cases/             # Use cases organizados por domínio
│   └── branch/
│       └── create_branch/
│           ├── __init__.py
│           ├── dtos.py       # Input/Output dataclasses
│           ├── use_case.py   # Lógica de negócio
│           ├── factory.py    # Instancia o use case com suas dependências
│           └── view.py       # Controller HTTP (APIView DRF)
│
├── middlewares/           # Middlewares Django
│
└── management/
    └── commands/
        └── make_usecase.py  # Gerador de use cases (equivalente ao npx plop)
```

## Onde fica o "schema.prisma"?

Não existe um arquivo único como no Prisma. No Django, cada domínio declara
seus próprios models em `src/entities/<dominio>/models.py`, e as migrations
são geradas a partir deles — não escritas à mão.

| Prisma | Django |
|---|---|
| `schema.prisma` (um arquivo, todos os models) | `src/entities/<dominio>/models.py` (um por domínio) |
| `model Branch { ... }` | `class Branch(models.Model): ...` |
| `npx prisma migrate dev` | `python manage.py makemigrations <app_label> && python manage.py migrate` |
| `prisma/migrations/` | `src/entities/<dominio>/migrations/` (gerado automaticamente) |

### Criando uma nova entidade — passo a passo

```bash
# 1. Criar a pasta do domínio
mkdir -p src/entities/<dominio>
touch src/entities/<dominio>/__init__.py

# 2. Criar apps.py (registra o domínio como app Django)
cat > src/entities/<dominio>/apps.py << 'PYEOF'
from django.apps import AppConfig

class <Dominio>Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "src.entities.<dominio>"
    label = "<dominio>"
PYEOF

# 3. Criar models.py com as classes do domínio
#    (veja src/entities/branch/models.py como referência)

# 4. Registrar em config/settings.py -> INSTALLED_APPS
#    'src.entities.<dominio>',

# 5. Gerar e aplicar a migration
python manage.py makemigrations <dominio>
python manage.py migrate

# 6. Criar o repository.py (acesso a dados)
#    (veja src/entities/branch/repository.py como referência)
```

> ⚠️ Cada domínio com `models.py` precisa estar listado em `INSTALLED_APPS`
> com seu `label` — é assim que o Django sabe rastrear as migrations dele
> separadamente. O app `src._app` existe só para os management commands
> (como o `make_usecase`) funcionarem, e não tem models.

## Gerador de Use Cases (substituto do Plop)

### Modo interativo (igual ao `npx plop`)

```bash
python manage.py make_usecase
```

Ele vai perguntar, em sequência:
```
🏷️  Domínio (ex: branch, auth, execution):
📦 Nome do use case (kebab-case, ex: create-branch):
🌐 Método HTTP:
   1) GET
   2) POST
   3) PUT
   4) PATCH
   5) DELETE
   Escolha [1-5] (default: 2-POST):
🔗 Path da rota (default: <dominio>/):
```

### Modo direto (via flags, sem prompts — útil em scripts/CI)

```bash
python manage.py make_usecase branch create-branch --method post --path branches/
python manage.py make_usecase auth login --method post --path auth/login/
python manage.py make_usecase execution list-executions --method get --path executions/
python manage.py make_usecase branch update-branch --method patch --path "branches/<uuid:id>/"
```

> 💡 Quando o path tem parâmetros (`<uuid:id>`, `<int:pk>`, etc.), o gerador já cria
> a assinatura do método na view com esses kwargs.

### Preview sem criar arquivos

```bash
python manage.py make_usecase demand list-demands --dry-run
```

Isso gera os 5 arquivos do use case:

| Arquivo | Equivalente TS | Responsabilidade |
|---|---|---|
| `dtos.py` | `dtos.ts` | Tipos de Input e Output (dataclasses) |
| `use_case.py` | `use-case.ts` | Lógica de negócio (validate + execute) |
| `factory.py` | `factory.ts` | Instancia o use case com dependências |
| `view.py` | `controller.ts` | Handler HTTP, já com o método correto (get/post/put/patch/delete) |
| `__init__.py` | — | Exportações do módulo |

Ao final, o comando também imprime o snippet pronto para colar em `config/urls.py`:

```python
from src.use_cases.branch.create_branch.view import CreateBranchView
path("branches/", CreateBranchView.as_view(), name="create-branch"),
```

## Padrão Either

O mesmo padrão `right/wrong` do TypeScript:

```python
from src.core.either import right, wrong

# Em vez de throw/try-catch, retorna Either
return right(output)   # sucesso  — equivalente ao right() do TS
return wrong(error)    # falha    — equivalente ao wrong() do TS

# No controller/view:
result = use_case.run(input_data)

if result.is_wrong():   # equivalente ao result.isWrong()
    error = result.value
    return self.map_error(error, {
        InputValidationError: self.bad_request,
        UnknownError: self.internal_server_error,
    })

return self.ok(result.value)
```

## Criando um Use Case — Passo a Passo

```bash
# 1. Gerar o scaffold (modo interativo ou com flags)
python manage.py make_usecase branch create-branch --method post --path branches/

# 2. Definir os campos em dtos.py
# 3. Implementar validate() e execute() em use_case.py
# 4. Configurar o repository em factory.py
# 5. Colar a rota sugerida em config/urls.py
```

## Variáveis de ambiente

Ver `.env.example` para a lista completa. As principais:

| Variável | Descrição | Default |
|---|---|---|
| `DJANGO_DEBUG` | Modo debug | `True` |
| `DJANGO_SECRET_KEY` | Secret key do Django | (chave insegura de dev) |
| `DB_HOST` | Host do Postgres | `db` (nome do serviço no compose) |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` | Credenciais do Postgres | `django_ddd` |
