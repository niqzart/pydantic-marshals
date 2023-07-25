from __future__ import annotations

from collections.abc import Sequence
from typing import Self

from pydantic import BaseModel

from pydantic_marshals.base.fields.properties import PropertyType
from pydantic_marshals.base.models import MarshalModel
from pydantic_marshals.sqlalchemy.fields.columns import ColumnType
from pydantic_marshals.sqlalchemy.fields.relationships import RelationshipType

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
