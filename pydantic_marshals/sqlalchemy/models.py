from __future__ import annotations

from collections.abc import Iterator, Sequence

from pydantic import BaseModel
from typing_extensions import Self

from pydantic_marshals.base.fields.base import MarshalField, PatchMarshalField
from pydantic_marshals.base.fields.properties import PropertyField, PropertyType
from pydantic_marshals.base.models import MarshalModel
from pydantic_marshals.sqlalchemy.fields.columns import ColumnField, ColumnType
from pydantic_marshals.sqlalchemy.fields.relationships import (
    RelationshipField,
    RelationshipType,
)


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
            *cls.convert_fields(*columns),
            *cls.convert_fields(*relationships),
            *cls.convert_fields(*properties),
            *(field for model in includes for field in model.fields),
            bases=list(bases) + [base for model in includes for base in model.bases],
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

    def patch_fields(self) -> Iterator[MarshalField]:
        for field in self.fields:
            if isinstance(field, PatchMarshalField):
                yield field.as_patch()
            else:
                yield field

    def as_patch(self) -> Self:
        return type(self)(*self.patch_fields(), bases=self.bases)
