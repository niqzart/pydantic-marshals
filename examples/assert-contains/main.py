from typing import Any

from pydantic import conlist

from pydantic_marshals.contains.models import assert_contains
from pydantic_marshals.contains.type_generators.collections import UnorderedLiteralCollection

if __name__ == "__main__":
    checker = {
        "a": "3",
        "b": 3,
        "c": [{"d": int, "e": None}],
        "d": conlist(item_type=str),
        "e": {"g": str, "b": ..., "e": Any},
        "l": UnorderedLiteralCollection(items={True, "hey", 4}, check_extra=False),
        "r": UnorderedLiteralCollection(items={True, "hey", 4}, check_repeats=False),
        "s": UnorderedLiteralCollection(items={True, "hey", 4}),
    }

    assert_contains(
        {
            "a": "3",
            "b": 3,
            "c": [{"d": 4}],
            "d": ["str", "wow"],
            "e": {"g": "ger", "b": object()},
            "l": [4, "hey", True, "wow"],
            "r": [4, "hey", True, 4, "hey", True],
            "s": [4, "hey", True],
        },
        checker,
    )

    assert_contains(
        {
            "a": "5",
            "b": 6,
            "c": [{"d": "4", "e": 4}],
            "d": ["str", 3, object()],
            "e": {"g": 5},
            "l": [True],
            "r": [4, "hey", True, 4, "hey", True, False],
            "s": [4, "hey", True, 4, "hey", True, 4, "hey", True],
        },
        checker,
    )
