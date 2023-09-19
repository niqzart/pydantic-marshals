import typing
from collections.abc import Awaitable, Callable, Generator, Iterator
from enum import Enum

import pytest
from pydantic import BaseModel

from pydantic_marshals.base.type_aliases import TypeHint
from tests.unit.conftest import SampleEnum


@pytest.mark.parametrize(
    "type_hint",
    [
        pytest.param(bool, id="type-bool"),
        #
        pytest.param(int, id="type-int"),
        pytest.param(float, id="type-float"),
        #
        pytest.param(bytes, id="type-bytes"),
        pytest.param(str, id="type-str"),
        #
        pytest.param(object, id="type-object"),
        pytest.param(BaseModel, id="type-class"),
        pytest.param(Enum, id="type-enum"),
        #
        pytest.param(None, id="form-none"),
        pytest.param(typing.Any, id="form-any"),
        pytest.param(typing.Literal[0], id="form-literal"),
        #
        pytest.param(typing.Optional[int], id="typing-optional"),  # noqa: NU002
        pytest.param(typing.Union[int, str], id="typing-union"),  # noqa: NU002
        pytest.param(typing.Set[int], id="typing-set"),  # noqa: NU002 PEA001
        pytest.param(typing.List[int], id="typing-list"),  # noqa: NU002 PEA001
        pytest.param(typing.Tuple[int], id="typing-tuple"),  # noqa: NU002 PEA001
        pytest.param(typing.Dict[int, int], id="typing-dict"),  # noqa: NU002 PEA001
        pytest.param(typing.Type[int], id="typing-type"),  # noqa: NU002 PEA001
        #
        pytest.param(int | None, id="pipe-union"),
        pytest.param(set[int], id="generic-set"),
        pytest.param(list[int], id="generic-list"),
        pytest.param(tuple[int], id="generic-tuple"),
        pytest.param(dict[int, int], id="generic-dict"),
        pytest.param(type[int], id="generic-type"),  # type: ignore[index]
        #
        pytest.param(Callable[[int], int], id="collections-callable"),
        pytest.param(Awaitable[int], id="collections-awaitable"),
        pytest.param(Generator[int, int, int], id="collections-generator"),
        pytest.param(Iterator[int], id="collections-iterator"),
    ],
)
def test_correct_type_hits(type_hint: typing.Any) -> None:
    assert isinstance(type_hint, TypeHint)


@pytest.mark.parametrize(
    "type_hint",
    [
        pytest.param(True, id="literal-bool"),  # noqa: WPS425
        #
        pytest.param(1, id="literal-int"),
        pytest.param(1.0, id="literal-float"),
        #
        pytest.param(b"hey", id="literal-bytes"),
        pytest.param("hey", id="literal-str"),
        #
        pytest.param(object(), id="constructed-object"),
        pytest.param(SampleEnum.A, id="enum-element"),
    ],
)
def test_wrong_type_hits(type_hint: typing.Any) -> None:
    assert not isinstance(type_hint, TypeHint)
