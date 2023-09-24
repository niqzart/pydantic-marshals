from collections.abc import Callable
from typing import Any, get_type_hints

from typing_extensions import Self

from pydantic_marshals.base.fields.base import MarshalField
from pydantic_marshals.base.type_aliases import TypeHint
from pydantic_marshals.utils import ModeledType


class PropertyField(MarshalField):
    """
    Implementation of :py:class:`MarshalField` to use with properties
    Can be used directly or with an added type hit override
    """

    def __init__(
        self,
        mapped_property: property,
        type_: TypeHint | None = None,
        alias: str | None = None,
    ) -> None:
        super().__init__(alias)
        self.mapped_property = mapped_property

        if self.mapped_property.fget is None:
            raise RuntimeError("Property's fget is None somehow")
        self.getter: Callable[[Any], Any] = self.mapped_property.fget

        self.name: str = self.getter.__name__
        self.type_: TypeHint = type_ or get_type_hints(self.getter).get("return", Any)

    @classmethod
    def convert(cls, mapped: Any = None, type_: Any = None, *_: Any) -> Self | None:
        if isinstance(mapped, property) and isinstance(type_, TypeHint):
            return cls(mapped, type_)
        return None

    def generate_name(self) -> str:
        return self.name

    def generate_type(self) -> TypeHint:
        return self.type_


PropertyType = (
    property
    | ModeledType[property]
    | Callable[[Any], Any]
    | ModeledType[Callable[[Any], Any]]
    | PropertyField
)
