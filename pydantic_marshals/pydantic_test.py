from datetime import date, datetime
from enum import Enum, auto
from json import dumps

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.config import Base
from app.common.fullstack import MappedModel


class E(int, Enum):
    A = auto()
    B = auto()


class Avatar(Base):
    __tablename__ = "avatars"

    id: Mapped[int] = mapped_column(primary_key=True)

    CreateModel = MappedModel.create(columns=[id])


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    CreateModel = MappedModel.create(columns=[id])


class AbstractUser(Base):
    __abstract__ = True

    t: Mapped[int] = mapped_column()

    BaseModel = MappedModel.create(columns=[t])
    # TODO replace with create_abstract which won't be a descriptor


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    a: Mapped[int | None] = mapped_column()
    b: Mapped[int | None] = mapped_column(default=0)
    c: Mapped[int] = mapped_column(default=0)
    e: Mapped[E] = mapped_column()

    d1: Mapped[date] = mapped_column()
    d2: Mapped[datetime] = mapped_column()
    # di: Mapped[dict] = mapped_column(type_=JSON)

    avatar_id: Mapped[int] = mapped_column(ForeignKey("avatars.id"))
    avatar: Mapped[Avatar] = relationship()

    addresses: Mapped[list[Address]] = relationship()

    @property
    def hey(self) -> str:
        return "hey"

    @property
    def av(self) -> Avatar:
        return self.avatar

    CreateModel = MappedModel.create(
        columns=[name],
        relationships=[
            (avatar, Avatar.CreateModel),
            (addresses, Address.CreateModel),
        ],
        properties=[hey, (av, Avatar.CreateModel)]
        # bases=[AbstractUser.BaseModel]
    )
    FullModel = CreateModel.extend(columns=[id, a, b, c, e, d2])


if __name__ == "__main__":
    from pydantic import BaseModel

    def t1(_: type[BaseModel]) -> None:
        pass

    class R(User.CreateModel):
        y: str

    class T(User.FullModel):
        y: str

    t1(User.CreateModel)
    t1(User.FullModel)
    t1(T)

    print(dumps(T.model_json_schema(), indent=2))
