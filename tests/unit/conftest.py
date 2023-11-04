from collections.abc import Iterator
from contextlib import ExitStack
from datetime import datetime
from enum import Enum
from typing import Any, Protocol, overload
from unittest.mock import Mock, PropertyMock, patch

import pytest
from pydantic_core import PydanticUndefined, PydanticUndefinedType

DummyException = BaseException


class SampleEnum(Enum):
    A = 1
    B = 2


sample_datetime = datetime.utcnow()
sample_date = sample_datetime.date()
sample_time = sample_datetime.time()


class DummyObject:
    def __init__(self, item: Any) -> None:
        self.item = item

    def __repr__(self) -> str:
        return f"DummyObject from {self.item!r}"

    def __str__(self) -> str:
        return repr(self)


class DummyFactory(Protocol):
    def __call__(self, item: Any) -> Any:
        pass


@pytest.fixture(scope="session")
def dummy_factory() -> DummyFactory:  # TODO sentinel
    dummies: dict[Any, DummyObject] = {}

    def dummy_factory_inner(item: Any) -> Any:
        return dummies.setdefault(item, DummyObject(item))

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
        property_value: Any | None | PydanticUndefinedType = PydanticUndefined,
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
        property_value: Any | None | PydanticUndefinedType = PydanticUndefined,
    ) -> Mock:
        ...

    def enter_mock(
        self,
        target: Any,
        attribute: str | None = None,
        mock: Mock | None = None,
        return_value: Any | None = None,
        property_value: Any | None | PydanticUndefinedType = PydanticUndefined,
    ) -> Mock:
        if mock is None:
            if property_value is PydanticUndefined:
                mock = Mock(return_value=return_value)
            else:
                mock = PropertyMock(return_value=property_value)
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
