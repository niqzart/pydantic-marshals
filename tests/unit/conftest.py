from enum import Enum
from typing import Any, Protocol
from unittest.mock import Mock

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
