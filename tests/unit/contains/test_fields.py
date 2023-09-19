from collections.abc import Iterator
from typing import Any, Literal
from unittest.mock import Mock, patch

import pytest
from pydantic import BaseModel
from pydantic.fields import FieldInfo

from pydantic_marshals.base.fields.base import MarshalField
from pydantic_marshals.base.type_aliases import TypeHint
from pydantic_marshals.contains.fields import constants, typed, wildcards
from pydantic_marshals.contains.models import AssertContainsModel
from pydantic_marshals.contains.type_aliases import LiteralType
from pydantic_marshals.utils import is_subtype
from tests.unit.conftest import SampleEnum


@pytest.fixture()
def sample_field() -> typed.TypedField:
    return typed.TypedField(int)


@pytest.fixture()
def convert_field_mock_to_sample(sample_field: typed.TypedField) -> Iterator[Mock]:
    with patch.object(AssertContainsModel, "convert_field") as mock:
        mock.return_value = sample_field
        yield mock


NestedField = AssertContainsModel.field_types[5]  # type: ignore[misc]
StrictListField = AssertContainsModel.field_types[6]  # type: ignore[misc]

SOURCE_TO_KLASS: list[Any] = [
    pytest.param(None, wildcards.NothingField, id="none-nothing"),
    pytest.param(..., wildcards.SomethingField, id="...-something"),
    pytest.param(Any, wildcards.AnythingField, id="any-anything"),
    #
    pytest.param(True, constants.ConstantField, id="bool-constant"),
    pytest.param(1, constants.ConstantField, id="int-constant"),
    pytest.param(1.1, constants.ConstantField, id="float-constant"),
    pytest.param(b"test", constants.ConstantField, id="bytes-constant"),
    pytest.param("test", constants.ConstantField, id="str-constant"),
    pytest.param(SampleEnum.A, constants.ConstantField, id="enum-constant"),
    #
    pytest.param(bool, typed.TypedField, id="bool-typed"),
    pytest.param(int, typed.TypedField, id="int-typed"),
    pytest.param(float, typed.TypedField, id="float-typed"),
    pytest.param(bytes, typed.TypedField, id="bytes-typed"),
    pytest.param(str, typed.TypedField, id="str-typed"),
    pytest.param(SampleEnum, typed.TypedField, id="enum-typed"),
    #
    pytest.param([], StrictListField, id="empty-list"),
    pytest.param([1], StrictListField, id="single-list"),
    pytest.param([1, int], StrictListField, id="double-list"),
    #
    pytest.param({}, NestedField, id="empty-nested"),
    pytest.param({"a": 1}, NestedField, id="single-nested"),
    pytest.param({"a": 1, "b": int}, NestedField, id="double-nested"),
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
        pytest.param(None, wildcards.NothingField, type(None), True, id="none-nothing"),
        pytest.param(..., wildcards.SomethingField, Any, False, id="...-something"),
        pytest.param(Any, wildcards.AnythingField, Any, True, id="any-anything"),
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
def test_typed_generation(source: type) -> None:
    field = typed.TypedField.convert(source)

    assert isinstance(field, typed.TypedField)
    assert field.generate_type() is source
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
