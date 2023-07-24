from collections.abc import Callable
from typing import Any, Self, get_type_hints

from pydantic_marshals.fields.base import MarshalField


class MarshalPropertyField(MarshalField):
    """
    Implementation of :py:class:`MarshalField` to use with properties
    Can be used directly or with an added type_override
    """

    def __init__(
        self,
        mapped_property: property,
        type_override: type | None = None,
        alias: str | None = None,
    ) -> None:
        super().__init__(alias)
        self.mapped_property = mapped_property
        self.type_override = type_override

    @classmethod
    def convert(cls, mapped: Any = None, type_: Any = None, *_: Any) -> Self | None:
        if isinstance(mapped, property) and (type_ is None or isinstance(type_, type)):
            return cls(mapped, type_)
        return None

    @property
    def getter(self) -> Callable[[Any], Any]:
        if self.mapped_property.fget is None:
            raise RuntimeError("Property's fget is None somehow")
        return self.mapped_property.fget

    def generate_name(self) -> str:
        return self.getter.__name__

    def generate_type(self) -> type:
        if self.type_override is not None:
            return self.type_override
        return get_type_hints(self.getter).get("return", Any)
