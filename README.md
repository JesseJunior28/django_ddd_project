# Backend Django

API construída com Django, Django REST Framework e PostgreSQL. O projeto organiza
as regras por domínio, serviços e casos de uso.

## Requisitos

- Docker Engine com Docker Compose v2; ou
- Python 3.12 e PostgreSQL 16 para execução sem Docker.

## Início rápido com Docker

```bash
git clone https://github.com/JesseJunior28/django_ddd_project.git
cd django_ddd_project
cp .env.example .env
docker compose up --build
```

O Docker aplica as migrations antes de iniciar a aplicação. Com os contêineres
em execução, a API está disponível em `http://localhost:8000`.

Verifique o serviço e o banco:

```bash
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

Para encerrar os contêineres:

```bash
make down
```

Para apagar também o volume local do PostgreSQL:

```bash
make down-v
```

> Esse último comando remove os dados locais do banco.

## Comandos do dia a dia

```bash
make up            # inicia os contêineres
make build         # inicia reconstruindo a imagem
make build-d       # inicia em segundo plano
make logs          # acompanha os logs da aplicação
make shell         # abre um shell no contêiner web
make migrate       # cria migrations pendentes e as aplica
make superuser     # cria usuário para /admin/
make make-usecase  # abre o gerador interativo de caso de uso
```

Também é possível executar comandos diretamente:

```bash
docker compose exec web python manage.py check
docker compose exec web python manage.py test
docker compose exec web python manage.py createsuperuser
```

O painel administrativo fica em `http://localhost:8000/admin/` após criar um
superusuário.

## Execução sem Docker

Crie um banco PostgreSQL e configure as credenciais em `.env`:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Neste modo, defina `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` e `DB_PASSWORD`
para o PostgreSQL local. O projeto usa recursos específicos do PostgreSQL; SQLite
não é um substituto suportado para testes de integração.

## Variáveis de ambiente

Copie `.env.example` para `.env` e ajuste os valores conforme o ambiente.

| Variável | Uso |
| --- | --- |
| `DJANGO_DEBUG` | Ativa o modo de desenvolvimento. |
| `DJANGO_SECRET_KEY` | Chave secreta da aplicação. Use um valor exclusivo fora do desenvolvimento. |
| `DJANGO_ALLOWED_HOSTS` | Hosts aceitos pela aplicação. |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Credenciais do PostgreSQL. |
| `DB_HOST`, `DB_PORT` | Endereço do PostgreSQL. |
| `JWT_SECRET` | Chave de assinatura dos tokens JWT. |

Não versione o arquivo `.env` com credenciais reais.

## Organização do código

```text
config/                 configuração do Django e rotas HTTP
src/
  _app/                 health checks, observabilidade e comandos técnicos
  core/                 abstrações compartilhadas de casos de uso e controllers
  entities/             modelos, migrations e regras por domínio
  middlewares/          autenticação e limites de requisição
  services/             hash, token, e-mail e armazenamento
  use_cases/            operações da aplicação organizadas por domínio
```

Cada domínio em `src/entities/` possui seu próprio `models.py` e migrations.
Depois de alterar um modelo, gere e revise a migration correspondente antes de
aplicá-la:

```bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

## Criando um caso de uso

O gerador cria a estrutura inicial de `dtos.py`, `use_case.py`, `factory.py` e
`view.py`:

```bash
make make-usecase

# ou sem interação
docker compose exec web python manage.py make_usecase branch create-branch --method post --path create-branch
```

Depois, implemente as regras, registre a rota em `config/urls.py` e adicione os
testes do fluxo.

## Segurança e produção

Os valores padrão de `.env.example` servem somente para desenvolvimento local.
Antes de publicar a aplicação, use segredos exclusivos, `DJANGO_DEBUG=False`,
hosts permitidos restritos e um PostgreSQL gerenciado ou adequadamente protegido.
