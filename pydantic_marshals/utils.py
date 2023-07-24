from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T")
ModeledType = tuple[T, type[BaseModel]]


def is_subtype(maybe_type: Any, klass: type) -> bool:
    return isinstance(maybe_type, type) and issubclass(maybe_type, klass)
