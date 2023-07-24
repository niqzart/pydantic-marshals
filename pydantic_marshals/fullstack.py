from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any, ClassVar, Optional, Self, Sequence, TypeVar, get_type_hints
from warnings import warn

from pydantic import BaseModel, create_model
from pydantic.fields import Field, FieldInfo
from pydantic_core import PydanticUndefined, PydanticUndefinedType
from sqlalchemy.orm import Mapped, MappedColumn, Relationship
from sqlalchemy.sql.schema import Column, ScalarElementColumnDefault
from sqlalchemy.sql.sqltypes import String


def is_subtype(maybe_type: Any, klass: type) -> bool:
    return isinstance(maybe_type, type) and issubclass(maybe_type, klass)


class MappedField:
    def __init__(self, alias: str | None = None) -> None:
        self.alias = alias

    @classmethod
    def convert(cls, *source: Any) -> Self | None:
        raise NotImplementedError

    def generate_name(self) -> str:
        raise NotImplementedError

    def generate_type(self) -> type:
        raise NotImplementedError

    # TODO type with TypedDict? Use _FieldInfoInputs?
    def generate_field_data(self) -> Iterator[tuple[str, Any]]:
        yield "alias", self.alias

    def generate_field(self) -> tuple[type, FieldInfo]:
        return (
            self.generate_type(),
            Field(**dict(self.generate_field_data())),  # type: ignore[pydantic-field]
        )


class MappedColumnField(MappedField):
    def __init__(
        self,
        mapped_column: MappedColumn[Any],
        alias: str | None = None,
    ) -> None:
        super().__init__(alias)
        self.mapped = mapped_column

    @classmethod
    def convert(
        cls, source: Any = None, *_: Any
    ) -> Self | None:  # TODO convert_or_none
        if isinstance(source, MappedColumn):
            return cls(source)
        return None

    @property
    def column(self) -> Column[Any]:
        return self.mapped.column

    def generate_name(self) -> str:
        return self.column.name

    def generate_type(self) -> type:
        result = self.column.type.python_type
        if self.column.nullable:
            return Optional[result]  # type: ignore[return-value]
        return result

    def generate_default(self) -> Any | None | PydanticUndefinedType:
        if self.column.default is None:
            return None if self.column.nullable else PydanticUndefined
        elif isinstance(self.column.default, ScalarElementColumnDefault):
            return self.column.default.arg
        else:
            warn(f"Default: {self.column.default} is not supported, skipping")
            return PydanticUndefined

    def generate_field_data(self) -> Iterator[tuple[str, Any]]:
        yield from super().generate_field_data()

        yield "default", self.generate_default()

        column_type = self.column.type
        if isinstance(column_type, String):
            yield "max_length", column_type.length


class MappedRelationshipField(MappedField):
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


class MappedPropertyField(MappedField):
    def __init__(
        self,
        mapped_property: property,
        type_override: type | None = None,
        alias: str | None = None,
    ) -> None:
        super().__init__(alias)
        self.mapped_property = mapped_property
        self.type_override = type_override

    @classmethod
    def convert(cls, mapped: Any = None, type_: Any = None, *_: Any) -> Self | None:
        if isinstance(mapped, property) and (type_ is None or isinstance(type_, type)):
            return cls(mapped, type_)
        return None

    def generate_name(self) -> str:
        if self.mapped_property.fget is None:
            raise RuntimeError("TODO")
        return self.mapped_property.fget.__name__

    def generate_type(self) -> type:
        if self.type_override is not None:
            return self.type_override
        result = get_type_hints(self.mapped_property.fget).get("return")
        if isinstance(result, type):
            return result
        raise RuntimeError("TODO")


class MarshalModel(BaseModel, from_attributes=True, populate_by_name=True):
    pass


# TODO move to pydantic-marshals
# TODO flat nesting (or an issue)
# TODO JSONs (or an issue)


class _MappedModel:
    def __init__(
        self,
        *fields: MappedField,
        bases: list[type[BaseModel]],
    ) -> None:
        self.fields: list[MappedField] = list(fields)
        self.bases: list[type[BaseModel]] = bases
        self._generated_model: type[BaseModel] | None = None

    def __set_name__(self, owner: type, name: str) -> None:
        self.model_name: str = f"{owner.__qualname__}.{name}"

    model_base_class: ClassVar[type[BaseModel]] = MarshalModel

    def generate_base(self) -> type[BaseModel] | tuple[type[BaseModel], ...]:
        if self.bases:
            return self.model_base_class, *self.bases
        return self.model_base_class

    def generate_model(self) -> type[BaseModel]:
        return create_model(  # type: ignore[call-overload, no-any-return]
            self.model_name,
            __base__=self.generate_base(),
            **{
                mapped_field.generate_name(): mapped_field.generate_field()
                for mapped_field in self.fields
            },
        )

    @property
    def generated_model(self) -> type[BaseModel]:
        if self._generated_model is None:
            self._generated_model = self.generate_model()
        return self._generated_model

    def __get__(self, instance: Any, owner: Any | None = None) -> type[BaseModel]:
        return self.generated_model


T = TypeVar("T")
ModeledType = tuple[T, type[BaseModel]]
ColumnType = MappedColumn[Any] | Mapped[Any] | MappedColumnField
RelationshipType = (
    ModeledType[Relationship[Any]] | ModeledType[Mapped[Any]] | MappedRelationshipField
)
PropertyType = (
    property
    | ModeledType[property]
    | Callable[[Any], Any]
    | ModeledType[Callable[[Any], Any]]
    | MappedPropertyField
)


class MappedModel(_MappedModel):
    field_types: tuple[type[MappedField], ...] = (
        MappedColumnField,
        MappedRelationshipField,
        MappedPropertyField,
    )

    @classmethod
    def convert_field(cls, raw_field: Any) -> MappedField:
        if isinstance(raw_field, MappedField):
            return raw_field

        if not isinstance(raw_field, tuple):
            raw_field = (raw_field,)

        for field_type in cls.field_types:
            result: MappedField | None = field_type.convert(*raw_field)
            if result is not None:
                return result
        raise RuntimeError("TODO")

    @classmethod
    def convert_aliased_field(cls, raw_field: Any, alias: str | None) -> MappedField:
        result = cls.convert_field(raw_field)
        result.alias = alias
        return result

    @classmethod
    def convert_fields(
        cls, *fields: Any, **aliased_fields: Any
    ) -> Iterator[MappedField]:
        for field in fields:
            yield cls.convert_field(field)
        for alias, field in aliased_fields.items():
            yield cls.convert_aliased_field(field, alias)

    @classmethod
    def create(
        cls,
        columns: Sequence[ColumnType] = (),
        relationships: Sequence[RelationshipType] = (),
        properties: Sequence[PropertyType] = (),
        bases: Sequence[type[BaseModel]] = (),
        includes: Sequence[_MappedModel] = (),
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
        includes: Sequence[_MappedModel] = (),
    ) -> Self:
        return self.create(
            columns=columns,
            relationships=relationships,
            properties=properties,
            bases=bases,
            includes=(self, *includes),
        )
