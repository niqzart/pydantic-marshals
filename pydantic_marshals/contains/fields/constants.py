from __future__ import annotations

from datetime import date, time
from typing import Annotated, Any, Literal, TypeVar

from pydantic import AfterValidator
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


T = TypeVar("T")


class DatetimeField(MarshalField):
    def __init__(self, timestamp: date | time) -> None:
        super().__init__()
        self.timestamp = timestamp
        self.type_ = type(timestamp)

    @classmethod
    def convert(cls, timestamp: Any = None, *_: Any) -> Self | None:
        if isinstance(timestamp, date | time):
            return cls(timestamp)
        return None

    def constant_validator(self, value: T) -> T:
        if value != self.timestamp:
            raise ValueError(f"timestamp should be '{self.timestamp}'")
        return value

    def generate_type(self) -> TypeHint:
        return Annotated[self.type_, AfterValidator(self.constant_validator)]
