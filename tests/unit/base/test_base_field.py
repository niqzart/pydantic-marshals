import pytest
from pydantic import RootModel
from pydantic_core import PydanticUndefined

from pydantic_marshals.base.fields.base import (
    MarshalField,
    PatchDefault,
    PatchMarshalField,
)
from tests.unit.conftest import DummyFactory, MockStack


@pytest.mark.parametrize("alias", [None, "something"])
def test_generate_aliased_field(
    alias: str | None, dummy_factory: DummyFactory, mock_stack: MockStack
) -> None:
    expected = {}
    if alias is not None:
        expected["alias"] = alias

    field = MarshalField(alias=alias)
    assert dict(field.generate_field_data()) == expected

    generate_type_mock = mock_stack.enter_mock(
        MarshalField, "generate_type", return_value=dummy_factory("type")
    )
    pydantic_field_mock = mock_stack.enter_mock(
        "pydantic_marshals.base.fields.base.Field", return_value=dummy_factory("field")
    )

    annotation, field_info = field.generate_field()
    assert annotation is dummy_factory("type")
    assert field_info is dummy_factory("field")

    generate_type_mock.assert_called_once_with()
    pydantic_field_mock.assert_called_once_with(**expected)


@pytest.mark.parametrize("patch", [False, True])
def test_generate_patch_field(
    patch: bool, dummy_factory: DummyFactory, mock_stack: MockStack
) -> None:
    expected = {"default": PatchDefault if patch else PydanticUndefined}
    field = PatchMarshalField(patch=patch)
    assert dict(field.generate_field_data()) == expected


def test_generate_root_model(
    mock_stack: MockStack,
    dummy_factory: DummyFactory,
) -> None:
    root_model_mock = mock_stack.enter_mock(
        RootModel, "__class_getitem__", return_value=dummy_factory("return")
    )
    generate_type_mock = mock_stack.enter_mock(
        MarshalField, "generate_type", return_value=dummy_factory("type")
    )

    field = MarshalField()
    assert field.generate_root_model() is dummy_factory("return")

    generate_type_mock.assert_called_once_with()
    root_model_mock.assert_called_once_with(dummy_factory("type"))
