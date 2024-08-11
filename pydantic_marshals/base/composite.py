from __future__ import annotations

from typing import Any, get_origin

from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo

from pydantic_marshals.base.models import MarshalBaseModel
from pydantic_marshals.utils import is_optional, is_subtype


class CompositeMarshalModel(MarshalBaseModel):
    @classmethod
    def generate_marshal_model_name(cls) -> str:
        return f"{cls.__name__}Marshal"

    @classmethod
    def convert_field(cls, field: FieldInfo) -> tuple[Any, Any]:
        if len(field.metadata) == 1 and is_subtype(field.metadata[0], MarshalBaseModel):
            if is_subtype(get_origin(field.annotation), list):
                return list[field.metadata[0]], field.default  # type: ignore
            if is_optional(field.annotation):
                return field.metadata[0] | None, field.default
            return field.metadata[0], field.default
        if field.annotation is None:
            raise TypeError("Annotation is somehow None")
        return field.annotation, field

    @classmethod
    def build_marshal(cls) -> type[BaseModel]:
        return create_model(  # type: ignore[call-overload, no-any-return]
            cls.generate_marshal_model_name(),
            **{
                file_name: cls.convert_field(field)
                for file_name, field in cls.model_fields.items()
            },
        )
