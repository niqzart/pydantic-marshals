from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Optional, Self
from warnings import warn

from pydantic_core import PydanticUndefined, PydanticUndefinedType
from sqlalchemy.orm import Mapped, MappedColumn
from sqlalchemy.sql.schema import Column, ScalarElementColumnDefault
from sqlalchemy.sql.sqltypes import String

from pydantic_marshals.base.fields.base import MarshalField


class ColumnField(MarshalField):
    """
    Implementation of :py:class:`MarshalField` to use with SQLAlchemy's columns
    This will only work with 2.0-style MappedColumns
    """

    def __init__(
        self,
        mapped_column: MappedColumn[Any],
        alias: str | None = None,
    ) -> None:
        super().__init__(alias)
        self.mapped = mapped_column

    @classmethod
    def convert(cls, source: Any = None, *_: Any) -> Self | None:
        if isinstance(source, MappedColumn):
            return cls(source)
        return None

    @property
    def column(self) -> Column[Any]:
        return self.mapped.column

    def generate_name(self) -> str:
        return self.column.name

    def generate_type(self) -> type:
        type_ = self.column.type.python_type
        if self.column.nullable:
            return Optional[type_]  # type: ignore[return-value]  # noqa: NU002
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

        yield "default", self.generate_default()

        column_type = self.column.type
        if isinstance(column_type, String):
            yield "max_length", column_type.length


ColumnType = MappedColumn[Any] | Mapped[Any] | ColumnField
