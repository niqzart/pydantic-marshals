from __future__ import annotations

from typing import Annotated, Any, Optional, Self, get_origin

from pydantic_marshals.base.fields.base import MarshalField
from pydantic_marshals.base.type_aliases import TypeHint


class TypedField(MarshalField):
    def __init__(self, type_: TypeHint) -> None:  # TODO optional
        super().__init__()
        self.type_ = type_

    @classmethod
    def convert(cls, source: Any = None, *_: Any) -> Self | None:
        if (
            source is not Any
            and isinstance(source, type)
            or get_origin(source) in {Annotated, Optional}
        ):
            return cls(source)
        return None

    def generate_type(self) -> TypeHint:
        return self.type_
