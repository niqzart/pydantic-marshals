from pydantic_marshals.contains.type_aliases import LiteralType
from pydantic_marshals.contains.type_generators.base import BaseTypeGenerator


class UnorderedLiteralCollection(BaseTypeGenerator):
    data_type = list[LiteralType]

    def __init__(
        self,
        items: set[LiteralType],
        check_extra: bool = True,
        check_repeats: bool = True,
    ) -> None:
        """
        :param items: set of literal values to search for
        :param check_extra: (default True) determines if extra values are allowed
        :param check_repeats: (default True) determines if repeating values are allowed
        """
        self.items = items
        self.check_extra = check_extra
        self.check_repeats = check_repeats

    def _validate(self, data: list[LiteralType]) -> None:
        data_set: set[LiteralType] = set(data)

        missing: set[LiteralType] = self.items - data_set
        if missing:
            raise ValueError(f"items missing: {missing}")

        if self.check_extra:
            extra: set[LiteralType] = data_set - self.items
            if extra:
                raise ValueError(f"extra items found: {extra}")

        if self.check_repeats:
            repeats: set[LiteralType] = set()
            seen: set[LiteralType] = set()

            for item in data:
                if item in seen:
                    repeats.add(item)
                else:
                    seen.add(item)

            if repeats:
                raise ValueError(f"repeating items found: {repeats}")
