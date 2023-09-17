from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Self

from pydantic_marshals.base.fields.base import MarshalField
from pydantic_marshals.base.type_aliases import TypeHint


class NothingField(MarshalField):
    @classmethod
    def convert(cls, source: Any = None, *_: Any) -> Self | None:
        if source is None:
            return cls()
        return None

    def generate_type(self) -> TypeHint:
        return type(None)

    def generate_field_data(self) -> Iterator[tuple[str, Any]]:
        yield "default", None


class SomethingField(MarshalField):
    @classmethod
    def convert(cls, source: Any = None, *_: Any) -> Self | None:
        if source is ...:
            return cls()
        return None

    def generate_type(self) -> TypeHint:
        return Any


class AnythingField(MarshalField):
    @classmethod
    def convert(cls, source: Any = None, *_: Any) -> Self | None:
        if source is Any:
            return cls()
        return None

    def generate_type(self) -> TypeHint:
        return Any

    def generate_field_data(self) -> Iterator[tuple[str, Any]]:
        yield "default", None
