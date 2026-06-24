# Django DDD — Arquitetura Domain-Driven Design

Projeto Django com arquitetura DDD.

**Stack:** Django 5.2 LTS · Django REST Framework · PostgreSQL 16 · Docker

## Subindo o projeto com Docker (recomendado)

```bash
# 1. Copiar o arquivo de variáveis de ambiente
cp .env.example .env

# 2. Subir os containers (Django + Postgres)
docker compose up --build

# A API estará em http://localhost:8000
```

Isso já roda as migrations automaticamente antes de subir o servidor.

## Makefile — atalhos para os comandos do dia a dia

Em vez de digitar `docker compose exec web python manage.py ...` toda vez,
use os atalhos do `Makefile` (equivalente aos `scripts` do `package.json`):

```bash
make up           # docker compose up
make build        # docker compose up --build
make down         # docker compose down (mantém os dados do Postgres)
make down-v       # docker compose down -v (remove também o volume do banco)
make shell        # abre um shell dentro do container web
make make-usecase # docker compose exec web python manage.py make_usecase (modo interativo)
make migrate      # makemigrations + migrate
make superuser    # cria um superusuário do Django (acesso ao /admin/)
make logs         # acompanha os logs do container web
```

Exemplo de uso:
```bash
make up
make make-usecase
make migrate
make superuser
```

> O `Makefile` usa **TAB** para indentar os comandos (não espaço) — é uma exigência
> do `make`, não uma preferência de estilo. Se for editá-lo, atenção a isso.

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
│       ├── admin.py       # registra a entidade no /admin/ (CRUD visual)
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

## Onde ficam as migrations?

No Django, cada domínio declara seus próprios models em `src/entities/<dominio>/models.py`, 
e as migrations são geradas a partir deles — não escritas à mão.

| Prisma | Django |
|---|---|
| `schema.prisma` (um arquivo, todos os models) | `src/entities/<dominio>/models.py` (um por domínio) |
| `model Branch { ... }` | `class Branch(models.Model): ...` |
| `npx prisma migrate dev` | `make migrate` (ou `python manage.py makemigrations <app_label> && python manage.py migrate`) |
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
make migrate
# ou: python manage.py makemigrations <dominio> && python manage.py migrate

# 6. Criar o repository.py (acesso a dados)
#    (veja src/entities/branch/repository.py como referência)

# 7. Registrar a entidade no admin (veja seção "Admin do Django" abaixo)
```

> ⚠️ Cada domínio com `models.py` precisa estar listado em `INSTALLED_APPS`
> com seu `label` — é assim que o Django sabe rastrear as migrations dele
> separadamente. O app `src._app` existe só para os management commands
> (como o `make_usecase`) funcionarem, e não tem models.

## Admin do Django (CRUD visual em `/admin/`)

O Django só lista no admin o que é **explicitamente registrado** — diferente de
ferramentas que expõem tudo automaticamente. Por padrão, `/admin/` mostra apenas
Users e Groups; para uma entidade aparecer lá, crie um `admin.py` na pasta dela.

**Passo a passo:**

1. Crie um superusuário (se ainda não tiver um):
   ```bash
   make superuser
   ```

2. Crie `src/entities/<dominio>/admin.py`, por exemplo para `Branch`:
   ```python
   from django.contrib import admin
   from .models import Branch

   @admin.register(Branch)
   class BranchAdmin(admin.ModelAdmin):
       list_display = ("id", "name", "city", "uf", "address", "created_at")
       search_fields = ("name", "city", "uf")
   ```

3. Acesse `http://localhost:8000/admin/` e logue com o superusuário.

Não precisa de migration nem de configuração extra — o Django descobre o
`admin.py` automaticamente ao iniciar.

> ⚠️ No WSL, o autoreload do `runserver` às vezes não detecta o arquivo novo
> (limitação de notificação de filesystem entre Windows/WSL). Se o admin
> não aparecer depois de criar o `admin.py`, reinicie o container:
> `make down && make up`.

## Entidades disponíveis

| Entidade | Campos | App label |
|---|---|---|
| `Branch` (`src/entities/branch/`) | `id` (int), `name`, `city`, `uf`, `address`, `created_at`, `updated_at` | `branch` |
| `Product` (`src/entities/product/`) | `id` (int), `ean` (único), `name`, `is_active`, `width`, `height`, `length`, `created_at`, `updated_at` | `product` |

Cada uma já tem `models.py`, `repository.py`, `apps.py`, `admin.py` e migrations geradas.
Use cases de exemplo prontos: `create-branch` (POST `/branches/`) e `create-product` (POST `/products/`).

Para criar use cases novos para essas entidades, use o gerador:
```bash
docker compose exec web python manage.py make_usecase product list-products --method get --path products/
docker compose exec web python manage.py make_usecase product update-product --method patch --path "products/<int:id>/"
docker compose exec web python manage.py make_usecase branch list-branches --method get --path branches/
```

E no `factory.py` gerado, conecte ao repository já existente:
```python
from src.entities.product.repository import ProductRepository
```

## Gerador de Use Cases (substituto do Plop)

### Modo interativo (igual ao `npx plop`)

```bash
make make-usecase
# ou: docker compose exec web python manage.py make_usecase
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

> 💡 Quando o path tem parâmetros (`<uuid:id>`, `<int:pk>`, etc.), o gerador já cria
> a assinatura do método na view com esses kwargs.

### Preview sem criar arquivos

```bash
docker compose exec web python manage.py make_usecase demand list-demands --dry-run
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

### Passo a passo completo (gerar + implementar)

```bash
# 1. Gerar o scaffold (modo interativo ou com flags)
make make-usecase
# ou: docker compose exec web python manage.py make_usecase branch create-branch --method post --path branches/

# 2. Definir os campos em dtos.py
# 3. Implementar validate() e execute() em use_case.py
# 4. Configurar o repository em factory.py
# 5. Colar a rota sugerida em config/urls.py
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

## Variáveis de ambiente

Ver `.env.example` para a lista completa. As principais:

| Variável | Descrição | Default |
|---|---|---|
| `DJANGO_DEBUG` | Modo debug | `True` |
| `DJANGO_SECRET_KEY` | Secret key do Django | (chave insegura de dev) |
| `DB_HOST` | Host do Postgres | `db` (nome do serviço no compose) |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` | Credenciais do Postgres | `django_ddd` |