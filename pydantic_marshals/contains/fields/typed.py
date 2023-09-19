from __future__ import annotations

from types import UnionType
from typing import Annotated, Any, Union, get_origin

from typing_extensions import Self

from pydantic_marshals.base.fields.base import MarshalField
from pydantic_marshals.base.type_aliases import TypeHint
from pydantic_marshals.contains.type_generators.base import BaseTypeGenerator


class TypedField(MarshalField):
    def __init__(self, type_: TypeHint) -> None:  # TODO optional
        super().__init__()
        self.type_ = type_

    @classmethod
    def convert(cls, source: Any = None, *_: Any) -> Self | None:
        if (
            source is not Any
            and isinstance(source, type)
            or get_origin(source) in {Annotated, Union, UnionType}
        ):
            return cls(source)
        return None

    def generate_type(self) -> TypeHint:
        return self.type_


class GeneratedTypeField(TypedField):
    @classmethod
    def convert(cls, source: Any = None, *_: Any) -> Self | None:
        if isinstance(source, BaseTypeGenerator):
            return cls(source.to_typehint())
        return None
