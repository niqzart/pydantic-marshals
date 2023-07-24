from __future__ import annotations

from collections.abc import Sequence
from typing import Self

from pydantic import BaseModel

from pydantic_marshals.fields.properties import PropertyField, PropertyType
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
    - properties (constructed with built-in ``@property()``)
    - properties with overriden type (see :py:class:`PropertyField`)

    An alternative constructor :py:meth:`create` is available to make this happen
    """

    field_types = (
        ColumnField,
        RelationshipField,
        PropertyField,
    )

    @classmethod
    def create(
        cls,
        columns: Sequence[ColumnType] = (),
        relationships: Sequence[RelationshipType] = (),
        properties: Sequence[PropertyType] = (),
        bases: Sequence[type[BaseModel]] = (),
        includes: Sequence[MarshalModel] = (),
    ) -> Self:
        return cls(
            *cls.convert_fields(columns),
            *cls.convert_fields(relationships),
            *cls.convert_fields(properties),
            *(field for model in includes for field in model.fields),
            bases=list(bases),
        )

    def extend(
        self,
        columns: Sequence[ColumnType] = (),
        relationships: Sequence[RelationshipType] = (),
        properties: Sequence[PropertyType] = (),
        bases: Sequence[type[BaseModel]] = (),
        includes: Sequence[MarshalModel] = (),
    ) -> Self:
        return self.create(
            columns=columns,
            relationships=relationships,
            properties=properties,
            bases=bases,
            includes=(self, *includes),
        )
