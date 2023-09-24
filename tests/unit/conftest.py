from collections.abc import Iterator
from contextlib import ExitStack
from enum import Enum
from typing import Any, Protocol, overload
from unittest.mock import Mock, patch

import pytest

DummyObject = Any
DummyException = BaseException


class SampleEnum(Enum):
    A = 1


class DummyFactory(Protocol):
    def __call__(self, item: Any) -> DummyObject:
        pass


@pytest.fixture(scope="session")
def dummy_factory() -> DummyFactory:  # TODO sentinel
    dummies: dict[Any, DummyObject] = {}

    def dummy_factory_inner(item: Any) -> DummyObject:
        return dummies.setdefault(item, object())

    return dummy_factory_inner


@pytest.fixture(scope="session")
def dummy_exception() -> DummyException:
    return BaseException()


@pytest.fixture()
def function_mock_to_dummy(dummy_factory: DummyFactory) -> Mock:
    return Mock(return_value=dummy_factory("return"))


class MockStack(ExitStack):
    @overload
    def enter_mock(
        self,
        target: Any,
        attribute: str,
        /,
        *,
        mock: Mock | None = None,
        return_value: Any | None = None,
    ) -> Mock:
        ...

    @overload
    def enter_mock(
        self,
        target: str,
        /,
        *,
        mock: Mock | None = None,
        return_value: Any | None = None,
    ) -> Mock:
        ...

    def enter_mock(
        self,
        target: Any,
        attribute: str | None = None,
        mock: Mock | None = None,
        return_value: Any | None = None,
    ) -> Mock:
        if mock is None:
            mock = Mock(return_value=return_value)
        if attribute is None:
            return self.enter_context(patch(target, mock))
        return self.enter_context(patch.object(target, attribute, mock))

    @overload
    def enter_patch(self, target: Any, attribute: str, /) -> Mock:
        ...

    @overload
    def enter_patch(self, target: str, /) -> Mock:
        ...

    def enter_patch(self, target: Any, attribute: str | None = None) -> Mock:
        if attribute is None:
            return self.enter_context(patch(target))
        return self.enter_context(patch.object(target, attribute))


@pytest.fixture()
def mock_stack() -> Iterator[MockStack]:
    with MockStack() as stack:
        yield stack
