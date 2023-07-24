from __future__ import annotations

from typing import Any, Self

from pydantic import BaseModel
from sqlalchemy.orm import Mapped, Relationship

from pydantic_marshals.fields.base import MarshalField
from pydantic_marshals.utils import ModeledType, is_subtype


class RelationshipField(MarshalField):
    """
    Implementation of :py:class:`MarshalField` to use with SQLAlchemy's relationships
    A conversion model has to be specified, preferably one made with
    :py:class:`pydantic_marshals.models.sqlalchemy.MappedModel`
    """

    def __init__(
        self,
        mapped_relationship: Relationship[Any],
        model: type[BaseModel],
        alias: str | None = None,
    ) -> None:
        super().__init__(alias)
        self.relationship = mapped_relationship
        self.model = model

    @classmethod
    def convert(cls, mapped: Any = None, model: Any = None, *_: Any) -> Self | None:
        if isinstance(mapped, Relationship) and is_subtype(model, BaseModel):
            return cls(mapped, model)
        return None

    def generate_name(self) -> str:
        return self.relationship.key

    def generate_type(self) -> type[BaseModel]:
        collection_class = self.relationship.collection_class
        if collection_class is None:
            return self.model
        if not isinstance(collection_class, type):
            raise RuntimeError(f"Collection is not a type: {collection_class}")
        if issubclass(collection_class, list):
            return list[self.model]  # type: ignore[return-value, name-defined]
        raise RuntimeError(f"Bad collection class: {collection_class}")


RelationshipType = (
    ModeledType[Relationship[Any]] | ModeledType[Mapped[Any]] | RelationshipField
)
