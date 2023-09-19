# Assert Contains
The "assert contains" is an interface for validating data, mainly used in testing. It is based on [pydantic](https://docs.pydantic.dev/2.0/) (2.0-ish!) with additions for stricter checks (for example, you might need to check if the value is *exactly* 3). For simplicity and inline-usage models are created from so-called `TypeChecker`s (described below) at runtime

## Base Usage
```py
from pydantic_marshals.contains import assert_contains

def test_something():
    assert_contains(
        ...,  # something you received during a test
        ...,  # the TypeChecker to use
    )
```

The code above will raise an AssertionError if `real` does not pass the check. The error will contain standard pydantic ValidationError message and, because it is an AssertionError, pytest will be able to do [assertion introspection](https://docs.pytest.org/en/7.1.x/how-to/assert.html#assert-details) on it (normally the real and expected values would be readable)

## TypeChecker Format
TypeChecker is the second argument to the `assert_contains` call. It may be any literal value (`int`, `str`, `bool`, `float`, `Enum`); `type` to check only the type, not the exact value; pydantic's [constrained](https://docs.pydantic.dev/2.0/api/types/#pydantic.types.conint) or [strict](https://docs.pydantic.dev/2.0/usage/types/strict_types/) type; `None` to represent the absense of data; `Any` and `...` as wildcards; a `dict` with models as values; a `list` with models as items; or even a full pydantic model class

## Validation Details
### Dict-Based TypeChecker
Dicts are used to create full pydantic models instead of checking just one field. Most use cases are based on dicts, so are the examples bellow, but you *can* use one-field-models if you need

### Literal Values
Any literal value is compared by the exact value, using pydantic's type conversion. Multiple possible literal values per filed can be specified via `typing.Literal`. If real is anything but the exact value, an error will be raised. This is extremely useful for tests, for example:
```py
from enum import Enum, auto
from typing import Literal
from pydantic_marshals.contains import assert_contains

class UserType(Enum):
    BASIC = auto()
    ADMIN = auto()


def test_authorization():
    assert_contains(
        get_my_user(),
        {
            "id": 1,
            "username": "jeff",
            "email-confirmed": True,
            "status": Literal["online", "idle"],
            "type": UserType.ADMIN,
        }
    )
```

The simplest example of this is that you actually could use `assert_contains` instead of an equality check:
```py
assert_contains(3, 3)  # no errors raised
assert_contains(5, 3)  # ValidationError: Input should be 3 [type=literal_error, input_value=5, input_type=int]
```

### Only checking the type
Sometimes you do not know the exact value of a field, but you might need to check its type and some type-based constraints (like string length). For this you can use:

- Exact types, including custom classes
- [Constrained types](https://docs.pydantic.dev/usage/types/#constrained-types) for additional checks
- [Strict types](https://docs.pydantic.dev/usage/types/#strict-types) to disable type conversion
- Anything that is a subclass of `type` and [works in `pydantic`](https://docs.pydantic.dev/usage/types/) should also work (not guaranteed)

```py
from uuid import UUID
from pydantic import constr, StrictBool
from pydantic_marshals.contains import assert_contains

def test_page_data():
    assert_contains(
        fetch_some_page(),
        {
            # we don't know the exact id, but it's an integer
            "id": int,
            # custom classes should also work
            "guid": UUID,
            # created is a date, so we'll check a simple regex
            "created": constr(pattern=r"\d{2}\.\d{2}\.\d{4}"),
            # published can only be a boolean value
            "published": StrictBool,
        }
    )
```

The simplest example of this is that you actually could use `assert_contains` instead of an `isinstance` check:
```py
assert_contains(3, int)  # no errors raised
assert_contains(3, str)  # ValidationError: Input should be a valid string [type=string_type, input_value=3, input_type=int]
```

### Everything or nothing
Simple checks for existing or absent fields are also supported:
- Use `None` if you want to check field's absense (`None`s will pass)
- Use `...` if a not-`None` field should be present with any value
- Use `Any` if anything in a filed (including `None`) is allowed

```py
from typing import Any
from pydantic_marshals.contains import assert_contains

def test_wildcards():
    assert_contains(
        load_resource(),
        {
            # a field so wild, we can't stop it
            "wild": Any,
            # some data should be here
            "data": ...,
            # we don't want deadlines
            "deadline": None,
        }
    )
```

### Checking Lists
Depending on the circumstances, three ways of validating lists could be used:
- Validating all items with one schema: can be done via [`conlist`](https://docs.pydantic.dev/usage/types/#arguments-to-conlist)
- Validating each individual item, via applying `assert_contains` for each of them
- Validating list as an unordered collection of literal values, see [`UnorderedLiteralCollection`](#unorderedliteralcollection)

```py
from pydantic import conlist
from pydantic_marshals.contains import assert_contains

def test_lists():
    assert_contains(
        gather_lists(),
        {
            "list_of_ints": conlist(item_type=int, max_length=3),
            "specific_list": [
                {"id": 1, "username": "jeff"},
                {"id": 2, "entity": "school", "number": 34},
            ]
        }
    )
```

### Using pydantic models
```py
from pydantic import BaseModel
from pydantic_marshals.contains import assert_contains


class SomeModel(BaseModel):
    id: int
    name: str


def test_pydantic():
    assert_contains(
        model_the_model(),
        SomeModel,
    )
```

### Custom Types
Pydantic allows [custom data types](https://docs.pydantic.dev/2.0/usage/types/custom) via `Annotated`. These are also supported in assert-contains, including pydantic-agnostic variants from [`annotated-types`](https://github.com/annotated-types/annotated-types) and complex checks via [`AfterValidator`](https://docs.pydantic.dev/2.0/usage/types/custom/#adding-validation-and-serialization).
In addition to that, assert-contains offers a few useful [custom-type generators](#type-generators)

```py
from typing import Annotated
from annotated_types import Gt
from pydantic import AfterValidator, Field
from pydantic_marshals.contains import assert_contains


def validate_divisible_by_three(value: int) -> int:
    if value % 3 != 0:
        raise ValueError("value not divisible by three")
    return value  # return is not required, but is "more correct"


def test_custom():
    assert_contains(
        complex_stuff(),
        {
            "t_celsius": Annotated[float, Field(gt=-273.15)],
            "t_fahrenheit": Annotated[float, Gt(-459.67)],
            "times_three": Annotated[int, AfterValidator(validate_divisible_by_three)]
        },
    )
```

## Utils
### Type Generators
#### UnorderedLiteralCollection
```py
from pydantic_marshals.contains import assert_contains, UnorderedLiteralCollection


def test_flags():
    assert_contains(
        collect_flags(),
        UnorderedLiteralCollection({"editable", "deletable"}, check_extra=False),
    )
```
