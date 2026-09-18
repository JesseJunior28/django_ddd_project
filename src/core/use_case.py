import logging
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

from src.errors import UnknownError
from .either import Either, wrong

logger = logging.getLogger(__name__)

Input = TypeVar("Input")
FailureOutput = TypeVar("FailureOutput")
SuccessOutput = TypeVar("SuccessOutput")


class UseCase(ABC, Generic[Input, FailureOutput, SuccessOutput]):
    """
    Classe base para todos os use cases.
    Segue o mesmo padrão do TS: validate() -> execute()
    """

    @abstractmethod
    def validate(self, input_data: Input) -> Either:
        """Valida o input antes de executar. Retorna wrong(error) ou right(None)."""
        ...

    @abstractmethod
    def execute(self, input_data: Input) -> Either:
        """Executa a lógica de negócio. Retorna wrong(error) ou right(output)."""
        ...

    def run(self, input_data: Input) -> Either[FailureOutput, SuccessOutput]:
        """
        Ponto de entrada do use case. Chama validate e depois execute.

        Exceção inesperada (bug, banco fora do ar...) é logada com traceback
        e vira UnknownError genérico — o detalhe nunca chega ao cliente.
        Erros esperados devem ser retornados com wrong() pelo próprio use case.
        """
        try:
            validation = self.validate(input_data)
            if validation.is_wrong():
                return wrong(validation.value)
            return self.execute(input_data)
        except Exception:
            logger.exception("Erro inesperado em %s", type(self).__name__)
            return wrong(UnknownError())
