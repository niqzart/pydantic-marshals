from collections.abc import Iterator
from typing import Any
from unittest.mock import Mock, patch

import pytest
from pydantic import RootModel

from pydantic_marshals.base.fields.base import MarshalField
from pydantic_marshals.contains.models import AssertContainsModel
from tests.unit.conftest import DummyException, DummyFactory
from tests.unit.contains.test_fields import SOURCE_TO_KLASS


def test_field_types() -> None:
    types = AssertContainsModel.field_types
    assert len(types) == 7
    assert len(set(types)) == 7


@pytest.mark.parametrize(("source", "klass"), SOURCE_TO_KLASS)
def test_convert_field(source: Any, klass: type[MarshalField]) -> None:
    field = AssertContainsModel.convert_field(source)
    assert isinstance(field, klass)


@pytest.fixture()
def field_mock() -> Mock:
    return Mock(spec=MarshalField)


@pytest.fixture()
def convert_field_mock_to_mock(field_mock: Mock) -> Iterator[Mock]:
    with patch.object(AssertContainsModel, "convert_field") as mock:
        mock.return_value = field_mock
        yield mock


@pytest.mark.parametrize("method", ["type", "field"])
def test_conversions(
    dummy_factory: DummyFactory,
    function_mock_to_dummy: Mock,
    convert_field_mock_to_mock: Mock,
    field_mock: Mock,
    method: str,
) -> None:
    setattr(field_mock, f"generate_{method}", function_mock_to_dummy)

    real = getattr(AssertContainsModel, f"convert_to_{method}")(dummy_factory("source"))

    assert real is function_mock_to_dummy.return_value
    convert_field_mock_to_mock.assert_called_once_with(dummy_factory("source"))
    function_mock_to_dummy.assert_called_once_with()


@pytest.fixture()
def model_contains_mock(
    dummy_factory: DummyFactory,
    convert_field_mock_to_mock: Mock,
    field_mock: Mock,
) -> Iterator[Mock]:
    root_model_mock = Mock(spec=RootModel)
    root_model_mock.model_validate = Mock()
    field_mock.generate_root_model = Mock(return_value=root_model_mock)

    yield root_model_mock.model_validate

    convert_field_mock_to_mock.assert_called_once_with(dummy_factory("expected"))
    field_mock.generate_root_model.assert_called_once_with()
    root_model_mock.model_validate.assert_called_once_with(dummy_factory("real"))


@pytest.mark.usefixtures(model_contains_mock.__name__)
def test_contains_success(dummy_factory: DummyFactory) -> None:
    AssertContainsModel.contains(dummy_factory("real"), dummy_factory("expected"))


def test_contains_exception(
    dummy_exception: DummyException,
    model_contains_mock: Mock,
    dummy_factory: DummyFactory,
) -> None:
    model_contains_mock.side_effect = dummy_exception
    with pytest.raises(type(dummy_exception)) as exc:
        AssertContainsModel.contains(dummy_factory("real"), dummy_factory("expected"))
    assert exc.value is dummy_exception
