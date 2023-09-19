from __future__ import annotations

from collections.abc import Callable
from typing import Any, Self

from pydantic_marshals.base.fields.base import MarshalField
from pydantic_marshals.base.type_aliases import TypeHint
from pydantic_marshals.contains.fields.typed import TypedField
from pydantic_marshals.contains.type_aliases import TypeChecker


def strict_list_field_factory(
    convert_type: Callable[[TypeChecker], TypeHint],
) -> type[MarshalField]:
    class StrictListFieldInner(TypedField):
        @classmethod
        def convert(cls, source: Any = None, *_: Any) -> Self | None:
            if isinstance(source, list):
                return cls(
                    tuple[  # type: ignore[misc]
                        *(  # noqa: WPS356 (bug in WPS)
                            convert_type(value) for value in source
                        )
                    ],
                )
            return None

    return StrictListFieldInner
