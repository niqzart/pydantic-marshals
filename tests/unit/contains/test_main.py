from collections.abc import Iterator
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from pydantic_marshals.contains.models import AssertContainsModel, assert_contains
from tests.unit.conftest import DummyFactory, MockStack


@pytest.fixture()
def contains_mock(dummy_factory: DummyFactory, mock_stack: MockStack) -> Iterator[Mock]:
    contains_mock = mock_stack.enter_mock(AssertContainsModel, "contains")
    yield contains_mock
    contains_mock.assert_called_once_with(
        dummy_factory("real"),
        dummy_factory("expected"),
    )


def test_assert_contains_success(
    dummy_factory: DummyFactory,
    contains_mock: Mock,
) -> None:
    assert_contains(dummy_factory("real"), dummy_factory("expected"))


def test_assert_contains_exception(
    dummy_factory: DummyFactory,
    contains_mock: Mock,
    mock_stack: MockStack,
) -> None:
    validation_error = ValidationError.from_exception_data("", [])
    contains_mock.side_effect = validation_error

    str_mock = mock_stack.enter_mock(
        "pydantic_marshals.contains.models.str", return_value=dummy_factory("return")
    )

    with pytest.raises(AssertionError) as exc:
        assert_contains(dummy_factory("real"), dummy_factory("expected"))
    str_mock.assert_called_once_with(validation_error)

    assert isinstance(exc.value, AssertionError)
    assert len(exc.value.args) == 1
    assert exc.value.args[0] is dummy_factory("return")
