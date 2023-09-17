from __future__ import annotations

from types import GenericAlias, UnionType
from typing import Any, Literal, TypeAlias

from pydantic.fields import FieldInfo

BaseGenericAlias: TypeAlias = type(  # type: ignore[name-defined]
    Literal[0],
).__base__.__base__
SpecialForm: TypeAlias = type(Any)  # type: ignore[valid-type]
TypeHint: TypeAlias = (
    type  # type: ignore[valid-type]
    | GenericAlias
    | UnionType
    | BaseGenericAlias
    | SpecialForm
    | type(None)
)

FieldType: TypeAlias = tuple[TypeHint, FieldInfo]
