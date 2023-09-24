# mypy: disable-error-code="method-assign"

from typing import Any
from unittest.mock import Mock, PropertyMock

import pytest
from pydantic import create_model

from pydantic_marshals.base import models
from pydantic_marshals.base.fields.base import MarshalField
from pydantic_marshals.contains.models import assert_contains
from tests.unit.conftest import DummyFactory, MockStack


def test_base_model_class() -> None:
    pydantic_model = create_model("T", __base__=models.MarshalModel.model_base_class)
    assert_contains(
        pydantic_model.model_config,
        {
            "from_attributes": True,
            "populate_by_name": True,
        },
    )


@pytest.mark.parametrize("base_count", [0, 1, 2])
def test_generate_base(dummy_factory: DummyFactory, base_count: int) -> None:
    model = models.MarshalModel(bases=[dummy_factory(i) for i in range(base_count)])

    real_bases = model.generate_base()
    assert isinstance(real_bases, tuple)
    assert len(real_bases) == base_count + 1
    assert real_bases[0] is models.MarshalBaseModel
    for i in range(base_count):
        assert real_bases[i + 1] is dummy_factory(i)


def test_generated_model_caching(
    dummy_factory: DummyFactory,
    mock_stack: MockStack,
) -> None:
    model = models.MarshalModel(bases=[])
    generate_model_mock = mock_stack.enter_mock(
        model, "generate_model", return_value=dummy_factory("return")
    )

    assert model._generated_model is None
    assert model.generated_model is dummy_factory("return")

    assert model._generated_model is dummy_factory("return")
    assert model.generated_model is dummy_factory("return")

    generate_model_mock.assert_called_once_with()


@pytest.fixture()
def simple_model() -> models.MarshalModel:
    return models.MarshalModel(bases=[])


@pytest.fixture()
def classed_model(simple_model: models.MarshalModel) -> Any:
    class M:
        model = simple_model

    return M


def test_model_naming(classed_model: Any) -> None:
    assert classed_model.model.__name__ == "classed_model.<locals>.M.model"


def test_descriptor(
    dummy_factory: DummyFactory,
    mock_stack: MockStack,
    simple_model: models.MarshalModel,
    classed_model: Any,
) -> None:
    generate_model_mock = mock_stack.enter_mock(
        simple_model,
        "generate_model",
        mock=PropertyMock(return_value=dummy_factory("return")),
    )

    assert classed_model.model is dummy_factory("return")

    generate_model_mock.assert_called_once_with()


def test_model_generation(
    dummy_factory: DummyFactory,
    mock_stack: MockStack,
    simple_model: models.MarshalModel,
) -> None:
    field_mock = Mock(MarshalField)
    field_mock.generate_name.return_value = "field_name"
    field_mock.generate_field.return_value = dummy_factory("field_field")

    simple_model.model_name = dummy_factory("name")
    simple_model.generate_base = Mock(return_value=dummy_factory("base"))
    simple_model.fields = [field_mock]

    create_model_mock = mock_stack.enter_mock(
        models, "create_model", return_value=dummy_factory("return")
    )

    assert simple_model.generate_model() is dummy_factory("return")

    create_model_mock.assert_called_once_with(
        dummy_factory("name"),
        __base__=dummy_factory("base"),
        field_name=dummy_factory("field_field"),
    )
