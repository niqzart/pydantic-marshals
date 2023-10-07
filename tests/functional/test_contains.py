from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Annotated, Any, Optional, Union

import pytest
from pydantic import ValidationError, conlist

from pydantic_marshals.contains import (
    AssertContainsModel,
    TypeChecker,
    UnorderedLiteralCollection,
    assert_contains,
)
from pydantic_marshals.contains.type_aliases import LiteralType
from tests.unit.conftest import SampleEnum


class LiteralValue(Enum):
    NONE = None
    TRUE = True
    FALSE = False
    INT = 2
    FLOAT = 1.1
    BYTES = b"test"
    STR = "test"
    ENUM = SampleEnum.A

    @classmethod
    def number_values(cls) -> set[LiteralValue]:
        return {cls.TRUE, cls.FALSE, cls.INT, cls.FLOAT}

    @classmethod
    def string_values(cls) -> set[LiteralValue]:
        return {cls.STR, cls.BYTES}

    @property
    def slug(self) -> str:
        return self.name.lower()


@pytest.mark.parametrize(
    "common_modifier",
    [
        pytest.param(lambda x: x, id="no_modifier"),
        pytest.param(lambda x: {"a": x}, id="dict_modifier"),
        pytest.param(lambda x: [x], id="list_modifier"),
        # TODO sets?
    ],
)
@pytest.mark.parametrize(
    ("type_checker", "literal_value"),
    [
        pytest.param(type_checker, literal, id=f"{converter_slug}-{literal.slug}")
        for literal in LiteralValue
        for type_checker, converter_slug in (
            (Any, "any"),
            (..., "..."),
            (literal.value, f"literal_{literal.slug}"),
            (type(literal.value), f"type_{literal.slug}"),
            (Union[type(literal.value)], f"typing_union_{literal.slug}"),  # noqa: NU001
            (Optional[type(literal.value)], f"optional_{literal.slug}"),  # noqa: NU002
            (type(literal.value) | None, f"pipe_union_{literal.slug}"),
            (Annotated[type(literal.value), 3], f"annotated_{literal.slug}"),
        )
        if type_checker is not ... or literal is not LiteralValue.NONE
    ],
)
def test_simple_success(
    type_checker: TypeChecker,
    literal_value: LiteralValue,
    common_modifier: Callable[[Any], Any],
) -> None:
    assert_contains(common_modifier(literal_value.value), common_modifier(type_checker))


@pytest.mark.parametrize(
    "literal_value",
    [literal.value for literal in LiteralValue if literal is not LiteralValue.NONE],
)
def test_ulc_success(literal_value: LiteralType) -> None:
    assert_contains([literal_value], UnorderedLiteralCollection({literal_value}))


def test_complex_fail() -> None:
    with pytest.raises(ValidationError) as exc:
        AssertContainsModel.contains(
            {
                "a": "5",
                "b": 6,
                "c": [{"d": "4", "e": 4}],
                "d": ["str", object()],
                "e": {"g": 5},
                "l": [True, 4],
                "r": [4, "hey", True, 4, "hey", True, 2],
                "s": [4, "hey", True, 4, "hey", True, 4, "hey", True],
                "w": str,
            },
            {
                "a": "3",
                "b": 3,
                "c": [{"d": int, "e": None}],
                "d": conlist(item_type=str),
                "e": {"g": str, "b": ..., "e": Any},
                "l": UnorderedLiteralCollection(
                    items={True, "hey", 4},
                    check_extra=False,
                ),
                "r": UnorderedLiteralCollection(
                    items={True, "hey", 4},
                    check_repeats=False,
                ),
                "s": UnorderedLiteralCollection(
                    items={True, "hey", 4},
                ),
            },
        )

    assert exc.type is ValidationError

    loc_to_error = {}
    for error in exc.value.errors():
        location = error.get("loc")
        assert location is not None
        assert location not in loc_to_error
        loc_to_error[location] = {
            "type": error.get("type"),
            "msg": error.get("msg"),
        }

    assert loc_to_error == {
        ("a",): {"type": "literal_error", "msg": "Input should be '3'"},
        ("b",): {"type": "literal_error", "msg": "Input should be 3"},
        ("c", 0, "e"): {"type": "none_required", "msg": "Input should be None"},
        ("d", 1): {"type": "string_type", "msg": "Input should be a valid string"},
        ("e", "g"): {"type": "string_type", "msg": "Input should be a valid string"},
        ("e", "b"): {"type": "missing", "msg": "Field required"},
        ("l",): {"type": "value_error", "msg": "Value error, items missing: {'hey'}"},
        ("r",): {"type": "value_error", "msg": "Value error, extra items found: {2}"},
    }


@pytest.mark.parametrize(
    ("data_type", "skip_values", "error_type", "error_msg"),
    [
        pytest.param(
            bool,
            LiteralValue.number_values(),
            "bool_parsing",
            "boolean",
            id="type_bool",
        ),
        pytest.param(
            int,
            LiteralValue.number_values(),
            "int_parsing",
            "integer",
            id="type_int",
        ),
        pytest.param(
            float,
            LiteralValue.number_values(),
            "float_parsing",
            "number",
            id="type_float",
        ),
        pytest.param(
            bytes,
            LiteralValue.string_values(),
            "bytes_type",
            "bytes",
            id="type_bytes",
        ),
        pytest.param(
            str,
            LiteralValue.string_values(),
            "string_type",
            "string",
            id="type_str",
        ),
    ],
)
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(literal, id=f"literal_{literal.slug}")
        for literal in LiteralValue
        if literal not in {LiteralValue.NONE, LiteralValue.ENUM}
    ],
)
def test_unordered_literal_collection_types(
    data_type: type[LiteralType],
    skip_values: set[LiteralValue],
    error_type: str,
    error_msg: str,
    value: LiteralValue,
) -> None:
    if value in skip_values:
        return

    collection = UnorderedLiteralCollection([value.value], data_type=data_type)

    with pytest.raises(ValidationError) as exc:
        AssertContainsModel.contains([value.value], collection)

    assert exc.type is ValidationError
    errors = exc.value.errors()
    assert len(errors) == 1
    assert errors[0].get("type") == error_type
    assert errors[0].get("msg") is not None
    assert errors[0]["msg"].startswith(f"Input should be a valid {error_msg}")
