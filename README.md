# Pydantic Marshals
Library for creating partial pydantic models (automatic converters) from different mappings. Currently, it consists of basic boilerplate parts and functional implementation for sqlalchemy 2.0+ (included via extra)

## Base Interface
TBA

## Implementations
TBA

### SQLAlchemy: Basic usage
```py
# sqlalchemy 2.0+ is required
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pydantic_marshals.sqlalchemy import MappedModel

class Avatar(Base):
    __tablename__ = "avatars"
    id: Mapped[int] = mapped_column(primary_key=True)
    IdModel = MappedModel.create(columns=[id])

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text())
    admin: Mapped[bool] = mapped_column()  # empty `mapped_column()` is required for models

    avatar_id: Mapped[int] = mapped_column(ForeignKey("avatars.id"))
    avatar: Mapped[Avatar] = relationship()

    @property
    def representation(self) -> str:
        return f"User #{self.id}: {self.name}"

    BaseModel = MappedModel.create(columns=[id])
    CreateModel = MappedModel.create(columns=[name, description])
    PatchModel = CreateModel.as_patch()
    IndexModel = MappedModel.create(properties=[representation])
    FullModel = BaseModel.extend(
        columns=[admin],
        relationships=[(avatar, Avatar.IdModel)],
        includes=[CreateModel, IndexModel],
    )


with sessionmaker.begin() as session:
    user = User(name="alex", description="cool person", avatar=Avatar(), admin=False)
    session.add(user)
    session.flush()

    print(User.BaseModel.model_validate(user).model_dump())
    # {"id": 0}
    print(User.PatchModel.model_validate({}).model_dump(exclude_defaults=True))
    # {}
    print(User.PatchModel.model_validate({"description": None}).model_dump(exclude_defaults=True))
    # {"description": None}
    print(User.CreateModel.model_validate(user).model_dump())
    # {"name": "alex", "description": "cool person"}
    print(User.IndexModel.model_validate(user).model_dump())
    # {"representation": "User #0: alex"}
    print(User.FullModel.model_validate(user).model_dump())
    # {
    #   "id": 0,
    #   "name": "alex",
    #   "description": "cool person",
    #   "representation": "User #0: alex",
    #   "avatar": {"id": 0},
    #   "admin": False
    # }
```

### Assert Contains
The "assert contains" is an interface for validating data, mainly used in testing. Use `"assert-contains"` extra to install this module:
```sh
pip install pydantic-marshals[assert-contains]
```

#### Documentation:
- [Usage with Examples](https://github.com/niqzart/pydantic-marshals/blob/master/docs/assert-contains.md)

## Local development
1. Clone the repository
2. Setup python (the library is made with python 3.10+)
3. Install poetry (should work with v1.4.1)
4. Install dependencies
5. Install pre-commit hooks

Commands to use:
```sh
pip install poetry==1.4.1
poetry install
pre-commit install
```
