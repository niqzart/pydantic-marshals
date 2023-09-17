from __future__ import annotations

from collections.abc import Iterator
from enum import Enum
from types import EllipsisType
from typing import Annotated, Any, Literal, Optional, TypeAlias, get_origin

from pydantic import BaseModel, RootModel, ValidationError, create_model
from pydantic.fields import Field, FieldInfo

# TODO put all of this in a MarshalField (mb think about a Model, minimalist-style)

# TODO TypingGenericAlias = type(Literal[int]).__base__ (or .__base__ of that)
TypeHint = Any
# TODO ``from types import UnionType, GenericAlias`` to allow `int | None` & such
# TODO ``type(Literal[int]).__base__`` to allow type-hints from typing
# TODO add both things from above to the return type (also in base.fields.base)
#   https://stackoverflow.com/questions/73763352/how-do-i-type-hint-a-variable-whose-value-is-itself-a-type-hint
LiteralType: TypeAlias = int | str | bool | float | Enum
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


def convert_model(source: dict[str, TypeChecker]) -> type[BaseModel]:
    fields: dict[str, FieldType] = {
        key: convert_field(value) for key, value in source.items()
    }
    return create_model("Model", **fields)  # type: ignore[call-overload, no-any-return]


def convert_type(source: TypeChecker) -> TypeHint:
    if source is None:
        return type(None)
    if source is ... or source is Any:
        return Any
    if isinstance(source, LiteralType):  # type: ignore[misc, arg-type]
        # https://github.com/python/mypy/issues/12155 ^^^^^^^^^^^^^^^^^
        return Literal[source]
    if isinstance(source, type):
        return source
    if isinstance(source, dict):
        return convert_model(source)
    if isinstance(source, list):
        return tuple[  # type: ignore[misc]
            *(convert_type(value) for value in source)  # noqa: WPS356 (bug in WPS)
        ]
    if get_origin(source) in {Annotated, Optional}:
        return source
    raise RuntimeError(f"Can't convert {source} to a type")


def convert_field_data(source: TypeChecker) -> Iterator[tuple[str, Any]]:
    if source is None or source is Any:
        yield "default", None


def convert_field(source: TypeChecker) -> FieldType:
    return (
        convert_type(source),
        Field(**dict(convert_field_data(source))),
    )


def build_contains_model(source: TypeChecker) -> type[BaseModel]:
    return RootModel[convert_field(source)[0]]  # type: ignore[no-any-return, misc]


def assert_contains(real: Any, expected: TypeChecker) -> None:
    try:
        build_contains_model(expected).model_validate(real)
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
