from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from typing import Any, Self

from pydantic import BaseModel, create_model

from pydantic_marshals.base.fields.base import MarshalField
from pydantic_marshals.contains.type_aliases import FieldType, TypeChecker, TypeHint


def nested_field_factory(  # noqa: N802
    convert_field: Callable[[TypeChecker], FieldType],
) -> type[MarshalField]:
    class NestedFieldInner(MarshalField):
        def __init__(self, model: type[BaseModel]) -> None:
            super().__init__()
            self.model = model

        @classmethod
        def convert(cls, source: Any = None, *_: Any) -> Self | None:
            if isinstance(source, dict):
                with suppress(RuntimeError):
                    fields: dict[str, FieldType] = {
                        key: convert_field(value) for key, value in source.items()
                    }  # TODO check if `isinstance(value, TypeChecker)`
                    return cls(
                        create_model("Model", **fields),  # type: ignore[call-overload]
                    )
            return None

        def generate_type(self) -> TypeHint:
            return self.model

    return NestedFieldInner
