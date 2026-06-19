from typing import TypeVar, Generic, Union

L = TypeVar("L")
R = TypeVar("R")


class Either(Generic[L, R]):
    def __init__(self, value: Union[L, R], is_right: bool):
        self._value = value
        self._is_right = is_right

    @property
    def value(self) -> Union[L, R]:
        return self._value

    def is_right(self) -> bool:
        return self._is_right

    def is_wrong(self) -> bool:
        return not self._is_right


def right(value: R) -> Either:
    return Either(value, is_right=True)


def wrong(value: L) -> Either:
    return Either(value, is_right=False)
