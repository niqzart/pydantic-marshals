from collections.abc import Iterator
from typing import Annotated, Any, Literal, Optional, Union
from unittest.mock import Mock, patch

import pytest
from pydantic import BaseModel
from pydantic.fields import FieldInfo

from pydantic_marshals.base.fields.base import MarshalField
from pydantic_marshals.base.type_aliases import TypeHint
from pydantic_marshals.contains.fields import constants, typed, wildcards
from pydantic_marshals.contains.models import AssertContainsModel
from pydantic_marshals.contains.type_aliases import LiteralType
from pydantic_marshals.contains.type_generators.base import BaseTypeGenerator
from pydantic_marshals.contains.type_generators.collections import (
    UnorderedLiteralCollection,
)
from pydantic_marshals.utils import is_subtype
from tests.unit.conftest import DummyFactory, SampleEnum


@pytest.fixture()
def sample_field() -> typed.TypedField:
    return typed.TypedField(int)


@pytest.fixture()
def convert_field_mock_to_sample(sample_field: typed.TypedField) -> Iterator[Mock]:
    with patch.object(AssertContainsModel, "convert_field") as mock:
        mock.return_value = sample_field
        yield mock


NestedField = AssertContainsModel.field_types[6]  # type: ignore[misc]
StrictListField = AssertContainsModel.field_types[7]  # type: ignore[misc]

SOURCE_TO_KLASS: list[Any] = [
    pytest.param(None, wildcards.NothingField, id="none_nothing"),
    pytest.param(..., wildcards.SomethingField, id="..._something"),
    pytest.param(Any, wildcards.AnythingField, id="any_anything"),
    #
    pytest.param(True, constants.ConstantField, id="bool_constant"),
    pytest.param(1, constants.ConstantField, id="int_constant"),
    pytest.param(1.1, constants.ConstantField, id="float_constant"),
    pytest.param(b"test", constants.ConstantField, id="bytes_constant"),
    pytest.param("test", constants.ConstantField, id="str_constant"),
    pytest.param(SampleEnum.A, constants.ConstantField, id="enum_constant"),
    #
    pytest.param(bool, typed.TypedField, id="bool_typed"),
    pytest.param(int, typed.TypedField, id="int_typed"),
    pytest.param(float, typed.TypedField, id="float_typed"),
    pytest.param(bytes, typed.TypedField, id="bytes_typed"),
    pytest.param(str, typed.TypedField, id="str_typed"),
    pytest.param(SampleEnum, typed.TypedField, id="enum_typed"),
    #
    pytest.param(Optional[bool], typed.TypedField, id="optional_bool_typed"),
    pytest.param(Optional[int], typed.TypedField, id="optional_int_typed"),
    pytest.param(Optional[float], typed.TypedField, id="optional_float_typed"),
    pytest.param(Optional[bytes], typed.TypedField, id="optional_bytes_typed"),
    pytest.param(Optional[str], typed.TypedField, id="optional_str_typed"),
    pytest.param(Optional[SampleEnum], typed.TypedField, id="optional_enum_typed"),
    #
    pytest.param(Union[bool], typed.TypedField, id="typing_union_bool_typed"),
    pytest.param(Union[int], typed.TypedField, id="typing_union_int_typed"),
    pytest.param(Union[float], typed.TypedField, id="typing_union_float_typed"),
    pytest.param(Union[bytes], typed.TypedField, id="typing_union_bytes_typed"),
    pytest.param(Union[str], typed.TypedField, id="typing_union_str_typed"),
    pytest.param(Union[SampleEnum], typed.TypedField, id="typing_union_enum_typed"),
    #
    pytest.param(bool | None, typed.TypedField, id="pipe_union_bool_typed"),
    pytest.param(int | None, typed.TypedField, id="pipe_union_int_typed"),
    pytest.param(float | None, typed.TypedField, id="pipe_union_float_typed"),
    pytest.param(bytes | None, typed.TypedField, id="pipe_union_bytes_typed"),
    pytest.param(str | None, typed.TypedField, id="pipe_union_str_typed"),
    pytest.param(SampleEnum | None, typed.TypedField, id="pipe_union_enum_typed"),
    #
    pytest.param(Annotated[bool, 3], typed.TypedField, id="annotated_bool_typed"),
    pytest.param(Annotated[int, 3], typed.TypedField, id="annotated_int_typed"),
    pytest.param(Annotated[float, 3], typed.TypedField, id="annotated_float_typed"),
    pytest.param(Annotated[bytes, 3], typed.TypedField, id="annotated_bytes_typed"),
    pytest.param(Annotated[str, 3], typed.TypedField, id="annotated_str_typed"),
    pytest.param(Annotated[SampleEnum, 3], typed.TypedField, id="annotated_enum_typed"),
    #
    pytest.param(
        UnorderedLiteralCollection(set()),
        typed.GeneratedTypeField,
        id="literal_collection_generator",
    ),
    #
    pytest.param([], StrictListField, id="empty_list"),
    pytest.param([1], StrictListField, id="single_list"),
    pytest.param([1, int], StrictListField, id="double_list"),
    #
    pytest.param({}, NestedField, id="empty_nested"),
    pytest.param({"a": 1}, NestedField, id="single_nested"),
    pytest.param({"a": 1, "b": int}, NestedField, id="double_nested"),
]


