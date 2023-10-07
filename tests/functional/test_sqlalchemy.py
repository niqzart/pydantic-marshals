from datetime import date, datetime, time, timedelta
from typing import Any, Generic, TypeVar

import pytest
from pydantic import BaseModel, ValidationError
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined
from sqlalchemy import ForeignKey, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from pydantic_marshals.base.fields.base import PatchDefault
from pydantic_marshals.sqlalchemy import MappedModel
from pydantic_marshals.utils import is_subtype
from tests.unit.conftest import SampleEnum


@pytest.fixture()
def declarative_base() -> type[DeclarativeBase]:
    db_meta = MetaData()

    class Base(DeclarativeBase):
        metadata = db_meta

    class AbstractBase(Base):
        __tablename__ = "table"
        __abstract__ = True
        id: Mapped[int] = mapped_column(primary_key=True)  # noqa: VNE003

    return AbstractBase


T = TypeVar("T")


class PytestRequest(Generic[T]):
    @property
    def param(self) -> T:
        raise NotImplementedError


now = datetime.utcnow()
future = datetime.utcnow() + timedelta(hours=3)


@pytest.fixture(
    params=[
        pytest.param((bool, True, False), id="bool"),
        pytest.param((int, 1, -1), id="int"),
        pytest.param((float, 1.1, -1.1), id="float"),
        pytest.param((bytes, b"hey", b"yeh"), id="bytes"),
        pytest.param((str, "hey", "yeh"), id="str"),
        pytest.param((date, now.date(), future.date()), id="date"),
        pytest.param((time, now.time(), future.time()), id="time"),
        pytest.param((datetime, now, future), id="datetime"),
        pytest.param((SampleEnum, SampleEnum.A, SampleEnum.B), id="enum"),
    ]
)
def column_data(request: PytestRequest[tuple[Any, Any, Any]]) -> tuple[Any, Any, Any]:
    return request.param


@pytest.fixture()
def column_type(column_data: tuple[Any, Any, Any], column_nullable: bool) -> Any:
    if column_nullable:
        return column_data[0] | None
    return column_data[0]


@pytest.fixture()
def column_default(column_data: tuple[Any, Any, Any]) -> Any:
    return column_data[1]


@pytest.fixture()
def column_value(column_data: tuple[Any, Any, Any]) -> Any:
    return column_data[2]


@pytest.fixture(params=[False, True], ids=["no_default", "with_default"])
def column_use_default(request: PytestRequest[bool]) -> bool:
    return request.param


@pytest.fixture(params=[False, True], ids=["required", "nullable"])
def column_nullable(request: PytestRequest[bool]) -> bool:
    return request.param


@pytest.fixture()
def column_model(
    declarative_base: type[DeclarativeBase],
    column_type: Any,
    column_default: Any,
    column_nullable: bool,
    column_use_default: bool,
) -> type[DeclarativeBase]:
    kwargs = {}
    if column_use_default:
        kwargs["default"] = column_default

    class T(declarative_base):  # type: ignore[valid-type, misc]
        field: Mapped[column_type] = mapped_column(**kwargs)

        Model = MappedModel.create(columns=[field])
        ExtendedModel = Model.extend()
        PatchModel = Model.as_patch()
        ExtendedPatchModel = PatchModel.extend()

    return T


@pytest.fixture(params=[False, True], ids=["full", "patch"])
def column_patch_mode(request: PytestRequest[bool]) -> bool:
    return request.param


@pytest.fixture(params=[False, True], ids=["normal", "extended"])
def column_marshal_model(
    column_model: Any,
    column_patch_mode: bool,
    request: PytestRequest[bool],
) -> type[BaseModel]:
    if request.param:
        if column_patch_mode:
            return column_model.ExtendedPatchModel  # type: ignore[no-any-return]
        return column_model.ExtendedModel  # type: ignore[no-any-return]
    if column_patch_mode:
        return column_model.PatchModel  # type: ignore[no-any-return]
    return column_model.Model  # type: ignore[no-any-return]


def test_column_model_inspection(
    column_type: Any,
    column_default: Any,
    column_nullable: bool,
    column_patch_mode: bool,
    column_use_default: bool,
    column_marshal_model: type[BaseModel],
) -> None:
    assert is_subtype(column_marshal_model, BaseModel)
    assert len(column_marshal_model.model_fields) == 1

    field = column_marshal_model.model_fields.get("field")
    assert isinstance(field, FieldInfo)
    assert field.annotation == column_type

    expected_required = not (column_nullable or column_use_default or column_patch_mode)
    assert field.is_required() == expected_required

    if column_patch_mode:
        expected_default = PatchDefault
    elif column_use_default:
        expected_default = column_default
    elif column_nullable:
        expected_default = None
    else:
        expected_default = PydanticUndefined

    assert field.default is expected_default


def test_column_model_usage(
    column_type: Any,
    column_default: Any,
    column_value: Any,
    column_nullable: bool,
    column_use_default: bool,
    column_model: Any,
    column_marshal_model: type[BaseModel],
) -> None:
    instance = column_model(field=column_value)
    real = column_marshal_model.model_validate(instance)
    assert real.model_dump() == {"field": column_value}

    nullable_instance = column_model()
    if column_nullable:
        real = column_marshal_model.model_validate(nullable_instance)
        assert real.model_dump() == {"field": None}
        # doesn't depend on default because it isn't applied before flushing
    else:
        with pytest.raises(ValidationError) as exc:
            column_marshal_model.model_validate(nullable_instance)

        errors = exc.value.errors()
        assert len(errors) == 1


