from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class Controller(APIView):
    """
    Classe base para todos os controllers (views DRF).
    Equivalente ao Controller do @overnightjs/core.
    """

    def ok(self, data=None) -> Response:
        return Response(data, status=status.HTTP_200_OK)

    def created(self, data=None) -> Response:
        return Response(data, status=status.HTTP_201_CREATED)

    def no_content(self) -> Response:
        return Response(status=status.HTTP_204_NO_CONTENT)

    def bad_request(self, data=None) -> Response:
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    def unauthorized(self, data=None) -> Response:
        return Response(data, status=status.HTTP_401_UNAUTHORIZED)

    def forbidden(self, data=None) -> Response:
        return Response(data, status=status.HTTP_403_FORBIDDEN)

    def not_found(self, data=None) -> Response:
        return Response(data, status=status.HTTP_404_NOT_FOUND)

    def internal_server_error(self, data=None) -> Response:
        return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def map_error(self, error, error_map: dict) -> Response:
        """
        Mapeia um erro para um método de resposta HTTP.
        Equivalente ao mapError() do TS.

        Uso:
            return self.map_error(error, {
                InputValidationError: self.bad_request,
                NotFoundError: self.not_found,
            })
        """
        handler = error_map.get(type(error))
        if handler:
            return handler({"error": str(error)})
        return self.internal_server_error({"error": "UnknownError"})
