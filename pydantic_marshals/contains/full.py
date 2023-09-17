from __future__ import annotations

from collections.abc import Iterator
from enum import Enum
from types import EllipsisType
from typing import Annotated, Any, Literal, Optional, Self, TypeAlias, get_origin

from pydantic import ValidationError, create_model
from pydantic.fields import FieldInfo

from pydantic_marshals.base.fields.base import MarshalField

# TODO put all of this in a MarshalField (mb think about a Model, minimalist-style)

# TODO TypingGenericAlias = type(Literal[int]).__base__ (or .__base__ of that)
TypeHint = Any
# TODO ``from types import UnionType, GenericAlias`` to allow `int | None` & such
# TODO ``type(Literal[int]).__base__`` to allow type-hints from typing
# TODO add both things from above to the return type (also in base.fields.base)
#   https://stackoverflow.com/questions/73763352/how-do-i-type-hint-a-variable-whose-value-is-itself-a-type-hint
LiteralType: TypeAlias = bool | int | float | bytes | str | Enum
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


class ContainsField(MarshalField):
    def __init__(self, source: TypeChecker) -> None:
        super().__init__()
        self.source = source

    @classmethod
    def convert(cls, source: TypeChecker = None, *_: Any) -> Self | None:
        # TODO `isinstance(source, TypeChecker)`
        return cls(source)

    # TODO generate_name?

    @classmethod
    def convert_to_type(cls, source: TypeChecker) -> TypeHint:
        return cls(source).generate_type()

    @classmethod
    def convert_to_field(cls, source: TypeChecker) -> TypeHint:
        return cls(source).generate_field()

    def generate_type(self) -> TypeHint:
        if self.source is None:
            return type(None)
        if self.source is ... or self.source is Any:
            return Any
        if isinstance(self.source, LiteralType):  # type: ignore[misc, arg-type]
            # https://github.com/python/mypy/issues/12155 ^^^^^^^^^^^^^^^^^
            return Literal[self.source]
        if isinstance(self.source, type):
            return self.source
        if isinstance(self.source, dict):
            fields: dict[str, FieldType] = {
                key: self.convert_to_field(value) for key, value in self.source.items()
            }
            return create_model("Model", **fields)  # type: ignore[call-overload]
        if isinstance(self.source, list):
            return tuple[  # type: ignore[misc]
                *(  # noqa: WPS356 (bug in WPS)
                    self.convert_to_type(value) for value in self.source
                )
            ]
        if get_origin(self.source) in {Annotated, Optional}:
            return self.source
        raise RuntimeError(f"Can't convert {self.source!r} to a type")

    def generate_field_data(self) -> Iterator[tuple[str, Any]]:
        if self.source is None or self.source is Any:
            yield "default", None


def assert_contains(real: Any, expected: TypeChecker) -> None:
    try:
        ContainsField(expected).generate_root_model().model_validate(real)
    except ValidationError as e:
        raise AssertionError(str(e))


if __name__ == "__main__":
    from pydantic import conlist  # noqa: WPS433

    checker = {
        "a": "3",
        "b": 3,
        "c": [{"d": int, "e": None}],
        "d": conlist(item_type=str),
        "e": {"g": str, "b": ..., "e": Any},
    }

    assert_contains(
        {
            "a": "3",
            "b": 3,
            "c": [{"d": 4}],
            "d": ["str", "wow"],
            "e": {"g": "ger", "b": object()},
        },
        checker,
    )

    assert_contains(
        {
            "a": "5",
            "b": 6,
            "c": [{"d": "4", "e": 4}],
            "d": ["str", 3, object()],
            "e": {"g": 5},
        },
        checker,
    )
