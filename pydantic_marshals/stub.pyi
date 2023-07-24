from collections.abc import Sequence
from typing import Self

from pydantic import BaseModel

from app.common.fullstack import (
    ColumnType,
    PropertyType,
    RelationshipType,
    _MappedModel,
)

class Stub:
    @classmethod
    def extend(
        cls,
        columns: Sequence[ColumnType] = (),
        relationships: Sequence[RelationshipType] = (),
        properties: Sequence[PropertyType] = (),
        bases: Sequence[type[BaseModel]] = (),
        includes: Sequence[_MappedModel | Stub] = (),
    ) -> Self: ...
