from __future__ import annotations

from enum import Enum
from types import EllipsisType
from typing import Any, TypeAlias

from pydantic.fields import FieldInfo

# TODO TypingGenericAlias = type(Literal[int]).__base__ (or .__base__ of that)

TypeHint = Any
# TODO ``from types import UnionType, GenericAlias`` to allow `int | None` & such
# TODO ``type(Literal[int]).__base__`` to allow type-hints from typing
# TODO add both things from above to the return type (also in base.fields.base)
#   https://stackoverflow.com/questions/73763352/how-do-i-type-hint-a-variable-whose-value-is-itself-a-type-hint

LiteralType: TypeAlias = (
    bool | int | float | bytes | str | Enum
)  # TODO move to constants
TypeChecker: TypeAlias = (
    None  # noqa: WPS465
    | type
    | dict
    | list
    | type[LiteralType]
    | LiteralType
    | EllipsisType
)
FieldType: TypeAlias = tuple[TypeHint, FieldInfo]
