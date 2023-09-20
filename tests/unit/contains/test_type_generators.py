from contextlib import nullcontext
from typing import Annotated, get_args, get_origin
from unittest.mock import Mock, patch

import pytest
from pydantic import AfterValidator

from pydantic_marshals.contains.type_generators.base import BaseTypeGenerator
from pydantic_marshals.contains.type_generators.collections import (
    UnorderedLiteralCollection,
)
from tests.unit.conftest import DummyFactory


def test_typehint_generation(dummy_factory: DummyFactory) -> None:
    generator = BaseTypeGenerator(data_type=Mock())
    generator.validate = dummy_factory("validate")  # type: ignore[method-assign]

    type_hint = generator.to_typehint()
    assert get_origin(type_hint) is Annotated
    type_hint_args = get_args(type_hint)
    assert len(type_hint_args) == 2
    assert type_hint_args[0] is generator.data_type
    assert isinstance(type_hint_args[1], AfterValidator)
    assert type_hint_args[1].func is generator.validate


def test_validation(dummy_factory: DummyFactory) -> None:
    generator = BaseTypeGenerator(data_type=dummy_factory("data_type"))

    with patch.object(generator, "_validate") as validate_mock:
        assert generator.validate(dummy_factory("data")) is dummy_factory("data")
        validate_mock.assert_called_once_with(dummy_factory("data"))


@pytest.mark.parametrize(
    "check_extra",
    [True, False],
    ids=("check_extra", "allow_extra"),
)
@pytest.mark.parametrize(
    ("extras_count", "extras_error"),
    [
        pytest.param(0, False, id="no_extras"),
        pytest.param(1, True, id="one_extra"),
        pytest.param(2, True, id="two_extras"),
    ],
)
@pytest.mark.parametrize(
    "check_repeats",
    [True, False],
    ids=("check_repeats", "allow_repeats"),
)
@pytest.mark.parametrize(
    ("repeats_count", "repeats_error"),
    [
        pytest.param(0, False, id="no_repetition"),
        pytest.param(0.5, True, id="partial_repetition"),
        pytest.param(1, True, id="one_repeated_set"),
        pytest.param(2, True, id="two_repeated_sets"),
    ],
)
@pytest.mark.parametrize(
    ("data_count", "supply_count", "supply_error", "allow_repeat_from"),
    [
        pytest.param(0, 0, False, 2, id="required_none-supplied_none"),
        pytest.param(1, 0, True, 2, id="required_one-supplied_none"),
        pytest.param(1, 1, False, 0.5, id="required_one-supplied_one"),
        pytest.param(2, 0, True, 2, id="required_two-supplied_none"),
        pytest.param(2, 1, True, 0.5, id="required_two-supplied_one"),
        pytest.param(2, 2, False, 0, id="required_two-supplied_two"),
    ],
)
def test_unordered_literal_collection(
    dummy_factory: DummyFactory,
    #
    data_count: int,
    allow_repeat_from: int,  # how many repeats are required for a repetition error
    supply_count: int,
    supply_error: bool,
    #
    check_extra: bool,
    extras_count: int,
    extras_error: bool,
    #
    check_repeats: bool,
    repeats_count: float,
    repeats_error: bool,
) -> None:
    extras_error = check_extra and extras_error
    allow_repeat_error = repeats_count > allow_repeat_from
    repeats_error = allow_repeat_error and check_repeats and repeats_error
    error: bool = supply_error or repeats_error or extras_error

    extra_items = [dummy_factory(f"extra_{i}") for i in range(extras_count)]
    required_items = [dummy_factory(f"required_{i}") for i in range(data_count)]
    supplied_items = [required_items[i] for i in range(supply_count)]
    repeated_items = [
        supplied_items[i % supply_count]
        for i in range(int(supply_count * repeats_count))
    ]
    missing_items = [item for item in required_items if item not in supplied_items]
    data = supplied_items + repeated_items + extra_items

    collection = UnorderedLiteralCollection(
        items=required_items,
        check_extra=check_extra,
        check_repeats=check_repeats,
    )
    with pytest.raises(ValueError) if error else nullcontext() as exc:
        collection._validate(data)

    if error:
        assert exc is not None
        assert exc.type is ValueError
        assert len(exc.value.args) == 1

        error_message = exc.value.args[0]
        assert isinstance(error_message, str)

        if supply_error:
            assert error_message.startswith("items missing: ")
            expected_items = missing_items
        elif extras_error:
            assert error_message.startswith("extra items found: ")
            expected_items = extra_items
        elif repeats_error:
            assert error_message.startswith("repeating items found: ")
            expected_items = repeated_items

        real_items = set(error_message.partition(": ")[2].strip("{}").split(", "))
        assert real_items == {f"{item}" for item in expected_items}
