"""
make_usecase — gerador de use cases DDD para Django
Equivalente ao `npx plop` do projeto TypeScript.

Uso (interativo, igual o Plop):
    python manage.py make_usecase

Uso (direto, sem prompts):
    python manage.py make_usecase <domain> <use-case-name> --method post --path branches/

Exemplos:
    python manage.py make_usecase branch create-branch --method post --path branches/
    python manage.py make_usecase auth login --method post --path auth/login/
    python manage.py make_usecase execution list-executions --method get --path executions/

Gera a estrutura:
    src/use_cases/<domain>/<use_case_name>/
        __init__.py
        dtos.py
        use_case.py
        factory.py
        view.py
"""

import os
import re
from django.core.management.base import BaseCommand, CommandError

HTTP_METHODS = ["get", "post", "put", "patch", "delete"]


def to_snake_case(name: str) -> str:
    """create-branch → create_branch"""
    return name.replace("-", "_").lower()


def to_pascal_case(name: str) -> str:
    """create-branch → CreateBranch"""
    return "".join(word.capitalize() for word in re.split(r"[-_]", name))


def to_snake_domain(name: str) -> str:
    """branch-layout → branch_layout"""
    return name.replace("-", "_").lower()


def to_kebab_case(name: str) -> str:
    """create_branch → create-branch"""
    return name.replace("_", "-").lower()


# ──────────────────────────────────────────────
# Templates — equivalentes aos .hbs do Plop
# ──────────────────────────────────────────────

TEMPLATE_DTOS = '''\
from dataclasses import dataclass


@dataclass
class {pascal_name}Input:
    pass  # TODO: defina os campos do input


@dataclass
class {pascal_name}Output:
    pass  # TODO: defina os campos do output
'''

TEMPLATE_USE_CASE = '''\
from src.core import UseCase
from src.core.either import Either, right, wrong
from src.errors import InputValidationError, ApplicationError, BusinessError, UnknownError
from .dtos import {pascal_name}Input, {pascal_name}Output

Input = {pascal_name}Input
FailureOutput = BusinessError | ApplicationError | UnknownError
SuccessOutput = {pascal_name}Output


class {pascal_name}UseCase(UseCase):
    def __init__(self, repository):
        self.repository = repository

    def validate(self, input_data: Input) -> Either:
        if not input_data:
            return wrong(InputValidationError("invalid input"))
        return right(None)

    def execute(self, input_data: Input) -> Either:
        try:
            # TODO: implemente a lógica de negócio
            return right({pascal_name}Output())
        except Exception as e:
            return wrong(UnknownError(str(e)))
'''

TEMPLATE_FACTORY = '''\
from .use_case import {pascal_name}UseCase

# from src.entities.{snake_domain}.repository import {pascal_domain}Repository


def build_use_case() -> {pascal_name}UseCase:
    # repository = {pascal_domain}Repository()
    repository = None  # TODO: substitua pelo repository real
    return {pascal_name}UseCase(repository)
'''

# view.py — o nome do método Python (get/post/put/patch/delete) é {http_method}
TEMPLATE_VIEW = '''\
from rest_framework.request import Request
from rest_framework.response import Response

from src.core import Controller
from src.errors import InputValidationError, UnknownError
from .dtos import {pascal_name}Input
from .factory import build_use_case


class {pascal_name}View(Controller):
    def {http_method}(self, request: Request{url_kwargs}) -> Response:
        use_case = build_use_case()

        input_data = {pascal_name}Input(
            # TODO: mapeie os campos do request.data{kwargs_hint}
        )

        result = use_case.run(input_data)

        if result.is_wrong():
            error = result.value
            return self.map_error(error, {{
                InputValidationError: self.bad_request,
                UnknownError: self.internal_server_error,
            }})

        return self.{success_response}(result.value)
'''

TEMPLATE_INIT = '''\
from .view import {pascal_name}View
from .use_case import {pascal_name}UseCase
from .factory import build_use_case
'''

URL_SNIPPET = '''\

# Adicione em config/urls.py:
#   from src.use_cases.{snake_domain}.{snake_name}.view import {pascal_name}View
#   path("{http_path}", {pascal_name}View.as_view(), name="{kebab_name}"),
'''


