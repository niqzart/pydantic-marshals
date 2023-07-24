from __future__ import annotations

from collections.abc import Sequence
from typing import Self

from pydantic_marshals.fields.sqlalchemy.columns import ColumnField, ColumnType
from pydantic_marshals.fields.sqlalchemy.relationships import (
    RelationshipField,
    RelationshipType,
)
from pydantic_marshals.models.base import MarshalModel


class MappedModel(MarshalModel):
    """
    Implementation of :py:class:`MarshalModel` to use inside SQLAlchemy's
    (ORM style) table definitions (i.e. classes inherited from `Base`).

    Right now it can accept and convert into fields:
    - columns (constructed with ``mapped_column()``)
    - relationships (constructed with ``relationship()``)

    An alternative constructor :py:meth:`create` is available to make this happen
    """

    field_types = (
        ColumnField,
        RelationshipField,
    )

    @classmethod
    def create(
        cls,
        columns: Sequence[ColumnType] = (),
        relationships: Sequence[RelationshipType] = (),
    ) -> Self:
        return cls(
            *cls.convert_fields(columns),
            *cls.convert_fields(relationships),
            bases=[],
        )
