from collections.abc import Iterable, Iterator
from typing import Any, TypeVar
from unittest.mock import Mock, call

import pytest
from pydantic import BaseModel
from sqlalchemy.orm import MappedColumn, Relationship

from pydantic_marshals.base.fields.base import MarshalField
from pydantic_marshals.base.fields.properties import PropertyField
from pydantic_marshals.base.models import MarshalModel
from pydantic_marshals.sqlalchemy.fields.columns import ColumnField
from pydantic_marshals.sqlalchemy.fields.relationships import RelationshipField
from pydantic_marshals.sqlalchemy.models import MappedModel
from tests.unit.conftest import DummyFactory, MockStack


def test_field_types() -> None:
    types = MappedModel.field_types
    assert len(types) == 3
    assert len(set(types)) == 3


class SampleClass:
    @property
    def prop(self) -> int:
        return 3


@pytest.mark.parametrize(
    ("source", "klass"),
    [
        pytest.param(MappedColumn(), ColumnField, id="column"),
        pytest.param((Relationship(), BaseModel), RelationshipField, id="relationship"),
        pytest.param(SampleClass.prop, PropertyField, id="property"),
    ],
)
def test_convert_field(source: Any, klass: type[MarshalField]) -> None:
    field = MappedModel.convert_field(source)
    assert isinstance(field, klass)


T = TypeVar("T")


def _lum(list_generator: Iterator[Iterable[T]]) -> Iterator[T]:
    for items in list_generator:
        yield from (item for item in items)


def lum(list_generator: Iterator[Iterable[T]]) -> list[T]:
    return list(_lum(list_generator))


# haha parametrizations go brrrrr
@pytest.mark.parametrize("column_count", [None, 0, 1, 2])
@pytest.mark.parametrize("relationship_count", [None, 0, 1, 2])
@pytest.mark.parametrize("properties_count", [None, 0, 1, 2])
@pytest.mark.parametrize("bases_count", [None, 0, 1, 2])
@pytest.mark.parametrize("included_count", [None, 0, 1, 2])
def test_creation(
    dummy_factory: DummyFactory,
    mock_stack: MockStack,
    column_count: int | None,
    relationship_count: int | None,
    properties_count: int | None,
    bases_count: int | None,
    included_count: int | None,
) -> None:
    def dummy_list(name: str, count: int) -> list[Any]:
        return [dummy_factory(f"{name}_{i}") for i in range(count)]

    kwargs: dict[str, Any] = {}
    if column_count is not None:
        kwargs["columns"] = dummy_list("column", column_count)
    if relationship_count is not None:
        kwargs["relationships"] = dummy_list("relationship", relationship_count)
    if properties_count is not None:
        kwargs["properties"] = dummy_list("property", properties_count)
    if bases_count is not None:
        kwargs["bases"] = dummy_list("base", bases_count)

    if included_count is not None:
        kwargs["includes"] = [
            MarshalModel(
                dummy_factory(f"field_{i}_0"),
                dummy_factory(f"field_{i}_1"),
                bases=[dummy_factory(f"base_{i}_0"), dummy_factory(f"base_{i}_1")],
            )
            for i in range(included_count)
        ]

    def noop(*args: Any) -> Any:
        return args

    convert_fields_mock = mock_stack.enter_mock(
        MarshalModel, "convert_fields", mock=Mock(side_effect=noop)
    )

    model = MappedModel.create(**kwargs)

    for i, field_dummy in enumerate(
        lum(kwargs.get(key, []) for key in ("columns", "relationships", "properties"))
        + lum(include.fields for include in kwargs.get("includes", ()))
    ):
        assert model.fields[i] is field_dummy

    for i, base_dummy in enumerate(
        kwargs.get("bases", [])
        + lum(include.bases for include in kwargs.get("includes", ())),
    ):
        assert model.bases[i] is base_dummy

    convert_fields_mock.assert_has_calls(
        [
            call(*kwargs.get(key, ()))
            for key in ("columns", "relationships", "properties")
        ]
    )


@pytest.mark.parametrize("included_count", [None, 0, 1, 2])
def test_extends(
    dummy_factory: DummyFactory,
    mock_stack: MockStack,
    included_count: int | None,
) -> None:
    create_mock = mock_stack.enter_mock(
        MappedModel, "create", return_value=dummy_factory("return")
    )

    kwargs = {}
    if included_count is not None:
        kwargs["includes"] = [
            dummy_factory(f"include_{i}") for i in range(included_count)
        ]

    model = MappedModel(bases=[])
    assert model.extend(
        columns=dummy_factory("columns"),
        relationships=dummy_factory("relationships"),
        properties=dummy_factory("properties"),
        bases=dummy_factory("bases"),
        **kwargs,
    ) is dummy_factory("return")

    assert create_mock.call_count == 1
    for key in ("columns", "relationships", "properties", "bases"):
        assert create_mock.mock_calls[0].kwargs.get(key) is dummy_factory(key)
    real_includes = create_mock.mock_calls[0].kwargs.get("includes")
    assert isinstance(real_includes, tuple)
    assert real_includes[0] is model
    for i in range(included_count or 0):
        assert real_includes[i + 1] is dummy_factory(f"include_{i}")
