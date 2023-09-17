from __future__ import annotations

from enum import Enum
from types import EllipsisType
from typing import Any, Literal, TypeAlias

from pydantic import Field, ValidationError, create_model
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

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


def convert_to_type(source: TypeChecker) -> TypeHint:
    # TODO somehow support Optional[{"hey": 1}] (and may be Union aka OR? via set?)
    # TODO port new features to ffs whenever possible

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
        fields: dict[str, FieldType] = {
            key: convert_to_field(value) for key, value in source.items()
        }
        return create_model("Model", **fields)  # type: ignore[call-overload]
    if isinstance(source, list):
        return tuple[  # type: ignore[misc]
            *(convert_to_field(value) for value in source)  # noqa: WPS356 (bug in WPS)
        ]
    raise RuntimeError(f"Can't convert {source} to a type")


def convert_to_default(source: TypeChecker) -> Any | None:
    if source is None or source is Any:
        return None
    return PydanticUndefined


def convert_to_field(source: TypeChecker) -> FieldType:
    return convert_to_type(source), Field(default=convert_to_default(source))
    # TODO default=None for Anything but not Something in v2


def check_contains(real: Any, expected: TypeChecker, field_name: str) -> None:
    create_model(  # type: ignore[call-overload]
        "Model",
        **{field_name: convert_to_field(expected)},
    ).model_validate({field_name: real})


def assert_contains(real: Any, expected: TypeChecker) -> None:
    try:
        create_model("Model", __root__=convert_to_field(expected)).model_validate(real)
    except ValidationError as e:
        raise AssertionError(str(e))