@pytest.fixture()
def related_model(declarative_base: type[DeclarativeBase]) -> Any:
    class Related(declarative_base):  # type: ignore[valid-type, misc]
        __tablename__ = "related"
        Model = MappedModel.create()

    return Related


# TODO allow nullable relationships
@pytest.fixture()
def relationship_model(
    declarative_base: type[DeclarativeBase],
    related_model: Any,
) -> Any:
    class T(declarative_base):  # type: ignore[valid-type, misc]
        fk: Mapped[int] = mapped_column(ForeignKey("related.id"))
        field: Mapped[related_model] = relationship()

        Model = MappedModel.create(relationships=[(field, related_model.Model)])
        ExtendedModel = Model.extend()

    return T


@pytest.fixture(params=[False, True], ids=["normal", "extended"])
def relationship_marshal_model(
    relationship_model: Any,
    request: PytestRequest[bool],
) -> type[BaseModel]:
    if request.param:
        return relationship_model.ExtendedModel  # type: ignore[no-any-return]
    return relationship_model.Model  # type: ignore[no-any-return]


def test_relationship_inspection(
    related_model: Any,
    relationship_marshal_model: type[BaseModel],
) -> None:
    assert is_subtype(relationship_marshal_model, BaseModel)
    assert len(relationship_marshal_model.model_fields) == 1

    field = relationship_marshal_model.model_fields.get("field")
    assert isinstance(field, FieldInfo)
    assert field.annotation == related_model.Model
    assert field.is_required()
    assert field.default is PydanticUndefined


def test_relationship_usage(
    related_model: Any,
    relationship_model: Any,
    relationship_marshal_model: type[BaseModel],
) -> None:
    instance = relationship_model(field=related_model())
    real = relationship_marshal_model.model_validate(instance)
    assert real.model_dump() == {"field": {}}


@pytest.fixture()
def property_simple_model(
    column_type: Any,
    column_value: Any,
    declarative_base: type[DeclarativeBase],
) -> Any:
    class T(declarative_base):  # type: ignore[valid-type, misc]
        @property
        def field(self) -> column_type:
            return column_value

        Model = MappedModel.create(properties=[field])
        ExtendedModel = Model.extend()

    return T


@pytest.fixture(params=[False, True], ids=["normal", "extended"])
def property_simple_marshal_model(
    property_simple_model: Any,
    request: PytestRequest[bool],
) -> type[BaseModel]:
    if request.param:
        return property_simple_model.ExtendedModel  # type: ignore[no-any-return]
    return property_simple_model.Model  # type: ignore[no-any-return]


def test_property_simple_inspection(
    column_type: Any,
    property_simple_marshal_model: type[BaseModel],
) -> None:
    assert is_subtype(property_simple_marshal_model, BaseModel)
    assert len(property_simple_marshal_model.model_fields) == 1

    field = property_simple_marshal_model.model_fields.get("field")
    assert isinstance(field, FieldInfo)
    assert field.annotation == column_type
    assert field.is_required()
    assert field.default is PydanticUndefined


def test_property_simple_usage(
    column_type: Any,
    column_value: Any,
    property_simple_model: Any,
    property_simple_marshal_model: type[BaseModel],
) -> None:
    instance = property_simple_model()
    real = property_simple_marshal_model.model_validate(instance)
    assert real.model_dump() == {"field": column_value}


@pytest.fixture()
def property_related_model(
    column_type: Any,
    column_value: Any,
    declarative_base: type[DeclarativeBase],
    related_model: Any,
) -> Any:
    class T(declarative_base):  # type: ignore[valid-type, misc]
        fk: Mapped[int] = mapped_column(ForeignKey("related.id"))
        related: Mapped[related_model] = relationship()

        @property
        def field(self) -> related_model:
            return self.related

        Model = MappedModel.create(properties=[(field, related_model.Model)])
        ExtendedModel = Model.extend()

    return T


@pytest.fixture(params=[False, True], ids=["normal", "extended"])
def property_related_marshal_model(
    property_related_model: Any,
    request: PytestRequest[bool],
) -> type[BaseModel]:
    if request.param:
        return property_related_model.ExtendedModel  # type: ignore[no-any-return]
    return property_related_model.Model  # type: ignore[no-any-return]


def test_property_related_inspection(
    property_related_marshal_model: type[BaseModel],
    related_model: Any,
) -> None:
    assert is_subtype(property_related_marshal_model, BaseModel)
    assert len(property_related_marshal_model.model_fields) == 1

    field = property_related_marshal_model.model_fields.get("field")
    assert isinstance(field, FieldInfo)
    assert field.annotation == related_model.Model
    assert field.is_required()
    assert field.default is PydanticUndefined


def test_property_related_usage(
    related_model: Any,
    property_related_model: Any,
    property_related_marshal_model: type[BaseModel],
) -> None:
    instance = property_related_model(related=related_model())
    real = property_related_marshal_model.model_validate(instance)
    assert real.model_dump() == {"field": {}}
