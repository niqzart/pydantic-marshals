from __future__ import annotations

from typing import Annotated, Any, Generic, Literal, TypeVar

from pydantic import AfterValidator
from typing_extensions import Self

from pydantic_marshals.base.fields.base import MarshalField
from pydantic_marshals.base.type_aliases import TypeHint
from pydantic_marshals.contains.type_aliases import LiteralType


class LiteralConstantField(MarshalField):
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


FieldType = TypeVar("FieldType")


class ArbitraryConstantField(MarshalField, Generic[FieldType]):
    def __init__(self, expected: FieldType) -> None:
        super().__init__()
        self.expected = expected
        self.type_ = type(expected)

    @classmethod
    def convert(cls, expected: Any = None, *_: Any) -> Self | None:
        if expected == expected:  # noqa: WPS312
            # check if equality operator is supported
            return cls(expected)
        return None

    def equality_validator(self, real: FieldType) -> FieldType:
        if real != self.expected:
            raise ValueError(f"should be equal to '{self.expected}'")
        return real

    def generate_type(self) -> TypeHint:
        return Annotated[self.type_, AfterValidator(self.equality_validator)]
