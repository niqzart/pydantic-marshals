from types import NoneType, UnionType
from typing import Any, TypeVar, get_args, get_origin

from pydantic import BaseModel

T = TypeVar("T")
ModeledType = tuple[T, type[BaseModel]]


def is_subtype(maybe_type: Any, klass: type) -> bool:
    return isinstance(maybe_type, type) and issubclass(maybe_type, klass)


def is_optional(annotation: Any) -> bool:
    return get_origin(annotation) == UnionType and NoneType in get_args(annotation)
