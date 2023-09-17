from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from pydantic import ValidationError

from pydantic_marshals.base.fields.base import MarshalField
from pydantic_marshals.base.models import FieldConverter
from pydantic_marshals.base.type_aliases import FieldType, TypeHint
from pydantic_marshals.contains.fields.constants import ConstantField
from pydantic_marshals.contains.fields.lists import strict_list_field_factory
from pydantic_marshals.contains.fields.nested import nested_field_factory
from pydantic_marshals.contains.fields.typed import TypedField
from pydantic_marshals.contains.fields.wildcards import (
    AnythingField,
    NothingField,
    SomethingField,
)
from pydantic_marshals.contains.type_aliases import TypeChecker


class UniterModel(FieldConverter):
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
        raise AssertionError(str(e)) from None


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
