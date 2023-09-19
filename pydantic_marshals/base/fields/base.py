from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Self

from pydantic import BaseModel, RootModel
from pydantic.fields import Field

from pydantic_marshals.base.type_aliases import FieldType, TypeHint


class MarshalField:
    """
    Basic boilerplate class for all pydantic-marshals' models' fields.
    This is an interface, and it requires implementing all methods to function
    and to be used in :py:class:`pydantic_marshals.models.base.MarshalModel`
    """

    def __init__(self, alias: str | None = None) -> None:
        """
        :param alias: same as Field(alias=...), can be None for no alias
        """
        self.alias = alias

    @classmethod
    def convert(cls, *source: Any) -> Self | None:
        """
        Convert something into a field.
        If conversion is not possible, this method should return None
        """
        raise NotImplementedError

    def generate_name(self) -> str:
        """
        Generates the name for the field, used in
        :py:meth:`pydantic_marshals.models.base.MarshalModel.generate_model`
        """
        raise NotImplementedError

    def generate_type(self) -> TypeHint:
        """
        Generates the type annotation for the field, used in
        :py:meth:`pydantic_marshals.models.base.MarshalModel.generate_model`
        """
        raise NotImplementedError

    # TODO type with TypedDict? Use _FieldInfoInputs?
    def generate_field_data(self) -> Iterator[tuple[str, Any]]:
        """
        Generates field data (kwargs for :py:func:`pydantic.fields.Field`),
        and returns it in the for of an Iterator,
        compatible with the ``dict[str, Any]`` constructor

        Kwarg names and types can be found in
        :py:class:`pydantic.fields._FieldInfoInputs`
        """
        if self.alias is not None:
            yield "alias", self.alias

    def generate_field(self) -> FieldType:
        """
        Generates field info for the field, used in
        :py:meth:`pydantic_marshals.models.base.MarshalModel.generate_model`
        """
        return (
            self.generate_type(),
            Field(**dict(self.generate_field_data())),
        )

    def generate_root_model(self) -> type[BaseModel]:
        return RootModel[self.generate_type()]  # type: ignore[no-any-return, misc]
