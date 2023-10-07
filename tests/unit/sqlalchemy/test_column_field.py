from typing import Any
from unittest.mock import Mock, PropertyMock

import pytest
from pydantic_core import PydanticUndefined
from sqlalchemy import Enum, Integer, String
from sqlalchemy.orm import MappedColumn
from sqlalchemy.sql.schema import ScalarElementColumnDefault
from sqlalchemy.sql.type_api import TypeEngine

from pydantic_marshals.base.fields.base import PatchDefault
from pydantic_marshals.sqlalchemy.fields.columns import ColumnField
from tests.unit.conftest import DummyFactory, MockStack, SampleEnum


@pytest.fixture()
def mapped_column_dummy() -> MappedColumn[Any]:
    return MappedColumn()


def test_conversion(mapped_column_dummy: MappedColumn[Any]) -> None:
    column_field = ColumnField.convert(mapped_column_dummy)
    assert isinstance(column_field, ColumnField)
    assert column_field.mapped is mapped_column_dummy


def test_conversion_fails() -> None:
    assert ColumnField.convert(int) is None


@pytest.fixture()
def column_field(mapped_column_dummy: MappedColumn[Any]) -> ColumnField:
    return ColumnField(mapped_column_dummy)


def test_before_column_initiation(
    dummy_factory: DummyFactory,
    mock_stack: MockStack,
    column_field: ColumnField,
) -> None:
    assert column_field.generate_name() is None
    with pytest.raises(NotImplementedError):
        column_field.generate_type()
    assert column_field.generate_default() is None
    assert dict(column_field.generate_field_data()) == {"default": None}


def test_column(
    dummy_factory: DummyFactory,
    mock_stack: MockStack,
    mapped_column_dummy: MappedColumn[Any],
    column_field: ColumnField,
) -> None:
    column_mock = mock_stack.enter_mock(
        mapped_column_dummy, "column", property_value=dummy_factory("column")
    )
    assert column_field.column is column_mock


@pytest.fixture()
def column_mock(mock_stack: MockStack, mapped_column_dummy: MappedColumn[Any]) -> Mock:
    return mock_stack.enter_patch(mapped_column_dummy, "column")


def test_name_generation(
    dummy_factory: DummyFactory,
    column_field: ColumnField,
    column_mock: Mock,
) -> None:
    column_mock.name = dummy_factory("return")
    assert column_field.generate_name() is dummy_factory("return")


@pytest.mark.parametrize("nullable", [False, True], ids=["required", "nullable"])
def test_type_generation(
    dummy_factory: DummyFactory,
    column_field: ColumnField,
    column_mock: Mock,
    nullable: bool,
) -> None:
    column_mock.nullable = nullable
    column_mock.type = PropertyMock()

    if nullable:
        column_mock.type.python_type = PropertyMock()
        column_mock.type.python_type.__or__ = Mock(return_value=dummy_factory("return"))
    else:
        column_mock.type.python_type = dummy_factory("return")

    assert column_field.generate_type() is dummy_factory("return")


@pytest.mark.parametrize(
    ("nullable", "expected"),
    [
        pytest.param(False, PydanticUndefined, id="required"),
        pytest.param(True, None, id="nullable"),
    ],
)
def test_no_default_generation(
    column_field: ColumnField,
    column_mock: Mock,
    nullable: bool,
    expected: Any,
) -> None:
    column_mock.nullable = nullable
    column_mock.default = None
    assert column_field.generate_default() is expected


@pytest.mark.parametrize("nullable", [False, True], ids=["required", "nullable"])
def test_default_generation(
    dummy_factory: DummyFactory,
    column_field: ColumnField,
    column_mock: Mock,
    nullable: bool,
) -> None:
    column_mock.nullable = nullable
    column_mock.default = ScalarElementColumnDefault(dummy_factory("return"))
    assert column_field.generate_default() is dummy_factory("return")


@pytest.mark.parametrize("nullable", [False, True], ids=["required", "nullable"])
def test_default_generation_warning(
    dummy_factory: DummyFactory,
    column_field: ColumnField,
    column_mock: Mock,
    nullable: bool,
) -> None:
    column_mock.nullable = nullable
    column_mock.default = dummy_factory("return")

    with pytest.warns() as exc:
        assert column_field.generate_default() is PydanticUndefined

    assert len(exc.list) == 1
    assert isinstance(exc.list[0].message, UserWarning)
    assert len(exc.list[0].message.args) == 1
    assert (
        exc.list[0].message.args[0]
        == f"Default: {dummy_factory('return')} is not supported, skipping"
    )


@pytest.mark.parametrize(
    ("type_", "max_length"),
    [
        pytest.param(Integer, None, id="integer"),
        pytest.param(String(100), 100, id="string_100"),
        pytest.param(Enum(SampleEnum), None, id="enum"),
    ],
)
def test_generate_field_data(
    dummy_factory: DummyFactory,
    mock_stack: MockStack,
    column_field: ColumnField,
    column_mock: Mock,
    type_: TypeEngine[Any],
    max_length: int | None,
) -> None:
    expected: dict[str, Any] = {"default": dummy_factory("default")}
    if max_length is not None:
        expected["max_length"] = max_length

    column_mock.type = type_
    generate_default_mock = mock_stack.enter_mock(
        column_field, "generate_default", return_value=dummy_factory("default")
    )

    assert dict(column_field.generate_field_data()) == expected
    generate_default_mock.assert_called_once_with()

    generate_default_mock.reset_mock()
    assert dict(column_field.as_patch().generate_field_data()) == {
        **expected,
        "default": PatchDefault,
    }
    generate_default_mock.assert_not_called()
