from __future__ import annotations

from collections.abc import Iterator
from enum import Enum
from typing import Any
from warnings import warn

from pydantic_core import PydanticUndefined, PydanticUndefinedType
from sqlalchemy.orm import Mapped, MappedColumn
from sqlalchemy.sql.schema import Column, ScalarElementColumnDefault
from sqlalchemy.sql.sqltypes import String
from typing_extensions import Self

from pydantic_marshals.base.fields.base import PatchMarshalField
from pydantic_marshals.base.type_aliases import TypeHint
from pydantic_marshals.utils import is_subtype


class ColumnField(PatchMarshalField):
    """
    Implementation of :py:class:`MarshalField` to use with SQLAlchemy's columns
    This will only work with 2.0-style MappedColumns
    """

    def __init__(
        self,
        mapped_column: MappedColumn[Any],
        alias: str | None = None,
        patch: bool = False,
    ) -> None:
        super().__init__(alias, patch)
        self.mapped = mapped_column

    def as_patch(self) -> ColumnField:
        return ColumnField(mapped_column=self.mapped, alias=self.alias, patch=True)

    @classmethod
    def convert(cls, source: Any = None, *_: Any) -> Self | None:
        if isinstance(source, MappedColumn):
            return cls(mapped_column=source)
        return None

    @property
    def column(self) -> Column[Any]:
        return self.mapped.column

    def generate_name(self) -> str:
        return self.column.name

    def generate_type(self) -> TypeHint:
        type_: TypeHint = self.column.type.python_type
        if self.column.nullable:
            return type_ | None
        return type_

    def generate_default(self) -> Any | None | PydanticUndefinedType:
        if self.column.default is None:
            return None if self.column.nullable else PydanticUndefined
        if isinstance(self.column.default, ScalarElementColumnDefault):
            return self.column.default.arg
        warn(f"Default: {self.column.default} is not supported, skipping")
        return PydanticUndefined

    def generate_field_data(self) -> Iterator[tuple[str, Any]]:
        yield from super().generate_field_data()

        column_type = self.column.type
        if isinstance(column_type, String) and not is_subtype(
            column_type.python_type,
            Enum,
        ):  # enums are kept by name in the database
            yield "max_length", column_type.length


ColumnType = MappedColumn[Any] | Mapped[Any] | ColumnField
