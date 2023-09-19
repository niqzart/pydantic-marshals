from __future__ import annotations

from typing import Any, Literal

from typing_extensions import Self

from pydantic_marshals.base.fields.base import MarshalField
from pydantic_marshals.base.type_aliases import TypeHint
from pydantic_marshals.contains.type_aliases import LiteralType


class ConstantField(MarshalField):
    def __init__(self, constant: LiteralType) -> None:
        super().__init__()
        self.constant = constant

    @classmethod
    def convert(cls, constant: Any = None, *_: Any) -> Self | None:
        if isinstance(constant, LiteralType):  # type: ignore[misc, arg-type]
            # https://github.com/python/mypy/issues/12155 ^^^^^^^^^^^^^^^^^^^
            return cls(constant)
        return None

    def generate_type(self) -> TypeHint:
        # noinspection PyTypeHints
        return Literal[self.constant]  # pycharm bug
