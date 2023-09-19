from typing import Any, Annotated

from pydantic import conlist, AfterValidator

from pydantic_marshals.base.type_aliases import TypeHint
from pydantic_marshals.contains.models import assert_contains
from pydantic_marshals.contains.type_aliases import LiteralType


def UnorderedLiteralCollection(
    items: set[LiteralType],
    allow_extra: bool = False,
    allow_repeats: bool = False,
) -> TypeHint:
    def checker(data: list[LiteralType]) -> list[LiteralType]:
        data_set: set[LiteralType] = set(data)
        missing: set[LiteralType] = items - data_set

        if len(missing):
            raise ValueError(f"items missing: {missing}")

        if not allow_extra:
            extra: set[LiteralType] = data_set - items
            if len(extra):
                raise ValueError(f"extra items found: {extra}")

        if not allow_repeats:
            repeats: set[LiteralType] = set()
            seen: set[LiteralType] = set()

            for x in data:
                if x in seen:
                    repeats.add(x)
                else:
                    seen.add(x)

            if len(repeats):
                raise ValueError(f"repeating items found: {repeats}")

        return data

    return Annotated[list, AfterValidator(checker)]


if __name__ == "__main__":
    checker = {
        "a": "3",
        "b": 3,
        "c": [{"d": int, "e": None}],
        "d": conlist(item_type=str),
        "e": {"g": str, "b": ..., "e": Any},
        "l": UnorderedLiteralCollection(items={True, "hey", 4}, allow_extra=True),
        "r": UnorderedLiteralCollection(items={True, "hey", 4}, allow_repeats=True),
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
