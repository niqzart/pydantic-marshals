from __future__ import annotations

from collections.abc import Sequence
from typing import Self

from pydantic import BaseModel

from pydantic_marshals.fields.properties import PropertyType
from pydantic_marshals.fields.sqlalchemy.columns import ColumnType
from pydantic_marshals.fields.sqlalchemy.relationships import RelationshipType
from pydantic_marshals.models.base import MarshalModel

class MappedModelStub:
    @classmethod
    def extend(
        cls,
        columns: Sequence[ColumnType] = (),
        relationships: Sequence[RelationshipType] = (),
        properties: Sequence[PropertyType] = (),
        bases: Sequence[type[BaseModel]] = (),
        includes: Sequence[MarshalModel | MappedModelStub] = (),
    ) -> Self: ...
