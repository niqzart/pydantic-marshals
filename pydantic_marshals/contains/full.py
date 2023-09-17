from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import suppress
from enum import Enum
from types import EllipsisType
from typing import Annotated, Any, Literal, Optional, Self, TypeAlias, get_origin

from pydantic import BaseModel, ValidationError, create_model
from pydantic.fields import FieldInfo

from pydantic_marshals.base.fields.base import MarshalField
from pydantic_marshals.base.models import MarshalModel

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


class NothingField(MarshalField):
    @classmethod
    def convert(cls, source: Any = None, *_: Any) -> Self | None:
        if source is None:
            return cls()
        return None

    def generate_type(self) -> TypeHint:
        return type(None)

    def generate_field_data(self) -> Iterator[tuple[str, Any]]:
        yield "default", None


class SomethingField(MarshalField):
    @classmethod
    def convert(cls, source: Any = None, *_: Any) -> Self | None:
        if source is ...:
            return cls()
        return None

    def generate_type(self) -> TypeHint:
        return Any


class AnythingField(MarshalField):
    @classmethod
    def convert(cls, source: Any = None, *_: Any) -> Self | None:
        if source is Any:
            return cls()
        return None

    def generate_type(self) -> TypeHint:
        return Any

    def generate_field_data(self) -> Iterator[tuple[str, Any]]:
        yield "default", None


class ConstantField(MarshalField):
    def __init__(self, constant: LiteralType) -> None:
        super().__init__()
        self.constant = constant

    @classmethod
    def convert(cls, constant: Any = None, *_: Any) -> Self | None:
        if isinstance(constant, LiteralType):  # type: ignore[misc, arg-type]
            # https://github.com/python/mypy/issues/12155 ^^^^^^^^^^^^^^^^^^^^^^
            return cls(constant)
        return None

    def generate_type(self) -> TypeHint:
        # noinspection PyTypeHints
        return Literal[self.constant]  # pycharm bug


class TypedField(MarshalField):
    def __init__(self, type_: TypeHint) -> None:  # TODO optional
        super().__init__()
        self.type_ = type_

    @classmethod
    def convert(cls, source: Any = None, *_: Any) -> Self | None:
        if isinstance(source, type) or get_origin(source) in {Annotated, Optional}:
            return cls(source)
        return None

    def generate_type(self) -> TypeHint:
        return self.type_


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
                    }
                    return cls(
                        create_model("Model", **fields),  # type: ignore[call-overload]
                    )
            return None

        def generate_type(self) -> TypeHint:
            return self.model

    return NestedFieldInner


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


class UniterModel(MarshalModel):  # TODO only ``convert_field`` is needed
    field_types = (
        NothingField,
        SomethingField,
        AnythingField,
        ConstantField,
        TypedField,
    )

    @classmethod
    def dynamic_field_types(cls) -> Iterator[type[MarshalField]]:
        yield nested_field_factory(cls.convert_to_field)
        yield strict_list_field_factory(cls.convert_to_type)

    @classmethod
    def convert_to_type(cls, source: TypeChecker) -> TypeHint:
        return cls.convert_field(source).generate_type()

    @classmethod
    def convert_to_field(cls, source: TypeChecker) -> FieldType:
        return cls.convert_field(source).generate_field()

    @classmethod
    def contains(cls, real: Any, expected: TypeChecker) -> None:
        cls.convert_field(expected).generate_root_model().model_validate(real)


def assert_contains(real: Any, expected: TypeChecker) -> None:
    try:
        UniterModel.contains(real, expected)
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
