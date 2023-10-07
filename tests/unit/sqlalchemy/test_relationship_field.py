from typing import Any, get_args, get_origin
from unittest.mock import Mock

import pytest
from pydantic import BaseModel
from pydantic_core import PydanticUndefined
from sqlalchemy.orm import Relationship

from pydantic_marshals.base.fields.base import PatchDefault
from pydantic_marshals.sqlalchemy.fields.relationships import RelationshipField
from tests.unit.conftest import DummyFactory


def test_conversion() -> None:
    relationship_dummy: Relationship[Any] = Relationship()
    model_dummy = BaseModel

    column_field = RelationshipField.convert(relationship_dummy, model_dummy)
    assert isinstance(column_field, RelationshipField)
    assert column_field.relationship is relationship_dummy
    assert column_field.model is model_dummy


@pytest.mark.parametrize(
    "source",
    [
        pytest.param((int,), id="single_random_argument"),
        pytest.param((int, int), id="double_random_argument"),
        pytest.param((Relationship(),), id="only_relationship"),
        pytest.param((int, BaseModel), id="only_model"),
    ],
)
def test_conversion_fails(source: tuple[Any] | tuple[Any, Any]) -> None:
    assert RelationshipField.convert(*source) is None


@pytest.fixture()
def mapped_relationship_mock() -> Mock:
    return Mock()


@pytest.fixture()
def relationship_field(
    dummy_factory: DummyFactory,
    mapped_relationship_mock: Mock,
) -> RelationshipField:
    return RelationshipField(mapped_relationship_mock, dummy_factory("model"))


def test_name_generation(
    dummy_factory: DummyFactory,
    relationship_field: RelationshipField,
    mapped_relationship_mock: Mock,
) -> None:
    mapped_relationship_mock.key = dummy_factory("return")
    assert relationship_field.generate_name() is dummy_factory("return")


def test_type_generation(
    dummy_factory: DummyFactory,
    relationship_field: RelationshipField,
    mapped_relationship_mock: Mock,
) -> None:
    mapped_relationship_mock.collection_class = None
    assert relationship_field.generate_type() is dummy_factory("model")


def test_type_generation_list(
    dummy_factory: DummyFactory,
    relationship_field: RelationshipField,
    mapped_relationship_mock: Mock,
) -> None:
    mapped_relationship_mock.collection_class = list

    real = relationship_field.generate_type()
    assert get_origin(real) is list
    assert len(get_args(real)) == 1
    assert get_args(real)[0] is dummy_factory("model")


@pytest.mark.parametrize(
    ("collection_type", "error_message"),
    [
        pytest.param(3, "Collection is not a type: 3", id="not_a_type"),
        pytest.param(dict, "Bad collection class: <class 'dict'>", id="bad_class"),
    ],
)
def test_type_generation_collection_error(
    dummy_factory: DummyFactory,
    relationship_field: RelationshipField,
    mapped_relationship_mock: Mock,
    collection_type: Any,
    error_message: str,
) -> None:
    mapped_relationship_mock.collection_class = collection_type

    with pytest.raises(RuntimeError) as exc:
        relationship_field.generate_type()

    assert len(exc.value.args) == 1
    assert exc.value.args[0] == error_message


@pytest.mark.parametrize("as_patch", [False, True])
def test_field_data_generation(
    relationship_field: RelationshipField, as_patch: bool
) -> None:
    expected = {"default": PatchDefault if as_patch else PydanticUndefined}
    if as_patch:
        relationship_field = relationship_field.as_patch()
    assert dict(relationship_field.generate_field_data()) == expected
