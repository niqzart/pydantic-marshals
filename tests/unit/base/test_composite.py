from typing import Annotated, Any
from unittest.mock import Mock

import pytest
from pydantic import create_model
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from pydantic_marshals.base import composite
from pydantic_marshals.base.models import MarshalBaseModel
from tests.unit.conftest import DummyFactory, MockStack


@pytest.fixture()
def composite_marshal_model_name() -> str:
    return "T"


@pytest.fixture()
def composite_marshal_model(
    composite_marshal_model_name: str,
) -> type[composite.CompositeMarshalModel]:
    return create_model(
        composite_marshal_model_name,
        __base__=composite.CompositeMarshalModel,
    )


def test_composite_model_config(
    composite_marshal_model: type[composite.CompositeMarshalModel],
) -> None:
    assert composite_marshal_model.model_config.get("from_attributes") is True


def test_generate_marshal_model_name(
    composite_marshal_model_name: str,
    composite_marshal_model: type[composite.CompositeMarshalModel],
) -> None:
    real_marshal_model_name = composite_marshal_model.generate_marshal_model_name()
    assert real_marshal_model_name == f"{composite_marshal_model_name}Marshal"


def test_convert_field_ignored(
    dummy_factory: DummyFactory,
    mock_stack: MockStack,
    composite_marshal_model: type[composite.CompositeMarshalModel],
) -> None:
    field_info_mock = Mock(FieldInfo)
    field_info_mock.metadata = []
    field_info_mock.annotation = dummy_factory("annotation")

    converted_field = composite_marshal_model.convert_field(field_info_mock)

    assert isinstance(converted_field, tuple)
    assert len(converted_field) == 2

    assert converted_field[0] is dummy_factory("annotation")
    assert converted_field[1] is field_info_mock


some_marshal_model = create_model("T", __base__=MarshalBaseModel)


@pytest.mark.parametrize(
    (
        "initial_annotation",
        "expected_annotation",
        "default",
    ),
    [
        pytest.param(
            Annotated[int, some_marshal_model],
            some_marshal_model,
            PydanticUndefined,
            id="required",
        ),
        pytest.param(
            Annotated[int | None, some_marshal_model],
            some_marshal_model | None,
            PydanticUndefined,
            id="required_union",
        ),
        pytest.param(
            Annotated[int | None, some_marshal_model],
            some_marshal_model | None,
            None,
            id="optional",
        ),
        pytest.param(
            Annotated[list[int], some_marshal_model],
            list[some_marshal_model],  # type: ignore[valid-type]
            PydanticUndefined,
            id="list",
        ),
        pytest.param(
            Annotated[list[int], some_marshal_model],
            list[some_marshal_model],  # type: ignore[valid-type]
            [],
            id="list_with_default",
        ),
    ],
)
def test_convert_field_unpacked(
    mock_stack: MockStack,
    composite_marshal_model: type[composite.CompositeMarshalModel],
    initial_annotation: Any,
    expected_annotation: Any,
    default: Any,
) -> None:
    some_field_info = FieldInfo.from_annotated_attribute(initial_annotation, default)

    converted_field = composite_marshal_model.convert_field(some_field_info)

    assert isinstance(converted_field, tuple)
    assert len(converted_field) == 2

    assert converted_field[0] == expected_annotation
    assert converted_field[1] is default


def test_build_marshal(
    dummy_factory: DummyFactory,
    mock_stack: MockStack,
    composite_marshal_model: type[composite.CompositeMarshalModel],
) -> None:
    model_fields_mock = mock_stack.enter_mock(
        composite_marshal_model,
        "model_fields",
        property_value={"field_name": dummy_factory("initial_field")},
    )
    generate_marshal_model_name_mock = mock_stack.enter_mock(
        composite_marshal_model,
        "generate_marshal_model_name",
        return_value=dummy_factory("name"),
    )
    convert_field_mock = mock_stack.enter_mock(
        composite_marshal_model,
        "convert_field",
        return_value=dummy_factory("converted_field"),
    )

    create_model_mock = mock_stack.enter_mock(
        composite, "create_model", return_value=dummy_factory("return")
    )

    assert composite_marshal_model.build_marshal() is dummy_factory("return")

    create_model_mock.assert_called_once_with(
        dummy_factory("name"),
        field_name=dummy_factory("converted_field"),
    )

    convert_field_mock.assert_called_once_with(dummy_factory("initial_field"))

    generate_marshal_model_name_mock.assert_called_once_with()
    model_fields_mock.assert_called_once_with()
