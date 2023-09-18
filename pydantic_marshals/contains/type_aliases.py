from __future__ import annotations

from enum import Enum
from types import EllipsisType
from typing import TypeAlias

LiteralType: TypeAlias = (
    bool | int | float | bytes | str | Enum
)  # TODO move to constants
TypeChecker: TypeAlias = (
    None | type | dict | list | type[LiteralType] | LiteralType | EllipsisType
)