class Command(BaseCommand):
    help = "Gera a estrutura de um use case DDD (equivalente ao npx plop)"

    def add_arguments(self, parser):
        parser.add_argument("domain", type=str, nargs="?", default=None,
                             help="Nome do domínio (ex: branch, auth, execution)")
        parser.add_argument("use_case", type=str, nargs="?", default=None,
                             help="Nome do use case em kebab-case (ex: create-branch)")
        parser.add_argument("--method", type=str, choices=HTTP_METHODS, default=None,
                             help="Método HTTP do use case (get, post, put, patch, delete)")
        parser.add_argument("--path", type=str, default=None,
                             help="Path da rota (ex: branches/, branches/<uuid:id>/)")
        parser.add_argument("--dry-run", action="store_true",
                             help="Mostra o que seria gerado sem criar os arquivos")

    def handle(self, *args, **options):
        domain_raw = options["domain"]
        use_case_raw = options["use_case"]
        http_method = options["method"]
        http_path = options["path"]
        dry_run: bool = options["dry_run"]

        # ── Modo interativo, igual o prompt do Plop ──
        if not domain_raw:
            domain_raw = input("🏷️  Domínio (ex: branch, auth, execution): ").strip()
        if not use_case_raw:
            use_case_raw = input("📦 Nome do use case (kebab-case, ex: create-branch): ").strip()
        if not http_method:
            self.stdout.write("🌐 Método HTTP:")
            for i, m in enumerate(HTTP_METHODS, 1):
                self.stdout.write(f"   {i}) {m.upper()}")
            choice = input(f"   Escolha [1-{len(HTTP_METHODS)}] (default: 2-POST): ").strip()
            try:
                http_method = HTTP_METHODS[int(choice) - 1] if choice else "post"
            except (ValueError, IndexError):
                http_method = "post"
        if not http_path:
            snake_name_guess = to_snake_case(use_case_raw)
            domain_guess = to_snake_domain(domain_raw)
            default_path = f"{domain_guess}/"
            http_path = input(f"🔗 Path da rota (default: {default_path}): ").strip() or default_path

        if not domain_raw or not use_case_raw:
            raise CommandError("Domínio e nome do use case são obrigatórios.")

        http_method = http_method.lower()
        if http_method not in HTTP_METHODS:
            raise CommandError(f"Método HTTP inválido: {http_method}. Use um de {HTTP_METHODS}")

        snake_domain = to_snake_domain(domain_raw)
        pascal_domain = to_pascal_case(domain_raw)
        snake_name = to_snake_case(use_case_raw)
        pascal_name = to_pascal_case(use_case_raw)
        kebab_name = to_kebab_case(snake_name)

        # path params (ex: branches/<uuid:id>/) viram kwargs no método da view
        path_params = re.findall(r"<[\w:]+:(\w+)>", http_path or "")
        url_kwargs = "".join(f", {p}=None" for p in path_params)
        kwargs_hint = f"\n            # Path params disponíveis: {', '.join(path_params)}" if path_params else ""

        success_response = "created" if http_method == "post" else "ok"
        if http_method == "delete":
            success_response = "no_content"

        base_path = os.path.join("src", "use_cases", snake_domain, snake_name)

        files = {
            "__init__.py": TEMPLATE_INIT.format(pascal_name=pascal_name),
            "dtos.py": TEMPLATE_DTOS.format(pascal_name=pascal_name),
            "use_case.py": TEMPLATE_USE_CASE.format(pascal_name=pascal_name),
            "factory.py": TEMPLATE_FACTORY.format(
                pascal_name=pascal_name,
                snake_domain=snake_domain,
                pascal_domain=pascal_domain,
            ),
            "view.py": TEMPLATE_VIEW.format(
                pascal_name=pascal_name,
                http_method=http_method,
                url_kwargs=url_kwargs,
                kwargs_hint=kwargs_hint,
                success_response=success_response,
            ),
        }

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\n🚀 Gerando use case: {pascal_name} ({http_method.upper()} /{http_path}) — domínio: {pascal_domain}\n"
        ))

        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️  Modo dry-run — nenhum arquivo será criado\n"))

        domain_init = os.path.join("src", "use_cases", snake_domain, "__init__.py")
        if not dry_run:
            os.makedirs(base_path, exist_ok=True)
            if not os.path.exists(domain_init):
                open(domain_init, "w").close()
                self.stdout.write(f"  + {domain_init}")

        for filename, content in files.items():
            file_path = os.path.join(base_path, filename)

            if not dry_run and os.path.exists(file_path):
                raise CommandError(
                    f"Arquivo já existe: {file_path}\n"
                    "Use --dry-run para inspecionar antes de sobrescrever."
                )

            if dry_run:
                self.stdout.write(self.style.SUCCESS(f"\n📄 {file_path}"))
                self.stdout.write(self.style.HTTP_INFO("─" * 60))
                self.stdout.write(content)
            else:
                with open(file_path, "w") as f:
                    f.write(content)
                self.stdout.write(self.style.SUCCESS(f"  ✓ {file_path}"))

        url_snippet = URL_SNIPPET.format(
            snake_domain=snake_domain,
            snake_name=snake_name,
            pascal_name=pascal_name,
            http_path=http_path,
            kebab_name=kebab_name,
        )

        if dry_run:
            self.stdout.write(self.style.HTTP_INFO(url_snippet))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\n✅ Use case '{pascal_name}' criado em {base_path}\n"
            ))
            self.stdout.write(url_snippet)
            self.stdout.write(
                f"\n💡 Próximos passos:\n"
                f"   1. Defina os campos em {base_path}/dtos.py\n"
                f"   2. Implemente a lógica em {base_path}/use_case.py\n"
                f"   3. Configure o repository em {base_path}/factory.py\n"
                f"   4. Registre a rota em config/urls.py (snippet acima)\n"
            )