@pytest.mark.usefixtures(convert_field_mock_to_sample.__name__)
@pytest.mark.parametrize(("source", "exclude_klass"), SOURCE_TO_KLASS)
def test_klass_skips(source: Any, exclude_klass: type[MarshalField]) -> None:
    klass: type[MarshalField]
    for klass in AssertContainsModel.field_types:
        if klass is exclude_klass:
            continue
        assert klass.convert(source) is None


@pytest.mark.usefixtures(convert_field_mock_to_sample.__name__)
@pytest.mark.parametrize(
    ("source", "klass", "type_", "has_default"),
    [
        pytest.param(None, wildcards.NothingField, type(None), True, id="none_nothing"),
        pytest.param(..., wildcards.SomethingField, Any, False, id="..._something"),
        pytest.param(Any, wildcards.AnythingField, Any, True, id="any_anything"),
    ],
)
def test_wildcard_generation(
    source: Any,
    klass: type[MarshalField],
    type_: TypeHint,
    has_default: bool,
) -> None:
    field = klass.convert(source)

    assert isinstance(field, klass)
    assert field.generate_type() is type_

    if has_default:
        assert dict(field.generate_field_data()) == {"default": None}
    else:
        assert dict(field.generate_field_data()) == {}


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(True, id="bool"),
        pytest.param(1, id="int"),
        pytest.param(1.1, id="float"),
        pytest.param(b"test", id="bytes"),
        pytest.param("test", id="str"),
        pytest.param(SampleEnum.A, id="enum"),
    ],
)
def test_constant_generation(source: LiteralType) -> None:
    field = constants.ConstantField.convert(source)

    assert isinstance(field, constants.ConstantField)
    # noinspection PyTypeHints
    assert field.generate_type() is Literal[source]
    assert dict(field.generate_field_data()) == {}


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(bool, id="bool"),
        pytest.param(int, id="int"),
        pytest.param(float, id="float"),
        pytest.param(bytes, id="bytes"),
        pytest.param(str, id="str"),
        pytest.param(SampleEnum, id="enum"),
    ],
)
@pytest.mark.parametrize("kind", ["normal", "optional", "typing_union", "pipe_union"])
def test_typed_generation(source: TypeHint, kind: str) -> None:
    if kind == "optional":
        source = Optional[source]
    elif kind == "typing_union":
        source = Union[source]
    elif kind == "pipe_union":
        source = source | None

    field = typed.TypedField.convert(source)

    assert isinstance(field, typed.TypedField)
    assert field.generate_type() is source
    assert dict(field.generate_field_data()) == {}


def test_generated_types(dummy_factory: DummyFactory) -> None:
    generator_mock = Mock(BaseTypeGenerator)
    generator_mock.to_typehint = Mock(return_value=dummy_factory("return"))

    field = typed.GeneratedTypeField.convert(generator_mock)

    assert isinstance(field, typed.GeneratedTypeField)
    assert field.generate_type() is dummy_factory("return")
    assert dict(field.generate_field_data()) == {}


@pytest.mark.usefixtures(convert_field_mock_to_sample.__name__)
@pytest.mark.parametrize(
    "length",
    [
        pytest.param(0, id="empty"),
        pytest.param(1, id="single"),
        pytest.param(2, id="double"),
    ],
)
def test_strict_list_generation(
    sample_field: typed.TypedField,
    length: int,
) -> None:
    source: list[type] = [int for _ in range(length)]
    expected: TypeHint = tuple[  # type: ignore[misc]
        *(sample_field.generate_type() for _ in range(length))  # noqa: WPS356
    ]

    field = StrictListField.convert(source)

    assert isinstance(field, StrictListField)
    assert field.generate_type() == expected
    assert dict(field.generate_field_data()) == {}


@pytest.mark.usefixtures(convert_field_mock_to_sample.__name__)
@pytest.mark.parametrize(
    ("source", "fields"),
    [
        pytest.param({}, (), id="empty"),
        pytest.param({"a": int}, ("a",), id="single"),
        pytest.param({"a": 1, "b": 1}, ("a", "b"), id="double"),
    ],
)
def test_nested_generation(
    sample_field: typed.TypedField,
    source: dict[str, Any],
    fields: tuple[str, ...],
) -> None:
    field = NestedField.convert(source)

    assert isinstance(field, NestedField)
    assert dict(field.generate_field_data()) == {}

    field_type: type[BaseModel] = field.generate_type()
    assert is_subtype(field_type, BaseModel)
    assert field_type.__name__ == "Model"

    assert set(field_type.model_fields.keys()) == set(fields)

    expected_field = FieldInfo.from_annotated_attribute(*sample_field.generate_field())
    for field_name in fields:
        value = field_type.model_fields.get(field_name)
        assert isinstance(value, FieldInfo)
        assert repr(value) == repr(expected_field)
