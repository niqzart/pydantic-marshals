from typing import Any

from pydantic import conlist

from pydantic_marshals.contains.models import assert_contains

if __name__ == "__main__":
    checker = {
        "a": "3",
        "b": 3,
        "c": [{"d": int, "e": None}],
        "d": conlist(item_type=str),
        "e": {"g": str, "b": ..., "e": Any},
    }

    assert_contains(
        {
            "a": "3",
            "b": 3,
            "c": [{"d": 4}],
            "d": ["str", "wow"],
            "e": {"g": "ger", "b": object()},
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
        },
        checker,
    )
