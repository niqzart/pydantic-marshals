from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from typing import Any, Self

from pydantic import create_model

from pydantic_marshals.base.fields.base import MarshalField
from pydantic_marshals.base.type_aliases import FieldType
from pydantic_marshals.contains.fields.typed import TypedField
from pydantic_marshals.contains.type_aliases import TypeChecker


def nested_field_factory(  # noqa: N802
    convert_field: Callable[[TypeChecker], FieldType],
) -> type[MarshalField]:
    class NestedFieldInner(TypedField):
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

    return NestedFieldInner
