from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from typing import Any

from pydantic import ConfigDict, create_model
from typing_extensions import Self

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
                        create_model(  # type: ignore[call-overload]
                            "Model",
                            **fields,
                            __config__=ConfigDict(  # TODO maybe move to `contains`
                                from_attributes=True,
                                populate_by_name=True,
                                arbitrary_types_allowed=True,
                            ),
                        ),
                    )
            return None

    return NestedFieldInner
