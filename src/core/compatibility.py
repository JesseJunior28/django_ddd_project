"""Convenções HTTP compartilhadas pelos controladores."""
import math
import re

from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

from .controller import Controller


def js_number(value):
    if isinstance(value, list):
        value = ",".join(str(item) for item in value)
    if isinstance(value, dict):
        return float("nan")
    if value is None:
        return 0
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return 0
        try:
            if re.match(r"^0[xob]", value, re.I):
                return int(value, 0)
            if value.lower() in ("inf", "+inf", "-inf", "infinity", "+infinity", "-infinity"):
                return float(value) if value in ("Infinity", "+Infinity", "-Infinity") else float("nan")
            return float(value)
        except ValueError:
            return float("nan")
    return float(value)


def js_truthy(value):
    return value is not None and value is not False and value != "" and not (
        isinstance(value, (float, int)) and (value == 0 or math.isnan(value)))


def query_value(query, key):
    """Lê valores escalares, repetidos e arrays com chaves entre colchetes."""
    values = query.getlist(key)
    bracket = query.getlist(key + "[]")
    indexed = [(name, query.getlist(name)) for name in query if name.startswith(key + "[")
               and name != key + "[]"]
    if indexed:
        entries = {name[len(key) + 1:-1]: items[0] if len(items) == 1 else items
                   for name, items in indexed}
        if all(index.isdigit() and int(index) <= 20 for index in entries):
            return values + bracket + [entries[index] for index in sorted(entries, key=int)]
        return entries
    if bracket:
        return values + bracket
    return values if len(values) > 1 else values[0] if values else None


class HttpContractError(Exception):
    def __init__(self, status, name, message):
        self.status, self.name, self.message = status, name, message


class CompatibilityController(Controller):
    authentication_classes = []
    permission_classes = []
    renderer_classes = [JSONRenderer]

    def handle_exception(self, exc):
        if isinstance(exc, HttpContractError):
            return Response({"name": exc.name, "message": exc.message}, status=exc.status)
        return super().handle_exception(exc)

    def respond(self, result, error_status):
        if result.is_wrong():
            error = result.value
            return Response({"name": type(error).__name__, "message": str(error)},
                            status=error_status.get(type(error).__name__, 500))
        return self.ok(result.value)
