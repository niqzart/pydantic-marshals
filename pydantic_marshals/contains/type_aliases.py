from __future__ import annotations

from enum import Enum
from types import EllipsisType
from typing import TypeAlias

from pydantic_marshals.contains.type_generators.base import BaseTypeGenerator

LiteralType: TypeAlias = bool | int | float | bytes | str | Enum
TypeChecker: TypeAlias = (
    None
    | type
    | dict
    | list
    | type[LiteralType]
    | LiteralType
    | EllipsisType
    | BaseTypeGenerator
)
