from typing import Any
from unittest.mock import Mock

import pytest
from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from pydantic_marshals.base.fields import properties
from pydantic_marshals.base.fields.base import PatchDefault
from tests.unit.conftest import DummyFactory, MockStack


@pytest.fixture()
def mapped_property_mock() -> Mock:
    return Mock()


@pytest.fixture()
def mapped_property_fget_mock(
    dummy_factory: DummyFactory,
    mapped_property_mock: Mock,
) -> Mock:
    mapped_property_mock.fget = Mock()
    mapped_property_mock.fget.__name__ = dummy_factory("getter_name")
    return mapped_property_mock.fget


def test_property_field(
    dummy_factory: DummyFactory,
    mock_stack: MockStack,
    mapped_property_mock: Mock,
    mapped_property_fget_mock: Mock,
) -> None:
    type_hints_mock = Mock()
    type_hints_mock.get = Mock(return_value=dummy_factory("return_annotation"))
    get_type_hints_mock = mock_stack.enter_mock(
        properties, "get_type_hints", return_value=type_hints_mock
    )

    field = properties.PropertyField(mapped_property_mock)
    assert field.generate_name() is dummy_factory("getter_name")
    assert field.generate_type() is dummy_factory("return_annotation")

    get_type_hints_mock.assert_called_once_with(mapped_property_fget_mock)
    type_hints_mock.get.assert_called_once_with("return", Any)


def test_property_field_fget_is_none(
    dummy_factory: DummyFactory,
    mock_stack: MockStack,
    mapped_property_mock: Mock,
) -> None:
    mapped_property_mock.fget = None

    with pytest.raises(RuntimeError) as exc:
        properties.PropertyField(mapped_property_mock)

    assert len(exc.value.args) == 1
    assert exc.value.args[0] == "Property's fget is None somehow"


@pytest.mark.parametrize(
    "type_override",
    [
        pytest.param(None, id="no_override"),
        pytest.param(int, id="some_override"),
    ],
)
def test_property_field_conversion(
    dummy_factory: DummyFactory,
    type_override: Any,
) -> None:
    class T:
        @property
        def prop(
            self,
        ) -> dummy_factory("property_type"):  # type: ignore[valid-type]  # noqa: F821
            raise NotImplementedError

    field = properties.PropertyField.convert(T.prop, type_override)

    assert isinstance(field, properties.PropertyField)
    assert field.generate_type() is (type_override or dummy_factory("property_type"))
    assert field.generate_name() == "prop"
    assert dict(field.generate_field_data()) == {"default": PydanticUndefined}
    assert dict(field.as_patch().generate_field_data()) == {"default": PatchDefault}


@pytest.mark.skip("isinstance doesn't support parametrized generics")
@pytest.mark.parametrize(
    "source",
    [
        pytest.param(property(), id="property"),
        pytest.param(lambda x: x, id="callable"),
    ],
)
@pytest.mark.parametrize("modeled", [False, True], ids=["raw", "modeled"])
def test_property_type_checks(source: Any, modeled: bool) -> None:
    if modeled:
        source = (source, BaseModel)
    assert isinstance(source, properties.PropertyType)  # type: ignore[arg-type]
