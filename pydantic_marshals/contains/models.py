from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from pydantic import ValidationError

from pydantic_marshals.base.fields.base import MarshalField
from pydantic_marshals.base.models import FieldConverter
from pydantic_marshals.base.type_aliases import FieldType, TypeHint
from pydantic_marshals.contains.fields.constants import ConstantField, DatetimeField
from pydantic_marshals.contains.fields.lists import strict_list_field_factory
from pydantic_marshals.contains.fields.nested import nested_field_factory
from pydantic_marshals.contains.fields.typed import GeneratedTypeField, TypedField
from pydantic_marshals.contains.fields.wildcards import (
    AnythingField,
    NothingField,
    SomethingField,
)
from pydantic_marshals.contains.type_aliases import TypeChecker


class AssertContainsModel(FieldConverter):
    field_types = (
        NothingField,
        SomethingField,
        AnythingField,
        ConstantField,
        DatetimeField,
        TypedField,
        GeneratedTypeField,
        # TODO plain object (with __eq__) field
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
        AssertContainsModel.contains(real, expected)
    except ValidationError as e:
        raise AssertionError(str(e)) from None
